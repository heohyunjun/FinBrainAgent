


from dotenv import load_dotenv
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START, END

from agents.agent_library import agent_configs


load_dotenv() 

class AnalystState(MessagesState):
    query: str

analyst_llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18")


def reporter_node(state):
    return state

anaylst_team_leader_system_prompt = agent_configs['anaylst_team_leader']['prompt']

anaylst_team_leader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", anaylst_team_leader_system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ]
)


analyst_team_leader_agent = create_react_agent(
    analyst_llm, 
    tools=agent_configs['anaylst_team_leader']['tools'], 
    prompt=anaylst_team_leader_prompt
)


def analyst_team_leader_node(state: AnalystState) -> Command[Literal["reporter"]]:
    result = analyst_team_leader_agent.invoke(state)

    return Command(
        update={'messages': [HumanMessage(content=result['messages'][-1].content, name='analyst_team_leader')]},
        goto='reporter'
    )



analyst_graph_builder = StateGraph(AnalystState)

analyst_graph_builder.add_node("analyst_team_leader", analyst_team_leader_node)
analyst_graph_builder.add_node("reporter", reporter_node)
analyst_graph_builder.add_edge(START, "analyst_team_leader")

analyst_graph = analyst_graph_builder.compile()




