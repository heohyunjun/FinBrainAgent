
import os 
from dotenv import load_dotenv
from datetime import datetime

from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv() 
openai_api_key = os.getenv("OPENAI_API_KEY")
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

general_llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18",
                        api_key=openai_api_key)

general_system_prompt = PromptTemplate.from_template(
    """
<System> 
역할: General Knowledge Assistant  
목표: 질문에 대해 정확하고 친절하게 답변한다. </System>

<Instructions>
- 당신이 응답을 생성하는 현재 시간은 다음과 같다: {current_time} 시점을 기준으로, 학습된 정보와 현실의 차이를 인식해라
- 답변은 간결하고 명확하게 작성하되, 복잡한 주제일 경우 단계별로 생각해라.
- **모르는 경우에는 아는 척하지 말고, "모릅니다"라고 명확히 말하라.** 
- **모든 응답에는 반드시 `금융 외 질문에 대한 답변은 정확도가 떨어질 수 있다는 점을 인지해주세요` 문장을 포함하라.**  
- 과도한 추측, 불확실한 내용, 허위 정보는 절대 포함하지 않는다.  
- 질문이 모호하면, 추가 정보 요청으로 질문을 명확히 유도하라. </Instructions>

<Question>
{question}
</Question>
"""
).partial(current_time=current_time)


general_chain = general_system_prompt | general_llm | StrOutputParser()

def general_node(state: MessagesState):
    """
    general_node

    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        dict: 분석 결과 메시지를 포함하는 딕셔너리를 반환
    """

    general_answer = general_chain.invoke({"question" : state['messages'][0].content})
    return {"messages" : general_answer}


general_graph_builder = StateGraph(MessagesState)

general_graph_builder.add_node("general", general_node)

general_graph_builder.add_edge(START, "general")
general_graph_builder.add_edge("general", END)
general_graph = general_graph_builder.compile()
