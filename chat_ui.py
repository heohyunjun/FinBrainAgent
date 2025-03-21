import uuid  

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START, END
from sec_tool.market_data_tool import MarketDataTools, FinancialDataTools
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler


# Streamlit UI 설정
st.set_page_config(page_title="FinBrain", layout="wide")
st.title("FinBrain")

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

# OpenAI LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18")

# 검색 에이전트 설정
news_and_sentiment_retrieval_agent = create_react_agent(
    llm,
    tools=[MarketDataTools.get_stock_news, MarketDataTools.get_websearch_tool()],
    state_modifier="You are an expert in finding financial news and analyst opinions. Provide facts only, not opinions."
)

def web_search_node(state: MessagesState):
    """웹 검색 에이전트를 실행하는 노드"""
    return news_and_sentiment_retrieval_agent.invoke(state)

# LangGraph 상태 그래프 구성
builder = StateGraph(MessagesState)
builder.add_node("web_search", web_search_node)
builder.add_edge(START, "web_search")
builder.add_edge("web_search", END)

graph = builder.compile()

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
            state = MessagesState(messages=st.session_state.messages)
            response = graph.invoke(state)

        st.session_state.messages = response["messages"]
        ui_messages = [msg for msg in st.session_state.messages if not isinstance(msg, ToolMessage)]

        assistant_message = ui_messages[-1]
        st.write(assistant_message.content)  # 응답 출력