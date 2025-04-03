
from dotenv import load_dotenv
from typing import Literal
from typing_extensions import TypedDict 

from langchain_openai import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START, END

from agents.agent_library import agent_configs


load_dotenv() 



Model_NAME = "gpt-4o-mini-2024-07-18"

insider_team_leader_llm = ChatOpenAI(model=Model_NAME)


class InsiderState(MessagesState):
    query: str

def data_team_leader_node(state):
    return state

insider_team_members = agent_configs['insider_team_leader']['members']
insider_team_leader_system_prompt = agent_configs['insider_team_leader']['prompt']
insider_team_options_for_next = insider_team_members + ['FINISH']

insider_team_leader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", insider_team_leader_system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ]
).partial(options=str(insider_team_options_for_next), members=insider_team_members)

class InsiderTeamRouter(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*insider_team_options_for_next]


def insider_team_leader_node(state: InsiderState) -> Command[Literal[*insider_team_members, "data_team_leader"]]:
    insider_team_chain = insider_team_leader_prompt | insider_team_leader_llm.with_structured_output(InsiderTeamRouter)
    response = insider_team_chain.invoke(state)

    goto = response["next"]
    if goto == "FINISH":
        goto = "data_team_leader"

    return Command(goto=goto)



domestic_insider_researcher_agent = create_react_agent(
    insider_team_leader_llm, 
    tools=agent_configs['domestic_insider_researcher']['tools'],
    prompt=agent_configs['domestic_insider_researcher']['prompt']
)

international_insider_researcher_agent = create_react_agent(
    insider_team_leader_llm, 
    tools=agent_configs['international_insider_researcher']['tools'], 
    prompt=agent_configs['international_insider_researcher']['prompt']
)

def domestic_insider_researcher_node(state: InsiderState) -> Command[Literal["insider_team_leader"]]:
    result = domestic_insider_researcher_agent.invoke(state)
    return Command(
        update={'messages': [HumanMessage(content=result['messages'][-1].content, name='domestic_insider_researcher')]},
        goto='insider_team_leader'
    )




def international_insider_researcher_node(state: InsiderState) -> Command[Literal["insider_team_leader"]]:
    result = international_insider_researcher_agent.invoke(state)

    return Command(
        update={'messages': [HumanMessage(content=result['messages'][-1].content, name='international_insider_researcher')]},
        goto='insider_team_leader'
    )


insider_graph_builder = StateGraph(InsiderState)
insider_graph_builder.add_node("insider_team_leader", insider_team_leader_node)
insider_graph_builder.add_node("data_team_leader", data_team_leader_node)
insider_graph_builder.add_node("domestic_insider_researcher", domestic_insider_researcher_node)
insider_graph_builder.add_node("international_insider_researcher", international_insider_researcher_node)

insider_graph_builder.add_edge(START, "insider_team_leader")
insider_graph = insider_graph_builder.compile()