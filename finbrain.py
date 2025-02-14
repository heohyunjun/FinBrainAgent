# 표준 라이브러리
import os
import requests

# 서드파티 라이브러리
import streamlit as st
import openai
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import TypedDict, List, Annotated, Literal

# LangChain 및 LangGraph 관련 라이브러리
from langchain_openai import OpenAI
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

# LangGraph 관련 라이브러리
from langgraph.types import Command
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import create_react_agent


# 환경 변수 로드
load_dotenv()

# 환경 변수에서 키 가져오기
openai_api_key = os.getenv("OPENAI_API_KEY")
alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

MODEL_NAME = "gemma2-9b-it"

# State 정의
class FinanceState(TypedDict):
    messages: Annotated[list, add_messages]


# make_supervisor_node 함수 정의
def make_supervisor_node(
        MODEL_NAME: str, 
        members: List[str], 
        system_prompt: str) -> str:
    
    options_for_next  = ["FINISH"] + members

    # 구조화된 응답 스키마 정의 (Python 3.11 이상의 Literal unpacking 사용)
    class Router(TypedDict):
        next: Literal["FINISH", *options_for_next ]

    def supervisor_node(state: FinanceState) -> Command[Literal[*options_for_next, "__end__"]]:
        # system_prompt를 메시지 맨 앞에 추가한 후, 상태에 저장된 메시지와 결합
        messages = [{"role": "system", "content": system_prompt}] + state["messages"]
        
        llm = ChatGroq(
            model=MODEL_NAME, temperature=0,
            max_tokens=None, timeout=None,
            max_retries=2,
        )

        # LLM 호출하여 구조화된 응답 획득
        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END
        return Command(goto=goto, update={"next": goto})
    
    return supervisor_node
class AgentMaker:
    def __init__(self, model_name: str):
        self.llm = ChatGroq(model=model_name, temperature=0)

    def create_agent(self, tools: List, prompt: str = None):
        return create_react_agent(self.llm, tools=tools, prompt=prompt)

    def create_agent_node(self, agent, name: str):
        return self._agent_node_function(agent, name)

    def _agent_node_function(self, agent, name: str):
        def agent_node(state):
            result = agent.invoke(state)
            return {
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name=name)
                ]
            }
        return agent_node



# 각 Supervisor 노드가 호출할 에이전트 노드 리스트 정의
data_agent_agent_node_list = ["data_retrieval", "data_cleaning"]
financial_agent_node_list = ["news_sentiment", "market_trend", "investment_strategy"]
reporter_agent_node_list = ["report_generation", "summary_extraction"]

# 각 Suppervisor 노드가 사용할 프롬프트트
data_system_prompt = """ \n
    You are a supervisor tasked with managing a conversation between the \n
    following workers: data_retrieval, data_cleaning. Given the following user request,\n
    respond with the worker to act next. Each worker will perform a \n
    task and respond with their results and status. When finished, \n
    respond with FINISH. """

financial_system_prompt = """ \n
    You are a supervisor tasked with managing a conversation between the \n
    following workers: data_retrieval, data_cleaning. Given the following user request,\n
    respond with the worker to act next. Each worker will perform a \n
    task and respond with their results and status. When finished, \n
    respond with FINISH. """

reporter_system_prompt = """ \n
    You are a supervisor tasked with managing a conversation between the \n
    following workers: data_retrieval, data_cleaning. Given the following user request,\n
    respond with the worker to act next. Each worker will perform a \n
    task and respond with their results and status. When finished, \n
    respond with FINISH. """

# 각 Supervisor 노드 정의
data_supervisor_node = make_supervisor_node(MODEL_NAME, data_agent_agent_node_list, data_system_prompt)
financial_supervisor_node = make_supervisor_node(MODEL_NAME, financial_agent_node_list, financial_system_prompt)
reporter_supervisor_node = make_supervisor_node(MODEL_NAME, reporter_agent_node_list, reporter_system_prompt)


# 팩토리 인스턴스 생성
agent_maker = AgentMaker(model_name=MODEL_NAME)




def main():
    st.title("투자Agent")

    symbol = st.text_input("종목 심볼", "TSLA")
    user_question = st.text_input("질문", "테슬라가 무역분쟁의 영향을 받는 이유가 뭘까?")

    if st.button("답변 받기"):
        # A) 분류 수행

        st.markdown("**[최종 답변]**")
        st.write(user_question)

if __name__ == "__main__":
    main()
