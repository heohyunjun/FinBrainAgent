from datetime import datetime, timedelta
from typing import (
    List, Annotated, Literal, Dict, Callable, TypeVar, Tuple, Type, Generic, Optional, Any
)

import yfinance as yf
import pandas as pd
from dateutil.parser import parse
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.agent_toolkits.polygon.toolkit import PolygonToolkit
from langchain_community.utilities.polygon import PolygonAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun

from sec_tool.sec_financial_fiedls_definitions import FinancialNecessaryFields


# 환경 변수 로드
load_dotenv()

# Polygon API 설정
polygon = PolygonAPIWrapper()
polygon_toolkit = PolygonToolkit.from_polygon_api_wrapper(polygon)
polygon_tools = polygon_toolkit.get_tools()


class MarketDataTools:
    """주가 및 시장 데이터를 다루는 도구 클래스"""


    @staticmethod
    @tool
    def get_stock_price(ticker: str, period: str = "1d", start: str = None, end: str = None) -> dict:
        """
        주어진 주식 티커에 대해 지정된 기간의 가격 데이터를 반환합니다.

        Args:
            ticker (str): 다운로드할 주식 티커. 단일 문자열로 제공 (예: "AAPL").
            period (str): 데이터를 가져올 기간. 유효한 값: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max".
                        기본값은 "1d". "period"를 사용하거나 "start"와 "end"를 사용해야 함. 두 가지를 동시에 사용할 수 없음.
            start (str, optional): 데이터 다운로드 시작 날짜(포함). 형식: "YYYY-MM-DD". 예: "2020-01-01".
                                "period" 대신 사용할 수 있으며, 기본값은 None (99년 전부터).
            end (str, optional): 데이터 다운로드 종료 날짜(미포함). 형식: "YYYY-MM-DD". 예: "2023-01-01" (마지막 데이터는 "2022-12-31").
                                "period" 대신 사용할 수 있으며, 기본값은 None (현재 날짜까지).

        Returns:
            dict: 지정된 티커에 대한 주식 가격 데이터를 딕셔너리 형태로 반환.
        """
        stock_info = yf.download(ticker, period=period, start=start, end=end).to_dict()
        return stock_info

    @staticmethod
    def get_polygon_tools():
        """Polygon API에서 제공하는 모든 도구를 반환합니다."""
        return polygon_tools

    
    @staticmethod
    def get_websearch_tool():
        return DuckDuckGoSearchRun()

    @staticmethod
    @tool
    def get_stock_news(ticker: Annotated[str, "Stock ticker symbol"]) -> Annotated[List[Dict[str, str]], "List of stock news details"]:
        """
        Retrieves the latest news related to the given stock ticker.

        Returns:
            - A list of dictionaries, each containing:
                - title (str): The title of the news article.
                - description (str): A brief description of the news content.
                - pubDate (str): The publication date of the news article.
                - url (str): The URL to the full news article.
        """
        stock = yf.Ticker(ticker)
        news = stock.news if stock.news else []
        
        news_data = []
        
        for item in news:
            if 'content' in item:
                content = item['content']
                news_item = {
                    "title": content.get("title", "No Title Available"),
                    "summary": content.get("summary", "No summary Available"),
                    "pubDate": content.get("pubDate", "No Date Available"),
                    "url": content.get("canonicalUrl", {}).get("url", "No URL Available")
                }
                news_data.append(news_item)

        return news_data
