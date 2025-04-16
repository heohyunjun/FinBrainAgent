import os
import logging
from datetime import datetime
from uuid import uuid4
from typing import Annotated, Optional, List

from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from langchain_core.messages import HumanMessage, AnyMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages

from data_team_subgraph import graph as main_graph

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
# FastAPI 설정
# =======================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
# PI 엔드포인트
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
        response = await main_graph.ainvoke(state, config=config)

        if not response.get("messages"):
            raise ValueError("LangGraph 응답에 메시지가 없습니다.")

        ai_msg = response["messages"][-1]
        assistant_content = ai_msg.content

        memory_store[thread_id] = prev_messages + [human_msg, ai_msg]

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
