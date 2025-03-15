class FinancialNecessaryFields:
    """
    기업의 손익계산서에서 핵심 지표들을 정리한 클래스.
    """
    
    # 수익 및 비용 관련 지표
    TOTAL_REVENUE = "TotalRevenue"  # 총 매출 (회사의 전체 매출액)
    COST_OF_REVENUE = "CostOfRevenue"  # 매출 원가 (제품 또는 서비스 제공 비용)
    GROSS_PROFIT = "GrossProfit"  # 매출 총이익 (총 매출 - 매출 원가)
    
    # 이익 관련 지표
    OPERATING_INCOME = "OperatingIncome"  # 영업이익 (주요 영업 활동에서 발생한 이익)
    EBITDA = "EBITDA"  # 상각전영업이익 (세금, 이자, 감가상각비 제외 이익)
    EBIT = "EBIT"  # 이자 및 세금 차감 전 이익 (운영 성과 평가용)
    NET_INCOME = "NetIncome"  # 순이익 (최종 이익, 모든 비용과 세금 차감 후)
    
    # 주당순이익 (EPS)
    BASIC_EPS = "BasicEPS"  # 기본 주당순이익 (보통주 한 주당 이익)
    DILUTED_EPS = "DilutedEPS"  # 희석 주당순이익 (옵션, 채권 등을 고려한 주당순이익)
    
    # 금융 비용 및 세금
    INTEREST_EXPENSE = "InterestExpense"  # 이자 비용 (부채에 대한 이자 지급 비용)
    TAX_PROVISION = "TaxProvision"  # 법인세 비용 (기업이 납부해야 하는 세금)

class FinancialUnnecessaryFields:
    """
    손익계산서 데이터에서 불필요한 지표들을 정리한 클래스.
    """
    
    # 중복된 순이익 관련 지표
    NET_INCOME_COMMON = "NetIncomeCommonStockholders"  # 보통주 주주 순이익 (NetIncome과 동일)
    DILUTED_NI_AVAIL = "DilutedNIAvailtoComStockholders"  # 희석 주당순이익 계산용 순이익 (NetIncome과 유사)
    NET_INCOME_CONTINUOUS = "NetIncomeContinuousOperations"  # 계속사업 기준 순이익 (NetIncome과 유사)
    NET_INCOME_INCL_NONCONTROLLING = "NetIncomeIncludingNoncontrollingInterests"  # 소수 지분 포함 순이익
    
    # 비영업적 및 일회성 항목
    TOTAL_UNUSUAL_ITEMS = "TotalUnusualItems"  # 비정상적 항목 (일회성 비용/수익 포함)
    TOTAL_UNUSUAL_EXCL_GOODWILL = "TotalUnusualItemsExcludingGoodwill"  # 영업권 제외 비정상 항목
    GAIN_ON_SALE_OF_SECURITY = "GainOnSaleOfSecurity"  # 투자 증권 매각 이익
    OTHER_NON_OPERATING = "OtherNonOperatingIncomeExpenses"  # 비영업적 기타 비용
    SPECIAL_INCOME_CHARGES = "SpecialIncomeCharges"  # 특별손익 항목
    OTHER_SPECIAL_CHARGES = "OtherSpecialCharges"  # 기타 특별 손실
    
    # 기타 불필요한 항목
    OTHER_GA = "OtherGandA"  # 기타 일반관리비 (이미 GeneralAndAdministrativeExpense 포함)