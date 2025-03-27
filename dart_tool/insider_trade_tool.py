import os
import requests
import pandas as pd
from typing import Optional
from langchain.tools import tool
from datetime import datetime, timedelta


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
            print("기업코드 조회 실패 - 유효한 종목코드 또는 회사명을 입력하세요.")
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