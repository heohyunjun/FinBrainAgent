import requests
from dotenv import load_dotenv
import json
import os
from typing import Optional
from langchain.tools import tool
from datetime import datetime, timedelta
class SECBaseAPI:
    """
    SEC API의 공통 로직을 처리하는 기반 클래스.
    """
    SEC_API_KEY = os.getenv("SEC_API_KEY")
    SEC_INSIDER_TRADE_API_URL = "https://api.sec-api.io/insider-trading"
    SEC_13D_13G_API_URL = "https://api.sec-api.io/form-13d-13g"
    SEC_13F_HOLDINGS_API_URL = "https://api.sec-api.io/form-13f/holdings"
    @staticmethod
    def _fetch_sec_data(api_url: str, query: str, from_value: int = 0) -> dict:
        """
        공통적인 SEC API 요청 메서드.
        :param api_url: SEC API 엔드포인트
        :param query: Lucene Query 형식의 검색 조건
        :param from_value: 페이징 오프셋
        :return: API 응답 JSON 데이터
        """
        headers = {
            "Authorization": SECBaseAPI.SEC_API_KEY,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }

        payload = {
            "query": query,
            "from": from_value,
            "size": 5,
            "sort": [{"filedAt": {"order": "desc"}}] # 최신 데이터 우선 정렬
        }

        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            print(response.status_code)
            return response.json()
        except requests.RequestException as e:
            status = response.status_code if response is not None else 'N/A'
            text = response.text if response is not None else 'N/A'
            print(f"요청 실패 상태 코드: {status}, 응답: {text}, 오류: {str(e)}")
            return None


