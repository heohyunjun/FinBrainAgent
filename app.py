# app.py
import os
import requests
import feedparser
import streamlit as st

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain



# OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
# Alpha Vantage
alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")


# 1) LangChain용 OpenAI LLM 초기화
# - temperature=0.7 정도면 답변의 창의성과 일관성 사이 적절한 밸런스를 기대할 수 있음
# llm = OpenAI(
#     model_name="gpt-3.5-turbo-instruct",
#     temperature=0.7,
#     max_tokens=200,
#     openai_api_key=openai_api_key
# )


# 2) PromptTemplate 구성
# 프롬프트 템플릿: 질문, 주가 정보, 뉴스 헤드라인을 종합해 답변
prompt = PromptTemplate(
    input_variables=["question", "stock_info", "news_headlines"],
    template="""
당신은 금융 투자 전문가입니다.
사용자의 질문을 분석하고, 아래 제공된 시세 정보와 뉴스 헤드라인을 참고하여
근거있는 답변을 간결하게 작성해라

질문:
{question}

시세 정보:
{stock_info}

뉴스 헤드라인:
{news_headlines}

답변:
""",
)


# 3) LLMChain 생성
# chain = LLMChain(
#     llm=llm,
#     prompt=prompt
# )




def fetch_stock_price(symbol: str) -> str:
    """
    Alpha Vantage에서 종목 시세 정보를 가져와 문자열로 정리해 반환.
    심볼이 유효하지 않거나 API 에러가 나면 빈 문자열 반환.
    """
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": alpha_vantage_key
    }
    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        # 'Global Quote' 키가 없는 경우 등 에러 처리
        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            price = quote.get("05. price", "N/A")
            change_percent = quote.get("10. change percent", "N/A")
            result = f"현재 주가: {price}, 변동률: {change_percent}"
        else:
            result = "주가 정보를 찾을 수 없음"
    except Exception:
        result = "시세 API 호출 에러 발생"
    return result


def fetch_news_rss(rss_url: str, max_items=3) -> str:
    """
    RSS 피드를 읽어 상위 n개 헤드라인을 문자열로 합쳐 반환.
    """
    try:
        feed = feedparser.parse(rss_url)
        headlines = []
        for entry in feed.entries[:max_items]:
            headlines.append(f"- {entry.title}")
        if not headlines:
            return "관련 뉴스 헤드라인을 찾지 못함"
        return "\n".join(headlines)
    except Exception:
        return "뉴스 RSS 파싱 중 오류 발생"


def main():
    st.title("투자 고수 agent")
    st.write("종목 심볼과 궁금한 질문을 입력하면, 관련 주가 정보와 뉴스 헤드라인을 참고해 답변을 생성")

    symbol = st.text_input("종목 심볼 (예: TSLA, AAPL, GOOG 등)", "TSLA")
    user_question = st.text_input("질문을 입력하세요", "테슬라 전망이 어때?")

    if st.button("답변받기"):
        # 1) 종목 시세 정보 가져오기
        stock_info = fetch_stock_price(symbol)

        # 2) 뉴스 헤드라인 가져오기
        # (테슬라 예시: Yahoo Finance 테슬라 RSS)
        # 실제론 다양한 RSS를 선택적으로 쓸 수 있음.
        rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
        news_headlines = fetch_news_rss(rss_url)

        # 3) LangChain 체인 실행
        # answer = chain.run(
        #     question=user_question,
        #     stock_info=stock_info,
        #     news_headlines=news_headlines
        # )
        answer = "답변"

        # 결과 표시
        st.markdown("**[시세 정보]**")
        st.write(stock_info)
        st.markdown("**[뉴스 헤드라인]**")
        st.write(news_headlines)
        st.markdown("**[AI 답변]**")
        st.write(answer.strip())


if __name__ == "__main__":
    main()