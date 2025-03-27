import os
import requests
import pandas as pd
from typing import Optional
from langchain.tools import tool


class DartBaseAPI:
    """
    DART API의 공통 로직을 처리하는 기반 클래스.
    """
    DART_API_KEY = os.getenv("DART_API_KEY")
    DART_BASE_URL = "https://opendart.fss.or.kr/api"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CORP_LIST_FILE = os.path.join(BASE_DIR, "corp_list.pkl")

    @staticmethod
    def _fetch_dart_data(endpoint: str, params: dict) -> dict:
        """
        공통적인 DART API 요청 메서드.
        
        Args:
            endpoint (str): API 엔드포인트 경로
            params (dict): API 요청 파라미터

        Returns:
            dict: API 응답 JSON 데이터
        """
        if DartBaseAPI.DART_API_KEY is None:
            raise ValueError("DART_API_KEY 환경변수가 설정되지 않았습니다.")

        params['crtfc_key'] = DartBaseAPI.DART_API_KEY
        url = f"{DartBaseAPI.DART_BASE_URL}/{endpoint}"

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.RequestException as e:
            print(f"요청 실패: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def return_corp_code(
        stock_code: Optional[str] = None,
        corp_name: Optional[str] = None
    ) -> Optional[str]:
        """
        종목코드 또는 회사명을 통해 기업 고유번호(corp_code)를 반환합니다.

        Args:
            stock_code (Optional[str]): 6자리 종목코드 (예: "005930")
            corp_name (Optional[str]): 회사명 (예: "삼성전자")

        Returns:
            Optional[str]: 고유번호(corp_code) 또는 None
        """
        if stock_code is None and corp_name is None:
            print("종목코드 또는 회사명 중 하나는 반드시 입력해야 합니다.")
            return None

        try:
            df = pd.read_pickle(DartBaseAPI.CORP_LIST_FILE)

            if stock_code:
                result = df[df['stock_code'] == stock_code]
            elif corp_name:
                clean_name  = corp_name.strip().replace(" ", "")
                df['corp_name_cleaned'] = df['corp_name'].str.replace(" ", "")
                result = df[df['corp_name_cleaned'] == clean_name ]
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
class DARTExecutiveShareholdingAPI(DartBaseAPI):
    """
    임원 및 주요주주 소유 보고 API를 처리하는 클래스.
    """

    @staticmethod
    def _get_executive_shareholding(
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
        # 기업코드 리턴턴
        corp_code = DartBaseAPI.resolve_corp_code(stock_code=stock_code, corp_name=corp_name)
        if corp_code is None:
            print("기업코드 조회 실패 - 유효한 종목코드 또는 회사명을 입력하세요.")
            return pd.DataFrame()
        
        endpoint = "elestock.json"
        params = {"corp_code": corp_code}
        data = DartBaseAPI._fetch_dart_data(endpoint, params)

        if data['status'] != '000':
            print(f"오류 발생: {data['status']} - {data['message']}")
            return pd.DataFrame()

        df = pd.DataFrame(data['list'])
        df['rcept_dt'] = pd.to_datetime(df['rcept_dt'], errors='coerce')
        # 날짜 필터 로직
        if start_date or end_date:
            if start_date:
                df = df[df['rcept_dt'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['rcept_dt'] <= pd.to_datetime(end_date)]

        elif reference_date:
            ref = pd.to_datetime(reference_date)
            start = ref - pd.Timedelta(days=30)
            df = df[(df['rcept_dt'] >= start) & (df['rcept_dt'] <= ref)]

        # 정렬 및 필드 정리
        df = df.sort_values(by='rcept_dt', ascending=False)
        df = df.drop(columns=["rcept_no"], errors="ignore")

        return df.head(limit).reset_index(drop=True)

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
        LangGraph용 툴 메서드: 내부자 거래 내역 반환
        """
        df = DARTExecutiveShareholdingAPI._get_executive_shareholding(
            stock_code=stock_code,
            corp_name=corp_name,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )
        return df.to_dict(orient="records")