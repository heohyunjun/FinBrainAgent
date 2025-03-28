class Dart_TreasuryStockDispositionDecision_Necessary_Fields:
    """
    자기주식 처분 결정 API 응답 중 주요 분석 필드 정의
    """
    DATE = "dp_dd"                          # 처분 결정일
    COMPANY = "corp_name"                  # 회사명
    STOCK_PLAN_COMMON = "dppln_stk_ostk"   # 처분 예정 주식 수 (보통주식)
    PRICE_COMMON = "dpstk_prc_ostk"        # 주식 가격 (보통주식)
    AMOUNT_COMMON = "dppln_prc_ostk"       # 처분 예정 금액 (보통주식)
    PERIOD_START = "dpprpd_bgd"            # 처분 예정 시작일
    PERIOD_END = "dpprpd_edd"              # 처분 예정 종료일
    PURPOSE = "dp_pp"                      # 처분 목적
    METHOD_MARKET = "dp_m_mkt"             # 처분 방법 - 시장
    METHOD_OTC = "dp_m_otc"                # 처분 방법 - 장외
    METHOD_BLOCK = "dp_m_ovtm"             # 처분 방법 - 시간외 대량매매

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
