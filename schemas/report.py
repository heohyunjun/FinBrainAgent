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

class ReportDetailOut(BaseModel):
    id: UUID
    title: str
    broker: str
    theme: str
    date: date
    summary: str

class QuestionRequest(BaseModel):
    message: str

class QuestionResponse(BaseModel):
    response: str

class ReportOut(BaseModel):
    id: uuid4
    title: str
    broker: str
    theme: str
    date: date

class UserInput(BaseModel):
    message: str
    thread_id: Optional[str] = None