
import os 
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Annotated, Literal, Dict, Callable, TypeVar, Tuple, Type, Generic, Optional, Union, Any

from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder

from langgraph.types import Command
from typing_extensions import TypedDict 
load_dotenv() 
openai_api_key = os.getenv("OPENAI_API_KEY")
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

Model_NAME = "gpt-4o-mini-2024-07-18"

general_team_leader_llm = ChatOpenAI(model=Model_NAME,
                        api_key=openai_api_key)

general_members_llm = ChatOpenAI(model=Model_NAME,
                        api_key=openai_api_key,
                        temperature=0.7)

class GeneralState(MessagesState):
    query: str

# general_team_leader가 관리할 멤버와 옵션 정의
general_team_members = ["general_query_node", "meta_node"]
general_team_options_for_next = general_team_members

# general_team_leader 프롬프트
general_team_system_prompt = (
    "You are the general_team_leader in an AI agent service, responsible for handling questions outside finance and investment. "
    "Your role is to route user requests to the appropriate specialized workers: {members}.\n"
    "Worker roles:\n"
    "- 'general_query_node': Handles general knowledge questions unrelated to the service itself.\n"
    "- 'meta_node': Handles meta-questions about this service.\n"
    "Given the user request, strictly select ONLY ONE most suitable worker to act next based on the task description above. "
)

general_team_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", general_team_system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, who should act next? "
            "Or should we FINISH? Select one of: {options}",
        ),
    ]
).partial(options=str(general_team_options_for_next), members=", ".join(general_team_members))

# Router 클래스 (general_team_leader용)
class GeneralTeamRouter(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*general_team_options_for_next]

# general_team_leader 노드
def general_team_leader_node(state: GeneralState) -> Command[Literal[*general_team_members]]:
    """
    general_team_leader node 
    주어진 State를 기반으로 일반 질문과 메타 질문을 구분해 적절한 노드로 라우팅
    모든 작업이 완료되면 reporter node로 이동
    """
    general_team_chain = general_team_prompt | general_team_leader_llm.with_structured_output(GeneralTeamRouter)
    response = general_team_chain.invoke(state)

    goto = response["next"]

    return Command(goto=goto)


general_system_prompt = PromptTemplate.from_template(
    "<System>\n"
    "역할: General Knowledge Assistant\n"
    "목표: 질문에 대해 정확하고 친절하게 답변한다. </System>\n"
    
    "<Instructions>\n"
    "- 너가 응답을 생성하는 현재 시간은 다음과 같다: {current_time} 시점을 기준으로, 학습된 정보와 현실의 차이를 인식해라\n"
    "- 답변은 간결하고 명확하게 작성하되, 복잡한 주제일 경우 단계별로 생각해라.\n"
    "- **모르는 경우에는 아는 척하지 말고, '모릅니다' 라고 명확히 말하라.**\n"
    "- **모든 응답에는 반드시 `금융 외 질문에 대한 답변은 정확도가 떨어질 수 있다는 점을 인지해주세요` 문장을 포함하라.**\n" 
    "- 과도한 추측, 불확실한 내용, 허위 정보는 절대 포함하지 않는다.\n"
    "- 질문이 모호하면, 추가 정보 요청으로 질문을 명확히 유도하라. </Instructions>\n"
    
    "<Question>{question}</Question>"

).partial(current_time=current_time)

meta_system_prompt = PromptTemplate.from_template(
    "<System> 너는 finbrain이라는 금융 투자 어드바이저 AI 서비스의 일부로, 미국 주식 관련 질문에 답하기 위해 설계된 AI 어시스턴트입니다.\n"
    "finbrain은 SEC Filing 데이터, 주가 정보, 뉴스, 경제 지표를 활용해 답변을 제공한다다.\n" 
    "당신의 역할은 finbrain 서비스 자체에 대한 메타 질문을 처리해야 한다.</System>\n"

    "<Instructions> 사용자의 finbrain에 대한 메타 질문에 간결하고 유용하게 답변해라.\n" 
    "질문을 만족시킬 만큼만 정보를 제공하되, 내부 처리 과정이나 기술적 세부사항은 드러내지 마라라.\n" 
    "답변은 짧고 명확하게, finbrain이 무엇을 하거나 사용자에게 어떻게 도움이 되는지에 초점을 맞추세요.</Instructions>\n"

    "<Question>{question}</Question>"
)

general_query_chain = general_system_prompt | general_members_llm | StrOutputParser()
general_meta_chain = meta_system_prompt | general_members_llm | StrOutputParser()

def general_query_node(state: GeneralState):
    """
    general_node

    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        dict: 분석 결과 메시지를 포함하는 딕셔너리를 반환
    """

    query = state['query']
    
    general_answer = general_query_chain.invoke({"question" : query})
    return {"messages" : general_answer}

def meta_node(state: GeneralState):
    """
    general_node

    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        dict: 분석 결과 메시지를 포함하는 딕셔너리를 반환
    """
    query = state['query']
    general_answer = general_meta_chain.invoke({"question" : query})
    return {"messages" : general_answer}

# 그래프 
general_graph_builder = StateGraph(GeneralState)

general_graph_builder.add_node("general_team_leader", general_team_leader_node)
general_graph_builder.add_node("general_query_node", general_query_node)
general_graph_builder.add_node("meta_node", meta_node)

general_graph_builder.add_edge(START, "general_team_leader")
general_graph_builder.add_edge("general_query_node", END)
general_graph_builder.add_edge("meta_node", END)
general_graph = general_graph_builder.compile()