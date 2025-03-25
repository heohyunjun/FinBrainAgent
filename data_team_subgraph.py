
import json
import streamlit as st
import openai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Annotated, Literal, Dict, Callable, TypeVar, Tuple, Type, Generic, Optional, Union, Any
from typing_extensions import TypedDict 

# LangChain 및 LangGraph 관련 라이브러리
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.agents import AgentExecutor

from langgraph.types import Command
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import create_react_agent
from langsmith import utils 
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate


from sec_tool.insider_trade_tool import SECInsiderTradeAPI
from sec_tool.market_data_tool import MarketDataTools, FinancialDataTools, EconomicDataTools

from team_graph.report_team_subgraph import report_graph
from team_graph.general_chat_subgraph import general_graph


# 환경 변수 로드
load_dotenv()
print(utils.tracing_is_enabled())

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class AgentState(MessagesState):
    query: str


llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18")

news_and_sentiment_retrieval_prompt = f"""You are an expert in finding financial news and analyst opinions. 
Provide fact only not opinions
The current time is {current_time}. Use this time when invoking tools that require the current time as an argument."""

# 시장 조사 에이전트
news_and_sentiment_retrieval_agent = create_react_agent(
    llm, 
    tools=[MarketDataTools.get_stock_news, MarketDataTools.get_websearch_tool()],
    prompt=news_and_sentiment_retrieval_prompt
)

def news_and_sentiment_retrieval_node(state: AgentState) -> Command[Literal["data_retrieval_leader"]]:
    """
    금융 뉴스 및 애널리스트 의견 수집

    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        Command: supervisor node로 이동하기 위한 명령을 반환
    """
    # 시장 조사 에이전트를 호출하여 결과를 얻습니다.
    result = news_and_sentiment_retrieval_agent.invoke(state)
    
    # 결과 메시지를 업데이트하고 supervisor node로 이동합니다.
    return Command(
        update={'messages': [HumanMessage(content=result['messages'][-1].content, name='news_and_sentiment_retrieval')]},
        goto='data_retrieval_leader'
    )



stock_research_tools = [MarketDataTools.get_stock_price]
stock_research_agent = create_react_agent(
    llm, tools=stock_research_tools, state_modifier='You are an expert in  market data retrieval. Your mission is to collect stock price information. Provide fact only not opinions'
)


def market_data_retrieval_node(state: AgentState) -> Command[Literal["data_retrieval_leader"]]:
    """
    실시간 주가 및 거래량 수집
    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        Command: supervisor node로 이동하기 위한 명령을 반환
    """
    result = stock_research_agent.invoke(state)

    return Command(
        update={'messages': [HumanMessage(content=result['messages'][-1].content, name='market_data_retrieval')]},
        goto='data_retrieval_leader'
    )

# %%
economic_data_prompt = f"""You are an expert in macroeconomic data retrieval.
Your mission is to collect accurate and up-to-date macroeconomic indicators from reliable sources.
You have access to the following tools: [get_core_cpi_data, get_core_pce_data, get_personal_income_data,get_mortgage_rate_data, get_unemployment_rate_data, get_jobless_claims_data.]
The current time is {current_time}. Use this time when invoking tools that require the current time as an argument.
Provide factual data only, without interpretation or opinion."""

economic_data_retrieval_tools = [EconomicDataTools.get_core_cpi_data]
economic_data_retrieval_agent = create_react_agent(
    llm, tools=economic_data_retrieval_tools, prompt=economic_data_prompt)

def economic_data_retrieval_node(state: AgentState) -> Command[Literal["data_retrieval_leader"]]:
    """
    거시경제 데이터(GDP, 금리, 인플레이션) 수집
    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        Command: supervisor node로 이동하기 위한 명령을 반환
    """
    result = economic_data_retrieval_agent.invoke(state)

    return Command(
        update={'messages': [HumanMessage(content=result['messages'][-1].content, name='economic_data_retrieval')]},
        goto='data_retrieval_leader'
    )

financial_statement_retrieval_tools = [FinancialDataTools.get_income_statement, FinancialDataTools.get_financial_event_filings]