class FinancialDataTools:
    """기업 재무 데이터를 다루는 도구 클래스"""

    @staticmethod
    def filter_income_statement_info(financial_df: pd.DataFrame) -> pd.DataFrame:
        """
        손익계산서 데이터에서 핵심 지표만 필터링하는 함수.
        
        :param financial_df: company_research_tool("TSLA") 로 가져온 dict 데이터
        :return: 필터링된 DataFrame (핵심 재무 지표만 포함)
        """


        if financial_df.empty:
            return financial_df  # 데이터가 없으면 그대로 반환

        # 핵심 지표 리스트
        key_metrics = [
            FinancialNecessaryFields.TOTAL_REVENUE,
            FinancialNecessaryFields.COST_OF_REVENUE,
            FinancialNecessaryFields.GROSS_PROFIT,
            FinancialNecessaryFields.OPERATING_INCOME,
            FinancialNecessaryFields.EBITDA,
            FinancialNecessaryFields.EBIT,
            FinancialNecessaryFields.NET_INCOME,
            FinancialNecessaryFields.BASIC_EPS,
            FinancialNecessaryFields.DILUTED_EPS,
            FinancialNecessaryFields.INTEREST_EXPENSE,
            FinancialNecessaryFields.TAX_PROVISION
        ]

        # DataFrame의 인덱스에서 key_metrics와 교집합을 찾아 필터링
        filtered_df = financial_df.loc[financial_df.index.intersection(key_metrics)]
        return filtered_df

    
    @staticmethod
    @tool
    def get_income_statement(ticker: str, freq: str = "quarterly") -> pd.DataFrame:
        """
        주어진 티커에 대해 회사의 손익계산서 데이터를 반환합니다.

        Args:
            ticker (str): 조회할 주식 티커. 단일 문자열로 제공 (예: "AAPL").
            freq (str, optional): 데이터의 주기. 유효한 값: "quarterly" (분기별), "yearly" (연간).
                                기본값은 "quarterly".

        Returns:
            pd.DataFrame: 지정된 주기(freq)에 따라 필터링된 손익계산서 데이터.
        """
        company_info = yf.Ticker(ticker)
        financial_info = company_info.get_financials(freq=freq)
        filtered_financial_info = FinancialDataTools.filter_income_statement_info(financial_info)
        return filtered_financial_info
    
    @staticmethod
    @tool
    def get_financial_event_filings(ticker: str) -> dict:
        """
        주어진 티커에 대해 회사의 재무 보고 및 주요 사건 관련 SEC 제출 자료를 반환합니다.
        대상 문서 유형: '10-K', '10-Q', '8-K', '10-K/A', '10-Q/A', '8-K/A', '20-F', '6-K'.

        Args:
            ticker (str): 조회할 주식 티커. 단일 문자열로 제공 (예: "AAPL").

        Returns:
            dict: 지정된 유형의 SEC 제출 자료를 필터링한 결과. 키는 'financial_event_filings'이며, 값은 필터링된 리스트.
        """
        # 대상 문서 유형 정의
        target_types = {'10-K', '10-Q', '8-K', '10-K/A', '10-Q/A', '8-K/A', '20-F', '6-K'}

        # SEC 제출 자료 가져오기
        company_info = yf.Ticker(ticker)
        sec_filings = company_info.get_sec_filings()

        # 리스트에서 대상 유형만 필터링
        filtered_filings = [filing for filing in sec_filings if filing.get('type') in target_types]

    
        filtered_filings = SECFilingsTools.filter_sec_filings(filtered_filings)

        return {'financial_event_filings': filtered_filings}
class SECFilingsTools:
    """SEC 보고서 데이터를 다루는 도구 클래스"""

    @staticmethod
    def filter_sec_filings(sec_filings, report_types=None):
        """
        SEC Filings에서 1년 이내 데이터만 가져오고, 특정 리포트 유형을 필터링하며, EXCEL 파일은 제외.
        
        - report_types가 None이면 모든 리포트를 가져옴
        - 특정 리스트가 들어오면 해당 유형만 필터링
        """
        one_year_ago = datetime.today() - timedelta(days=365)

        filtered_filings = []
        for filing in sec_filings:
            filing_date = parse(str(filing["date"]))  # 날짜 변환
            is_recent = filing_date >= one_year_ago
            is_valid_type = report_types is None or filing["type"] in report_types

            if is_recent and is_valid_type:
                # EXCEL 파일을 제외한 exhibits 필터링
                filtered_exhibits = {key: value for key, value in filing["exhibits"].items() if key != "EXCEL"}

                filtered_filings.append({
                    "date": filing["date"],
                    "type": filing["type"],
                    "title": filing["title"],
                    "exhibits": filtered_exhibits  # 필터링된 exhibits 추가
                })

        return filtered_filings
