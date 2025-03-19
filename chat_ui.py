import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START, END
from sec_tool.market_data_tool import MarketDataTools, FinancialDataTools
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

# Streamlit UI 설정
st.set_page_config(page_title="Multi-Agent Chat", layout="wide")
st.title("Multi-Agent Chat with Streamlit")

# OpenAI LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18")

# 검색 에이전트 설정
news_and_sentiment_retrieval_agent = create_react_agent(
    llm, 
    tools=[MarketDataTools.get_stock_news, MarketDataTools.get_websearch_tool()],
    state_modifier="You are an expert in finding financial news and analyst opinions. Provide facts only, not opinions."
)

# Streamlit 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

def web_search_node(state: MessagesState):
    """웹 검색 에이전트를 실행하는 노드"""
    return news_and_sentiment_retrieval_agent.invoke(state)  # `st.status()` 제거

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

    # StreamlitCallbackHandler를 UI 피드백에 적용
    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=True)

        # ✅ `st.status()`를 graph.invoke() 바깥으로 이동
        with st.status("Processing request...", expanded=True):
            state = MessagesState(messages=st.session_state.messages)
            response = graph.invoke(state)  # ✅ 노드 내부에서 UI 변경 X

        # 상태 업데이트
        st.session_state.messages = response["messages"]
        ui_messages = [msg for msg in st.session_state.messages if not isinstance(msg, ToolMessage)]

        assistant_message = ui_messages[-1]
        st.write(assistant_message.content)  # 응답 출력


