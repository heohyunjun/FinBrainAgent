import os 
import uuid  
from dotenv import load_dotenv

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import MessagesState
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

from utils.st_utils import check_token_auth, get_role
from data_team_subgraph import graph as main_graph

load_dotenv() 

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
    st.session_state.history = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []  # UI 표시용: (role, content) 튜플 리스트

if "load_chat" not in st.session_state:
    st.session_state.load_chat = None

# 새 채팅 버튼 클릭 시 처리
with st.sidebar:
    if st.button("새 채팅"):
        if st.session_state.messages:
            first_user_message = next(
                (msg.content for msg in st.session_state.messages if isinstance(msg, HumanMessage)), 
                "New Chat"
            )
            if st.session_state.load_chat is None:
                chat_entry = {
                    "id": str(uuid.uuid4()),
                    "title": first_user_message,
                    "messages": st.session_state.messages,
                    "chat_messages": st.session_state.chat_messages,  # UI 메시지도 저장
                }
                st.session_state.history.insert(0, chat_entry)
            else:
                for chat in st.session_state.history:
                    if chat["id"] == st.session_state.load_chat:
                        chat["messages"] = st.session_state.messages
                        chat["chat_messages"] = st.session_state.chat_messages
                        break
        st.session_state.messages = []
        st.session_state.chat_messages = []
        st.session_state.load_chat = None
        st.rerun()

    st.markdown("### 채팅 기록")
    for idx, chat in enumerate(st.session_state.history):
        if st.button(f"{chat['title']}", key=f"chat_{idx}"):
            st.session_state.load_chat = chat["id"]
            st.session_state.messages = chat["messages"]
            st.session_state.chat_messages = chat["chat_messages"]
            st.rerun()


# 기존 채팅 메시지 표시
for role, content in st.session_state.chat_messages:
    with st.chat_message(role):
        st.write(content)

# 사용자 입력 받기
query = st.chat_input("검색할 내용을 입력하세요:")

if query:
    # 사용자 메시지 즉시 표시 및 상태에 추가
    with st.chat_message("user"):
        st.write(query)
    st.session_state.messages.append(HumanMessage(content=query))
    st.session_state.chat_messages.append(("user", query))

    # AI 응답 생성 및 표시
    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=True)
        with st.status("Processing request...", expanded=True):
            latest_question = query.strip()
            state = AgentState(messages=st.session_state.messages, query=latest_question)
            response = main_graph.invoke(state)

            # LangGraph 상태 업데이트
            st.session_state.messages = response["messages"]

            # UI용 메시지 추출 (ToolMessage 제외)
            assistant_content = response["messages"][-1].content
            st.session_state.chat_messages.append(("assistant", assistant_content))

        st.write(assistant_content)