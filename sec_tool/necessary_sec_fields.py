class SEC_Insider_Trade_NecessaryFields:
    """
    SEC API 응답 데이터에서 사용 중인 필드들을 정리한 클래스.
    """

    # 기본 거래 정보
    ACCESSION_NO = "accessionNo"  # SEC 신고서 고유 식별 번호
    FILED_AT = "filedAt"  # 신고 날짜 (YYYY-MM-DD)
    PERIOD_OF_REPORT = "periodOfReport"  # 거래 발생 날짜
    DOCUMENT_TYPE = "documentType"  # 신고 문서 유형 (보통 "4" = Form 4)

    # 기업 정보
    ISSUER_NAME = "issuer.name"  # 기업명 (예: Tesla, Inc.)
    ISSUER_TICKER = "issuer.tradingSymbol"  # 기업 티커 심볼 (예: TSLA)

    # 내부자 정보
    REPORTING_OWNER_NAME = "reportingOwner.name"  # 내부자 이름 (예: Elon Musk)
    REPORTING_OWNER_RELATIONSHIP = "reportingOwner.relationship"  # 내부자의 기업 내 역할
    IS_DIRECTOR = "reportingOwner.relationship.isDirector"  # 이사회 멤버 여부
    IS_OFFICER = "reportingOwner.relationship.isOfficer"  # 임원 여부
    OFFICER_TITLE = "reportingOwner.relationship.officerTitle"  # 임원 직책 (예: CEO, CFO)
    IS_TEN_PERCENT_OWNER = "reportingOwner.relationship.isTenPercentOwner"  # 10% 이상 지분 보유 여부

    # 비파생상품 거래 (주식 거래)
    NON_DERIVATIVE_TRANSACTIONS = "nonDerivativeTable.transactions"  # 비파생상품 거래 목록
    TRANSACTION_DATE = "transactionDate"  # 거래일
    SECURITY_TITLE = "securityTitle"  # 주식 종류 (예: Common Stock)
    SHARES = "amounts.shares"  # 거래 주식 수량
    PRICE_PER_SHARE = "amounts.pricePerShare"  # 주당 거래 가격 (옵션 행사 시 0일 수도 있음)
    TRANSACTION_TYPE = "coding.code"  # 거래 유형 (A = 매수, D = 매도, M = 옵션 행사, P = 시장 매수)
    SHARES_OWNED_AFTER = "postTransactionAmounts.sharesOwnedFollowingTransaction"  # 거래 후 총 보유 주식 수

    # 파생상품 거래 (옵션 등)
    DERIVATIVE_TRANSACTIONS = "derivativeTable.transactions"  # 파생상품 거래 목록
    CONVERSION_PRICE = "conversionOrExercisePrice"  # 옵션 행사 가격
    EXPIRATION_DATE = "expirationDate"  # 옵션 만기일

    # 풋노트 (거래 관련 추가 설명)
    FOOTNOTES = "footnotes.text"  # 풋노트 내용만 유지
