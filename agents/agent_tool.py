# agent_tool.py
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
from pydantic import BaseModel, Field
import yfinance as yf


# Define the input schema
class NewsInput(BaseModel):
    ticker: str = Field(..., description="The ticker symbol of the stock to fetch the latest news for")

class DataTools:
    """에이전트가 사용할 다양한 도구를 관리하는 클래스"""

    tavily_max_results = 5
    @classmethod
    def get_tavily_search_tool(cls):
        return TavilySearchResults(max_results=cls.tavily_max_results)


    @classmethod
    @tool(args_schema=NewsInput)
    def _get_stock_news_internal(ticker: str):
        """Fetch the latest news articles for a given ticker symbol."""
        stock = yf.Ticker(ticker)
        news = stock.news
        return news

    @classmethod
    def get_stock_news(cls, ticker: str):
        """
        사용자가 단순히 `get_stock_news("AAPL")`처럼 호출할 수 있도록 래퍼 함수 추가.
        내부적으로 `NewsInput`을 자동 생성하여 `_get_stock_news_internal()`에 전달.
        """
        return cls._get_stock_news_internal(NewsInput(ticker=ticker))