# 단일 에이전트 정의
financial_statement_retrieval_agent = create_react_agent(
    llm,
    tools=financial_statement_retrieval_tools,
    state_modifier='You are an expert in collecting corporate financial statements and performance data. Provide facts only, no opinions.'
)

def financial_statement_retrieval_node(state: AgentState) -> Command[Literal["data_retrieval_leader"]]:
    """
    회사 재무 보고서와 주요 사건 관련 자료를 조사하는 노드.
    손익계산서 데이터와 재무 및 주요 사건 관련 SEC 보고서를 처리합니다.

    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        Command: supervisor 노드로 이동하기 위한 명령을 반환
    """
    result = financial_statement_retrieval_agent.invoke(state)
    return Command(
        update={'messages': [HumanMessage(content=result['messages'][-1].content, name='financial_statement_retrieval')]},
        goto='data_retrieval_leader'
    )



insider_tracker_system_prompt = f"""You are an insider trading analyst.
You must provide factual data only, without any personal opinions or speculations.
The current time is {current_time}. Use this time when invoking tools that require the current time as an argument."""


insider_tracker_research_tools = [SECInsiderTradeAPI.fetch_filings]
insider_tracker_research_agent = create_react_agent(
    llm, tools=insider_tracker_research_tools, prompt=insider_tracker_system_prompt
)



def insider_tracker_research_node(state: AgentState) -> Command[Literal["data_retrieval_leader"]]:
    """
    내부자 거래 내역 조사 node 
    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        Command: supervisor node로 이동하기 위한 명령을 반환
    """
    result = insider_tracker_research_agent.invoke(state)

    return Command(
        update={'messages': [HumanMessage(content=result['messages'][-1].content, name='insider_tracker_research')]},
        goto='data_retrieval_leader'
    )




data_retrieval_team_members = [
    "news_and_sentiment_retrieval", "market_data_retrieval", 
    "financial_statement_retrieval","insider_tracker_research",
    "economic_data_retrieval"
    ]
data_retrieval_options_for_next = data_retrieval_team_members + ["FINISH"]

data_retrieval_leader_system_prompt = (
    "You are a supervisor tasked with managing a conversation between the following specialized workers: {members}.\n"
    "Each worker handles specific tasks:\n"
    "- news_and_sentiment_retrieval: Handles news articles, market trends, general industry updates.\n"
    "- market_data_retrieval: Handles current stock prices\n"
    "- financial_statement_retrieval: Handles income statements, financial statements, and SEC filings.\n"
    "- insider_tracker_research: Handles insider trading filings and insider transactions.\n"
    "- economic_data_retrieval: Handles macroeconomic data\n"
    "Given the user request, strictly select ONLY ONE most suitable worker to act next based on the task description above. "
    "When finished, respond with FINISH."
)



# ChatPromptTemplate 생성
data_retrieval_leader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", data_retrieval_leader_system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, who should act next? "
            "Or should we FINISH? Select one of: {options}",
        ),
    ]
).partial(options=str(data_retrieval_options_for_next), members=", ".join(data_retrieval_team_members))


class DataTeamRouter(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*data_retrieval_options_for_next]



def data_retrieval_leader_node(state: AgentState) -> Command[Literal[*data_retrieval_team_members, "data_cleansing"]]:
    """
    supervisor node 
    주어진 State를 기반으로 각 worker의 결과를 종합하고,
    다음에 수행할 worker를 결정
    모든 작업이 완료되면 data_cleansing node로 이동

    Args:
        state (AgentState): 현재 메시지 상태를 나타내는 객체

    Returns:
        Command: 다음에 수행할 worker 또는 data_cleansing node로 이동하기 위한 명령 반환 
    """

    data_retrieval_team_chain = data_retrieval_leader_prompt | llm.with_structured_output(DataTeamRouter)
    response= data_retrieval_team_chain.invoke(state)

    goto = response["next"]
    if goto == "FINISH":
        goto = "data_cleansing"

    return Command(goto=goto)


