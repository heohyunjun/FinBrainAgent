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


########  자기 주식 취득 신탁 해지 결정 ########
class Dart_TreasuryStockTrustCancel_Necessary_Fields:
    """
    자기주식취득 신탁계약 해지 결정 API 응답 중 분석에 필요한 필드 정의 
    """

    COMPANY: str = "corp_name"  # 회사명 (예: "신한지주", str)
    BOARD_DATE: str = "bddd"  # 이사회 결의일 (예: "2019년 09월 09일" 또는 "-", str → datetime)
    
    CONTRACT_AMOUNT_BEFORE: str = "ctr_prc_bfcc"  # 계약금액(해지 전) (예: "400,000,000,000", str → int)
    CONTRACT_AMOUNT_AFTER: str = "ctr_prc_atcc"  # 계약금액(해지 후) (예: "0", str → int)
    
    CONTRACT_PERIOD_START: str = "ctr_pd_bfcc_bgd"  # 해지 전 계약 시작일 (예: "2019년 05월 13일", str → datetime)
    CONTRACT_PERIOD_END: str = "ctr_pd_bfcc_edd"  # 해지 전 계약 종료일 (예: "2019년 11월 13일", str → datetime)

    CANCEL_PURPOSE: str = "cc_pp"  # 해지 목적 (예: "계약기간 만료에 따른 해지", str)
    CANCEL_INSTITUTION: str = "cc_int"  # 해지 기관 (예: "삼성증권(Samsung Securities Co., Ltd.)", str)
    CANCEL_DATE: str = "cc_prd"  # 해지 예정일자 (예: "2019년 11월 13일", str → datetime)

    RETURN_METHOD: str = "tp_rm_atcc"  # 해지 후 신탁재산 반환방법 (예: "현금 및 실물(자사주) 반환", str)

class Dart_TreasuryStockTrustCancel_Unnecessary_Fields:
    """
    자기주식취득 신탁계약 해지 결정 API 응답 중 분석에 불필요한 필드 정의
    """

    RECEIPT_NO: str = "rcept_no"  # 접수번호 (예: "20191113000578", str)
    CORP_CLASS: str = "corp_cls"  # 법인구분 (예: "Y", str)
    CORP_CODE: str = "corp_code"  # 고유번호 (예: "00382199", str)

    AQ_WTN_DIV_OSTK: str = "aq_wtn_div_ostk"  # 해지 전 보유 주식 수 (보통주식) (예: "9,214,206", str)
    AQ_WTN_DIV_OSTK_RT: str = "aq_wtn_div_ostk_rt"  # 보통주식 비율 (%) (예: "1.94", str)
    AQ_WTN_DIV_ESTK: str = "aq_wtn_div_estk"  # 해지 전 기타주식 수량 (예: "-", str)
    AQ_WTN_DIV_ESTK_RT: str = "aq_wtn_div_estk_rt"  # 기타주식 비율 (%) (예: "-", str)

    EAQ_OSTK: str = "eaq_ostk"  # 기타취득 보통주식 수량 (예: "-", str)
    EAQ_OSTK_RT: str = "eaq_ostk_rt"  # 기타취득 보통주식 비율 (%) (예: "-", str)
    EAQ_ESTK: str = "eaq_estk"  # 기타취득 기타주식 수량 (예: "-", str)
    EAQ_ESTK_RT: str = "eaq_estk_rt"  # 기타취득 기타주식 비율 (%) (예: "-", str)

    OUTSIDE_DIR_PRESENT: str = "od_a_at_t"  # 사외이사 참석 인원 (예: "-", str)
    OUTSIDE_DIR_ABSENT: str = "od_a_at_b"  # 사외이사 불참 인원 (예: "-", str)
    AUDIT_ATTEND: str = "adt_a_atn"  # 감사 참석 여부 (예: "-", str)

########################################################