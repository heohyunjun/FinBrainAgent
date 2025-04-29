from fastapi import APIRouter, Request, FastAPI
from uuid import UUID
import asyncio

from typing import List
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sqlalchemy_text
import os
from schemas.report import Report, ReportDetailResponse, ReportChatResponse, ReportChatRequest, ReportDetailRequest

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
    print(f"리포트 {len(reports_cache)}개 메모리에 캐싱 완료.")

async def preload_and_schedule_refresh(app: FastAPI):
    await preload_reports_from_db(app)  # 서버 부팅 시 1회
    while True:
        await asyncio.sleep(60 * 60 * 24)  # 24시간 대기
        print("24시간 지남: 리포트 리스트 DB에서 새로 불러오는 중...")
        await preload_reports_from_db(app)

@router.get("/reports", response_model=List[Report])
async def get_reports():
    return reports_cache

@router.post("/reports/detail", response_model=ReportDetailResponse)
async def get_report_detail(request: ReportDetailRequest):
    print(f"[POST] /reports/detail - 요청 도착")
    print(f"Report ID: {request.report_id}")

    return ReportDetailResponse(
        id=request.report_id,
        title="AI 대세전환",
        broker="미래에셋",
        theme="반도체",
        date=date.today(),
        summary="AI에 대한 전환적 투자 기회가 다가오고 있습니다...",
    )


@router.post("/reports/chat", response_model=ReportChatResponse)
async def ask_about_report(request: ReportChatRequest):
    print(f"리포트 ID: {request.report_id}")
    print(f"질문: {request.message}")

    return ReportChatResponse(response=f"'{request.message}'에 대한 답변입니다 (리포트 ID: {request.report_id})")