class SECInsiderTradeAPI(SECBaseAPI):
    """
    SEC 내부자 거래 API 클래스.
    """

    @staticmethod
    def build_query(
        ticker: Optional[str] = None,
        owner: Optional[str] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
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
            conditions.append(f"periodOfReport:[{start_date} TO *]")
        elif end_date:
            conditions.append(f"periodOfReport:[* TO {end_date}]")
        return " AND ".join(conditions) if conditions else "*:*"
    
    @staticmethod
    def filter_response(response_data):
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

            # 비파생상품 거래 필터링 (모든 거래 유형 유지)
            for trans in transaction.get("nonDerivativeTable", {}).get("transactions", []):
                filtered_transaction["nonDerivativeTransactions"].append({
                    "transactionDate": trans.get("transactionDate", None),
                    "securityTitle": trans.get("securityTitle", None),
                    "shares": trans.get("amounts", {}).get("shares", 0),
                    "pricePerShare": trans.get("amounts", {}).get("pricePerShare", None) if trans.get("amounts", {}).get("pricePerShare", 0) != 0 else None,
                    "transaction_code": trans.get("coding", {}).get("code", None), 
                    "sharesOwnedAfter": trans.get("postTransactionAmounts", {}).get("sharesOwnedFollowingTransaction", 0)
                })

            #  파생상품 거래 필터링 (모든 거래 유형 유지)
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
    def _fetch_filings_core(
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
            ticker (str, optional): 검색할 기업의 주식 티커 (예: "TSLA").
            owner (str, optional): 내부자의 이름 (예: "Elon Musk").
            transaction_type (str, optional): 거래 유형 (예: "P" (매수), "S" (매도)).
            start_date (str, optional): 검색 시작 날짜 ("YYYY-MM-DD").
            end_date (str, optional): 검색 종료 날짜 ("YYYY-MM-DD").
            from_value (int, optional): 페이징 시작 위치 (기본값: 0).

        Returns:
            dict: 필터링된 내부자 거래 데이터.
        """
        query = SECInsiderTradeAPI.build_query(ticker, owner, transaction_type, start_date, end_date)
        raw_data = SECBaseAPI._fetch_sec_data(SECBaseAPI.SEC_INSIDER_TRADE_API_URL, query, from_value)
        return SECInsiderTradeAPI.filter_response(raw_data) if raw_data else None

    @tool
    def fetch_filings(
        ticker: str = None,
        owner: str = None,
        transaction_type: str = None,
        start_date: str = None,
        end_date: str = None,
        from_value: int = 0,
        reference_date: str = None
        
    ) -> dict:
        """
        SEC Insider Trading API를 호출하여 지정된 조건에 맞는 내부자 거래 데이터를 가져옵니다.

        Args:
            ticker (str, optional): 검색할 기업의 주식 티커 (예: "TSLA").
            owner (str, optional): 내부자의 이름 (예: "Elon Musk").
            transaction_type (str, optional): 거래 유형 (예: "P" (매수), "S" (매도)).
            start_date (str, optional): 검색 시작 날짜 ("YYYY-MM-DD").
            end_date (str, optional): 검색 종료 날짜 ("YYYY-MM-DD").
            from_value (int, optional): 페이징 시작 위치 (기본값: 0).

        Returns:
            dict: 필터링된 내부자 거래 데이터.
        """

        if reference_date is None:
            reference_date = datetime.now().strftime("%Y-%m-%d")

        if end_date is None:
            end_date = reference_date

        if start_date is None:
            # 기본적으로 최근 30일 기준
            start_date = (datetime.strptime(reference_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")

        result = SECInsiderTradeAPI._fetch_filings_core(
            ticker, owner, transaction_type, start_date, end_date, from_value
        )
    
        # 명확한 결과가 없음을 메시지로 반환
        if not result or len(result) == 0:
            return {"message": f"No SEC filings found for {ticker or owner} between {start_date} and {end_date}."}
        
        return {"message": result}

class SEC13D13GAPI(SECBaseAPI):
    """
    SEC 13D/13G 보고서 API 클래스.
    """

    @staticmethod
    def build_query(
        issuer_name: Optional[str] = None,  # 변경된 부분
        owner: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_percent: Optional[float] = None,
        form_type: Optional[str] = None,
        cik: Optional[str] = None
    ) -> str:
        """
        사용자가 입력한 간단한 파라미터를 Lucene Query 형식으로 변환하는 함수
        
        :param issuer_name: 기업 명칭 (예: "Tesla, Inc.")  
        :param owner: 투자자 이름 (예: BlackRock Inc.)
        :param start_date: 검색 시작 날짜 (YYYY-MM-DD)
        :param end_date: 검색 종료 날짜 (YYYY-MM-DD)
        :param min_percent: 최소 지분율 (예: 5% 이상이면 5 입력)
        :param form_type: 보고서 유형 (예: 13D, 13G, 13D/A 등)
        :param cik: 특정 기업 CIK (발행 기업 검색)
        :return: Lucene Query 형식의 문자열
        """
        conditions = []
        if issuer_name: 
            conditions.append(f"nameOfIssuer:\"{issuer_name}\"")  
        if owner:
            conditions.append(f"owners.name:\"{owner}\"")
        if min_percent is not None:
            conditions.append(f"owners.amountAsPercent:[{min_percent} TO *]")
        if start_date and end_date:
            conditions.append(f"filedAt:[{start_date} TO {end_date}]")
        elif start_date:
            conditions.append(f"filedAt:[{start_date} TO *]")
        elif end_date:
            conditions.append(f"filedAt:[* TO {end_date}]")
        if form_type:
            conditions.append(f"formType:{form_type}")
        if cik:
            conditions.append(f"filers.cik:{cik}")
        return " AND ".join(conditions) if conditions else "*:*"
        
    def filter_response(response_data):
        """
        SEC 13D/13G API 응답 데이터를 필터링하여 필요한 정보만 반환하는 함수.

        :param response_data: API 응답 JSON (dict)
        :return: 필터링된 데이터 (list of dict)
        """
        filtered_filings = []

        for filing in response_data.get("filings", []):
            filtered_filing = {
                "accessionNo": filing.get("accessionNo"),
                "formType": filing.get("formType"),
                "filedAt": filing.get("filedAt")[:10],  # YYYY-MM-DD 형식으로 저장
                "nameOfIssuer": filing.get("nameOfIssuer"),
                "cusip": filing.get("cusip"),
                "eventDate": filing.get("eventDate"),

                
                "titleOfSecurities": filing.get("titleOfSecurities"),  # 증권 명칭 추가
                "filers": [
                    {
                        "cik": filer.get("cik"),
                        "name": filer.get("name")
                    }
                    for filer in filing.get("filers", [])
                ],  # 파일 제출자 목록 추가

                # 투자자 정보 필터링
                "owners": [
                    {
                        "name": owner.get("name"),
                        "amountAsPercent": owner.get("amountAsPercent"),
                        "soleVotingPower": owner.get("soleVotingPower"),
                        "sharedVotingPower": owner.get("sharedVotingPower"),
                        "soleDispositivePower": owner.get("soleDispositivePower"),
                        "sharedDispositivePower": owner.get("sharedDispositivePower"),
                        "aggregateAmountOwned": owner.get("aggregateAmountOwned"),
                        
           
                        "typeOfReportingPerson": owner.get("typeOfReportingPerson"),  # 신고자 유형 추가
                        "memberOfGroup": owner.get("memberOfGroup"),  # 그룹 소속 여부 추가
                    }
                    for owner in filing.get("owners", [])
                ],

                # 법적 이슈 정보 추가
                "legalProceedingsDisclosureRequired": filing.get("legalProceedingsDisclosureRequired", False),

                # 13D/13G 보고서 아이템 필터링 (7,9,10 제외)
                "item1": filing.get("item1"),  # 증권 및 발행자 정보
                "item2": filing.get("item2"),  # 투자자 신원 및 배경
                "item3": filing.get("item3"),  # 자금 출처
                "item4": filing.get("item4"),  # 거래 목적 
                "item5": filing.get("item5"),  # 주식 보유 현황
                "item6": filing.get("item6"),  # 계약 및 협력 관계
                "item8": filing.get("item8"),  # 공동 투자자 정보
            }

            filtered_filings.append(filtered_filing)

        return filtered_filings

    
    @staticmethod
    def _fetch_filings_core(
        issuer_name: str = None, 
        owner: str = None,
        start_date: str = None,
        end_date: str = None,
        min_percent: float = None,
        form_type: str = None,
        cik: str = None,
        from_value: int = 0,
    ) -> dict:
        """
        SEC 13D/13G API를 호출하여 지정된 조건에 맞는 투자 지분 공개 데이터를 가져옵니다.

        Args:
            issuer_name (str, optional): 검색할 기업의 명칭 (예: "Tesla, Inc."). 
            owner (str, optional): 투자자 이름 (예: "BlackRock Inc.").
            start_date (str, optional): 검색 시작 날짜 ("YYYY-MM-DD").
            end_date (str, optional): 검색 종료 날짜 ("YYYY-MM-DD").
            min_percent (float, optional): 최소 지분율 필터 (예: 5% 이상이면 5 입력).
            form_type (str, optional): 보고서 유형 (예: 13D, 13G, 13D/A).
            cik (str, optional): 특정 기업 CIK 검색.
            from_value (int, optional): 페이징 시작 위치 (기본값: 0).

        Returns:
            dict: 필터링된 13D/13G 데이터.
        """
        query = SEC13D13GAPI.build_query(issuer_name, owner, start_date, end_date, min_percent, form_type, cik)
        raw_data = SECBaseAPI._fetch_sec_data(SECBaseAPI.SEC_13D_13G_API_URL, query, from_value)
        # return raw_data
        return SEC13D13GAPI.filter_response(raw_data) if raw_data else None

    @tool
    def fetch_filings(
        issuer_name: str = None,  
        owner: str = None,
        start_date: str = None,
        end_date: str = None,
        min_percent: float = None,
        form_type: str = None,
        cik: str = None,
        from_value: int = 0,
        reference_date: str = None
    ) -> dict:
        """
        SEC 13D/13G API를 호출하여 지정된 조건에 맞는 투자 지분 공개 데이터를 가져옵니다.

        Args:
            issuer_name (str, optional): 검색할 기업의 명칭 (예: "Tesla, Inc.").  
            owner (str, optional): 투자자 이름 (예: "BlackRock Inc."). 부분 일치 검색 가능. 기본값은 None.
            start_date (str, optional): 검색 시작 날짜 (형식: "YYYY-MM-DD"). 기본값은 None.
            end_date (str, optional): 검색 종료 날짜 (형식: "YYYY-MM-DD"). 기본값은 None.
            min_percent (float, optional): 최소 지분율 필터 (예: 5% 이상이면 5 입력). 기본값은 None.
            form_type (str, optional): 보고서 유형 (예: "13D", "13G", "13D/A"). 기본값은 None.
            cik (str, optional): 특정 기업 CIK 검색. 기본값은 None.
            from_value (int, optional): 페이징 시작 위치 (기본값: 0). 결과의 오프셋을 지정.
            reference_date (str, optional) : 현재 시간 
        Returns:
            dict: SEC API에서 반환된 JSON 데이터. 성공 시 13D/13G 데이터가 포함된 딕셔너리, 실패 시 None.
        """
        if reference_date is None:
            reference_date = datetime.now().strftime("%Y-%m-%d")

        if end_date is None:
            end_date = reference_date

        if start_date is None:
            # 기본적으로 최근 30일 기준
            start_date = (datetime.strptime(reference_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
    
        result = SEC13D13GAPI._fetch_filings_core(
            issuer_name, owner, start_date, end_date, min_percent, form_type, cik, from_value
        )

        # 명확한 결과가 없음을 메시지로 반환
        if not result or len(result) == 0:
            return {"message": f"No SEC filings found for {issuer_name or owner} between {start_date} and {end_date}."}
        
        return {"message": result}

class SEC13FHoldingsAPI(SECBaseAPI):
    """
    SEC 13F Holdings 보고서 API 클래스.
    """

    @staticmethod
    def build_query(
        cik: Optional[str] = None,
        company_name: Optional[str] = None,
        issuer_name: Optional[str] = None,
        ticker: Optional[str] = None,
        cusip: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        min_shares: Optional[int] = None,
        max_shares: Optional[int] = None
    ) -> str:
        """
        사용자가 입력한 간단한 파라미터를 Lucene Query 형식으로 변환하는 함수
        
        :param cik: 기관의 CIK 코드 (예: "0001067983")
        :param company_name: 기관 이름 (예: "BlackRock")
        :param issuer_name: 보유 종목의 발행사 이름 (예: "Tesla, Inc.")
        :param ticker: 보유 종목의 티커 (예: "TSLA")
        :param cusip: 보유 종목의 CUSIP 번호 (예: "88160R101")
        :param start_date: 검색 시작 날짜 (YYYY-MM-DD)
        :param end_date: 검색 종료 날짜 (YYYY-MM-DD)
        :param min_value: 보유 종목 가치의 최소값 (단위: USD)
        :param max_value: 보유 종목 가치의 최대값 (단위: USD)
        :param min_shares: 보유 주식 수의 최소값
        :param max_shares: 보유 주식 수의 최대값
        :return: Lucene Query 형식의 문자열
        """
        conditions = []
        if cik:
            conditions.append(f"cik:{cik}")
        if company_name:
            conditions.append(f"companyName:\"{company_name}\"")
        if issuer_name:
            conditions.append(f"holdings.nameOfIssuer:\"{issuer_name}\"")
        if ticker:
            conditions.append(f"holdings.ticker:{ticker}")
        if cusip:
            conditions.append(f"holdings.cusip:{cusip}")
        if start_date and end_date:
            conditions.append(f"filedAt:[{start_date} TO {end_date}]")
        elif start_date:
            conditions.append(f"filedAt:[{start_date} TO *]")
        elif end_date:
            conditions.append(f"filedAt:[* TO {end_date}]")
        if min_value is not None and max_value is not None:
            conditions.append(f"holdings.value:[{min_value} TO {max_value}]")
        elif min_value is not None:
            conditions.append(f"holdings.value:[{min_value} TO *]")
        elif max_value is not None:
            conditions.append(f"holdings.value:[* TO {max_value}]")
        if min_shares is not None and max_shares is not None:
            conditions.append(f"holdings.sshPrnamt:[{min_shares} TO {max_shares}]")
        elif min_shares is not None:
            conditions.append(f"holdings.sshPrnamt:[{min_shares} TO *]")
        elif max_shares is not None:
            conditions.append(f"holdings.sshPrnamt:[* TO {max_shares}]")

        return " AND ".join(conditions) if conditions else "*:*"

    @staticmethod
    def filter_response(response_data):
        """
        SEC 13F Holdings API 응답 데이터를 필터링하여 필요한 정보만 반환하는 함수.

        :param response_data: API 응답 JSON (dict)
        :return: 필터링된 데이터 (list of dict)
        """
        filtered_holdings = []

        for filing in response_data.get("data", []):  # API 응답에서 data 필드 사용
            filtered_filing = {
                "accessionNo": filing.get("accessionNo"),
                "formType": filing.get("formType"),
                "filedAt": filing.get("filedAt", "")[:10],  # YYYY-MM-DD 형식으로 저장, 기본값 빈 문자열
                "cik": filing.get("cik"),
                "institutionName": filing.get("companyName"),  # SEC API에서는 companyName 사용
                "companyNameLong": filing.get("companyNameLong"),  # 기관의 전체 이름 추가
                "description": filing.get("description"),  # 보고서 설명 추가
                "linkToFilingDetails": filing.get("linkToFilingDetails"),  # 상세 XML 링크 추가
                "periodOfReport": filing.get("periodOfReport"),
                "effectivenessDate": filing.get("effectivenessDate"),  # 효력 발생 날짜 추가
                "holdings": [
                    {
                        "nameOfIssuer": holding.get("nameOfIssuer"),
                        "ticker": holding.get("ticker"),
                        "cusip": holding.get("cusip"),
                        "titleOfClass": holding.get("titleOfClass"),
                        "value": holding.get("value"),  # 포트폴리오 내 해당 종목의 총 가치
                        "shrsOrPrnAmt": holding.get("shrsOrPrnAmt", {}).get("sshPrnamt"),  # 주식 수 정확히 매핑
                        "shrsOrPrnAmtType": holding.get("shrsOrPrnAmt", {}).get("sshPrnamtType"),  # 주식 유형 정확히 매핑
                        "putCall": holding.get("putCall"),  # 옵션 여부
                        "investmentDiscretion": holding.get("investmentDiscretion"),
                        "votingAuthority": {  # 의결권 정보 정확히 매핑
                            "sole": holding.get("votingAuthority", {}).get("Sole"),
                            "shared": holding.get("votingAuthority", {}).get("Shared"),
                            "none": holding.get("votingAuthority", {}).get("None")
                        },
                        "cik": holding.get("cik")  # 발행사의 CIK 번호 추가
                    }
                    for holding in filing.get("holdings", [])
                ]
            }

            filtered_holdings.append(filtered_filing)

        return filtered_holdings

    @staticmethod
    def _fetch_filings_core(
        cik: str = None,
        company_name: str = None,
        issuer_name: str = None,
        ticker: str = None,
        cusip: str = None,
        start_date: str = None,
        end_date: str = None,
        min_value: int = None,
        max_value: int = None,
        min_shares: int = None,
        max_shares: int = None,
        from_value: int = 0
    ) -> dict:

        query = SEC13FHoldingsAPI.build_query(
            cik, company_name, issuer_name, ticker, 
            cusip, start_date, end_date, min_value, 
            max_value, min_shares, max_shares
        )
        raw_data = SECBaseAPI._fetch_sec_data(SECBaseAPI.SEC_13F_HOLDINGS_API_URL, query, from_value)
        # return raw_data
        return SEC13FHoldingsAPI.filter_response(raw_data) if raw_data else None

    @tool
    def fetch_filings(
        cik: str = None,
        company_name: str = None,
        issuer_name: str = None,
        ticker: str = None,
        cusip: str = None,
        start_date: str = None,
        end_date: str = None,
        min_value: int = None,
        max_value: int = None,
        min_shares: int = None,
        max_shares: int = None,
        from_value: int = 0,
        reference_date: str = None
    ) -> dict:
        """
        SEC 13F Holdings API를 호출하여 지정된 조건에 맞는 기관 투자자의 보유 주식 데이터를 가져옵니다.

        Args:
            cik (str, optional): 기관의 CIK 코드 (예: "0001067983").
            company_name (str, optional): 기관 이름 (예: "BlackRock").
            issuer_name (str, optional): 보유 종목의 발행사 이름 (예: "Tesla, Inc.").
            ticker (str, optional): 보유 종목의 티커 (예: "TSLA").
            cusip (str, optional): 보유 종목의 CUSIP 번호 (예: "88160R101").
            start_date (str, optional): 검색 시작 날짜 (형식: "YYYY-MM-DD"). 기본값은 None.
            end_date (str, optional): 검색 종료 날짜 (형식: "YYYY-MM-DD"). 기본값은 None.
            min_value (int, optional): 보유 종목 가치의 최소값 (단위: USD).
            max_value (int, optional): 보유 종목 가치의 최대값 (단위: USD).
            min_shares (int, optional): 보유 주식 수의 최소값.
            max_shares (int, optional): 보유 주식 수의 최대값.
            from_value (int, optional): 페이징 시작 위치 (기본값: 0). 결과의 오프셋을 지정.
            reference_date (str, optional) : 현재 시간 

        Returns:
            dict: SEC API에서 반환된 JSON 데이터. 성공 시 13F Holdings 데이터가 포함된 딕셔너리, 실패 시 None.
        """

        if reference_date is None:
            reference_date = datetime.now().strftime("%Y-%m-%d")

        if end_date is None:
            end_date = reference_date

        if start_date is None:
            # 기본적으로 최근 30일 기준
            start_date = (datetime.strptime(reference_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")

        result= SEC13FHoldingsAPI._fetch_holdings_core(
            cik, company_name, issuer_name, ticker, cusip, start_date, end_date,
            min_value, max_value, min_shares, max_shares, from_value
        )

        # 명확한 결과가 없음을 메시지로 반환
        if not result or len(result) == 0:
            return {"message": f"No SEC filings found for {cik or company_name} between {start_date} and {end_date}."}
        
        return {"message": result}