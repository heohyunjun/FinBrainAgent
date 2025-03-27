import os
import requests
import pandas as pd

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
