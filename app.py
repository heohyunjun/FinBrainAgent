import os
import logging
import json
from datetime import datetime
from uuid import uuid4
from typing import Annotated, Optional, List
from contextlib import asynccontextmanager
import time
import asyncio
import platform


from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mcp_agent.mcp.mcp_agent_client_session import MCPAgentClientSession
from mcp_agent.mcp.mcp_connection_manager import MCPConnectionManager

from utils.mcp_loaders import get_server_registry
from langchain_core.messages import HumanMessage, AnyMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from utils.mcp_tool_mapping import bind_agent_tools, load_mcp_config, get_mcp_tool_name

from agents.agent_library import agent_configs

from utils.logger import logger
from main_graph import build_graph

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Server Start")

        # 1. MCP 서버 레지스트리 로드
        server_registry = get_server_registry()
        manager = MCPConnectionManager(server_registry)
        await manager.__aenter__()

        app.state.mcp_manager = manager

        # 2. MCP 서버 연결 및 초기화
        all_tools = []
        for name in server_registry.registry:
            try:
                server = await manager.get_server(name, client_session_factory=MCPAgentClientSession)
                tools = await load_mcp_tools(server.session)  
                all_tools.extend(tools)

                logger.info(f"[MCP] '{name}' 도구 로드됨: {get_mcp_tool_name(tools)}")
            except Exception as e:
                logger.warning(f"[MCP] '{name}' 연결 실패: {e}")


        app.state.mcp_tools = all_tools

        logger.info(f"MCP 전체 도구 목록: {get_mcp_tool_name(app.state.mcp_tools)}")

        # 3. LangGraph 초기화
        resolved_configs = bind_agent_tools(agent_configs, app.state.mcp_tools)
        app.state.main_graph = build_graph(resolved_configs)
        logger.info("LangGraph 초기화 완료")

    except Exception as e:
        logger.error(f"MCP 시스템 초기화 실패: {e}")
        app.state.mcp_tools = []
        app.state.main_graph = None

    yield

    # 종료 시 MCP 연결 정리
    if hasattr(app.state, "mcp_manager") and app.state.mcp_manager:
        await app.state.mcp_manager.__aexit__(None, None, None)
        logger.info("MCPConnectionManager 종료 완료")


# =======================
# FastAPI 앱 인스턴스 생성
# =======================
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN")],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================
# 데이터 구조
# =======================
class UserInput(BaseModel):
    message: str
    thread_id: Optional[str] = None

class AgentState(BaseModel):
    query: str
    messages: Annotated[List[AnyMessage], add_messages]

# 메모리 저장소
memory_store = {}  # key: thread_id, value: List[BaseMessage]

# =======================
# API 엔드포인트
# =======================
@app.post("/chat")
async def handle_chat(request: UserInput):
    user_message = request.message
    thread_id = request.thread_id or str(uuid4())
    config = RunnableConfig(configurable={"thread_id": thread_id})

    logger.info(f"수신된 메시지: {user_message}")
    logger.info(f"thread_id: {thread_id}")

    prev_messages = memory_store.get(thread_id, [])
    human_msg = HumanMessage(content=user_message)

    state = AgentState(
        query=user_message,
        messages=prev_messages + [human_msg]
    )

    try:
        graph = app.state.main_graph
        response = await graph.ainvoke(state, config=config)

        if not response.get("messages"):
            raise ValueError("LangGraph 응답에 메시지가 없습니다.")

        ai_msg = response["messages"][-1]
        assistant_content = ai_msg.content

        memory_store[thread_id] = prev_messages + [human_msg, HumanMessage(content=assistant_content)]

        logger.info(f"LangGraph 응답 생성 완료: {assistant_content}")

        return {
            "thread_id": thread_id,
            "response": assistant_content,
            "status": "ok",
            "error_message": None
        }

    except Exception as e:
        memory_store[thread_id] = prev_messages + [human_msg]
        assistant_content = "AI 응답을 생성하지 못했습니다. 잠시 후 다시 시도해주세요."
        logger.error(f"LangGraph 실행 중 예외 발생: {e}")

        return {
            "thread_id": thread_id,
            "response": assistant_content,
            "status": "error",
            "error_message": str(e)
        }