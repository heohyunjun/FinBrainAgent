#################### 자기 주식 처분 ####################
class Dart_TreasuryStockDispositionDecision_Necessary_Fields:
    """
    자기주식 처분 결정 API 응답 중 분석에 필요한 필드 정의 (타입 및 예시 포함).
    """

    COMPANY: str = "corp_name"  # 회사명 (예: "미원상사", str)
    DATE: str = "dp_dd"  # 처분 결정일 (예: "2019년 04월 29일", str → datetime)

    STOCK_PLAN_COMMON: str = "dppln_stk_ostk"  # 처분 예정 주식 수 - 보통주 (예: "846", str → int)
    PRICE_COMMON: str = "dpstk_prc_ostk"       # 주식 가격 (보통주식, 예: "43,350", str → int)
    AMOUNT_COMMON: str = "dppln_prc_ostk"      # 처분 예정 금액 (예: "36,674,100", str → int)

    PERIOD_START: str = "dpprpd_bgd"  # 처분 예정 시작일 (예: "2019년 04월 30일", str → datetime)
    PERIOD_END: str = "dpprpd_edd"    # 처분 예정 종료일 (예: "2019년 04월 30일", str → datetime)

    PURPOSE: str = "dp_pp"  # 처분 목적 (예: "무상증자시 발생한 단주 주식 \n우리사주조합에 매각", str)

    METHOD_MARKET: str = "dp_m_mkt"     # 시장을 통한 매도 수량 (예: "0" 또는 "-", str → int)
    METHOD_BLOCK: str = "dp_m_ovtm"     # 시간외 대량매매 수량 (예: "0" 또는 "-", str → int)
    METHOD_OTC: str = "dp_m_otc"        # 장외처분 수량 (예: "846", str → int)


class Dart_TreasuryStockDispositionDecision_UnNecessary_Fields:
    """
    자기주식 처분 결정 API 응답에서 분석 목적에는 불필요한 보조/부가 필드 목록
    """
    RECEIPT_NO = "rcept_no"                   # 접수번호
    CORP_CODE = "corp_code"                  # 고유번호
    CORP_CLASS = "corp_cls"                  # 법인구분
    STOCK_ETC = "dppln_stk_estk"             # 처분 예정 기타주식 수
    PRICE_ETC = "dpstk_prc_estk"             # 기타주식 가격
    AMOUNT_ETC = "dppln_prc_estk"            # 기타주식 금액
    BROKER = "cs_iv_bk"                      # 위탁 투자중개업자
    NOTE = "rm"                              # 비고
    OUTSIDE_DIR_PRESENT = "od_a_at_t"        # 사외이사 참석
    OUTSIDE_DIR_ABSENT = "od_a_at_b"         # 사외이사 불참
    AUDIT_ATTEND = "adt_a_atn"               # 감사 참석여부
    DAILY_LIMIT_COMMON = "d1_slodlm_ostk"    # 1일 매도 주문한도 (보통주)
    DAILY_LIMIT_ETC = "d1_slodlm_estk"       # 1일 매도 주문한도 (기타주식)

    # 처분 전 자기주식 보유현황 관련 필드
    AQ_WTN_DIV_OSTK = "aq_wtn_div_ostk"         # 배당가능이익 보통주
    AQ_WTN_DIV_OSTK_RT = "aq_wtn_div_ostk_rt"   # 배당가능이익 보통주 비율
    AQ_WTN_DIV_ESTK = "aq_wtn_div_estk"         # 배당가능이익 기타주
    AQ_WTN_DIV_ESTK_RT = "aq_wtn_div_estk_rt"   # 배당가능이익 기타주 비율
    EAQ_OSTK = "eaq_ostk"                        # 기타취득 보통주
    EAQ_OSTK_RT = "eaq_ostk_rt"                  # 기타취득 보통주 비율
    EAQ_ESTK = "eaq_estk"                        # 기타취득 기타주
    EAQ_ESTK_RT = "eaq_estk_rt"                  # 기타취득 기타주 비율



#################### 자기 주식 취득 ####################
class Dart_TreasuryStockAcquisitionDecision_Necessary_Fields:
    """
    자기주식 취득 결정 API에서 분석에 필요한 필드 정의.
    """

    CORP_NAME: str = "corp_name"  # 회사명 (예: "현대자동차")
    AQ_DD: str = "aq_dd"  # 취득결정일 (예: "2019년 10월 25일", str → datetime)
    
    AQPLN_STK_OSTK: str = "aqpln_stk_ostk"  # 취득예정 보통주 수 (예: "2,136,681", str → int)
    AQPLN_STK_ESTK: str = "aqpln_stk_estk"  # 취득예정 기타주 수 (예: "632,707", str → int)
    
    AQPLN_PRC_OSTK: str = "aqpln_prc_ostk"  # 취득예정 보통주 금액 (예: "259,606,741,500", str → int)
    AQPLN_PRC_ESTK: str = "aqpln_prc_estk"  # 취득예정 기타주 금액 (예: "48,811,874,300", str → int)
    
    AQEXPD_BGD: str = "aqexpd_bgd"  # 취득예상기간 시작일 (예: "2019년 10월 25일", str → datetime)
    AQEXPD_EDD: str = "aqexpd_edd"  # 취득예상기간 종료일 (예: "2019년 11월 27일", str → datetime)
    
    AQ_PP: str = "aq_pp"  # 취득 목적 (예: "자기주식 취득을 통한 주주가치 제고")
    AQ_MTH: str = "aq_mth"  # 취득 방법 (예: "장내매수")

class Dart_TreasuryStockAcquisitionDecision_Unnecessary_Fields:
    """
    자기주식 취득 결정 API에서 분석에 불필요한 필드 정의.
    """

    RECEIPT_NO: str = "rcept_no"  # 접수번호
    CORP_CLASS: str = "corp_cls"  # 법인구분
    CORP_CODE: str = "corp_code"  # 고유번호
    
    BROKER: str = "cs_iv_bk"  # 위탁투자중개업자 (예: "현대차증권")
    
    # 보유 예상 기간
    HOLD_BGN: str = "hdexpd_bgd"  # 보유예상 시작일 (예: "2019년 10월 25일", str)
    HOLD_END: str = "hdexpd_edd"  # 보유예상 종료일 (예: "2019년 11월 29일", str)

    # 기존 보유 현황 (분석에 직접 사용하지 않음)
    AQ_WTN_DIV_OSTK: str = "aq_wtn_div_ostk"
    AQ_WTN_DIV_OSTK_RT: str = "aq_wtn_div_ostk_rt"
    AQ_WTN_DIV_ESTK: str = "aq_wtn_div_estk"
    AQ_WTN_DIV_ESTK_RT: str = "aq_wtn_div_estk_rt"
    EAQ_OSTK: str = "eaq_ostk"
    EAQ_OSTK_RT: str = "eaq_ostk_rt"
    EAQ_ESTK: str = "eaq_estk"
    EAQ_ESTK_RT: str = "eaq_estk_rt"

    # 사외이사, 감사 출석
    OUTSIDE_DIR_PRESENT: str = "od_a_at_t"
    OUTSIDE_DIR_ABSENT: str = "od_a_at_b"
    AUDIT_ATTEND: str = "adt_a_atn"

    # 1일 매수 한도
    DAILY_LIMIT_COMMON: str = "d1_prodlm_ostk"
    DAILY_LIMIT_ETC: str = "d1_prodlm_estk"
