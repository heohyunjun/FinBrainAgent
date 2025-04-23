import os
import uuid
import datetime
import logging
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader, PDFPlumberLoader

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document

import operator
from typing import Annotated, List, TypedDict, Literal, Optional
from langgraph.types import Send

from langgraph.graph import END, START, StateGraph
from langchain.chains.combine_documents.reduce import (
    acollapse_docs, split_list_of_docs,
)

from langchain_google_cloud_sql_pg import PostgresEngine, PostgresVectorStore, Column
from sqlalchemy import text as sqlalchemy_text 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from utils.logger import logger

# .env 파일 로드
load_dotenv()


import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# === 1. 설정 ===
DB_NAME = "investment_db"
DB_USER = os.getenv("DB_USER")        
DB_PASSWORD = os.getenv("DB_PASSWORD") 
DB_HOST = os.getenv("DB_HOST")         #
DB_PORT = os.getenv("DB_PORT", "5432") 
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID") 
GCP_REGION = os.getenv("GCP_REGION")        
GCP_INSTANCE = os.getenv("GCP_INSTANCE")      

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PDF_FILE_PATH = "./reports_pdf/반도체_선제적빌드업수요로전년비33%성장_유진투자증권.pdf"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536 # 스키마와 일치 확인
LLM_MODEL = "gpt-4o-mini-2024-07-18"

REPORTS_TABLE_NAME = "reports"
CHUNKS_TABLE_NAME = "report_chunks"
DATABASE_URL = os.getenv("DATABASE_URL")
REPORTS_DIR = Path("./reports_pdf")

token_max = 1000
class OverallState(TypedDict):
    contents: List[str]
    summaries: Annotated[list, operator.add]
    collapsed_summaries: List[Document]
    final_summary: str
    translated_summary: str

# === 2. 컴포넌트 초기화 ===
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini-2024-07-18")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, future=True)

# === 3. LangGraph 구성 ===
map_chain = ChatPromptTemplate.from_template("Write a concise summary of the following: {context}.") | llm | StrOutputParser()
reduce_chain = ChatPromptTemplate.from_template(
    "The following is a set of summaries:\n{docs}\nTake these and distill it into a final summary."
) | llm | StrOutputParser()

def load_and_extract_docs_list(pdf_path: str, text_splitter: RecursiveCharacterTextSplitter) -> str:
    """PDF 파일을 로드하고 전체 텍스트 내용을 추출합니다."""

    logger.info(f"PDF 파일 로드 시작: {pdf_path}")
    loader = PDFPlumberLoader(pdf_path)
    try:
        docs = loader.load_and_split(text_splitter)
        docs = loader.load()
        split_docs = text_splitter.split_documents(docs)
        if not docs: 
            logger.error("PDF에서 텍스트를 추출하지 못했습니다.")
            return None, None

        logger.info(f"PDF 로드 완료. 총 {len(docs)} 페이지")
        return split_docs, len(docs)
    except Exception as e:
        logger.error(f"PDF 로드 중 오류 발생: {e}")
        return None, None
    

def extract_metadata_from_filename(filepath: str, total_pages:int) -> dict:
    """파일 경로에서 간단하게 메타데이터 추출"""

    logger.info("메타데이터 추출 중 (파일명 기반)...")
    filename = os.path.basename(filepath)
    name_part = filename.rsplit('.pdf', 1)[0]
    parts = name_part.split('_')
    title = " ".join(parts[:-1])
    broker = parts[-1]
    metadata = { 
        "title": title if title else "제목 없음", 
        "broker": broker if broker else "증권사 불명",
        "date": datetime.date.today(), 
        "view_count": total_pages, 
        "theme": "반도체"
        }
    logger.info(f"추출된 메타데이터: {metadata}")
    return metadata


async def insert_report_metadata(engine: AsyncEngine, report_data: dict) -> Optional[uuid.UUID]:
    logger.info("`reports` 테이블에 메타데이터 삽입 시도...")

    report_id = uuid.uuid4()

    sql = sqlalchemy_text("""
        INSERT INTO reports (id, title, broker, date, view_count, summary, theme)
        VALUES (:id, :title, :broker, :date, :view_count, :summary, :theme);
    """)

    try:
        async with engine.begin() as conn:  # 커넥션 + 트랜잭션
            await conn.execute(sql, {
                "id": report_id,
                "title": report_data["title"],
                "broker": report_data["broker"],
                "date": report_data["date"],  # datetime.date 객체 권장
                "view_count": report_data["view_count"],
                "summary": report_data["summary"],
                "theme": report_data["theme"]
            })
        logger.info(f"`reports` 테이블 삽입 완료 (report_id: {report_id})")
        return report_id
    except Exception as e:
        logger.error(f"`reports` 테이블 삽입 실패: {e}")
        return None

async def generate_summary_node(state: dict):
    logger.debug(f"Generating summary for content chunk...")
    response = await map_chain.ainvoke({"context": state["content"]})
    return {"summaries": [response]}


def collect_summaries_node(state: OverallState):
    logger.debug("Collecting summaries for potential collapsing...")
    return {"collapsed_summaries": [Document(page_content=summary) for summary in state["summaries"]]}

def length_function(documents: List[Document]) -> int: 
    return sum(llm.get_num_tokens(doc.page_content) for doc in documents)


