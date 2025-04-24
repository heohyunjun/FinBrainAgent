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
from langchain_core.documents import Document
from langchain_google_cloud_sql_pg import PostgresEngine, PostgresVectorStore, Column
from sqlalchemy import text as sqlalchemy_text 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from team_graph.pdf_summarize_graph import map_reduce_graph


from utils.logger import logger
logging.getLogger("pdfminer").setLevel(logging.ERROR)
# .env 파일 로드
load_dotenv()


DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")        
DB_PASSWORD = os.getenv("DB_PASSWORD") 
DB_HOST = os.getenv("DB_HOST")         #
DB_PORT = os.getenv("DB_PORT", "5432") 
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID") 
GCP_REGION = os.getenv("GCP_REGION")        
GCP_INSTANCE = os.getenv("GCP_INSTANCE")      
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536 
LLM_MODEL = "gpt-4o-mini-2024-07-18"

REPORTS_TABLE_NAME = "reports"
CHUNKS_TABLE_NAME = "report_chunks"
DATABASE_URL = os.getenv("DATABASE_URL")
REPORTS_DIR = Path("./reports_pdf")


class ReportProcessor:
    def __init__(self, pdf_path: Path, llm_model, embedding_model, db_url):
        self.pdf_path = pdf_path
        self.split_docs: list[Document] = []
        self.metadata: dict = {}
        self.report_id: uuid.UUID | None = None

        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.llm = ChatOpenAI(temperature=0, model_name=llm_model)
        self.engine: AsyncEngine = create_async_engine(db_url, echo=False, future=True)

    async def run(self):
        await self._load_pdf()
        self._extract_metadata()
        await self._summarize()
        await self._save_report()
        await self._save_chunks_to_vector_db()

    async def _load_pdf(self):
        logger.info(f"PDF 로드 중: {self.pdf_path}")
        loader = PDFPlumberLoader(str(self.pdf_path))
        docs = loader.load()
        self.split_docs = self.text_splitter.split_documents(docs)

    def _extract_metadata(self):
        logger.info("파일명에서 메타데이터 추출 중...")
        filename = self.pdf_path.stem
        theme, title, broker = filename.split("_")
        self.metadata = {
            "title": title,
            "broker": broker,
            "date": datetime.date.today(),
            "view_count": len(self.split_docs),
            "theme": theme
        }

    async def _summarize(self):
        contents = [doc.page_content for doc in self.split_docs]
        initial_state = {"contents": contents}
        result = await map_reduce_graph.ainvoke(initial_state, config={"recursion_limit": 10})
        self.metadata["summary"] = result.get("translated_summary")

    async def _save_report(self):
        logger.info("reports 테이블에 메타데이터 삽입 중...")
        report_id = uuid.uuid4()
        sql = sqlalchemy_text("""
            INSERT INTO reports (id, title, broker, date, view_count, summary, theme)
            VALUES (:id, :title, :broker, :date, :view_count, :summary, :theme);
        """)

        try:
            async with self.engine.begin() as conn:
                await conn.execute(sql, {
                    "id": report_id,
                    **self.metadata
                })
            self.report_id = report_id
            logger.info(f"메타데이터 삽입 완료: {report_id}")
        except Exception as e:
            logger.error(f"메타데이터 삽입 실패: {e}")
            self.report_id = None

    async def _save_chunks_to_vector_db(self):
        logger.info("Vector DB에 청크 삽입 중...")
        if not self.report_id:
            logger.error("report_id 없음. Vector DB 저장 생략")
            return

        postgres_engine = await PostgresEngine.afrom_instance(
            project_id=GCP_PROJECT_ID,
            region=GCP_REGION,
            instance=GCP_INSTANCE,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )

        documents = [
            Document(
                page_content=doc.page_content,
                metadata={"report_id": str(self.report_id), "chunk_index": i}
            )
            for i, doc in enumerate(self.split_docs)
        ]

        store = await PostgresVectorStore.create(
            engine=postgres_engine,
            table_name=CHUNKS_TABLE_NAME,
            embedding_service=self.embeddings,
            id_column="id",
            content_column="content",
            embedding_column="embedding",
            metadata_columns=["report_id", "chunk_index"]
        )
        await store.aadd_documents(documents)
        logger.info(f"{len(documents)}개 청크 Vector DB 삽입 완료")


async def process_all_reports():
    pdf_files = sorted(REPORTS_DIR.glob("*.pdf"))
    logger.info(f"총 {len(pdf_files)}개 리포트 파일 발견됨")
    success = 0

    for pdf_path in pdf_files:
        try:
            logger.info(f"처리 시작: {pdf_path.name}")
            processor = ReportProcessor(pdf_path= pdf_path, 
                                        llm_model=LLM_MODEL, 
                                        embedding_model =EMBEDDING_MODEL,
                                        db_url= DATABASE_URL)
            await processor.run()
            success += 1
        except Exception as e:
            logger.error(f"{pdf_path.name} 처리 중 오류 발생: {e}")

    logger.info(f"총 {success}/{len(pdf_files)} 리포트 처리 완료")


if __name__ == "__main__":
    import asyncio
    asyncio.run(process_all_reports())
