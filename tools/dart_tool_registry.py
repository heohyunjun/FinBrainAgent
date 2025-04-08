from langchain.tools import tool
from typing import Optional
from tools.dart_insider_trade_tool import (
    DARTMajorStockReportAPI, DARTExecutiveShareholdingAPI, 
    DartTSDispostionAPI, DartTSAcquisionAPI,
    DartTSAcquisionTrustContractAPI,
    DartTSAcquisionTrustCancelAPI
    )


class DartToolRegistry:
    exec_api = DARTExecutiveShareholdingAPI()
    major_api = DARTMajorStockReportAPI()
    ts_disposal_api = DartTSDispostionAPI()
    ts_acquisition_api = DartTSAcquisionAPI()
    ts_trust_contract_api = DartTSAcquisionTrustContractAPI()
    ts_trust_cancel_api = DartTSAcquisionTrustCancelAPI()

    @staticmethod
    @tool
    def get_executive_shareholding_tool(
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """
        임원 및 주요주주 소유 보고서 조회하는 도구

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
        df = DartToolRegistry.exec_api._get_executive_shareholding(
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )
        if df.empty:
            return {"messages": f"해당 정보로 데이터를 찾을 수 없습니다."}
        else:
            return {"messages" : df.to_dict(orient="records")}

    @staticmethod
    @tool
    def get_major_stock_reports_tool(
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
        대량보유 상황보고 정보를 제공하는 도구 
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
        df = DartToolRegistry.major_api._get_major_stock_reports(
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

        if df.empty:
            return {"messages": f"해당 정보로 데이터를 찾을 수 없습니다."}
        else:
            return {"messages" : df.to_dict(orient="records")}

    @staticmethod
    @tool
    def get_ts_disposal_tool(
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: str = None,
        end_date: str = None,
        reference_date: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """
        자기주식 처분 결정 내역을 조회하는 도구

        Args:
            stock_code (str, optional): 종목코드 (예: "005930")
            corp_name (str, optional): 회사명 (예: "삼성전자")
            start_date (str): 조회 시작일 ("YYYY-MM-DD")
            end_date (str): 조회 종료일 ("YYYY-MM-DD")
            reference_date (Optional[str]): 현재시간 
            limit (int, optional): 최대 결과 개수. 기본값은 20

        Returns:
            list[dict]: 자기주식 처분 결정 내역 리스트
        """
        df = DartToolRegistry.ts_disposal_api._get_treasury_stock_disposals(
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )
        if df.empty:
            return {"messages": f"해당 정보로 데이터를 찾을 수 없습니다."}
        else:
            return {"messages" : df.to_dict(orient="records")}

    @staticmethod
    @tool
    def get_ts_acquisition_tool(
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """
        자기주식 취득 결정 내역을 조회하는 도구

        Args:
            stock_code (str, optional): 조회할 기업의 종목코드. 예: "005930"
            corp_name (str, optional): 조회할 기업의 이름. 예: "삼성전자"
            start_date (str): 조회 시작일. 형식: "YYYY-MM-DD"
            end_date (str): 조회 종료일. 형식: "YYYY-MM-DD"
            reference_date (Optional[str]): 현재시간 
            limit (int, optional): 결과 최대 수. 기본값은 20개

        Returns:
            list[dict]: 자기주식 취득결정 공시 리스트 (최신순 정렬)
        """
        df = DartToolRegistry.ts_acquisition_api._get_treasury_stock_acquisitions(
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )
        if df.empty:
            return {"messages": f"해당 정보로 데이터를 찾을 수 없습니다."}
        else:
            return {"messages" : df.to_dict(orient="records")}

    @staticmethod
    @tool
    def get_ts_trust_contract_tool(
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """
        자기주식취득 신탁계약 체결 결정을 조회하는 도구

        Args:
            stock_code (Optional[str]): 종목코드 (예: "005930")
            corp_name (Optional[str]): 회사명 (예: "삼성전자")
            start_date (Optional[str]): 시작일 ("YYYY-MM-DD")
            end_date (Optional[str]): 종료일 ("YYYY-MM-DD")
            reference_date (Optional[str]): 현재시간 
            limit (int): 결과 개수 제한 (기본값 20)

        Returns:
            list[dict]: 조회된 자기주식 취득 신탁계약 공시 데이터
        """
        df = DartToolRegistry.ts_trust_contract_api._get_treasury_stock_trust_contracts(
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )
        if df.empty:
            return {"messages": f"해당 정보로 데이터를 찾을 수 없습니다."}
        else:
            return {"messages" : df.to_dict(orient="records")}

    @staticmethod
    @tool
    def get_ts_trust_cancel_tool(
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """
        자기주식취득 신탁계약 해지 결정 내역을 조회하는 도구

        Args:
            stock_code (str, optional): 종목코드 (예: "005930")
            corp_name (str, optional): 회사명 (예: "삼성전자")
            start_date (str, optional): 시작일 ("YYYY-MM-DD")
            end_date (str, optional): 종료일 ("YYYY-MM-DD")
            reference_date (str, optional): 기준일 (없으면 최근 30일로 계산)
            limit (int, optional): 최대 결과 수 (기본값 20)

        Returns:
            list[dict]: 해지된 신탁계약 공시 리스트
        """
        df = DartToolRegistry.ts_trust_cancel_api._get_treasury_stock_trust_cancellations(
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )
        if df.empty:
            return {"messages": f"해당 정보로 데이터를 찾을 수 없습니다."}
        else:
            return {"messages" : df.to_dict(orient="records")}
