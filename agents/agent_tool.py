# agent_tool.py
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
from pydantic import BaseModel, Field
import yfinance as yf
from typing import Annotated, List

# Define the input schema
class NewsInput(BaseModel):
    ticker: str = Field(..., description="The ticker symbol of the stock to fetch the latest news for")

class DataTools:
    """에이전트가 사용할 다양한 도구를 관리하는 클래스"""

    tavily_max_results = 5
    @classmethod
    def get_tavily_search_tool(cls):
        return TavilySearchResults(max_results=cls.tavily_max_results)


    @tool
    def get_stock_news(
        ticker: Annotated[str, "Stock ticker symbol"]
    ) -> Annotated[List[str], "List of summaries for the latest stock news of the given ticker"]:
        """
        Retrieves summaries of the latest news related to the given stock ticker.
        """
        stock = yf.Ticker(ticker)
        news = stock.news

        # 뉴스가 존재하고, 각 항목에서 'content'와 'summary'가 있는 경우만 추출
        summaries = [
            item['content']['summary'] for item in news 
            if 'content' in item and 'summary' in item['content']
        ] if news else []

        return summaries