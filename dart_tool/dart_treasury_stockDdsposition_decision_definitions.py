class Dart_TreasuryStockDispositionDecision_Necessary_Fields:
    """
    자기주식 처분 결정 API 응답 중 주요 분석 필드 정의
    """
    DATE = "rcept_dt"              # 공시일
    COMPANY = "corp_name"          # 회사명
    STOCK_TYPE = "se"              # 주식 종류 (보통주 등)
    QUANTITY = "stkqy"             # 처분 주식 수
    METHOD = "fb"                  # 처분 방법
    PRICE = "prc"                  # 처분 단가
    AMOUNT = "amt"                 # 총 처분금액
    DISPOSAL_DATE = "dispst"       # 실제 처분일
    PURPOSE = "fncls"              # 자금 용도

class Dart_TreasuryStockDispositionDecision_UnNecessary_Fields:
    """
    분석 시 불필요한 응답 필드 목록
    """
    RECEIPT_NO = "rcept_no"        # 접수번호
    CORP_CODE = "corp_code"        # 고유번호
    GUARANTEE_DATE = "grntymd"     # 담보설정일 (대부분 공란)
    REMARKS = "rm"                 # 비고