import os
from typing import Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_google_cloud_sql_pg import PostgresEngine, PostgresVectorStore
from dotenv import load_dotenv

load_dotenv()


class VectorStoreProvider:
    def __init__(self):
        self._vector_store = None
        self._engine = None
        self._embeddings = None
        self._llm = None

    async def init(self):
        self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self._llm = ChatOpenAI(model_name="gpt-4o-mini-2024-07-18", temperature=0)

        self._engine = await PostgresEngine.afrom_instance(
            project_id=os.getenv("GCP_PROJECT_ID"),
            region=os.getenv("GCP_REGION"),
            instance=os.getenv("GCP_INSTANCE"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )

        self._vector_store = await PostgresVectorStore.create(
            engine=self._engine,
            embedding_service=self._embeddings,
            id_column="id",
            content_column="content",
            embedding_column="embedding",
            table_name="report_chunks",
            metadata_columns=["report_id", "chunk_index"],
        )

    def get_vector_store(self) -> PostgresVectorStore:
        return self._vector_store

    def get_engine(self) -> PostgresEngine:
        return self._engine

    def get_embeddings(self) -> OpenAIEmbeddings:
        return self._embeddings

    def get_llm(self) -> ChatOpenAI:
        return self._llm
    
    @property
    def llm(self):
        return self._llm
    
    @property
    def vector_store(self) -> PostgresVectorStore:
        return self._vector_store

    @property
    def engine(self) -> PostgresEngine:
        return self._engine

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        return self._embeddings