from langchain.tools import tool
from typing import Optional
from insider_trade_tool import DARTMajorStockReportAPI, DARTExecutiveShareholdingAPI, DARTTreasuryStockDispositionDecisionAPI


class DartToolRegistry:
    """
    LangGraph에 등록할 DART 기반 툴들을 모아두는 레지스트리 클래스.
    각 툴은 내부적으로 인스턴스를 호출하며, self 없이 사용할 수 있도록 래핑됨.
    """

    def __init__(self):
        self.exec_shareholding_api = DARTExecutiveShareholdingAPI()
        self.major_stock_api = DARTMajorStockReportAPI()
        self.ts_disposal_api = DARTTreasuryStockDispositionDecisionAPI()

    @tool
    def get_executive_shareholding_tool(
        self,
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """
        임원 및 주요주주 소유 보고서 조회 도구

        Args:
            stock_code (str, optional): 종목코드
            corp_name (str, optional): 회사명
            start_date (str): 조회 시작일 ("YYYY-MM-DD")
            end_date (str): 조회 종료일 ("YYYY-MM-DD")
            reference_date (str, optional): 현재 시간 
            limit (int, optional): 최대 결과 수

        Returns:
            list[dict]: 내부자 주식 보유 및 변동 내역이 담긴 딕셔너리 리스트.
                        각 항목은 보고자, 임원직위, 소유 주식 수, 증감 내역 등을 포함함.
        """
        df = self.exec_api._get_executive_shareholding(
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )
        return df.to_dict(orient="records")

    @tool
    def get_major_stock_reports_tool(
        self,
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        min_ratio: Optional[float] = None,
        min_ratio_change: Optional[float] = None,
        min_share_count: Optional[int] = None,
        min_share_change: Optional[int] = None,
        max_share_change: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """
        대량보유 상황 보고서 조회 도구 
        Args:
            stock_code (str, optional): 종목코드
            corp_name (str, optional): 회사명
            min_ratio (float, optional): 최소 보유비율
            min_ratio_change (float, optional): 보유비율 증감 필터
            min_share_count (int, optional): 최소 주식 보유 수
            min_share_change (int, optional): 최소 주식 증가 수
            max_share_change (int, optional): 최대 주식 감소 수
            start_date (str): 조회 시작일 ("YYYY-MM-DD")
            end_date (str): 조회 종료일 ("YYYY-MM-DD")
            reference_date (str, optional): 현재 시간 
            limit (int, optional): 최대 결과 수

        Returns:
            list[dict]: 필터링된 대량보유 보고서, 내부자 주식 보유 및 변동 내역이 담긴 딕셔너리 리스트.
                        각 항목은 보고자, 임원직위, 소유 주식 수, 증감 내역 등을 포함함.
        """
        df = self.major_api._get_major_stock_reports(
            stock_code=stock_code,
            corp_name=corp_name,
            min_ratio=min_ratio,
            min_ratio_change=min_ratio_change,
            min_share_count=min_share_count,
            min_share_change=min_share_change,
            max_share_change=max_share_change,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )
        return df.to_dict(orient="records")
    

    @tool
    def get_treasury_stock_disposals_tool(
        self,
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> list[dict]:
        """
        자기주식 처분 결정을 조회하는 LangGraph용 툴입니다.

        Args:
            stock_code (str, optional): 종목코드 (예: "005930")
            corp_name (str, optional): 회사명 (예: "삼성전자")
            start_date (str): 조회 시작일 ("YYYY-MM-DD")
            end_date (str): 조회 종료일 ("YYYY-MM-DD")
            limit (int, optional): 최대 결과 개수. 기본값은 20

        Returns:
            list[dict]: 자기주식 처분 결정 내역 리스트
        """
        df = self._get_treasury_stock_disposals(
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return df.to_dict(orient="records")