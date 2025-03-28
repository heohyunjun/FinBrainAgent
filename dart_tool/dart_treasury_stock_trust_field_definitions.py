########  자기 주식 취득 신탁 계약 체결 ########
class Dart_TreasuryStockTrustContractDecision_Necessary_Fields:
    """
    자기주식취득 신탁계약 체결 결정 API 응답 중 필요한 필드 정의
    """
    DECISION_DATE = "bddd"                          # 이사회결의일 (예: "2019년 05월 13일", str → datetime)
    COMPANY = "corp_name"                           # 회사명 (예: "메리츠금융지주", str)
    CONTRACT_AMOUNT = "ctr_prc"                     # 계약금액 (예: "70,000,000,000", str → int)
    CONTRACT_START = "ctr_pd_bgd"                   # 계약 시작일 (예: "2019년 05월 14일", str → datetime)
    CONTRACT_END = "ctr_pd_edd"                     # 계약 종료일 (예: "2020년 05월 14일", str → datetime)
    CONTRACT_PURPOSE = "ctr_pp"                     # 계약 목적 (예: "주주가치 제고", str)
    CONTRACT_AGENCY = "ctr_cns_int"                 # 계약 체결 기관 (예: "NH투자증권", str)
    PLANNED_CONTRACT_DATE = "ctr_cns_prd"           # 계약체결 예정일자 (예: "2019년 05월 14일", str)


class Dart_TrustStockAcquisitionDecision_Unnecessary_Fields:
    """
    자기주식취득 신탁계약 체결 결정 API 응답 중 불필요한 필드 정의.
    """

    RECEIPT_NO = "rcept_no"                      # 접수번호
    CORP_CODE = "corp_code"                      # 고유번호
    CORP_CLASS = "corp_cls"                      # 법인구분
    
    # 사외이사/감사 관련
    OUTSIDE_DIR_PRESENT = "od_a_at_t"            # 사외이사 참석 수
    OUTSIDE_DIR_ABSENT = "od_a_at_b"             # 사외이사 불참 수
    AUDIT_ATTEND = "adt_a_atn"                   # 감사 참석 여부

    # 위탁 투자 중개업자
    BROKER = "cs_iv_bk"                          # 위탁투자중개업자

    # 계약 전 자기주식 보유현황
    AQ_WTN_DIV_OSTK = "aq_wtn_div_ostk"          # 배당가능 내 보통주식
    AQ_WTN_DIV_OSTK_RT = "aq_wtn_div_ostk_rt"    # 배당가능 내 보통주식 비율
    AQ_WTN_DIV_ESTK = "aq_wtn_div_estk"          # 배당가능 내 기타주식
    AQ_WTN_DIV_ESTK_RT = "aq_wtn_div_estk_rt"    # 배당가능 내 기타주식 비율
    EAQ_OSTK = "eaq_ostk"                        # 기타취득 보통주식
    EAQ_OSTK_RT = "eaq_ostk_rt"                  # 기타취득 보통주식 비율
    EAQ_ESTK = "eaq_estk"                        # 기타취득 기타주식
    EAQ_ESTK_RT = "eaq_estk_rt"                  # 기타취득 기타주식 비율
    
########################################################