from typing import Optional
from langchain.tools import tool
from tools.sec_insider_trade_tool import SECInsiderTradeAPI, SEC13D13GAPI, SEC13FHoldingsAPI  # 당신이 만든 클래스 위치 기준
from datetime import datetime, timedelta

class SecToolRegistry:
    insider_api = SECInsiderTradeAPI()
    form13d13g_api = SEC13D13GAPI()
    form13f_api = SEC13FHoldingsAPI()

    @staticmethod
    @tool
    def get_insider_trading_tool(
        ticker: Optional[str] = None,
        owner: Optional[str] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        from_value: int = 0,
        reference_date: Optional[str] = None
    ) -> dict:
        """
        내부자 주식 매매(Form 3, 4, 5) 내역을 조회하는 도구

        Args:
            ticker (str, optional): 기업 티커 (예: TSLA)
            owner (str, optional): 내부자 이름
            transaction_type (str, optional): 거래 유형 (예: P, S 등)
            start_date (str, optional): 조회 시작일 ("YYYY-MM-DD")
            end_date (str, optional): 조회 종료일 ("YYYY-MM-DD")
            from_value (int, optional): 페이지 오프셋
            reference_date (str, optional): 현재 시간

        Returns:
            dict: 내부자 거래 내역이 담긴 JSON 응답
        """

        result = SecToolRegistry.insider_api._fetch_filings_core(
            ticker=ticker,
            owner=owner,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date,
            from_value=from_value,
            reference_date=reference_date
        )

        if not result or len(result) == 0:
            return {"message": f"No SEC filings found for {ticker or owner} between {start_date} and {end_date}."}
        
        return {"message": result}

    @staticmethod
    @tool
    def get_ownership_disclosure_tool(
        issuer_name: Optional[str] = None,
        owner: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_percent: Optional[float] = None,
        form_type: Optional[str] = None,
        cik: Optional[str] = None,
        from_value: int = 0,
        reference_date: Optional[str] = None
    ) -> dict:
        """
        주요 지분 보유 공시(Form 13D, 13G)를 조회하는 도구
        행동주의 또는 패시브 투자자의 주요 지분 보유 현황(5% 이상)을 확인

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
        result = SecToolRegistry.insider_api._fetch_filings_core(
            issuer_name=issuer_name,
            owner=owner,
            start_date=start_date,
            end_date=end_date,
            min_percent=min_percent,
            form_type=form_type,
            cik=cik,
            from_value=from_value,
            reference_date=reference_date
        )
        # 명확한 결과가 없음을 메시지로 반환
        if not result or len(result) == 0:
            return {"message": f"No SEC filings found for {issuer_name or owner} between {start_date} and {end_date}."}
        
        return {"message": result}
    
    @staticmethod
    @tool
    def get_institutional_holdings_tool(
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
        max_shares: Optional[int] = None,
        from_value: int = 0,
        reference_date: Optional[str] = None
    ) -> dict:
        """
        기관투자자의 포트폴리오 보유 내역(Form 13F)을 조회하는 도구

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

        result= SecToolRegistry.form13f_api._fetch_filings_core(
            cik=cik,
            company_name=company_name,
            issuer_name=issuer_name,
            ticker=ticker,
            cusip=cusip,
            start_date=start_date,
            end_date=end_date,
            min_value=min_value,
            max_value=max_value,
            min_shares=min_shares,
            max_shares=max_shares,
            from_value=from_value,
            reference_date=reference_date
        )

        # 명확한 결과가 없음을 메시지로 반환
        if not result or len(result) == 0:
            return {"message": f"No SEC filings found for {cik or company_name} between {start_date} and {end_date}."}
        
        return {"message": result}