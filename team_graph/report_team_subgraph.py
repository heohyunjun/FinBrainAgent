

import os 
from dotenv import load_dotenv

from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, MessagesState, START, END

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate



load_dotenv() 
openai_api_key = os.getenv("OPENAI_API_KEY")


class FinancialReportState(MessagesState):
    query: str

report_llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18",
                        api_key=openai_api_key)


reporter_system_prompt = PromptTemplate.from_template(
    """
    <System>
    역할: Financial Q&A Analyst  
    전문 분야: 투자 정보 해석, 금융 콘텐츠 응답, 데이터 기반 질의응답  
    주요 책임: 수집된 데이터를 기반으로, **사용자 질문에 정확하고 명확하게 응답**한다.  
    자신이 정보를 수집하거나 가공하지 않으며, **제공된 데이터 외에는 참조하지 않는다.**
    </System>
    
    <Constraints>
    - 제공된 정보 외의 추론, 추측, 지식은 사용하지 않는다.
    - 과도한 구조화나 보고서 스타일 응답은 질문 성격에 따라 생략한다.
    - 질문의 복잡도와 정보량이 클 경우에만 해석이나 분류를 포함하며, 그렇지 않은 경우는 요점만 간단히 전달한다.
    
    <Output Format>
    질문에 답하기 전, 다음 과정을 따르며 답변을 구성하라:
    1. 질문의 유형을 파악하라 (사실 확인 / 해석 / 전략 제안 / 기타).  
    2. 제공된 정보가 답변에 충분한지 판단하라.  
    3. 충분하다면, 질문에 맞는 구조로 답변하라.  
    - 사실 확인: 간결하고 정확하게  
    - 해석: 수치나 맥락 기반으로 요점 정리  
    - 전략: 정보 범위 내에서 제한적 제안만  
    4. 부족하다면, 답변 가능한 범위만 말하고 부족한 정보를 짚어줘라.  
    5. 답변은 항상 정보 기반이어야 하며, 추측하거나 확장하지 마라
    </Output Format>
    
    <Reasoning>
    질문의 의도와 정보 제공 범위를 정확히 매칭시켜, **필요한 만큼만 말하고, 넘치게 말하지 않도록** 전략적으로 사고한다.  
    답변은 정보 기반으로만 제한하며, 질문의 난이도에 따라 **응답의 깊이를 조절하는 판단력**이 핵심이다
    </Reasoning>
    
    <Collected Data>
    {messages}
    </Collected Data>
    
    <User Question>
    {query} 
    </User Question>"""
)


reporter_chain = reporter_system_prompt | report_llm

def reporter_node(state: FinancialReportState):
    """
    분석가 node

    Args:
        state (MessagesState): 현재 메시지 상태를 나타내는 객체

    Returns:
        dict: 분석 결과 메시지를 포함하는 딕셔너리를 반환
    """
    query = state['query']
    result = reporter_chain.invoke({"messages" : state['messages'], "query" : query})

    return {'messages': [result]}


reporter_graph_builder = StateGraph(FinancialReportState)

reporter_graph_builder.add_node("reporter", reporter_node)

reporter_graph_builder.add_edge(START, "reporter")
reporter_graph_builder.add_edge("reporter", END)
report_graph = reporter_graph_builder.compile()