data_cleansing_system_prompt = (
    "You are a data cleansing agent responsible for refining raw data collected by the data team. "
    "Your role is to process the collected data to ensure it directly addresses the user's original question. "
    "Your tasks are: "
    "- Remove irrelevant or redundant information that does not help answer the user's question. "
    "- Fix inconsistencies (e.g., missing values, incorrect formats) to make the data usable. "
    "- Structure the data in a concise, clear format tailored to the user's request. "
    "Provide only factual, cleaned data without opinions or speculations. ")

# ChatPromptTemplate 생성
data_cleansing_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", data_cleansing_system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, "
            "Refine and process this data to align with the user's original question : {query}"
        )
    ]
)


def data_cleansing_node(state: AgentState) -> Command[Literal["supervisor"]]:
    """
    데이터 클렌징 노드. 수집된 데이터를 정제하여 supervisor로 전달

    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        dict: 분석 결과 메시지를 포함하는 딕셔너리를 반환
    """

    class CleanedData(BaseModel):
        relevant_data: str = Field(
            ..., description="사용자의 질문과 직접 연관이 있고, 중복 및 불필요한 정보가 제거된 정제된 데이터"
        )

    query = state['query']
    cleaning_chain = data_cleansing_prompt | llm.with_structured_output(CleanedData)
    result = cleaning_chain.invoke({"messages" : state['messages'], "query" : query})

    return Command(
        update={'messages': [HumanMessage(content=result.relevant_data, name='data_cleansing')]},
        goto='supervisor'
    )

# %%
supervisor_members = ["data_retrieval_leader", "general_team_leader"]
supervisor_options_for_next = supervisor_members + ["FINISH"]

supervisor_system_prompt = (
    "You are a supervisor tasked with managing a conversation between the following specialized workers: {members}.\n"
    "Each worker handles specific tasks:\n"
    "- 'data_team_leader':  role is responsible for collecting and refining the data required to answer user questions.\n"
    "- 'general_team_leader': role is responsible for handling general knowledge questions outside finance or investing.\n"
    "Given the user request, strictly select ONLY ONE most suitable worker to act next based on the task description above. "
    "When finished, respond with FINISH."
)



# ChatPromptTemplate 생성
supervisor_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", supervisor_system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, who should act next? "
            "Or should we FINISH? Select one of: {options}",
        ),
    ]
).partial(options=str(supervisor_options_for_next), members=", ".join(supervisor_members))


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*supervisor_options_for_next]



def supervisor_node(state: AgentState) -> Command[Literal[*supervisor_members, "reporter"]]:
    """
    supervisor node 
    주어진 State를 기반으로 각 worker의 결과를 종합하고,
    다음에 수행할 worker를 결정
    모든 작업이 완료되면 analyst node로 이동

    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        Command: 다음에 수행할 worker 또는 analyst node로 이동하기 위한 명령 반환 
    """

    supervisor_chain = supervisor_prompt | llm.with_structured_output(Router)
    response= supervisor_chain.invoke(state)

    goto = response["next"]
    if goto == "FINISH":
        goto = "reporter"

    return Command(goto=goto)


graph_builder = StateGraph(AgentState)

graph_builder.add_node("supervisor", supervisor_node)
graph_builder.add_node("news_and_sentiment_retrieval", news_and_sentiment_retrieval_node)
graph_builder.add_node("market_data_retrieval", market_data_retrieval_node)
graph_builder.add_node("financial_statement_retrieval", financial_statement_retrieval_node)
graph_builder.add_node("insider_tracker_research", insider_tracker_research_node)
graph_builder.add_node("data_retrieval_leader", data_retrieval_leader_node)
graph_builder.add_node("data_cleansing", data_cleansing_node)
graph_builder.add_node("economic_data_retrieval", economic_data_retrieval_node)
graph_builder.add_node("reporter", report_graph)
graph_builder.add_node("general_team_leader", general_graph)

graph_builder.add_edge(START, "supervisor")
graph_builder.add_edge("reporter", END)
graph_builder.add_edge("general_team_leader", END)
graph = graph_builder.compile()

