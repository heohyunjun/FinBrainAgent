from typing import List
from langchain_openai import OpenAI

class QuestionClassifier:
    def __init__(self, llm: OpenAI, categories: List[str] = None):
        """
        질문을 카테고리로 분류하는 클래스를 초기화.
        :param llm: OpenAI LLM 모델 인스턴스 (LangChain 기반)
        :param categories: 분류할 카테고리 리스트 (기본값: 사전 정의된 카테고리)
        """
        self.llm = llm
        self.categories = categories or ["거시경제", "기업분석", "산업동향", "암호화폐", "ETF/펀드", "기타"]

    def classify(self, question: str) -> str:
        """
        주어진 질문을 LLM을 사용하여 카테고리 중 하나로 분류.
        """
        if not question.strip():
            return "기타"

        classification_prompt = f"""
        너는 질문을 아래 카테고리 중 하나로 분류해라
        {self.categories}.

        사용자의 질문:
        {question}

        위 카테고리 중 가장 잘 맞는 것을 정확히 하나만 골라라
        카테고리 이름만 출력해라.
        """

        response_text = self.llm.invoke(classification_prompt)
        print(response_text)

        return response_text if response_text.content in self.categories else "기타"

