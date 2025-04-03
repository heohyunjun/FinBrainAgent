import os
import requests
from datetime import datetime, timedelta
from typing import (
    List, Annotated, Literal, Dict, Callable, TypeVar, Tuple, Type, Generic, Optional, Any
)

import yfinance as yf
import pandas as pd
from dateutil.parser import parse
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

from field_definitions.sec_financial_fiedls_definitions import FinancialNecessaryFields


# 환경 변수 로드
load_dotenv()


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
    @tool
    def get_websearch_tool(
        query: Annotated[str, "Search query"]
    ) -> Annotated[str, "Web search result from DuckDuckGo"]:
        """웹 검색을 수행하고 결과를 반환합니다."""
        tool = DuckDuckGoSearchRun()
        return tool.invoke(query)

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

class EconomicDataTools:
    """거시 경제 데이터 수집 도구 모음음"""
    
    FRED_API_KEY = os.getenv("FRED_API_KEY")

    @staticmethod
    def get_fred_data(series_id: str, observation_start: str, 
                      observation_end: str, limit: int, sort_order: str = "desc", units: str = None) -> List[Dict]:
        """
        FRED API에서 특정 경제 데이터를 가져오는 공통 메서드.
        """
        base_url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "api_key": EconomicDataTools.FRED_API_KEY,
            "file_type": "json",
            "series_id": series_id,
            "observation_start": observation_start,
            "observation_end": observation_end,
            "sort_order": sort_order,
            "limit": limit
        }
        if units:  # 변환 옵션 적용
            params["units"] = units
            
        response = requests.get(base_url, params=params)

        return response.json().get("observations", []) if response.status_code == 200 else []

    @staticmethod
    def get_fred_release_dates(release_id: int, limit: int) -> List[str]:
        """
        FRED API에서 특정 Release ID에 대한 발표 일정을 가져오는 공통 메서드.
        """
        release_url = "https://api.stlouisfed.org/fred/release/dates"
        params = {
            "api_key": EconomicDataTools.FRED_API_KEY,
            "file_type": "json",
            "release_id": release_id,
            "sort_order": "desc",
            "limit": limit
        }
        response = requests.get(release_url, params=params)

        return [release["date"] for release in response.json().get("release_dates", [])] if response.status_code == 200 else []

    @staticmethod
    @tool
    def get_core_cpi_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"] = 10  
    ) -> Annotated[List[Dict], "List of Core CPI data entries"]:
        """
        Retrieves Core CPI data (including YoY and MoM percentage changes) from FRED API within the specified date range.
        """
        CORE_CPI_ID = "CPILFESL"
        RELEASE_ID = 10

        core_cpi = EconomicDataTools.get_fred_data(CORE_CPI_ID, observation_start, observation_end, limit)
        core_cpi_yoy = EconomicDataTools.get_fred_data(CORE_CPI_ID, observation_start, observation_end, limit, units="pc1")
        core_cpi_mom = EconomicDataTools.get_fred_data(CORE_CPI_ID, observation_start, observation_end, limit, units="pch")
        release_dates = EconomicDataTools.get_fred_release_dates(RELEASE_ID, limit)

        if not core_cpi or not core_cpi_yoy or not core_cpi_mom:
            return []

        while len(release_dates) < len(core_cpi):
            release_dates.append("N/A")

        return [
            {
                "date": core_cpi[i]["date"],
                "core_cpi": core_cpi[i]["value"],
                "core_cpi_yoy": core_cpi_yoy[i]["value"],
                "core_cpi_mom": core_cpi_mom[i]["value"],
                "release_date": release_dates[i]
            }
            for i in range(len(core_cpi))
        ]

    @staticmethod
    @tool
    def get_core_pce_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"] = 10 
    ) -> Annotated[List[Dict], "List of Core PCE data entries"]:
        """
        Retrieves Core PCE data (including YoY and MoM percentage changes) from FRED API within the specified date range.
        """
        CORE_PCE_ID = "PCEPILFE"
        RELEASE_ID = 54

        core_pce = EconomicDataTools.get_fred_data(CORE_PCE_ID, observation_start, observation_end, limit)
        core_pce_yoy = EconomicDataTools.get_fred_data(CORE_PCE_ID, observation_start, observation_end, limit, units="pc1")
        core_pce_mom = EconomicDataTools.get_fred_data(CORE_PCE_ID, observation_start, observation_end, limit, units="pch")
        release_dates = EconomicDataTools.get_fred_release_dates(RELEASE_ID, limit)

        if not core_pce or not core_pce_yoy or not core_pce_mom:
            return []

        while len(release_dates) < len(core_pce):
            release_dates.append("N/A")

        return [
            {
                "date": core_pce[i]["date"],
                "core_pce": core_pce[i]["value"],
                "core_pce_yoy": core_pce_yoy[i]["value"],
                "core_pce_mom": core_pce_mom[i]["value"],
                "release_date": release_dates[i]
            }
            for i in range(len(core_pce))
        ]
    
    @staticmethod
    @tool
    def get_personal_income_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]  = 10 
    ) -> Annotated[List[Dict], "List of personal income data entries"]:
        """
        Retrieves U.S. Personal Income data from FRED API within the specified date range, including month-over-month percentage change.
        """
        PERSONAL_INCOME_ID = "PI"
        personal_income = EconomicDataTools.get_fred_data(PERSONAL_INCOME_ID, observation_start, observation_end, limit, sort_order="asc")

        if not personal_income:
            return []

        prev_value = None
        formatted_data = []
        for entry in personal_income:
            date = entry["date"]
            value = float(entry["value"])
            if prev_value is not None:
                change_percent = ((value - prev_value) / prev_value) * 100
                change_symbol = f"{change_percent:.2f}%"
            else:
                change_symbol = "N/A"
            formatted_data.append({
                "date": date,
                "personal_income": f"{value:,.0f}",
                "mom_change": change_symbol
            })
            prev_value = value

        return formatted_data
    
    @staticmethod
    @tool
    def get_mortgage_rate_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]  = 10  
    ) -> Annotated[List[Dict], "List of mortgage rate data entries"]:
        """
        Retrieves U.S. 30-year fixed mortgage rate data from FRED API within the specified date range.
        """
        MORTGAGE_RATE_ID = "MORTGAGE30US"
        mortgage_rate = EconomicDataTools.get_fred_data(MORTGAGE_RATE_ID, observation_start, observation_end, limit, sort_order="desc")

        if not mortgage_rate:
            return []

        return [
            {
                "date": entry["date"],
                "mortgage_rate": f"{float(entry['value']):.2f}%"
            }
            for entry in mortgage_rate
        ]
    
    @staticmethod
    @tool
    def get_unemployment_rate_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]  = 10  
    ) -> Annotated[List[Dict], "List of unemployment rate data entries"]:
        """
        Retrieves U.S. Unemployment Rate data from FRED API within the specified date range.
        """
        UNEMPLOYMENT_ID = "UNRATE"
        unemployment_data = EconomicDataTools.get_fred_data(UNEMPLOYMENT_ID, observation_start, observation_end, limit, sort_order="desc")

        if not unemployment_data:
            return []

        return [
            {
                "date": entry["date"],
                "unemployment_rate": f"{float(entry['value']):.1f}%"
            }
            for entry in unemployment_data
        ]
    
    @staticmethod
    @tool
    def get_jobless_claims_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]  = 10  
    ) -> Annotated[List[Dict], "List of jobless claims data entries"]:
        """
        Retrieves U.S. Initial Jobless Claims data from FRED API within the specified date range.
        """
        JOBLESS_CLAIMS_ID = "ICSA"
        jobless_claims = EconomicDataTools.get_fred_data(JOBLESS_CLAIMS_ID, observation_start, observation_end, limit, sort_order="desc")

        if not jobless_claims:
            return []

        return [
            {
                "date": entry["date"],
                "jobless_claims": f"{int(float(entry['value'])):,}"
            }
            for entry in jobless_claims
        ]