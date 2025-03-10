# %%
# 표준 라이브러리
from typing import Literal
from typing_extensions import TypedDict, List
import os 

# 서드파티 라이브러리
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, START, END
from pyzerox import zerox

# LangChain 관련 라이브러리
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    TextLoader,
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain import hub

load_dotenv()


# %%
MODEL_NAME = "gemma2-9b-it"

groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model_name=MODEL_NAME, api_key=groq_api_key)


# %%
class AgentState(TypedDict):
    query: str
    context: List[Document]
    answer: str

# %%
# 이미 생성된 크로마 db 가져오기
embeddings_model = HuggingFaceEmbeddings(
    model_name='jhgan/ko-sroberta-nli',
    model_kwargs={'device':'cpu'},
    encode_kwargs={'normalize_embeddings':True},
)


vector_store = Chroma(
    embedding_function=embeddings_model,
    collection_name = "income_tax_collection",
    persist_directory = "./income_tax_collection"
)

retriever = vector_store.as_retriever(search_kwargs = {"k":3})

# %%
prompt = hub.pull("rlm/rag-prompt")
generate_prompt = hub.pull("rlm/rag-prompt")
doc_relevance_prompt = hub.pull("langchain-ai/rag-document-relevance")

# %%

def retrieve(state: AgentState):
    query = state["query"]
    docs = retriever.invoke(query)
    return {"context" : docs}



def check_doc_relevance(state : AgentState) -> Literal['relevant', 'irrelevant']:
    query = state["query"]
    context = state["context"]
    print(f"context == {context}")
    doc_relevance_chain = doc_relevance_prompt | llm
    response = doc_relevance_chain.invoke({"question" : query, "documents" : context})
    print(f"response == {response}")
    if response["Score"] ==1:
        return "relevant"
    return "irrelevant"





dictionary = ['직장인 -> 거주자']
rewrite_prompt = PromptTemplate.from_template(f"""
사용자 질문을 보고, 우리 사전 참고해서 사용자의 질문을 변경해라
사전: {dictionary}
질문: {{query}}                                              
""")


def rewrite(state: AgentState):
    query = state["query"]
    rewrite_chain = rewrite_prompt | llm | StrOutputParser()
    

    response = rewrite_chain.invoke({"query" : query})
    print(f"rewrite_response =={response}")
    return {"query" : response}



# %%
# 할루시네이션 프롬프트 수정 
hallucination_prompt = PromptTemplate.from_template("""
You are a teacher tasked with evaluating whether a student's answer is based on documents or not,
Given documents, which are excerpts from income tax law, and a student's answer;
If the student's answer is based on documents, respond with "not hallucinated",
If the student's answer is not based on documents, respond with "hallucinated".

documents: {documents}
student_answer: {student_answer}
""")

generate_llm = ChatGroq(model_name=MODEL_NAME, api_key=groq_api_key, max_tokens=100)
hallucination_llm = ChatGroq(model_name=MODEL_NAME, api_key=groq_api_key, temperature=0)


def generate(state: AgentState) -> AgentState:

    context = state['context']
    query = state['query']
    rag_chain = generate_prompt | generate_llm | StrOutputParser()
    response = rag_chain.invoke({'question': query, 'context': context})
    print(f"response == {response}")

    return {'answer': response}

def check_hallucination(state: AgentState) -> Literal['hallucinated', 'not hallucinated']:
    answer = state['answer']
    context = state['context']
    context = [doc.page_content for doc in context]
    hallucination_chain = hallucination_prompt | hallucination_llm | StrOutputParser()
    response = hallucination_chain.invoke({'student_answer': answer, 'documents': context})
    print(f"hallucination_response == {response}")
    return response

# %%
helpfulness_prompt = hub.pull("langchain-ai/rag-answer-helpfulness")


# %%
def check_helpfulness_grader(state: AgentState) -> str:

    query = state['query']
    answer = state['answer']

    helpfulness_chain = helpfulness_prompt | llm
    
    response = helpfulness_chain.invoke({'question': query, 'student_answer': answer})

    if response['Score'] == 1:
        return 'helpful'
    
    return 'unhelpful'

def check_helpfulness(state: AgentState) -> AgentState:
    return state


# %%
graph_builder = StateGraph(AgentState)

graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("generate", generate)
graph_builder.add_node("rewrite", rewrite)

graph_builder.add_node("check_helpfulness", check_helpfulness)


graph_builder.add_edge(START, "retrieve")
graph_builder.add_conditional_edges(
    "retrieve",
    check_doc_relevance,
    {
        "relevant" : "generate",
        "irrelevant" : END
    }
)

# 거짓이면 재생성 
# 거짓아니면 답변이랑 체크 
graph_builder.add_conditional_edges(
    "generate",
    check_hallucination,
    {
        "hallucinated" : "generate",
        "not hallucinated" : "check_helpfulness"
    }
)

graph_builder.add_conditional_edges(
    "check_helpfulness",
    check_helpfulness_grader,
    {
        "helpful" : END,
        "unhelpful" : "rewrite"
    }
)

graph_builder.add_edge("rewrite", "retrieve")
graph  = graph_builder.compile()
# %%



