import os
import asyncio
from datetime import datetime
from uuid import uuid4
from typing import Annotated, List
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp_agent.mcp.mcp_agent_client_session import MCPAgentClientSession
from mcp_agent.mcp.mcp_connection_manager import MCPConnectionManager

from utils.mcp_loaders import get_server_registry
from langchain_core.messages import HumanMessage, AnyMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from utils.mcp_tool_mapping import bind_agent_tools, load_mcp_config, get_mcp_tool_name
from mcp_agent.core.exceptions import ServerInitializationError
from agents.agent_library import agent_configs

from utils.logger import logger
from routers.v1 import reports
from schemas.report import UserInput
from main_graph import build_graph

load_dotenv()

async def mcp_watchdog_task(app: FastAPI, interval: int = 180):
    logger.info("[Watchdog] 워치독 태스크 시작")
    while True:
        logger.debug(f"[Watchdog] 루프 시작: {datetime.now().isoformat()}")
        # 서버 목록 복사 (루프 중 변경될 수 있으므로)
        try:
            server_names = list(app.state.mcp_manager.server_registry.registry.keys())
        except Exception as e:
             logger.error(f"[Watchdog] 서버 목록 로드 실패: {e}", exc_info=True)
             await asyncio.sleep(interval) # 다음 주기에 다시 시도
             continue

        for name in server_names:
            logger.debug(f"[Watchdog] 서버 '{name}' 점검 중")
            server_conn = None
            try:
                server_conn = await app.state.mcp_manager.get_server(
                    name, client_session_factory=MCPAgentClientSession
                )

                try:
                    ping_timeout = app.state.mcp_manager.server_registry.registry[name].read_timeout_seconds or 10.0
                    await asyncio.wait_for(server_conn.session.send_ping(), timeout=ping_timeout)
                    logger.info(f"[Watchdog] MCP 서버 '{name}' 정상 작동 중 (ping 성공)")

                except asyncio.TimeoutError:
                    logger.warning(f"[Watchdog] MCP 서버 '{name}' ping 타임아웃. 연결 해제 요청.")

                    await app.state.mcp_manager.disconnect_server(name)
                except Exception as ping_err:
                    logger.warning(f"[Watchdog] MCP 서버 '{name}' ping 실패 ({type(ping_err).__name__}): {ping_err}. 연결 해제 요청.")
                    await app.state.mcp_manager.disconnect_server(name)

            except ServerInitializationError as init_err:
                logger.warning(f"[Watchdog] MCP 서버 '{name}' 초기화/연결 실패: {init_err}")

            except Exception as get_server_err:
                logger.error(f"[Watchdog] MCP 서버 '{name}' 점검 중 예상치 못한 오류: {get_server_err}", exc_info=True)
                try:
                    if name in app.state.mcp_manager.running_servers:
                         await app.state.mcp_manager.disconnect_server(name)
                except Exception as disconnect_err:
                     logger.error(f"[Watchdog] 오류 발생한 서버 '{name}' 연결 해제 중 추가 오류: {disconnect_err}", exc_info=True)

        logger.debug(f"[Watchdog] 루프 종료: {datetime.now().isoformat()}")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Server Start")

        # DB 
        database_url = os.getenv("DATABASE_URL")
        engine = create_async_engine(database_url, echo=False, future=True)
        app.state.engine = engine 

        # MCP 서버 레지스트리 로드
        server_registry = get_server_registry()
        manager = MCPConnectionManager(server_registry)
        await manager.__aenter__()
        app.state.mcp_manager = manager

        # MCP 서버 연결 및 초기화
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

        # LangGraph 초기화
        resolved_configs = bind_agent_tools(agent_configs, app.state.mcp_tools)
        app.state.main_graph = build_graph(resolved_configs)
        logger.info("LangGraph 초기화 완료")

        # 리포트 preload + 24시간마다 refresh task 시작
        report_refresh_task = asyncio.create_task(reports.preload_and_schedule_refresh(app))
        app.state.report_refresh_task = report_refresh_task
        logger.info("리포트 preload + 주기적 refresh Task 시작")

    #    # 4. MCP Watchdog 비동기 태스크 시작
    #     watchdog_task = asyncio.create_task(mcp_watchdog_task(app))
    #     app.state.watchdog_task = watchdog_task
    #     logger.info("MCP Watchdog 시작")

    except Exception as e:
        logger.error(f"MCP 시스템 초기화 실패: {e}")
        app.state.mcp_tools = []
        app.state.main_graph = None

    yield

    # 서버 종료 정리
    if hasattr(app.state, "report_refresh_task"):
        app.state.report_refresh_task.cancel()
        try:
            await app.state.report_refresh_task
        except asyncio.CancelledError:
            logger.info("리포트 preload+refresh Task 종료 완료")

    # # 종료 시 MCP 연결 정리
    # if hasattr(app.state, "mcp_watchdog_task"):
    #     app.state.mcp_watchdog_task.cancel()
    #     await asyncio.gather(app.state.mcp_watchdog_task, return_exceptions=True)
    #     logger.info("MCP Watchdog 종료")

    if hasattr(app.state, "mcp_manager") and app.state.mcp_manager:
        await app.state.mcp_manager.__aexit__(None, None, None)
        logger.info("MCPConnectionManager 종료 완료")

    if hasattr(app.state, "engine"):
        await app.state.engine.dispose()
        logger.info("DB 연결 풀 종료 완료")

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
app.include_router(reports.router, prefix="/v1")


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
    


