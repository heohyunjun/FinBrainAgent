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


class DARTExecutiveShareholdingAPI(DartBaseAPI):
    """
    임원 및 주요주주 소유 보고 API를 처리하는 클래스.
    """

    @staticmethod
    def _get_executive_shareholding(
        corp_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> pd.DataFrame:
        """
        내부자 소유 보고서 데이터 조회 (필터링 포함).
        """
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
        corp_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_date: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """
        LangGraph용 툴 메서드: 내부자 거래 내역 반환
        """
        df = DARTExecutiveShareholdingAPI._get_executive_shareholding(
            corp_code=corp_code,
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=limit
        )
        return df.to_dict(orient="records")