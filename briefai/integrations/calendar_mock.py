"""Mock calendar integration (Google/Outlook style) for BriefAI."""

from datetime import datetime
from typing import List
from models.schemas import Meeting


MOCK_MEETINGS: List[Meeting] = [
    Meeting(
        id="meet_001",
        contact_name="Rajesh Kumar",
        company="Infosys Limited",
        meeting_time=datetime(2026, 6, 7, 10, 0, 0),
        deal_stage="Proposal",
        notes="Discussed cloud migration needs. Budget approved for Q1.",
        brief_status="pending",
    ),
    Meeting(
        id="meet_002",
        contact_name="Priya Sharma",
        company="Tata Consultancy Services",
        meeting_time=datetime(2026, 6, 7, 14, 0, 0),
        deal_stage="Negotiation",
        notes="Enterprise license pricing discussion. Decision maker involved.",
        brief_status="pending",
    ),
    Meeting(
        id="meet_003",
        contact_name="Anand Mehta",
        company="Wipro Technologies",
        meeting_time=datetime(2026, 6, 8, 11, 0, 0),
        deal_stage="Discovery",
        notes="Initial call. Exploring AI/ML tooling requirements.",
        brief_status="pending",
    ),
    Meeting(
        id="meet_004",
        contact_name="Sarah Johnson",
        company="Accenture",
        meeting_time=datetime(2026, 6, 8, 15, 30, 0),
        deal_stage="Closing",
        notes="Final contract review. Legal approved. Awaiting signature.",
        brief_status="pending",
    ),
]


def get_upcoming_meetings() -> List[Meeting]:
    """Return upcoming meetings from the mock calendar."""
    now = datetime.now()
    upcoming = [m for m in MOCK_MEETINGS if m.meeting_time >= now]
    upcoming.sort(key=lambda m: m.meeting_time)
    return upcoming


def get_meeting_by_id(meeting_id: str) -> Meeting | None:
    """Return a specific meeting by ID."""
    for meeting in MOCK_MEETINGS:
        if meeting.id == meeting_id:
            return meeting
    return None
