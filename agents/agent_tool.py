import requests
import yfinance as yf
from typing import Annotated, List, Dict
import os
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

FRED_API_KEY = "YOUR_FRED_API_KEY"  # 자신의 FRED API 키 입력 필요

class DataTools:
    """에이전트가 사용할 다양한 도구를 관리하는 클래스"""

    tavily_max_results = 5
    FRED_API_KEY = os.getenv("FRED_API_KEY")

    @classmethod
    def get_tavily_search_tool(cls):
        return TavilySearchResults(max_results=cls.tavily_max_results)

    
    @staticmethod
    def get_fred_data(series_id: str, observation_start: str, observation_end: str, limit: int, sort_order: str = "desc"):
        """
        FRED API에서 특정 경제 데이터를 가져오는 공통 메서드.
        """
        base_url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "api_key": DataTools.FRED_API_KEY,
            "file_type": "json",
            "series_id": series_id,
            "observation_start": observation_start,
            "observation_end": observation_end,
            "sort_order": sort_order,
            "limit": limit
        }

        response = requests.get(base_url, params=params)
        return response.json().get("observations", []) if response.status_code == 200 else []
    
    @staticmethod
    def get_fred_release_dates(release_id: int, limit: int):
        """
        FRED API에서 특정 Release ID에 대한 발표 일정을 가져오는 공통 메서드.
        """
        release_url = "https://api.stlouisfed.org/fred/release/dates"
        params = {
            "api_key": DataTools.FRED_API_KEY,
            "file_type": "json",
            "release_id": release_id,
            "sort_order": "desc",
            "limit": limit
        }
        response = requests.get(release_url, params=params)
        return [release["date"] for release in response.json().get("release_dates", [])] if response.status_code == 200 else []

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

    @tool
    def get_core_cpi_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "Filtered Core CPI data from FRED API"]:
        """
        Retrieves Core CPI data (including YoY and MoM percentage changes) from FRED API within the specified date range.
        """
        CORE_CPI_ID = "CPILFESL"  # 근원 CPI (식료품·에너지 제외)
        RELEASE_ID = 10  # CPI 발표 일정 Release ID

        # 근원 CPI 관련 데이터 조회
        core_cpi = DataTools.get_fred_data(CORE_CPI_ID, observation_start, observation_end, limit)
        core_cpi_yoy = DataTools.get_fred_data(CORE_CPI_ID, observation_start, observation_end, limit, units="pc1")
        core_cpi_mom = DataTools.get_fred_data(CORE_CPI_ID, observation_start, observation_end, limit, units="pch")
        release_dates = DataTools.get_fred_release_dates(RELEASE_ID, limit)

        while len(release_dates) < len(core_cpi):
            release_dates.append("N/A")

        # 최종 데이터 반환
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

    @tool
    def get_core_pce_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "Filtered Core PCE data from FRED API"]:
        """
        Retrieves Core PCE data (including YoY and MoM percentage changes) from FRED API within the specified date range.
        """
        CORE_PCE_ID = "PCEPILFE"  # 근원 PCE (식료품·에너지 제외)
        RELEASE_ID = 54  # PCE 발표 일정 Release ID

        # 근원 PCE 관련 데이터 조회
        core_pce = DataTools.get_fred_data(CORE_PCE_ID, observation_start, observation_end, limit)
        core_pce_yoy = DataTools.get_fred_data(CORE_PCE_ID, observation_start, observation_end, limit, units="pc1")
        core_pce_mom = DataTools.get_fred_data(CORE_PCE_ID, observation_start, observation_end, limit, units="pch")
        release_dates = DataTools.get_fred_release_dates(RELEASE_ID, limit)

        while len(release_dates) < len(core_pce):
            release_dates.append("N/A")

        # 최종 데이터 반환
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
    @tool
    def get_personal_income_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "Recent U.S. Personal Income data with month-over-month change"]:
        """
        Retrieves U.S. Personal Income data from FRED API within the specified date range.
        Includes month-over-month percentage change.
        """
        PERSONAL_INCOME_ID = "PI"  # 미국 개인소득 시리즈 ID

        # 개인소득 데이터 조회 (과거 → 현재 순서로 정렬)
        personal_income = DataTools.get_fred_data(PERSONAL_INCOME_ID, observation_start, observation_end, limit, sort_order="asc")

        # 개인소득 데이터에서 전월 대비 변화율 계산
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
                "personal_income": f"{value:,.0f}",  # 천 단위 콤마 추가
                "mom_change": change_symbol
            })

            prev_value = value  # 현재 값을 다음 루프의 이전 값으로 저장

        return formatted_data

    @tool
    def get_mortgage_rate_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "Recent 30-year fixed mortgage rate data from FRED API"]:
        """
        Retrieves U.S. 30-year fixed mortgage rate data from FRED API within the specified date range.
        """
        MORTGAGE_RATE_ID = "MORTGAGE30US"  # 미국 30년 고정 주택담보대출 금리 시리즈 ID

        # 모기지 금리 데이터 조회 (최신 → 과거 정렬)
        mortgage_rate = DataTools.get_fred_data(MORTGAGE_RATE_ID, observation_start, observation_end, limit, sort_order="desc")

        # 최종 데이터 리스트 생성
        return [
            {
                "date": entry["date"],
                "mortgage_rate": f"{float(entry['value']):.2f}%"  # 소수점 두 자리까지 변환
            }
            for entry in mortgage_rate
        ]
    

    @tool
    def get_unemployment_rate_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "Recent U.S. Unemployment Rate data from FRED API"]:
        """
        Retrieves U.S. Unemployment Rate data from FRED API within the specified date range.
        """
        UNEMPLOYMENT_ID = "UNRATE"  # 미국 실업률 시리즈 ID

        # 실업률 데이터 조회
        unemployment_data = DataTools.get_fred_data(UNEMPLOYMENT_ID, observation_start, observation_end, limit, sort_order="desc")

        # 최종 데이터 리스트 생성
        return [
            {
                "date": entry["date"],
                "unemployment_rate": f"{float(entry['value']):.1f}%"  # 소수점 한 자리까지 변환
            }
            for entry in unemployment_data
        ]

    @tool
    def get_jobless_claims_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "Recent U.S. Jobless Claims data from FRED API"]:
        """
        Retrieves U.S. Initial Jobless Claims data from FRED API within the specified date range.
        """
        JOBLESS_CLAIMS_ID = "ICSA"  # 신규 실업수당 청구건수 시리즈 ID

        # 신규 실업수당 청구건수 데이터 조회
        jobless_claims = DataTools.get_fred_data(JOBLESS_CLAIMS_ID, observation_start, observation_end, limit, sort_order="desc")

        # 최종 데이터 리스트 생성
        return [
            {
                "date": entry["date"],
                "jobless_claims": f"{int(float(entry['value'])):,}"  # 천 단위 콤마 추가
            }
            for entry in jobless_claims
        ]
