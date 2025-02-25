import os
import streamlit as st
import requests
import openai
from dotenv import load_dotenv

from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

from question_classifier import QuestionClassifier

# 환경 변수 로드
load_dotenv()

# 환경 변수에서 키 가져오기
openai_api_key = os.getenv("OPENAI_API_KEY")
alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

####################################
# 2) 시세 정보 함수
####################################
def fetch_stock_price(symbol: str) -> str:
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": alpha_vantage_key
    }
    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            price = quote.get("05. price", "N/A")
            change_percent = quote.get("10. change percent", "N/A")
            result = f"현재 주가: {price}, 변동률: {change_percent}"
        else:
            result = "시세 정보를 찾을 수 없음"
    except Exception:
        result = "시세 API 호출 에러 발생"
    return result

####################################
# 3) 답변 생성용 LLM & 체인
####################################
# answer_llm = OpenAI(
#     temperature=0.7,
#     openai_api_key=openai_api_key,
#     model_name="text-davinci-003"
# )

#분류 전용 LLM 생성
# - temperature=0.0~0.2 권장 (분류 안정)
# classification_llm = OpenAI(
#     temperature=0.0,
#     openai_api_key=openai_api_key,
#     model_name="text-davinci-003"  # 혹은 gpt-3.5-turbo 등
# )

classification_llm = ChatGroq(
    model="mixtral-8x7b-32768",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,

)

answer_llm = ChatGroq(
    model="mixtral-8x7b-32768",
    temperature=0.7,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)



prompt_template = PromptTemplate(
    input_variables=["category", "question", "extra_data"],
    template="""
당신은 금융/투자 분야 전문가 AI입니다.

[카테고리]: {category}
[사용자 질문]: {question}
[추가 데이터]: {extra_data}

위 정보를 바탕으로 간결하고 핵심적인 답변을 작성해라
"""
)

answer_chain = prompt_template | answer_llm | StrOutputParser()

####################################
# 4) Streamlit App
####################################
def main():
    st.title("투자Agent")

    symbol = st.text_input("종목 심볼", "TSLA")
    user_question = st.text_input("질문", "테슬라가 무역분쟁의 영향을 받는 이유가 뭘까?")

    if st.button("답변 받기"):
        # A) 분류 수행


        # 분류기 객체 생성
        classify_question = QuestionClassifier(classification_llm)

        category = classify_question.classify(user_question)
        st.write(f"[질문 분류 결과] {category}")

        # B) 시세 정보 조회(샘플)
        stock_info = fetch_stock_price(symbol)

        # C) 최종 답변
        extra_data = f"시세 정보: {stock_info}"
        answer = answer_chain.invoke(
            {
                "category": category,  
                "question": user_question, 
                "extra_data": extra_data  
            }
        )

        st.markdown("**[최종 답변]**")
        st.write(answer)

if __name__ == "__main__":
    main()
