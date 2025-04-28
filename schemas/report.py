# app/schemas/report.py
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import date
from typing import Optional

class Report(BaseModel):
    id: UUID
    title: str
    broker: str
    date: date
    view_count: int
    summary: str
    theme: str

class ReportChatRequest(BaseModel):
    report_id: UUID
    message: str

class ReportChatResponse(BaseModel):
    response: str
class ReportDetailRequest(BaseModel):
    report_id: UUID

class ReportDetailResponse(BaseModel):
    id: UUID
    title: str
    broker: str
    theme: str
    date: date
    summary: str

class UserInput(BaseModel):
    message: str
    thread_id: Optional[str] = None