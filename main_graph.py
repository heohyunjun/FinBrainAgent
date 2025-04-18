from typing import Literal
from typing_extensions import TypedDict 
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

from team_graph.report_team_graph import report_graph
from team_graph.general_team_graph import general_graph
from team_graph.insider_team_graph import insider_graph 
from team_graph.analyst_team_graph import analyst_graph
from utils.logger import logger

# Agent 상태 정의
class AgentState(MessagesState):
    query: str

# 메모리 초기화
memory = MemorySaver()

# LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18")
data_team_leader_llm  = ChatOpenAI(model="gpt-4o-mini-2024-07-18")

def build_graph(resolved_agent_configs: dict) -> StateGraph:
    # MCP 포함 agent 생성

    logger.info(resolved_agent_configs['news_and_sentiment_retrieval_agent']['tools'])
    news_and_sentiment_retrieval_agent = create_react_agent(
        llm, 
        tools=resolved_agent_configs['news_and_sentiment_retrieval_agent']['tools'],
        prompt=resolved_agent_configs['news_and_sentiment_retrieval_agent']['prompt']
    )

    market_data_retrieval_agent = create_react_agent(
        llm, 
        tools=resolved_agent_configs['market_data_retrieval_agent']['tools'], 
        prompt=resolved_agent_configs['market_data_retrieval_agent']['prompt']
    )

    economic_data_retrieval_agent = create_react_agent(
        llm, 
        tools=resolved_agent_configs['economic_data_retrieval_agent']['tools'], 
        prompt=resolved_agent_configs['economic_data_retrieval_agent']['prompt']
    )

    financial_statement_retrieval_agent = create_react_agent(
        llm,
        tools=resolved_agent_configs['financial_statement_retrieval_agent']['tools'],
        prompt=resolved_agent_configs['financial_statement_retrieval_agent']['prompt']
    )

    data_retrieval_team_members = resolved_agent_configs['data_retrieval_leader_agent']['members']
    data_retrieval_options_for_next = data_retrieval_team_members + ["FINISH"]
    data_retrieval_leader_prompt = ChatPromptTemplate.from_messages([
        ("system", resolved_agent_configs['data_retrieval_leader_agent']['prompt']),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Given the conversation above, who should act next? Or should we FINISH? Select one of: {options}.")
    ]).partial(options=str(data_retrieval_options_for_next), members=", ".join(data_retrieval_team_members))

    supervisor_members = resolved_agent_configs['supervisor']['members']
    supervisor_options_for_next = supervisor_members + ["FINISH"]
    supervisor_prompt = ChatPromptTemplate.from_messages([
        ("system", resolved_agent_configs['supervisor']['prompt']),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Given the conversation above, who should act next? Or should we FINISH? Select one of: {options}")
    ]).partial(options=str(supervisor_options_for_next), members=", ".join(supervisor_members))

    class DataTeamRouter(TypedDict):
        next: Literal[*data_retrieval_options_for_next]

    class Router(TypedDict):
        next: Literal[*supervisor_options_for_next]

    async def news_and_sentiment_retrieval_node(state: AgentState):
        result = await news_and_sentiment_retrieval_agent.ainvoke(state)
        return Command(update={'messages': [HumanMessage(content=result['messages'][-1].content, name='news_and_sentiment_retrieval')]}, goto='data_team_leader')

    async def market_data_retrieval_node(state: AgentState):
        result = await market_data_retrieval_agent.ainvoke(state)
        return Command(update={'messages': [HumanMessage(content=result['messages'][-1].content, name='market_data_retrieval')]}, goto='data_team_leader')

    async def economic_data_retrieval_node(state: AgentState):
        result = await economic_data_retrieval_agent.ainvoke(state)
        return Command(update={'messages': [HumanMessage(content=result['messages'][-1].content, name='economic_data_retrieval')]}, goto='data_team_leader')

    async def financial_statement_retrieval_node(state: AgentState):
        result = await financial_statement_retrieval_agent.ainvoke(state)
        return Command(update={'messages': [HumanMessage(content=result['messages'][-1].content, name='financial_statement_retrieval')]}, goto='data_team_leader')

    async def data_team_leader_node(state: AgentState):
        query = state['query']
        chain = data_retrieval_leader_prompt | data_team_leader_llm.with_structured_output(DataTeamRouter)
        response = await chain.ainvoke({"messages": state["messages"], "query": query})
        return Command(goto=response["next"] if response["next"] != "FINISH" else "reporter")

    async def supervisor_node(state: AgentState):
        chain = supervisor_prompt | llm.with_structured_output(Router)
        response = await chain.ainvoke(state)
        return Command(goto=response["next"])

    # 그래프 구성
    builder = StateGraph(AgentState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("news_and_sentiment_retrieval", news_and_sentiment_retrieval_node)
    builder.add_node("market_data_retrieval", market_data_retrieval_node)
    builder.add_node("economic_data_retrieval", economic_data_retrieval_node)
    builder.add_node("financial_statement_retrieval", financial_statement_retrieval_node)
    builder.add_node("data_team_leader", data_team_leader_node)
    builder.add_node("insider_team_leader", insider_graph)
    builder.add_node("reporter", report_graph)
    builder.add_node("general_team_leader", general_graph)
    builder.add_node("analyst_team_leader", analyst_graph)

    builder.add_edge(START, "supervisor")
    builder.add_edge("insider_team_leader", "data_team_leader")
    builder.add_edge("analyst_team_leader", "reporter")
    builder.add_edge("reporter", END)
    builder.add_edge("general_team_leader", END)

    return builder.compile(checkpointer=memory)
