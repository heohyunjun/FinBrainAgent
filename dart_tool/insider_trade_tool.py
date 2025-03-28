import os
import requests
import pandas as pd
from typing import Optional
from langchain.tools import tool
from datetime import datetime, timedelta

from dart_tool.dart_treasury_stock_decision_field_definitions import (
    Dart_TreasuryStockDispositionDecision_UnNecessary_Fields as DTUF,
    Dart_TreasuryStockAcquisitionDecision_UnNecessary_Fields as DTAUF,
    )

from dart_tool.dart_treasury_stock_trust_field_definitions import(
    Dart_TrustStockAcquisitionDecision_Unnecessary_Fields as DTTUF
)

class DartBaseAPI:
    """
    DART API의 공통 로직을 처리하는 기반 클래스.
    """

    def __init__(
        self,
        corp_list_file: Optional[str] = None
    ):
        self.api_key = os.getenv("DART_API_KEY")
        self.base_url = "https://opendart.fss.or.kr/api"
        self.corp_list_file = corp_list_file or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "corp_list.pkl"
        )

        if self.api_key is None:
            raise ValueError("DART_API_KEY 환경변수가 설정되지 않았습니다.")

    def _fetch_dart_data(self, endpoint: str, params: dict) -> dict:
        """
        공통적인 DART API 요청 메서드.
        """
        params['crtfc_key'] = self.api_key
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"요청 실패: {e}")
            return {"status": "error", "message": str(e)}

    def return_corp_code(
        self,
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None
    ) -> Optional[str]:
        """
        종목코드 또는 회사명을 통해 기업 고유번호(corp_code)를 반환합니다.
        """
        if stock_code is None and corp_name is None:
            print("종목코드 또는 회사명 중 하나는 반드시 입력해야 합니다.")
            return None

        try:
            df = pd.read_pickle(self.corp_list_file)

            if stock_code:
                result = df[df['stock_code'] == stock_code]
            elif corp_name:
                clean_name = corp_name.strip().replace(" ", "")
                result = df[df['corp_name'].str.replace(" ", "") == clean_name]
            else:
                return None

            if not result.empty:
                return result.iloc[0]['corp_code']
            else:
                print(f"'{stock_code or corp_name}'에 해당하는 기업을 찾을 수 없습니다.")
                return None

        except Exception as e:
            print(f"기업코드 조회 중 오류 발생: {str(e)}")
            return None

    def filter_by_dates(self, 
        df: pd.DataFrame,
        date_column: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        날짜 필터링을 수행하는 공통 메서드.
        """
        if date_column not in df.columns:
            print(f"'{date_column}' 컬럼이 DataFrame에 존재하지 않습니다.")
            return df

        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

        if start_date or end_date:
            if start_date:
                df = df[df[date_column] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df[date_column] <= pd.to_datetime(end_date)]
        elif reference_date:
            ref = pd.to_datetime(reference_date)
            start = ref - timedelta(days=30)
            df = df[(df[date_column] >= start) & (df[date_column] <= ref)]

        return df
    
    def resolve_date_range(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        reference_date: Optional[str]
    ) -> tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
        """
        start_date, end_date, reference_date를 기준으로 조회 시작일과 종료일을 계산.
        """
        if start_date and end_date:
            return pd.to_datetime(start_date), pd.to_datetime(end_date)

        if start_date and reference_date:
            return pd.to_datetime(start_date), pd.to_datetime(reference_date)

        if not start_date and not end_date and reference_date:
            ref = pd.to_datetime(reference_date)
            return ref - timedelta(days=30), ref

        print("날짜 정보가 부족합니다. 최소 start_date 또는 reference_date가 필요합니다.")
        return None, None
class DARTExecutiveShareholdingAPI(DartBaseAPI):
    """
    임원 및 주요주주 소유 보고 API를 처리하는 클래스.
    """

    def _get_executive_shareholding(self,
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> pd.DataFrame:
        """
        내부자 소유 보고서 데이터 조회 (필터링 포함).
        종목코드 또는 회사명을 통해 기업코드를 자동 추론합니다.
        """
        # 기업코드 리턴
        corp_code = self.return_corp_code(stock_code=stock_code, corp_name=corp_name)
        if corp_code is None:
            print("기업코드 조회 실패")
            return pd.DataFrame()
        
        endpoint = "elestock.json"
        params = {"corp_code": corp_code}
        data = self._fetch_dart_data(endpoint, params)

        if data['status'] != '000':
            print(f"오류 발생: {data['status']} - {data['message']}")
            return pd.DataFrame()

        df = pd.DataFrame(data['list'])
        df['rcept_dt'] = pd.to_datetime(df['rcept_dt'], errors='coerce')

        df = self.filter_by_dates(
            df,
            date_column="rcept_dt",
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date
        )

        # 정렬 및 필드 정리
        df = df.sort_values(by='rcept_dt', ascending=False)
        df = df.drop(columns=["rcept_no"], errors="ignore")

        return df.head(limit).reset_index(drop=True)

class DARTMajorStockReportAPI(DartBaseAPI):
    """
    DART 대량보유 상황보고서(majorstock) API를 처리하는 클래스.
    """
    def _get_major_stock_reports(
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
    ) -> pd.DataFrame:
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
            start_date (str, optional): 시작일
            end_date (str, optional): 종료일
            reference_date (str, optional): 현재 시간 
            limit (int, optional): 최대 결과 수

        Returns:
            list[dict]: 필터링된 대량보유 보고서, 내부자 주식 보유 및 변동 내역이 담긴 딕셔너리 리스트.
                        각 항목은 보고자, 임원직위, 소유 주식 수, 증감 내역 등을 포함함.
        """
        corp_code = self.return_corp_code(stock_code=stock_code, corp_name=corp_name)
        if corp_code is None:
            print("기업코드 조회 실패")
            return pd.DataFrame()

        endpoint = "majorstock.json"
        params = {"corp_code": corp_code}
        data = self._fetch_dart_data(endpoint, params)

        if data["status"] != "000":
            print(f"오류 발생: {data['status']} - {data['message']}")
            return pd.DataFrame()

        df = pd.DataFrame(data["list"])
        df = self.filter_by_dates(
            df,
            date_column="rcept_dt",
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date
        )

        # 수치 컬럼 전처리
        for col in ["stkqy", "stkqy_irds"]:
            df[col] = df[col].astype(str).str.replace(",", "", regex=False).astype(int)
        for col in ["stkrt", "stkrt_irds"]:
            df[col] = df[col].astype(float)

        # 수치 필터
        if min_ratio is not None:
            df = df[df["stkrt"] >= min_ratio]
        if min_ratio_change is not None:
            df = df[df["stkrt_irds"] >= min_ratio_change]
        if min_share_count is not None:
            df = df[df["stkqy"] >= min_share_count]
        if min_share_change is not None:
            df = df[df["stkqy_irds"] >= min_share_change]
        if max_share_change is not None:
            df = df[df["stkqy_irds"] <= max_share_change]

        df = df.sort_values(by="rcept_dt", ascending=False)

        DROP_FIELDS = ["rcept_no", "ctr_stkqy", "ctr_stkrt"]
        df = df.drop(columns=DROP_FIELDS, errors="ignore")

        return df.head(limit).reset_index(drop=True)
    


class DartTSDectisonBaseAPI(DartBaseAPI):
    def _fetch_decision_data(
        self,
        endpoint: str,
        date_column: str,
        drop_fields: list[str],
        stock_code: Optional[str],
        corp_name: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
        reference_date: Optional[str],
        date_format: str = "%Y년 %m월 %d일",
        limit: int = 20
    ) -> pd.DataFrame:
        if not start_date and not end_date and not reference_date:
            print("start_date, end_date, reference_date 중 하나는 필수입니다.")
            return pd.DataFrame()

        corp_code = self.return_corp_code(stock_code, corp_name)
        if corp_code is None:
            print("기업코드 조회 실패")
            return pd.DataFrame()

        start_dt, end_dt = self.resolve_date_range(start_date, end_date, reference_date)
        if not start_dt or not end_dt:
            return pd.DataFrame()

        params = {
            "corp_code": corp_code,
            "bgn_de": start_dt.strftime("%Y%m%d"),
            "end_de": end_dt.strftime("%Y%m%d")
        }

        data = self._fetch_dart_data(endpoint, params)
        if data["status"] != "000":
            print(f"오류 발생: {data['status']} - {data['message']}")
            return pd.DataFrame()

        df = pd.DataFrame(data["list"])
        if date_column in df.columns:
            df[date_column] = pd.to_datetime(df[date_column], format=date_format, errors="coerce")

        df = self.filter_by_dates(
            df,
            date_column=date_column,
            start_date=start_dt.strftime("%Y-%m-%d"),
            end_date=end_dt.strftime("%Y-%m-%d"),
            reference_date=None
        )

        df = df.drop(columns=drop_fields, errors="ignore")
        df = df.sort_values(by=date_column, ascending=False)

        return df.head(limit).reset_index(drop=True)


class DartTSAcquisionAPI(DartTSDectisonBaseAPI):
    def _get_treasury_stock_acquisitions(
        self,
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> pd.DataFrame:
        """
        자기주식 취득 결정 내역을 반환

        Args:
            stock_code (Optional[str]): 종목코드
            corp_name (Optional[str]): 회사명
            start_date (str): 검색 시작일자 (YYYY-MM-DD)
            end_date (str): 검색 종료일자 (YYYY-MM-DD)
            limit (int): 최대 리턴 개수

        Returns:
            pd.DataFrame: 필터링된 자기주식 취득 결정 내역
        """

        drop_fields = [
            DTAUF.RECEIPT_NO,
            DTAUF.CORP_CLASS,
            DTAUF.CORP_CODE,
            DTAUF.BROKER,
            DTAUF.HOLD_BGN,
            DTAUF.HOLD_END,
            DTAUF.AQ_WTN_DIV_OSTK,
            DTAUF.AQ_WTN_DIV_OSTK_RT,
            DTAUF.AQ_WTN_DIV_ESTK,
            DTAUF.AQ_WTN_DIV_ESTK_RT,
            DTAUF.EAQ_OSTK,
            DTAUF.EAQ_OSTK_RT,
            DTAUF.EAQ_ESTK,
            DTAUF.EAQ_ESTK_RT,
            DTAUF.OUTSIDE_DIR_PRESENT,
            DTAUF.OUTSIDE_DIR_ABSENT,
            DTAUF.AUDIT_ATTEND,
            DTAUF.DAILY_LIMIT_COMMON,
            DTAUF.DAILY_LIMIT_ETC,
        ]

        return self._fetch_decision_data(
            endpoint="tsstkAqDecsn.json",
            date_column="aq_dd",
            drop_fields=drop_fields,
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )

class DartTSDispostionAPI(DartTSDectisonBaseAPI):
    def _get_treasury_stock_disposals(
        self,
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> pd.DataFrame:

        drop_fields = [
            DTUF.RECEIPT_NO,
            DTUF.CORP_CODE,
            DTUF.CORP_CLASS,
            DTUF.STOCK_ETC,
            DTUF.PRICE_ETC,
            DTUF.AMOUNT_ETC,
            DTUF.BROKER,
            DTUF.NOTE,
            DTUF.OUTSIDE_DIR_PRESENT,
            DTUF.OUTSIDE_DIR_ABSENT,
            DTUF.AUDIT_ATTEND,
            DTUF.DAILY_LIMIT_COMMON,
            DTUF.DAILY_LIMIT_ETC,
            DTUF.AQ_WTN_DIV_OSTK,
            DTUF.AQ_WTN_DIV_OSTK_RT,
            DTUF.AQ_WTN_DIV_ESTK,
            DTUF.AQ_WTN_DIV_ESTK_RT,
            DTUF.EAQ_OSTK,
            DTUF.EAQ_OSTK_RT,
            DTUF.EAQ_ESTK,
            DTUF.EAQ_ESTK_RT
        ]

        return self._fetch_decision_data(
            endpoint="tsstkDpDecsn.json",
            date_column="dp_dd",
            drop_fields=drop_fields,
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )


class DartTSAcquisionTrustAPI(DartTSDectisonBaseAPI):
    """
    DART 자기주식취득 신탁계약 체결 결정 API(tsstkAqTrctrCnsDecsn)를 처리하는 클래스.
    """

    def _get_treasury_stock_trust_contracts(
        self,
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> pd.DataFrame:
        """
        자기주식취득 신탁계약 체결 결정 내역을 반환

        Args:
            stock_code (Optional[str]): 종목코드
            corp_name (Optional[str]): 회사명
            start_date (str, optional): 검색 시작일자 (YYYY-MM-DD)
            end_date (str, optional): 검색 종료일자 (YYYY-MM-DD)
            reference_date (str, optional): 현재시간
            limit (int): 최대 리턴 개수

        Returns:
            pd.DataFrame: 필터링된 자기주식 취득 신탁계약 체결 내역
        """
        drop_fields = [
            DTTUF.RECEIPT_NO,
            DTTUF.CORP_CLASS,
            DTTUF.CORP_CODE,
            DTTUF.OUTSIDE_DIR_PRESENT,
            DTTUF.OUTSIDE_DIR_ABSENT,
            DTTUF.AUDIT_ATTEND,
            DTTUF.BROKER,
            DTTUF.AQ_WTN_DIV_OSTK,
            DTTUF.AQ_WTN_DIV_OSTK_RT,
            DTTUF.AQ_WTN_DIV_ESTK,
            DTTUF.AQ_WTN_DIV_ESTK_RT,
            DTTUF.EAQ_OSTK,
            DTTUF.EAQ_OSTK_RT,
            DTTUF.EAQ_ESTK,
            DTTUF.EAQ_ESTK_RT
        ]

        df = self._fetch_decision_data(
            endpoint="tsstkAqTrctrCnsDecsn.json",
            date_column="bddd",
            drop_fields=drop_fields,
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )

        # 추가 날짜 필드 파싱
        for col in ["ctr_pd_bgd", "ctr_pd_edd", "ctr_cns_prd"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format="%Y년 %m월 %d일", errors="coerce")

        return df