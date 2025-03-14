import requests
from dotenv import load_dotenv
import json
import os

from langchain.tools import tool
class SecInsiderTrade:

    SEC_API_KEY = os.getenv("SEC_API_KEY")
    SEC_API_URL = "https://api.sec-api.io/insider-trading"

    @staticmethod
    def filter_sec_response(response_data):
        """
        SEC API 응답 데이터를 필터링하여 필요한 정보만 반환하는 함수.
        
        KeyError 방지를 위해 모든 키를 안전하게 `.get()` 메서드로 접근한다.

        :param response_data: API 응답 JSON (dict)
        :return: 필터링된 데이터 (list of dict)
        """
        filtered_transactions = []

        for transaction in response_data.get("transactions", []):
            filtered_transaction = {
                "accessionNo": transaction.get("accessionNo", None),
                "filedAt": transaction.get("filedAt", "")[:10], 
                "periodOfReport": transaction.get("periodOfReport", None),
                "documentType": transaction.get("documentType", None),
                "issuer": {
                    "name": transaction.get("issuer", {}).get("name", None),
                    "tradingSymbol": transaction.get("issuer", {}).get("tradingSymbol", None)
                },
                "reportingOwner": {
                    "name": transaction.get("reportingOwner", {}).get("name", None),
                    "relationship": {
                        "isDirector": transaction.get("reportingOwner", {}).get("relationship", {}).get("isDirector", False),
                        "isOfficer": transaction.get("reportingOwner", {}).get("relationship", {}).get("isOfficer", False),
                        "officerTitle": transaction.get("reportingOwner", {}).get("relationship", {}).get("officerTitle", ""),
                        "isTenPercentOwner": transaction.get("reportingOwner", {}).get("relationship", {}).get("isTenPercentOwner", False)
                    }
                },
                "nonDerivativeTransactions": [],
                "derivativeTransactions": [],
                "footnotes": [footnote.get("text", "") for footnote in transaction.get("footnotes", [])]
            }

            # 🔹 비파생상품 거래 필터링 (모든 거래 유형 유지)
            for trans in transaction.get("nonDerivativeTable", {}).get("transactions", []):
                filtered_transaction["nonDerivativeTransactions"].append({
                    "transactionDate": trans.get("transactionDate", None),
                    "securityTitle": trans.get("securityTitle", None),
                    "shares": trans.get("amounts", {}).get("shares", 0),
                    "pricePerShare": trans.get("amounts", {}).get("pricePerShare", None) if trans.get("amounts", {}).get("pricePerShare", 0) != 0 else None,
                    "transaction_code": trans.get("coding", {}).get("code", None), 
                    "sharesOwnedAfter": trans.get("postTransactionAmounts", {}).get("sharesOwnedFollowingTransaction", 0)
                })

            # 🔹 파생상품 거래 필터링 (모든 거래 유형 유지)
            for trans in transaction.get("derivativeTable", {}).get("transactions", []):
                filtered_transaction["derivativeTransactions"].append({
                    "transactionDate": trans.get("transactionDate", None),
                    "securityTitle": trans.get("securityTitle", None),
                    "conversionOrExercisePrice": trans.get("conversionOrExercisePrice", None), 
                    "shares": trans.get("amounts", {}).get("shares", 0),
                    "transaction_code": trans.get("coding", {}).get("code", None), 
                    "expirationDate": trans.get("expirationDate", None)
                })

            filtered_transactions.append(filtered_transaction)

        return filtered_transactions


    @staticmethod
    def build_query(ticker: str = None, owner: str = None, transaction_type: str = None, 
                    start_date: str = None, end_date: str = None) -> str:
        """
        사용자가 입력한 간단한 파라미터를 Lucene Query 형식으로 변환하는 함수
        
        :param ticker: 기업 티커 (예: TSLA)
        :param owner: 내부자 이름 (예: Elon Musk)
        :param transaction_type: 거래 유형 (예: A, D, P 등)
        :param start_date: 검색 시작 날짜 (YYYY-MM-DD)
        :param end_date: 검색 종료 날짜 (YYYY-MM-DD)
        :return: Lucene Query 형식의 문자열
        """
        conditions = []

        if ticker:
            conditions.append(f"issuer.tradingSymbol:{ticker.upper()}")

        if owner:
            conditions.append(f"reportingOwner.name:\"{owner}\"")

        if transaction_type:
            conditions.append(f"nonDerivativeTable.transactions.coding.code:{transaction_type}")

        if start_date and end_date:
            conditions.append(f"periodOfReport:[{start_date} TO {end_date}]")
        elif start_date:
            conditions.append(f"periodOfReport:[{start_date} TO *]")  # 특정 날짜 이후 거래 검색
        elif end_date:
            conditions.append(f"periodOfReport:[* TO {end_date}]")  # 특정 날짜 이전 거래 검색

        return " AND ".join(conditions) if conditions else "*:*"  # 조건이 없으면 전체 조회


    def _fetch_insider_trades_core(
        ticker: str = None,
        owner: str = None,
        transaction_type: str = None,
        start_date: str = None,
        end_date: str = None,
        from_value: int = 0
    ) -> dict:

        headers = {
            "Authorization": SecInsiderTrade.SEC_API_KEY,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        query = SecInsiderTrade.build_query(ticker, owner, transaction_type, start_date, end_date)
        payload = {
            "query": query,
            "from": from_value,
            "size": 5,
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        try:
            response = requests.post(SecInsiderTrade.SEC_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return SecInsiderTrade.filter_sec_response(response.json())
        except requests.RequestException as e:
            status = response.status_code if response is not None else 'N/A'
            text = response.text if response is not None else 'N/A'
            print(f"요청 실패 상태 코드: {status}, 응답: {text}, 오류: {str(e)}")
            return None

    @tool
    def fetch_insider_trades(
        ticker: str = None,
        owner: str = None,
        transaction_type: str = None,
        start_date: str = None,
        end_date: str = None,
        from_value: int = 0
    ) -> dict:
        """
        SEC Insider Trading API를 호출하여 지정된 조건에 맞는 내부자 거래 데이터를 가져옵니다.

        Args:
            ticker (str, optional): 검색할 기업의 주식 티커 (예: "TSLA"). 기본값은 None.
            owner (str, optional): 내부자의 이름 (예: "Elon Musk"). 부분 일치 검색 가능. 기본값은 None.
            transaction_type (str, optional): 거래 유형 (예: "P" (매수), "S" (매도)). SEC API에서 지원하는 코드 사용. 기본값은 None.
            start_date (str, optional): 검색 시작 날짜 (형식: "YYYY-MM-DD"). 기본값은 None.
            end_date (str, optional): 검색 종료 날짜 (형식: "YYYY-MM-DD"). 기본값은 None.
            from_value (int, optional): 페이징 시작 위치 (기본값: 0). 결과의 오프셋을 지정.

        Returns:
            dict: SEC API에서 반환된 JSON 데이터. 성공 시 내부자 거래 데이터가 포함된 딕셔너리, 실패 시 None.


        """
        return SecInsiderTrade._fetch_insider_trades_core(ticker, owner, transaction_type, 
                                                          start_date, end_date, from_value)