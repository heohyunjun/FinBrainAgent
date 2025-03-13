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
