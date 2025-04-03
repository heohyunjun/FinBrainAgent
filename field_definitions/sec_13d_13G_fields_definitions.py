class SEC_13D_13G_NecessaryFields:
    """
    SEC 13D/13G API 응답 데이터에서 사용 중인 필드들을 정리한 클래스.
    """

    # 기본 신고 정보
    ACCESSION_NO = "accessionNo"  # SEC 신고서 고유 식별 번호
    FORM_TYPE = "formType"  # 신고서 유형 (예: 13D, 13G, 13D/A, 13G/A)
    FILED_AT = "filedAt"  # 신고 날짜 (YYYY-MM-DD)
    NAME_OF_ISSUER = "nameOfIssuer"  # 신고 대상 기업명
    CUSIP = "cusip"  # 증권 식별 번호 (여러 개 가능)
    EVENT_DATE = "eventDate"  # 거래 발생 날짜
    TITLE_OF_SECURITIES = "titleOfSecurities"  # 증권 명칭 (예: Common Stock, $0.001 par value per share)
    
    # 신고자 (Filers) 정보
    FILERS = "filers"  # 신고자 정보 리스트
    FILER_CIK = "filers.cik"  # 신고자 CIK
    FILER_NAME = "filers.name"  # 신고자 이름

    # 투자자 정보
    OWNERS = "owners"  # 투자자 정보 리스트 (하위 필드 포함)
    OWNER_NAME = "owners.name"  # 투자자 이름
    AMOUNT_AS_PERCENT = "owners.amountAsPercent"  # 보유 지분 비율 (%)
    SOLE_VOTING_POWER = "owners.soleVotingPower"  # 단독 의결권
    SHARED_VOTING_POWER = "owners.sharedVotingPower"  # 공동 의결권
    SOLE_DISPOSITIVE_POWER = "owners.soleDispositivePower"  # 단독 처분권
    SHARED_DISPOSITIVE_POWER = "owners.sharedDispositivePower"  # 공동 처분권
    AGGREGATE_AMOUNT_OWNED = "owners.aggregateAmountOwned"  # 총 보유 주식 수
    TYPE_OF_REPORTING_PERSON = "owners.typeOfReportingPerson"  # 신고자 유형 (예: 개인(IN), 기관 등)
    MEMBER_OF_GROUP = "owners.memberOfGroup"  # 그룹 소속 여부

    # 법적 이슈 여부
    LEGAL_PROCEEDINGS_DISCLOSURE_REQUIRED = "legalProceedingsDisclosureRequired"  # 법적 문제 여부

    # 13D/13G 세부 항목 (필수 유지, 7,9,10 제외)
    ITEM_1 = "item1"  # 증권 및 발행자 정보
    ITEM_2 = "item2"  # 투자자 신원 및 배경
    ITEM_3 = "item3"  # 자금 출처
    ITEM_4 = "item4"  # 거래 목적 
    ITEM_5 = "item5"  # 주식 보유 현황
    ITEM_6 = "item6"  # 계약 및 협력 관계
    ITEM_8 = "item8"  # 공동 투자자 정보


class SEC_13D_13G_UnnecessaryFields:
    """
    SEC 13D/13G API 응답 데이터에서 불필요한 필드들을 정리한 클래스.
    """

    # 기업 및 투자자 식별자 (CIK는 SEC 내부 식별 코드이므로 분석에 불필요)
    FILER_CIK = "filers.cik"  # 신고자 CIK (이미 기업명, 투자자명 존재)
    OWNER_CIK = "owners.cik"  # 투자자 CIK (이름으로 충분히 구분 가능)

    #  API 응답 스키마 버전 (데이터 분석과 무관)
    SCHEMA_VERSION = "schemaVersion"  # API 응답 스키마 버전

    # 삭제한 13D/13G 항목들 (세부 데이터는 필요 시 원본 데이터로 분석 가능)
    ITEM_7 = "item7"  # 부록 자료 (M&A 계약서 등) → LLM이 직접 분석해야 함
    ITEM_9 = "item9"  # 그룹 해체 공지 → 중요도 낮음
    ITEM_10 = "item10"  # 서명 및 인증 정보 → 필요 시 원본 데이터에서 확인 가능