async def collapse_summaries_node(state: OverallState):
    logger.info("Collapsing summaries as they exceed token_max...")
    collapsed_summaries = state["collapsed_summaries"]
    doc_lists = split_list_of_docs(collapsed_summaries, length_function, token_max)
    results = []
    for doc_list in doc_lists:
        collapsed_doc = await acollapse_docs(doc_list, reduce_chain.ainvoke)
        results.append(collapsed_doc)
    logger.info(f"Summaries collapsed into {len(results)} documents.")
    return {"collapsed_summaries": results}

async def generate_final_summary_node(state: OverallState):
    logger.info("Generating final summary...")
    response = await reduce_chain.ainvoke({"docs": state["collapsed_summaries"]})
    return {"final_summary": response}

def map_summaries_edge(state: OverallState):
    logger.debug("Mapping contents to summary nodes...")
    return [Send("generate_summary_node", {"content": content}) for content in state["contents"]]

def should_collapse_edge(state: OverallState) -> Literal["collapse_summaries_node", "generate_final_summary_node"]:
    num_tokens = length_function(state["collapsed_summaries"])
    logger.debug(f"Checking if summaries need collapsing. Current token count: {num_tokens}, Max: {token_max}")
    if num_tokens > token_max: 
        logger.info("Summaries exceed token limit, collapsing further.")
        return "collapse_summaries_node"
    else: 
        logger.info("Summaries within token limit, generating final summary.")
        return "generate_final_summary_node"


async def translate_to_korean_node(state: OverallState):
    logger.info("Translating final summary to Korean...")

    final_summary = state.get("final_summary")
    if not final_summary:
        logger.warning("No final summary found. Skipping translation.")
        return {"translated_summary": None}

    # 번역 프롬프트
    translate_template = (
        "Please translate the following text into **natural and professional Korean**:\n\n"
        f"{final_summary}"
    )


    translate_prompt = ChatPromptTemplate.from_template(translate_template)
    translate_chain = translate_prompt | llm | StrOutputParser()


    translated = await translate_chain.ainvoke({"final_summary" : state["final_summary"]})
    logger.info(f"translated = {translated}")

    return {"translated_summary": translated}


graph_builder = StateGraph(OverallState)
graph_builder.add_node("generate_summary_node", generate_summary_node)
graph_builder.add_node("collect_summaries_node", collect_summaries_node)
graph_builder.add_node("collapse_summaries_node", collapse_summaries_node)
graph_builder.add_node("generate_final_summary_node", generate_final_summary_node)
graph_builder.add_node("translate_to_korean_node", translate_to_korean_node)

graph_builder.add_conditional_edges(START, map_summaries_edge, ["generate_summary_node"])
graph_builder.add_edge("generate_summary_node", "collect_summaries_node")
graph_builder.add_conditional_edges("collect_summaries_node", should_collapse_edge)
graph_builder.add_conditional_edges("collapse_summaries_node", should_collapse_edge)
graph_builder.add_edge("generate_final_summary_node", "translate_to_korean_node")
graph_builder.add_edge("translate_to_korean_node", END)

map_reduce_graph = graph_builder.compile()

# === 4. 요약 처리 함수 ===
async def run_langgraph_summary(docs: list[Document]) -> str:
    contents = [doc.page_content for doc in docs]
    initial_state = {"contents": contents}
    result = await map_reduce_graph.ainvoke(initial_state, config={"recursion_limit": 10})
    return result.get("translated_summary")

# === 5. 메인 처리 ===
async def process_pdf_report_async(pdf_path: str):
    split_docs, page_count = load_and_extract_docs_list(pdf_path, text_splitter)
    if not split_docs:
        logger.error("문서 로드 실패")
        return

    metadata = extract_metadata_from_filename(pdf_path, page_count)
    metadata["summary"] = await run_langgraph_summary(split_docs)

    report_id = await insert_report_metadata(engine, metadata)
    if not report_id:
        logger.error("메타데이터 삽입 실패")
        return

    postgres_engine = await PostgresEngine.afrom_instance(
        project_id=GCP_PROJECT_ID, region=GCP_REGION, instance=GCP_INSTANCE,
        database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

    documents = [
        Document(page_content=doc.page_content, metadata={"report_id": str(report_id), "chunk_index": i})
        for i, doc in enumerate(split_docs)
    ]

    store = await PostgresVectorStore.create(
        engine=postgres_engine,
        table_name=CHUNKS_TABLE_NAME,
        embedding_service=embeddings,
        id_column="id",
        content_column="content",
        embedding_column="embedding",
        metadata_columns=["report_id", "chunk_index"]
    )

    await store.aadd_documents(documents)
    logger.info(f"{len(documents)}개의 청크 삽입 완료.")



async def process_multiple_reports():
    pdf_files = sorted(REPORTS_DIR.glob("*.pdf"))
    logger.info(f"총 {len(pdf_files)}개의 리포트 파일 발견됨")

    success_count = 0
    for pdf_path in pdf_files:
        try:
            logger.info(f"\n\n=== 리포트 처리 시작: {pdf_path.name} ===")
            await process_pdf_report_async(str(pdf_path))
            success_count += 1
        except Exception as e:
            logger.error(f" {pdf_path.name} 처리 중 오류 발생: {e}")
    
    logger.info(f"\n 총 {success_count}/{len(pdf_files)}개 리포트 처리 완료")

if __name__ == "__main__":
    import asyncio
    asyncio.run(process_multiple_reports())
