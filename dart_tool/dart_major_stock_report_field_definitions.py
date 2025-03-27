class Dart_MajorStockReport_Necessary_Fields:
    """
    DART 대량보유 상황보고서에서 주요 분석에 필요한 필드 정의 클래스.
    """

    # 필수 분석 필드
    RCEPT_DT = "rcept_dt"                   # 공시일자
    CORP_CODE = "corp_code"                 # 기업 고유번호
    CORP_NAME = "corp_name"                 # 회사명
    REPORT_TYPE = "report_tp"               # 보고 구분
    REPRESENTATIVE = "repror"               # 대표 보고자
    STOCK_COUNT = "stkqy"                   # 보유 주식 수
    STOCK_COUNT_CHANGE = "stkqy_irds"       # 주식 증감 수
    STOCK_RATIO = "stkrt"                   # 보유비율
    STOCK_RATIO_CHANGE = "stkrt_irds"       # 비율 증감
    REPORT_REASON = "report_resn"           # 보고 사유


class Dart_MajorStockReport_UnNecessary_Fields:
    RCEPT_NO = "rcept_no" # 접수번호(14자리)
    CTR_STKQY = "ctr_stkqy" # 주요체결 주식등의 수
    CTR_STKRT = "ctr_stkrt" # 주요체결 보유비율
