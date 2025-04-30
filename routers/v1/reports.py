import asyncio
from typing import List

from fastapi import APIRouter, FastAPI, HTTPException, Request
from sqlalchemy import text as sqlalchemy_text
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from schemas.report import Report, ReportDetailResponse, ReportChatResponse, ReportChatRequest, ReportDetailRequest
from utils.logger import logger

router = APIRouter()

# 전역 캐시
reports_cache: List[Report] = []


async def preload_reports_from_db(app: FastAPI):
    global reports_cache
    query = sqlalchemy_text("""
        SELECT id, title, broker, date, view_count, summary, theme
        FROM reports
        ORDER BY date DESC;
    """)

    try:
        async with app.state.engine.begin() as conn:
            result = await conn.execute(query)
            rows = result.fetchall()

            reports_cache = [
                Report(
                    id=row.id,
                    title=row.title,
                    broker=row.broker,
                    date=row.date,
                    view_count=row.view_count,
                    summary=row.summary,
                    theme=row.theme
                )
                for row in rows
            ]

            logger.info(f"리포트 {len(reports_cache)}개 메모리에 캐싱 완료.")
    except Exception as e:
        logger.error(f"preload_reports_from_db 실패: {e}", exc_info=True)
        reports_cache = []


async def preload_and_schedule_refresh(app: FastAPI):
    await preload_reports_from_db(app)  # 서버 부팅 시 1회
    while True:
        await asyncio.sleep(60 * 60 * 24)  # 24시간 대기
        logger.info("24시간 지남: 리포트 리스트 DB에서 새로 불러오는 중...")
        await preload_reports_from_db(app)

@router.get("/reports", response_model=List[Report])
async def get_reports():
    return reports_cache

# 리포트 상세 조회
@router.post("/reports/detail", response_model=ReportDetailResponse)
async def get_report_detail(request: ReportDetailRequest):
    print(f"[POST] /reports/detail - 요청 도착")
    print(f"Report ID: {request.report_id}")

    # reports_cache에서 해당 id를 가진 Report 찾기
    matching_report = next((r for r in reports_cache if r.id == request.report_id), None)

    if not matching_report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportDetailResponse(
        id=matching_report.id,
        title=matching_report.title,
        broker=matching_report.broker,
        theme=matching_report.theme,
        date=matching_report.date,
        summary=matching_report.summary,
    )

@router.post("/reports/chat", response_model=ReportChatResponse)
async def ask_about_report(request: ReportChatRequest, fastapi_req: Request):
    logger.info(f"/reports/chat 질문 도착 - ID: {request.report_id}, 질문: {request.message}")

    try:
        vector_provider = fastapi_req.app.state.vector_provider
        if vector_provider is None:
            logger.error("VectorStoreProvider is not initialized")
            return ReportChatResponse(response="서버의 벡터 데이터가 초기화되지 않았습니다. 잠시 후 다시 시도해주세요.")

        # 1. 질문 임베딩
        query_embedding = await vector_provider.embeddings.aembed_query(request.message)

        # 2. 유사 문서 검색 (report_id로 필터링)
        results = await vector_provider.vector_store.asimilarity_search_with_score_by_vector(
            embedding=query_embedding,
            k=5,
            filter=f"report_id = '{str(request.report_id)}'"
        )

        if not results:
            logger.warning(f"관련 문서 없음 - ID: {request.report_id}")
            return ReportChatResponse(response="해당 리포트에서 관련 정보를 찾을 수 없습니다.")

        # 3. context 구성
        context = "\n\n".join([doc.page_content for doc, _ in results])


        # 4. 프롬프트 템플릿 정의
        prompt_template = PromptTemplate(
            input_variables=["context", "message"],
            template="""
            리포트 내용:\n{context}\n\n
            사용자 질문:\n{message}\n\n
            위 내용을 참고하여 명확하고 친절하게 답변해 주세요.
            모르면 모른다라고 대답하세요"""
        )

        report_retrieval_chain = prompt_template | vector_provider.llm | StrOutputParser()


        answer = await report_retrieval_chain.ainvoke({
                    "context": context,
                    "message": request.message
                })
        return ReportChatResponse(response=answer)

    except Exception as e:
        logger.error(f"/reports/chat 처리 중 예외 발생: {e}", exc_info=True)
        return ReportChatResponse(response="답변 생성에 실패했습니다. 질문을 다시 시도해주세요.")
