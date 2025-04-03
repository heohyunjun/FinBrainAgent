class SEC_13F_Holdings_NecessaryFields:
    """
    SEC 13F Holdings API 응답 데이터에서 사용 중인 필드들을 정리한 클래스.
    """

    # 기본 보고서 정보
    ACCESSION_NO = "accessionNo"  # SEC 신고서 고유 식별 번호
    FORM_TYPE = "formType"  # 신고서 유형 (예: "13F-HR")
    FILED_AT = "filedAt"  # 신고 날짜 (YYYY-MM-DD 형식으로 저장)
    CIK = "cik"  # 기관의 CIK (Central Index Key)
    INSTITUTION_NAME = "companyName"  # 기관 이름 (예: "TABLEAUX LLC")
    COMPANY_NAME_LONG = "companyNameLong"  # 기관의 전체 이름 (예: "TABLEAUX LLC (Filer)")
    DESCRIPTION = "description"  # 보고서 설명 (예: "Form 13F-HR - Quarterly report filed by institutional managers, Holdings")
    LINK_TO_FILING_DETAILS = "linkToFilingDetails"  # 상세 XML 링크
    PERIOD_OF_REPORT = "periodOfReport"  # 보고 기간 (예: "2024-12-31")
    EFFECTIVENESS_DATE = "effectivenessDate"  # 효력 발생 날짜 (예: "2025-03-14")

    # 보유 종목 정보 (Holdings)
    HOLDINGS = "holdings"  # 보유 종목 목록
    NAME_OF_ISSUER = "nameOfIssuer"  # 발행사 이름 (예: "ABBOTT LABS")
    TICKER = "ticker"  # 주식 티커 (예: "ABT")
    CUSIP = "cusip"  # CUSIP 번호 (예: "002824100")
    TITLE_OF_CLASS = "titleOfClass"  # 주식 클래스 (예: "COM")
    VALUE = "value"  # 보유 가치 (USD, 예: 205068)
    SHRS_OR_PRN_AMT = "shrsOrPrnAmt.sshPrnamt"  # 보유 주식 수 (예: 1813)
    SHRS_OR_PRN_AMT_TYPE = "shrsOrPrnAmt.sshPrnamtType"  # 주식 유형 (예: "SH")
    PUT_CALL = "putCall"  # 옵션 여부 (없을 경우 None)
    INVESTMENT_DISCRETION = "investmentDiscretion"  # 투자 재량권 (예: "SOLE")
    VOTING_AUTHORITY = "votingAuthority"  # 의결권 정보
    VOTING_AUTHORITY_SOLE = "votingAuthority.Sole"  # 단독 의결권 (예: 0)
    VOTING_AUTHORITY_SHARED = "votingAuthority.Shared"  # 공유 의결권 (예: 0)
    VOTING_AUTHORITY_NONE = "votingAuthority.None"  # 의결권 없음 (예: 1813)
    ISSUER_CIK = "cik"  # 발행사의 CIK 번호 (예: "1800")



class SEC_13F_Holdings_UnnecessaryFields:
    """
    SEC 13F Holdings API 응답 데이터에서 사용하지 않는 필드들을 정리한 클래스.
    """

    # 상위 레벨 불필요 필드
    ID = "id"  # API 응답의 고유 식별자 (필터링에서 제외)
    TICKER = "ticker"  # 상위 레벨의 ticker (빈 문자열, 보유 종목에서만 사용됨)
    LINK_TO_TXT = "linkToTxt"  # 텍스트 형식 파일 링크 (필요 시 추가 가능)
    LINK_TO_HTML = "linkToHtml"  # HTML 형식 파일 링크 (필요 시 추가 가능)
    LINK_TO_XBRL = "linkToXbrl"  # XBRL 형식 파일 링크 (현재 빈 값)
    ENTITIES = "entities"  # 기관의 추가 메타데이터 (IRS 번호, 설립 주 등, 필요 시 추가 가능)
    DOCUMENT_FORMAT_FILES = "documentFormatFiles"  # 관련 파일 목록 (필요 시 추가 가능)
    DATA_FILES = "dataFiles"  # 데이터 파일 (현재 빈 리스트)
    SERIES_AND_CLASSES_CONTRACTS_INFORMATION = "seriesAndClassesContractsInformation"  # 시리즈 및 클래스 계약 정보 (현재 빈 리스트)