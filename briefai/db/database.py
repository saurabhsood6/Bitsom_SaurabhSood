"""SQLite database setup and operations for BriefAI."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List

DB_PATH = Path(__file__).parent / "briefai.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            contact_name TEXT NOT NULL,
            company TEXT NOT NULL,
            meeting_time TEXT NOT NULL,
            deal_stage TEXT NOT NULL,
            notes TEXT,
            brief_status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            company TEXT NOT NULL,
            contact_name TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            company_overview TEXT NOT NULL,
            recent_news TEXT NOT NULL,
            crm_context TEXT NOT NULL,
            talking_points TEXT NOT NULL,
            pain_points TEXT NOT NULL,
            conversation_angle TEXT NOT NULL,
            raw_content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        )
    """)

    conn.commit()
    conn.close()


def seed_meetings():
    """Seed sample meeting data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM meetings")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    meetings = [
        {
            "id": "meet_001",
            "contact_name": "Rajesh Kumar",
            "company": "Infosys Limited",
            "meeting_time": "2025-01-15 10:00:00",
            "deal_stage": "Proposal",
            "notes": "Discussed cloud migration needs. Budget approved for Q1.",
        },
        {
            "id": "meet_002",
            "contact_name": "Priya Sharma",
            "company": "Tata Consultancy Services",
            "meeting_time": "2025-01-15 14:00:00",
            "deal_stage": "Negotiation",
            "notes": "Enterprise license pricing discussion. Decision maker involved.",
        },
        {
            "id": "meet_003",
            "contact_name": "Anand Mehta",
            "company": "Wipro Technologies",
            "meeting_time": "2025-01-16 11:00:00",
            "deal_stage": "Discovery",
            "notes": "Initial call. Exploring AI/ML tooling requirements.",
        },
        {
            "id": "meet_004",
            "contact_name": "Sarah Johnson",
            "company": "Accenture",
            "meeting_time": "2025-01-16 15:30:00",
            "deal_stage": "Closing",
            "notes": "Final contract review. Legal approved. Awaiting signature.",
        },
    ]

    for m in meetings:
        cursor.execute(
            """INSERT OR IGNORE INTO meetings
               (id, contact_name, company, meeting_time, deal_stage, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (m["id"], m["contact_name"], m["company"],
             m["meeting_time"], m["deal_stage"], m["notes"])
        )

    conn.commit()
    conn.close()


def upsert_meetings_from_calendar(meetings: list):
    """Insert or update meetings synced from Google Calendar."""
    conn = get_connection()
    cursor = conn.cursor()
    for m in meetings:
        cursor.execute(
            """INSERT INTO meetings (id, contact_name, company, meeting_time, deal_stage, notes, brief_status)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 contact_name = excluded.contact_name,
                 company      = excluded.company,
                 meeting_time = excluded.meeting_time,
                 notes        = excluded.notes""",
            (m["id"], m["contact_name"], m["company"],
             m["meeting_time"], m.get("deal_stage", "Discovery"),
             m.get("notes", ""), m.get("brief_status", "pending"))
        )
    conn.commit()
    conn.close()


def get_all_meetings() -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meetings ORDER BY meeting_time ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_meeting_by_id(meeting_id: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_meeting_brief_status(meeting_id: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE meetings SET brief_status = ? WHERE id = ?",
        (status, meeting_id)
    )
    conn.commit()
    conn.close()


def save_brief(brief_data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO briefs
        (meeting_id, company, contact_name, generated_at, company_overview,
         recent_news, crm_context, talking_points, pain_points,
         conversation_angle, raw_content)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        brief_data["meeting_id"],
        brief_data["company"],
        brief_data["contact_name"],
        brief_data["generated_at"],
        brief_data["company_overview"],
        json.dumps(brief_data["recent_news"]),
        brief_data["crm_context"],
        json.dumps(brief_data["talking_points"]),
        json.dumps(brief_data["pain_points"]),
        brief_data["conversation_angle"],
        brief_data.get("raw_content", ""),
    ))
    brief_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return brief_id


def get_brief_by_meeting_id(meeting_id: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM briefs WHERE meeting_id = ? ORDER BY created_at DESC LIMIT 1",
        (meeting_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    result = dict(row)
    result["recent_news"] = json.loads(result["recent_news"])
    result["talking_points"] = json.loads(result["talking_points"])
    result["pain_points"] = json.loads(result["pain_points"])
    return result
