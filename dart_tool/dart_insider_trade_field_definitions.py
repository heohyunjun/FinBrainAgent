class Dart_Executive_Shareholding_Necessary_Fields:
    """
    임원ㆍ주요주주 소유보고서(Open DART API)의 핵심 필드를 정리한 클래스.
    """

    # 공시 정보 식별 필드
    RECEPTION_DATE = "rcept_dt"  # 접수일자 (공시 및 거래일자)

    # 기업 식별 필드
    CORP_CODE = "corp_code"  # 회사 고유번호
    CORP_NAME = "corp_name"  # 회사명

    # 내부자(거래 주체) 정보 필드
    REPORTER = "repror"  # 보고자명
    EXECUTIVE_REGISTRATION = "isu_exctv_rgist_at"  # 등기임원 여부 (등기임원, 비등기임원 등)
    EXECUTIVE_POSITION = "isu_exctv_ofcps"  # 임원 직위 (대표이사, 이사, 상무 등)
    MAIN_SHAREHOLDER = "isu_main_shrholdr"  # 주요 주주 여부 (10% 이상 주주 등)

    # 내부자 보유 주식 현황 필드
    STOCK_COUNT = "sp_stock_lmp_cnt"  # 특정 증권 등 소유 수 (거래 후 보유 주식 수)
    STOCK_CHANGE_COUNT = "sp_stock_lmp_irds_cnt"  # 특정 증권 등 소유 증감 수 (취득 또는 처분 주식 수)

    # 지분율 관련 필드
    STOCK_RATIO = "sp_stock_lmp_rate"  # 특정 증권 등 소유 비율 (거래 후 지분율)
    STOCK_CHANGE_RATIO = "sp_stock_lmp_irds_rate"  # 특정 증권 등 소유 증감 비율 (지분율 증감 비율)


class Dart_Executive_Shareholding_UNecessary_Fields:
    RECEPTION_Number = "rcept_no"