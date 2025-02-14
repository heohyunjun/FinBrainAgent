# 표준 라이브러리
import os
import requests
from IPython.display import Image, display
# 서드파티 라이브러리
import streamlit as st
import openai
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import TypedDict, List, Annotated, Literal, Dict

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

from agents.agent_library import agent_configs, AgentConfig

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
    next: str

# make_supervisor_node 함수 정의
def make_supervisor_node(
        MODEL_NAME: str, 
        members: List[str], 
        system_prompt: str) -> str:
    
    options_for_next  = ["FINISH"] + members

    # 구조화된 응답 스키마 정의 (Python 3.11 이상의 Literal unpacking 사용)
    class Router(TypedDict):
        next: Literal[*options_for_next ]

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
    def __init__(self, model_name: str, agent_configs: Dict[str, AgentConfig]):
        self.llm = ChatGroq(model=model_name, temperature=0)
        self.agent_configs = agent_configs  # 설정 파일 저장

    def create_agent(self, config: AgentConfig):
        """AgentConfig 타입을 받아서 에이전트 생성"""
        return create_react_agent(self.llm, tools=config["tools"], prompt=config.get("prompt"))

    def create_agent_node(self, agent, name: str):
        return self._agent_node_function(agent, name)

    def _agent_node_function(self, agent, name: str):
        def agent_node(state: FinanceState):
            result = agent.invoke(state)
            return Command(
                update={
                    "messages": [
                        HumanMessage(content=result["messages"][-1].content, name=name)
                    ]
                },
                goto="director",  
            )
        return agent_node

    def create_agent_and_node(self, name: str):
        """
        :param name: agent_configs에서 찾을 에이전트 이름
        :return: (생성된 agent, 생성된 node)
        """
        if name not in self.agent_configs:
            raise ValueError(f"'{name}'설정을 찾을 수 없습니다. (config에 존재하는 키 확인 필요)")

        each_agent_config = self.agent_configs[name]
        each_agent = self.create_agent(each_agent_config)
        each_node = self.create_agent_node(each_agent, name)
        return each_agent, each_node  


# 각 Supervisor 노드가 호출할 에이전트 노드 리스트 정의
team_node_list = ["data_team", "financial_team", "reporter_team"]

data_agent_agent_node_list = ["data_retrieval", "data_cleaning"]
financial_agent_node_list = ["news_sentiment", "market_trend", "investment_strategy"]
reporter_agent_node_list = ["report_generation", "summary_extraction"]

# 각 Suppervisor 노드가 사용할 프롬프트트
director_system_prompt = f""" \n
    You are a director tasked with managing a conversation between the \n
    following workers: {team_node_list}. Given the following user request,\n
    respond with the worker to act next. Each worker will perform a \n
    task and respond with their results and status. When finished, \n
    respond with FINISH. """

# 각 Supervisor 노드 정의
director_agent_node = make_supervisor_node(MODEL_NAME, team_node_list, director_system_prompt)

# 팩토리 인스턴스 생성
agent_maker = AgentMaker(model_name=MODEL_NAME, agent_configs=agent_configs)

# 에이전트, 노드 생성 
data_team_agent, data_team_node = agent_maker.create_agent_and_node(name="data_team")
financial_team_agent, financial_team_node = agent_maker.create_agent_and_node(name="financial_team")
reporter_team_agent, reporter_team_node = agent_maker.create_agent_and_node(name="reporter_team")

# 워크플로우
finance_builder = StateGraph(FinanceState)
finance_builder.add_node("director", director_agent_node)
finance_builder.add_node("data_team", data_team_node)
finance_builder.add_node("financial_team", financial_team_node)
finance_builder.add_node("reporter_team", reporter_team_node)

finance_builder.add_edge(START, "director")
finance_graph = finance_builder.compile()


# def main():
#     st.title("투자Agent")

#     symbol = st.text_input("종목 심볼", "TSLA")
#     user_question = st.text_input("질문", "테슬라가 무역분쟁의 영향을 받는 이유가 뭘까?")

#     if st.button("답변 받기"):
#         # A) 분류 수행

#         st.markdown("**[최종 답변]**")
#         st.write(user_question)

# if __name__ == "__main__":
#     main()
