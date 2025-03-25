import os 
import uuid  
from dotenv import load_dotenv

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import MessagesState
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

from utils.st_auth import check_token_auth
from data_team_subgraph import graph as main_graph

load_dotenv() 

openai_api_key = os.getenv("OPENAI_API_KEY")

class AgentState(MessagesState):
    query: str

# Streamlit UI 설정
st.set_page_config(page_title="FinBrain", layout="wide")
st.title("FinBrain - AI 금융 어드바이저")

token = check_token_auth()

st.markdown("""
    <style>
    /* 오른쪽 상단의 상태 표시 숨기기 */
    [data-testid="stStatusWidget"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 채팅 히스토리 저장용 세션 상태 초기화
if "history" not in st.session_state:
    st.session_state.history = []  # 리스트 형식으로 저장

if "messages" not in st.session_state:
    st.session_state.messages = []  # 현재 진행 중인 채팅 저장

if "load_chat" not in st.session_state:
    st.session_state.load_chat = None  # 현재 로드된 채팅 ID 저장

# 새 채팅 버튼 클릭 시, 현재 대화가 새 채팅이면 저장하고 기존 채팅이면 업데이트
with st.sidebar:
    if st.button("새 채팅"):
        if st.session_state.messages:
            first_user_message = next(
                (msg.content for msg in st.session_state.messages if isinstance(msg, HumanMessage)), 
                "New Chat"
            )  # 첫 번째 사용자 질문을 제목으로 설정

            if st.session_state.load_chat is None:
                # 완전히 새로운 채팅인 경우만 저장
                chat_entry = {
                    "id": str(uuid.uuid4()),  # 고유한 ID 생성
                    "title": first_user_message,
                    "messages": st.session_state.messages,
                }
                st.session_state.history.insert(0, chat_entry)  # 최신 채팅을 위쪽에 추가
            else:
                # 기존 채팅을 이어 한 경우, 고유한 ID로 히스토리를 업데이트
                for chat in st.session_state.history:
                    if chat["id"] == st.session_state.load_chat:  # ID 기반 비교
                        chat["messages"] = st.session_state.messages  # 기존 기록 업데이트
                        break

        # 새 채팅 시작 (기존 세션 초기화)
        st.session_state.messages = []
        st.session_state.load_chat = None  # 새 채팅이므로 로드된 채팅 해제
        st.rerun()  # 새로고침

    # 사이드바에 채팅 기록 리스트 표시
    st.markdown("### 채팅 기록")
    for idx, chat in enumerate(st.session_state.history):
        if st.button(f"{chat['title']}", key=f"chat_{idx}"):
            st.session_state.load_chat = chat["id"]  # ID 저장
            st.session_state.messages = chat["messages"]
            st.rerun()  # 즉시 채팅 불러오기


def get_role(message):
    """메시지 역할 변환"""
    if isinstance(message, AIMessage):
        return "assistant"
    elif isinstance(message, HumanMessage):
        return "user"
    return "system"

# 기존 대화 기록 표시
for message in st.session_state.messages:
    if isinstance(message, ToolMessage):
        continue
    with st.chat_message(get_role(message)):
        st.write(message.content)

# 사용자 입력 받기
query = st.chat_input("검색할 내용을 입력하세요:")

if query:
    user_message = HumanMessage(content=query)
    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=True)

        # `st.status()`를 graph.invoke() 바깥으로 이동
        with st.status("Processing request...", expanded=True):
            latest_question = query.strip()
            state = AgentState(messages=st.session_state.messages, query=latest_question)
            response = main_graph.invoke(state)

        st.session_state.messages = response["messages"]
        ui_messages = [msg for msg in st.session_state.messages if not isinstance(msg, ToolMessage)]

        assistant_message = ui_messages[-1]
        st.write(assistant_message.content)  # 응답 출력