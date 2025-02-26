import requests
import yfinance as yf
from typing import TypedDict, List, Annotated, Literal, Dict, Callable, TypeVar, Tuple, Type, Generic,Optional, Any
import os
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
import pandas as pd


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

class DataCleansingTools:
    @staticmethod
    def _to_float(value: str) -> float:
        """Helper to convert string values (e.g., '1,234.5', '5.0%') to float."""
        if isinstance(value, str):
            return float(value.replace(",", "").replace("%", ""))
        return float(value)

    @tool
    def remove_duplicates(
        data: Annotated[List[Dict], "List of dictionaries containing raw financial data"]
    ) -> Annotated[List[Dict], "List of dictionaries with duplicate entries removed"]:
        """Remove duplicate entries based on all keys."""
        df = pd.DataFrame(data)
        df.drop_duplicates(inplace=True)
        return df.to_dict("records")

    @tool
    def standardize_dates(
        data: Annotated[List[Dict], "List of dictionaries containing raw financial data"],
        date_key: Annotated[str, "Key name for the date field in each dictionary"] = "date"
    ) -> Annotated[List[Dict], "List of dictionaries with dates standardized to YYYY-MM-DD"]:
        """Ensure dates are in YYYY-MM-DD format."""
        for entry in data:
            if date_key in entry and entry[date_key]:
                entry[date_key] = pd.to_datetime(entry[date_key]).strftime("%Y-%m-%d")
        return data

    @tool
    def normalize_numbers(
        data: Annotated[List[Dict], "List of dictionaries containing raw financial data"],
        keys: Annotated[List[str], "List of keys whose values should be converted to floats"]
    ) -> Annotated[List[Dict], "List of dictionaries with specified numeric fields as floats"]:
        """Convert numeric strings (e.g., '1,234', '5.0%') to floats for specified keys."""
        for entry in data:
            for key in keys:
                if key in entry and entry[key] not in [None, "N/A"]:
                    entry[key] = DataCleansingTools._to_float(entry[key])
        return data

    @tool
    def handle_missing(
        data: Annotated[List[Dict], "List of dictionaries containing raw financial data"],
        keys: Annotated[List[str], "List of keys to check for missing values"],
        default: Annotated[Any, "Default value to replace missing entries (e.g., 0.0, 'Unknown')"] = 0.0
    ) -> Annotated[List[Dict], "List of dictionaries with missing values replaced"]:
        """Replace 'N/A' or None with a default value for specified keys."""
        for entry in data:
            for key in keys:
                if key in entry and entry[key] in [None, "N/A"]:
                    entry[key] = default
        return data

    @tool
    def detect_outliers(
        data: Annotated[List[Dict], "List of dictionaries containing raw financial data"],
        key: Annotated[str, "Key name for the numeric field to check for outliers"],
        threshold: Annotated[float, "Number of standard deviations to define an outlier"] = 3.0
    ) -> Annotated[List[Dict], "List of dictionaries with an 'outlier' boolean field added"]:
        """Flag outliers beyond threshold standard deviations for a numeric key."""
        df = pd.DataFrame(data)
        values = pd.to_numeric(df[key], errors="coerce")
        mean, std = values.mean(), values.std()
        df["outlier"] = values.apply(lambda x: abs(x - mean) > threshold * std if pd.notna(x) else False)
        return df.to_dict("records")

class ReportTools:
    """리포트 생성 및 요약을 위한 도구 모음"""
    
    @tool
    def generate_report_structure(
        data: Annotated[Dict, "Raw data to be included in the report"],
        report_type: Annotated[str, "Type of report (e.g., 'market_analysis', 'economic_indicators', 'investment_recommendation')"]
    ) -> Annotated[Dict, "Structured report outline with sections"]:
        """
        주어진 데이터를 기반으로 리포트 구조를 생성합니다.
        """
        sections = {
            "market_analysis": [
                "시장 개요",
                "주요 지표 분석",
                "시장 동향",
                "리스크 요인",
                "전망"
            ],
            "economic_indicators": [
                "주요 경제 지표 요약",
                "인플레이션 동향",
                "고용 시장 현황",
                "소비자 동향",
                "정책 영향 분석"
            ],
            "investment_recommendation": [
                "투자 요약",
                "시장 기회",
                "위험 요소",
                "투자 전략",
                "실행 계획"
            ]
        }
        
        return {
            "title": f"{report_type.replace('_', ' ').title()} Report",
            "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "sections": sections.get(report_type, ["개요", "분석", "결론"]),
            "data": data
        }

    @tool
    def format_report_section(
        content: Annotated[str, "Raw content for the section"],
        section_type: Annotated[str, "Type of section (e.g., 'summary', 'analysis', 'recommendation')"],
        max_length: Annotated[int, "Maximum character length for the section"] = 1000
    ) -> Annotated[str, "Formatted section content"]:
        """
        리포트 섹션의 내용을 지정된 형식과 길이로 포맷팅합니다.
        """
        # 내용 길이 제한
        formatted_content = content[:max_length] if len(content) > max_length else content
        
        return formatted_content

    @tool
    def extract_key_points(
        text: Annotated[str, "Text to analyze"],
        max_points: Annotated[int, "Maximum number of key points to extract"] = 5
    ) -> Annotated[List[str], "List of extracted key points"]:
        """
        텍스트에서 주요 포인트를 추출합니다.
        """
        # 문장 단위로 분리
        sentences = text.split('. ')
        
        # 중요도에 따라 문장 선택 (여기서는 간단히 처음 max_points개 선택)
        key_points = [s.strip() + '.' for s in sentences[:max_points] if s.strip()]
        
        return key_points

    @tool
    def generate_executive_summary(
        report_data: Annotated[Dict, "Complete report data"],
        max_length: Annotated[int, "Maximum character length for the summary"] = 500
    ) -> Annotated[str, "Concise executive summary"]:
        """
        전체 리포트에서 핵심적인 내용만을 추출하여 요약본을 생성합니다.
        """
        # 각 섹션의 첫 번째 문장이나 주요 포인트를 결합
        summary_points = []
        for section in report_data.get("sections", []):
            if isinstance(section, dict) and "content" in section:
                first_sentence = section["content"].split('. ')[0] + '.'
                summary_points.append(first_sentence)
        
        summary = " ".join(summary_points)
        return summary[:max_length] if len(summary) > max_length else summary