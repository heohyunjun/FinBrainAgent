import requests
import yfinance as yf
from typing import List, Annotated, Literal, Dict, Callable, TypeVar, Tuple, Type, Generic, Optional, Any

import os
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
import pandas as pd


class DataTools:
    """에이전트가 사용할 다양한 도구를 관리하는 클래스"""
    
    tavily_max_results = 1
    FRED_API_KEY = os.getenv("FRED_API_KEY")

    @tool
    def get_tavily_search_tool(query: Annotated[str, "Search query"]) -> Annotated[List[Dict], "List of search results"]:
        """
        Performs a web search using the Tavily API to find financial news and data relevant to the request.
        """
        try:
            search_tool = TavilySearchResults(max_results=DataTools.tavily_max_results)
            results = search_tool.invoke(query)
            return results if results else []
        except Exception:
            return []

    @staticmethod
    def get_fred_data(series_id: str, observation_start: str, observation_end: str, limit: int, sort_order: str = "desc") -> List[Dict]:
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
    def get_fred_release_dates(release_id: int, limit: int) -> List[str]:
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
    def get_stock_news(ticker: Annotated[str, "Stock ticker symbol"]) -> Annotated[List[str], "List of stock news summaries"]:
        """
        Retrieves summaries of the latest news related to the given stock ticker.
        """
        stock = yf.Ticker(ticker)
        news = stock.news
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
    ) -> Annotated[List[Dict], "List of Core CPI data entries"]:
        """
        Retrieves Core CPI data (including YoY and MoM percentage changes) from FRED API within the specified date range.
        """
        CORE_CPI_ID = "CPILFESL"
        RELEASE_ID = 10

        core_cpi = DataTools.get_fred_data(CORE_CPI_ID, observation_start, observation_end, limit)
        core_cpi_yoy = DataTools.get_fred_data(CORE_CPI_ID, observation_start, observation_end, limit, units="pc1")
        core_cpi_mom = DataTools.get_fred_data(CORE_CPI_ID, observation_start, observation_end, limit, units="pch")
        release_dates = DataTools.get_fred_release_dates(RELEASE_ID, limit)

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

    @tool
    def get_core_pce_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "List of Core PCE data entries"]:
        """
        Retrieves Core PCE data (including YoY and MoM percentage changes) from FRED API within the specified date range.
        """
        CORE_PCE_ID = "PCEPILFE"
        RELEASE_ID = 54

        core_pce = DataTools.get_fred_data(CORE_PCE_ID, observation_start, observation_end, limit)
        core_pce_yoy = DataTools.get_fred_data(CORE_PCE_ID, observation_start, observation_end, limit, units="pc1")
        core_pce_mom = DataTools.get_fred_data(CORE_PCE_ID, observation_start, observation_end, limit, units="pch")
        release_dates = DataTools.get_fred_release_dates(RELEASE_ID, limit)

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

    @tool
    def get_personal_income_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "List of personal income data entries"]:
        """
        Retrieves U.S. Personal Income data from FRED API within the specified date range, including month-over-month percentage change.
        """
        PERSONAL_INCOME_ID = "PI"
        personal_income = DataTools.get_fred_data(PERSONAL_INCOME_ID, observation_start, observation_end, limit, sort_order="asc")

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

    @tool
    def get_mortgage_rate_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "List of mortgage rate data entries"]:
        """
        Retrieves U.S. 30-year fixed mortgage rate data from FRED API within the specified date range.
        """
        MORTGAGE_RATE_ID = "MORTGAGE30US"
        mortgage_rate = DataTools.get_fred_data(MORTGAGE_RATE_ID, observation_start, observation_end, limit, sort_order="desc")

        if not mortgage_rate:
            return []

        return [
            {
                "date": entry["date"],
                "mortgage_rate": f"{float(entry['value']):.2f}%"
            }
            for entry in mortgage_rate
        ]

    @tool
    def get_unemployment_rate_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "List of unemployment rate data entries"]:
        """
        Retrieves U.S. Unemployment Rate data from FRED API within the specified date range.
        """
        UNEMPLOYMENT_ID = "UNRATE"
        unemployment_data = DataTools.get_fred_data(UNEMPLOYMENT_ID, observation_start, observation_end, limit, sort_order="desc")

        if not unemployment_data:
            return []

        return [
            {
                "date": entry["date"],
                "unemployment_rate": f"{float(entry['value']):.1f}%"
            }
            for entry in unemployment_data
        ]

    @tool
    def get_jobless_claims_data(
        observation_start: Annotated[str, "Start date for observations (YYYY-MM-DD)"],
        observation_end: Annotated[str, "End date for observations (YYYY-MM-DD)"],
        limit: Annotated[int, "Maximum number of results to return"]
    ) -> Annotated[List[Dict], "List of jobless claims data entries"]:
        """
        Retrieves U.S. Initial Jobless Claims data from FRED API within the specified date range.
        """
        JOBLESS_CLAIMS_ID = "ICSA"
        jobless_claims = DataTools.get_fred_data(JOBLESS_CLAIMS_ID, observation_start, observation_end, limit, sort_order="desc")

        if not jobless_claims:
            return []

        return [
            {
                "date": entry["date"],
                "jobless_claims": f"{int(float(entry['value'])):,}"
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
    ) -> Annotated[List[Dict], "List of deduplicated data entries"]:
        """Remove duplicate entries based on all keys."""
        if not data:
            return []
        df = pd.DataFrame(data)
        df.drop_duplicates(inplace=True)
        return df.to_dict("records")

    @tool
    def standardize_dates(
        data: Annotated[List[Dict], "List of dictionaries containing raw financial data"],
        date_key: Annotated[str, "Key name for the date field in each dictionary"] = "date"
    ) -> Annotated[List[Dict], "List of data entries with standardized dates"]:
        """Ensure dates are in YYYY-MM-DD format."""
        if not data:
            return []
        for entry in data:
            if date_key in entry and entry[date_key]:
                entry[date_key] = pd.to_datetime(entry[date_key]).strftime("%Y-%m-%d")
        return data

    @tool
    def normalize_numbers(
        data: Annotated[List[Dict], "List of dictionaries containing raw financial data"],
        keys: Annotated[List[str], "List of keys whose values should be converted to floats"]
    ) -> Annotated[List[Dict], "List of data entries with normalized numbers"]:
        """Convert numeric strings (e.g., '1,234', '5.0%') to floats for specified keys."""
        if not data:
            return []
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
    ) -> Annotated[List[Dict], "List of data entries with missing values handled"]:
        """Replace 'N/A' or None with a default value for specified keys."""
        if not data:
            return []
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
    ) -> Annotated[List[Dict], "List of data entries with outliers flagged"]:
        """Flag outliers beyond threshold standard deviations for a numeric key."""
        if not data:
            return []
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
    ) -> Annotated[Dict, "Structured report outline"]:
        """
        Generates a report structure based on the provided data.
        """
        if not data:
            return {}
        sections = {
            "market_analysis": ["시장 개요", "주요 지표 분석", "시장 동향", "리스크 요인", "전망"],
            "economic_indicators": ["주요 경제 지표 요약", "인플레이션 동향", "고용 시장 현황", "소비자 동향", "정책 영향 분석"],
            "investment_recommendation": ["투자 요약", "시장 기회", "위험 요소", "투자 전략", "실행 계획"]
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
        Formats the content of a report section according to specified format and length.
        """
        if not content.strip():
            return ""
        return content[:max_length] if len(content) > max_length else content

    @tool
    def extract_key_points(
        text: Annotated[str, "Text to analyze"],
        max_points: Annotated[int, "Maximum number of key points to extract"] = 5
    ) -> Annotated[List[str], "List of extracted key points"]:
        """
        Extracts key points from the provided text.
        """
        if not text.strip():
            return []
        sentences = text.split('. ')
        return [s.strip() + '.' for s in sentences[:max_points] if s.strip()]

    @tool
    def generate_executive_summary(
        report_data: Annotated[Dict, "Complete report data"],
        max_length: Annotated[int, "Maximum character length for the summary"] = 500
    ) -> Annotated[str, "Executive summary"]:
        """
        Generates an executive summary by extracting essential information from the complete report.
        """
        if not report_data or "sections" not in report_data:
            return ""
        summary_points = []
        for section in report_data.get("sections", []):
            if isinstance(section, dict) and "content" in section:
                first_sentence = section["content"].split('. ')[0] + '.'
                summary_points.append(first_sentence)
        summary = " ".join(summary_points)
        return summary[:max_length] if len(summary) > max_length else summary


class InvestmentTools:
    """Collection of tools for investment strategy development"""
    
    @tool
    def analyze_risk_reward(
        market_data: Annotated[Dict[str, Any], "Market analysis data including trends and indicators"],
        risk_tolerance: Annotated[str, "Risk tolerance level (conservative/moderate/aggressive)"]
    ) -> Annotated[Dict, "Risk-reward analysis results"]:
        """
        Performs risk-reward analysis based on market data.
        """
        if not market_data:
            return {}
        risk_thresholds = {
            "conservative": 0.05,
            "moderate": 0.10,
            "aggressive": 0.15
        }
        return {
            "risk_level": risk_tolerance,
            "max_drawdown": risk_thresholds.get(risk_tolerance, 0.10),
            "risk_factors": ["market_volatility", "economic_indicators", "sector_risks"],
            "potential_returns": {
                "conservative": "3-5%",
                "moderate": "6-10%",
                "aggressive": "11-15%"
            }.get(risk_tolerance, "6-10%")
        }

    @tool
    def generate_asset_allocation(
        risk_profile: Annotated[Dict, "Risk analysis results"],
        market_conditions: Annotated[Dict, "Current market conditions and trends"]
    ) -> Annotated[Dict, "Asset allocation recommendation"]:
        """
        Generates asset allocation strategy based on risk profile and market conditions.
        """
        if not risk_profile or not market_conditions:
            return {}
        allocations = {
            "conservative": {"stocks": 0.30, "bonds": 0.50, "cash": 0.15, "alternatives": 0.05},
            "moderate": {"stocks": 0.50, "bonds": 0.30, "cash": 0.10, "alternatives": 0.10},
            "aggressive": {"stocks": 0.70, "bonds": 0.15, "cash": 0.05, "alternatives": 0.10}
        }
        risk_level = risk_profile.get("risk_level", "moderate")
        base_allocation = allocations.get(risk_level, allocations["moderate"])
        return {
            "asset_allocation": base_allocation,
            "rebalancing_frequency": "Quarterly",
            "sector_weights": {"technology": 0.25, "healthcare": 0.20, "financials": 0.15, "consumer": 0.15, "others": 0.25}
        }

    @tool
    def create_investment_timeline(
        strategy: Annotated[Dict, "Investment strategy details"],
        investment_horizon: Annotated[str, "Investment time horizon (short/medium/long)"]
    ) -> Annotated[Dict, "Investment timeline and milestones"]:
        """
        Creates timeline and milestones for investment strategy execution.
        """
        if not strategy:
            return {}
        horizon_periods = {
            "short": {"period": "1-2 years", "review_frequency": "Monthly"},
            "medium": {"period": "3-5 years", "review_frequency": "Quarterly"},
            "long": {"period": "5+ years", "review_frequency": "Semi-annually"}
        }
        period_info = horizon_periods.get(investment_horizon, horizon_periods["medium"])
        return {
            "timeline": {
                "initial_setup": "Immediate",
                "first_allocation": "Within 1 week",
                "first_review": "1 month",
                "rebalancing": period_info["review_frequency"]
            },
            "milestones": [
                "Initial portfolio setup",
                "First rebalancing check",
                "Quarterly performance review",
                "Annual strategy reassessment"
            ],
            "monitoring_schedule": {
                "frequency": period_info["review_frequency"],
                "metrics": ["performance", "risk_levels", "allocation_drift"]
            }
        }