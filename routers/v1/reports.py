import asyncio
from typing import List

from fastapi import APIRouter, FastAPI, HTTPException
from sqlalchemy import text as sqlalchemy_text

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
        logger.error(f"리포트 캐싱 실패: {e}")
        reports_cache = []  # 실패 시 캐시 초기화

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
async def ask_about_report(request: ReportChatRequest):
    print(f"리포트 ID: {request.report_id}")
    print(f"질문: {request.message}")

    return ReportChatResponse(response=f"'{request.message}'에 대한 답변입니다 (리포트 ID: {request.report_id})")