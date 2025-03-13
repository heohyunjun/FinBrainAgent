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