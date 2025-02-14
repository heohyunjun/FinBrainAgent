import os
import streamlit as st
import requests
import openai

from typing import TypedDict, List, Annotated
from dotenv import load_dotenv

from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph.message import add_messages

# 환경 변수 로드
load_dotenv()

# 환경 변수에서 키 가져오기
openai_api_key = os.getenv("OPENAI_API_KEY")
alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

# State 정의
class State(TypedDict):
    messages: Annotated[list, add_messages]

def main():
    st.title("투자Agent")

    symbol = st.text_input("종목 심볼", "TSLA")
    user_question = st.text_input("질문", "테슬라가 무역분쟁의 영향을 받는 이유가 뭘까?")

    if st.button("답변 받기"):
        # A) 분류 수행

        st.markdown("**[최종 답변]**")
        st.write(user_question)

if __name__ == "__main__":
    main()
