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


class SEC_Insider_Trade_UnnecessaryFields:
    """
    SEC API 응답 데이터에서 불필요한 필드들을 정리한 클래스.
    """
    
    # 기업 식별자 (CIK는 SEC 내부 식별 코드이므로 분석에 불필요)
    ISSUER_CIK = "issuer.cik"  # 기업 식별자 (이미 기업명, 티커 존재)
    
    # 내부자 식별자 (이름으로 충분히 구분 가능)
    REPORTING_OWNER_CIK = "reportingOwner.cik"  # 내부자 식별자 (불필요)
    
    #  API 응답 스키마 버전 (데이터 분석과 무관)
    SCHEMA_VERSION = "schemaVersion"  # API 응답 스키마 버전
    
    # SEC 16조 적용 여부 (항상 False라 의미 없음)
    NOT_SUBJECT_TO_SECTION_16 = "notSubjectToSection16"
    
    # 풋노트 ID (풋노트 내용만 있으면 됨)
    FOOTNOTE_ID = "footnotes.id"  # 풋노트 ID (내용만 유지)
    
    # 내부자 전자 서명 정보 (필요 없음)
    OWNER_SIGNATURE_NAME = "ownerSignatureName"  # 내부자 서명
    OWNER_SIGNATURE_DATE = "ownerSignatureNameDate"  # 서명 날짜
    
    # 옵션 행사 가격 (이미 다른 필드에서 정보 제공)
    EXERCISE_PRICE_FOOTNOTE_ID = "exerciseDateFootnoteId"  # 옵션 행사 풋노트 ID
    EXPIRATION_DATE_FOOTNOTE_ID = "expirationDateFootnoteId"  # 옵션 만기 풋노트 ID
    
    # 매도 가격 풋노트 (평균 가격이 제공되므로 별도 풋노트 불필요)
    PRICE_PER_SHARE_FOOTNOTE_ID = "pricePerShareFootnoteId"
    
    # 가격이 0인 값 (대부분 옵션 행사, 분석에 의미 없음)
    ZERO_PRICE_PER_SHARE = "amounts.pricePerShare"  # 0이면 제거

    # 기타 내부 정보 (필요 없음)
    EQUITY_SWAP_INVOLVED = "coding.equitySwapInvolved"  # 주식 스왑 여부
    TRANSACTION_FOOTNOTE_ID = "coding.footnoteId"  # 거래 관련 풋노트
