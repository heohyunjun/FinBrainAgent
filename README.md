# FinBrainAgent

## 주의사항 & 확장 방안
### 1.무료 API 제한

Alpha Vantage는 무료 플랜에 호출 횟수 제한이 있으며, 지연(딜레이 시세) 가능성
많은 요청이 들어오면 1분당 호출 횟수를 초과할 수 있다.

### 2.뉴스 출처 확장

RSS가 없는 언론사는 직접 HTML 스크래핑이 필요
다양한 매체의 헤드라인을 합쳐 더 풍부한 데이터 제공 가능.

### 3. LLM 환각 방지

LLM이 종종 실제로 없는 근거를 제시할 수 있으므로, 사용자에게 “참고 정보”와 “LLM 추론”을 분리해 보여주는 방식
(추가 구현) “답변 정확도 개선”을 위해 RAG(Retrieval-Augmented Generation) 기법을 사용 고려 


### 4.추가 기능

NER(개체명 인식): 질문에서 종목명이나 티커(symbol)를 자동 추출.
한국어 뉴스·국내 증권사 API 연동: 국내 투자자를 위한 데이터 보강.
리포트·공시 DB 연동: 기업 공시나 주요 애널리스트 리포트를 함께 제공.