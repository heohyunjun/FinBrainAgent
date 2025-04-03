
from dotenv import load_dotenv
from typing import Literal
from typing_extensions import TypedDict 

# LangChain 및 LangGraph 관련 라이브러리
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from langgraph.types import Command
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import create_react_agent

from langsmith import utils 
from langchain_openai import ChatOpenAI

from agents.agent_library import agent_configs
from team_graph.report_team_subgraph import report_graph
from team_graph.general_chat_subgraph import general_graph
from team_graph.insider_team_graph import insider_graph 
from team_graph.analyst_team_graph import analyst_graph
# 환경 변수 로드
load_dotenv()
print(utils.tracing_is_enabled())

class AgentState(MessagesState):
    query: str

llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18")

# 시장 조사 에이전트
news_and_sentiment_retrieval_agent = create_react_agent(
    llm, 
    tools=agent_configs['news_and_sentiment_retrieval_agent']['tools'],
    prompt=agent_configs['news_and_sentiment_retrieval_agent']['prompt']
)

market_data_retrieval_agent = create_react_agent(
    llm, 
    tools=agent_configs['market_data_retrieval_agent']['tools'], 
    prompt = agent_configs['market_data_retrieval_agent']['prompt']
)


economic_data_retrieval_agent = create_react_agent(
    llm, 
    tools=agent_configs['economic_data_retrieval_agent']['tools'], 
    prompt=agent_configs['economic_data_retrieval_agent']['prompt']
)


financial_statement_retrieval_agent = create_react_agent(
    llm,
    tools=agent_configs['financial_statement_retrieval_agent']['tools'],
    prompt = agent_configs['financial_statement_retrieval_agent']['prompt']
)


data_retrieval_team_members=agent_configs['data_retrieval_leader_agent']['members']
data_retrieval_options_for_next = data_retrieval_team_members + ["FINISH"]
data_retrieval_leader_system_prompt = agent_configs['data_retrieval_leader_agent']['prompt']
data_retrieval_leader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", data_retrieval_leader_system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, who should act next? "
            "Or should we FINISH? Select one of: {options}. "
        ),
    ]
).partial(options=str(data_retrieval_options_for_next), members=", ".join(data_retrieval_team_members))


data_cleansing_system_prompt = agent_configs['data_cleansing_agent']['prompt']
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

supervisor_members = agent_configs['supervisor']['members']
supervisor_options_for_next = supervisor_members + ["FINISH"]
supervisor_system_prompt = agent_configs['supervisor']['prompt']
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



def news_and_sentiment_retrieval_node(state: AgentState) -> Command[Literal["data_team_leader"]]:
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
        goto='data_team_leader'
    )



def market_data_retrieval_node(state: AgentState) -> Command[Literal["data_team_leader"]]:
    """
    실시간 주가 및 거래량 수집
    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        Command: supervisor node로 이동하기 위한 명령을 반환
    """
    result = market_data_retrieval_agent.invoke(state)

    return Command(
        update={'messages': [HumanMessage(content=result['messages'][-1].content, name='market_data_retrieval')]},
        goto='data_team_leader'
    )

def economic_data_retrieval_node(state: AgentState) -> Command[Literal["data_team_leader"]]:
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
        goto='data_team_leader'
    )


def financial_statement_retrieval_node(state: AgentState) -> Command[Literal["data_team_leader"]]:
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
        goto='data_team_leader'
    )

class DataTeamRouter(TypedDict):
    """Worker to route to next. If no workers needed or question is vague, route to FINISH."""
    next: Literal[*data_retrieval_options_for_next]


def data_team_leader_node(state: AgentState) -> Command[Literal[*data_retrieval_team_members, "reporter"]]:

    query = state['query']
    data_retrieval_team_chain = data_retrieval_leader_prompt | llm.with_structured_output(DataTeamRouter)
    response= data_retrieval_team_chain.invoke({"messages" : state["messages"], "query" : query})


    goto = response["next"]

    if goto == "FINISH":
        goto = "reporter"  # 정상 종료 시

    
    return Command(goto=goto)

def data_cleansing_node(state: AgentState) -> Command[Literal["data_team_leader"]]:

    query = state['query']
    cleaning_chain = data_cleansing_prompt | llm | StrOutputParser()
    result = cleaning_chain.invoke({"messages" : state['messages'], "query" : query})

    return Command(
        update={'messages': [HumanMessage(content=result, name='data_cleansing')]},
        goto='data_team_leader'
    )

class Router(TypedDict):
    next: Literal[*supervisor_options_for_next]
    

def supervisor_node(state: AgentState) -> Command[Literal[*supervisor_members, END]]:
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
        goto = END

    return Command(goto=goto)


graph_builder = StateGraph(AgentState)

graph_builder.add_node("supervisor", supervisor_node)
graph_builder.add_node("news_and_sentiment_retrieval", news_and_sentiment_retrieval_node)
graph_builder.add_node("market_data_retrieval", market_data_retrieval_node)
graph_builder.add_node("financial_statement_retrieval", financial_statement_retrieval_node)
graph_builder.add_node("data_team_leader", data_team_leader_node)
graph_builder.add_node("data_cleansing", data_cleansing_node)
graph_builder.add_node("economic_data_retrieval", economic_data_retrieval_node)
graph_builder.add_node("insider_team_leader", insider_graph)
graph_builder.add_node("reporter", report_graph)
graph_builder.add_node("general_team_leader", general_graph)
graph_builder.add_node("analyst_team_leader", analyst_graph)

graph_builder.add_edge(START, "supervisor")
graph_builder.add_edge("insider_team_leader", "data_team_leader")
graph_builder.add_edge("analyst_team_leader", "reporter")
graph_builder.add_edge("reporter", END)
graph_builder.add_edge("general_team_leader", END)

graph = graph_builder.compile()


