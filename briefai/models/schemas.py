"""Pydantic models for BriefAI data structures."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class Meeting(BaseModel):
    id: str
    contact_name: str
    company: str
    meeting_time: datetime
    deal_stage: str
    notes: Optional[str] = None
    brief_status: str = "pending"  # pending, generating, ready, failed


class CRMData(BaseModel):
    company: str
    contact_name: str
    deal_stage: str
    deal_value: Optional[str] = None
    last_interaction: str
    notes: str
    open_tasks: List[str] = []


class NewsArticle(BaseModel):
    title: str
    summary: str
    source: str
    published_at: str
    url: Optional[str] = None


class Brief(BaseModel):
    meeting_id: str
    company: str
    contact_name: str
    generated_at: datetime
    company_overview: str
    recent_news: List[str]
    crm_context: str
    talking_points: List[str]
    pain_points: List[str]
    conversation_angle: str
    raw_content: Optional[str] = None


class BriefGenerationRequest(BaseModel):
    meeting_id: str


class NotificationRequest(BaseModel):
    meeting_id: str
    channel: str = "console"  # console or email
    email_to: Optional[str] = None
