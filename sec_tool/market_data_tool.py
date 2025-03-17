import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dateutil.parser import parse
from langchain.tools import tool
from sec_tool.sec_financial_fiedls_definitions import FinancialNecessaryFields
from langchain_community.agent_toolkits.polygon.toolkit import PolygonToolkit
from langchain_community.utilities.polygon import PolygonAPIWrapper
from dotenv import load_dotenv

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
    def get_stock_price(ticker: str) -> dict:
        """Given a stock ticker, return the price data for the past month"""
        stock_info = yf.download(ticker, period='1mo').to_dict()
        return stock_info

    @staticmethod
    def get_polygon_tools():
        """Polygon API에서 제공하는 모든 도구를 반환합니다."""
        return polygon_tools


class FinancialDataTools:
    """기업 재무 데이터를 다루는 도구 클래스"""

    @staticmethod
    def filter_financial_info(financial_dict: dict) -> pd.DataFrame:
        """
        손익계산서 데이터에서 핵심 지표만 필터링하는 함수.
        
        :param financial_dict: company_research_tool("TSLA") 로 가져온 dict 데이터
        :return: 필터링된 DataFrame (핵심 재무 지표만 포함)
        """
        # financial_info 키에서 DataFrame 가져오기
        financial_data = financial_dict.get("financial_info", pd.DataFrame())

        if financial_data.empty:
            return financial_data  # 데이터가 없으면 그대로 반환

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

        return financial_data.loc[financial_data.index.intersection(key_metrics)]

    @staticmethod
    @tool
    def company_research_tool(ticker: str) -> dict:
        """Given a ticker, return the financial information and SEC filings"""
        company_info = yf.Ticker(ticker)
        financial_info = company_info.get_financials(freq="quarterly")
        sec_filings = company_info.get_sec_filings()

        filtered_financial_info = FinancialDataTools.filter_financial_info(financial_info)
        filtered_filings = SECFilingsTools.filter_sec_filings(sec_filings)

        return {
            'financial_info': filtered_financial_info,
            'sec_filings': filtered_filings
        }


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
