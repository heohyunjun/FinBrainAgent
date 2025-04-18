import os
import logging
import json
from datetime import datetime
from uuid import uuid4
from typing import Annotated, Optional, List
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from langchain_core.messages import HumanMessage, AnyMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages

from langchain_mcp_adapters.client import MultiServerMCPClient
from utils.mcp_tool_mapping import bind_agent_tools
from agents.agent_library import agent_configs
from main_graph import build_graph
import time
import asyncio
import platform

# if platform.system() == "Windows":
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()

# =======================
# 로그 설정
# =======================
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
log_path = os.path.join(log_dir, f"{today}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_path, encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)

# =======================
# FastAPI Lifespan 설정
# =======================
@asynccontextmanager
async def lifespan(app: FastAPI):
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    config_path = "mcp_config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = json.load(f)
        mcp_config = raw_config.get("mcpServers", {})
        
    else:
        mcp_config = {}

    client = MultiServerMCPClient(mcp_config)
    await client.__aenter__()
    print(2222222222)
    app.state.mcp_client = client

    app.state.mcp_tools = client.get_tools()
    
    logger.info(f"MCP 도구 {len(app.state.mcp_tools)}개 로드됨")


    resolved_configs = bind_agent_tools(agent_configs, app.state.mcp_tools)
    app.state.main_graph = build_graph(resolved_configs)
    logger.info("LangGraph 초기화 완료")

    yield  # 앱 실행 시작

    # 종료 처리
    client = getattr(app.state, "mcp_client", None)
    if client:
        await client.__aexit__(None, None, None)
        logger.info("🧹 MCP 클라이언트 종료 완료")

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