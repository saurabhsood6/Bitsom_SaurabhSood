"""BriefAI — FastAPI application entry point."""

import os
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

load_dotenv()

from agents.brief_generator import generate_brief
from db.database import (
    get_all_meetings,
    get_brief_by_meeting_id,
    get_meeting_by_id,
    get_meeting_years_months,
    get_meetings_for_auto_brief,
    init_db,
    save_brief,
    seed_meetings,
    sync_brief_statuses,
    update_meeting_auto_brief,
    update_meeting_brief_status,
    update_meeting_stage,
    upsert_meetings_from_calendar,
)
from integrations.notification import notify, send_email_notification
from integrations.google_calendar import fetch_upcoming_from_google, is_google_calendar_configured
from models.schemas import Brief, NotificationRequest

app = FastAPI(title="BriefAI", description="AI-Powered Sales Intelligence Agent", version="1.0.0")

BASE_DIR = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ─── Scheduler ────────────────────────────────────────────────────────────────

def _run_auto_brief_job():
    """Called every 15 minutes. Generates briefs for meetings 2h away with auto_brief=1."""
    pending = get_meetings_for_auto_brief()
    for m in pending:
        try:
            print(f"[scheduler] Auto-generating brief for {m['company']} ({m['id']})")
            update_meeting_brief_status(m["id"], "generating")
            meeting_time = datetime.fromisoformat(m["meeting_time"])
            brief = generate_brief(
                meeting_id=m["id"],
                contact_name=m["contact_name"],
                company=m["company"],
                meeting_time=meeting_time,
            )
            brief_dict = brief.dict()
            brief_dict["generated_at"] = brief.generated_at.isoformat()
            save_brief(brief_dict)
            update_meeting_brief_status(m["id"], "ready")
            print(f"[scheduler] Brief ready for {m['company']}")

            # Send email if configured
            email = m.get("notify_email", "").strip()
            if email:
                send_email_notification(brief, email)
                print(f"[scheduler] Notification sent to {email}")
        except Exception as e:
            update_meeting_brief_status(m["id"], "failed")
            print(f"[scheduler] Auto-brief failed for {m['id']}: {e}")


@app.on_event("startup")
def startup_event():
    init_db()
    seed_meetings()
    sync_brief_statuses()   # fix any stale 'pending' statuses where a brief already exists

    if is_google_calendar_configured():
        print("[startup] Google Calendar detected — syncing meetings...")
        try:
            meetings = fetch_upcoming_from_google()
            upsert_meetings_from_calendar(meetings)
            print(f"[startup] Synced {len(meetings)} meetings from Google Calendar.")
        except Exception as e:
            print(f"[startup] Google Calendar sync failed: {e}.")

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(_run_auto_brief_job, "interval", minutes=15, id="auto_brief")
        scheduler.start()
        print("[startup] Auto-brief scheduler started (runs every 15 min).")
    except Exception as e:
        print(f"[startup] Scheduler not started: {e}")


def _meeting_to_display(m: dict) -> dict:
    try:
        dt = datetime.fromisoformat(m["meeting_time"])
        m["meeting_time_display"] = dt.strftime("%b %d, %Y — %I:%M %p")
        m["meeting_time_iso"] = dt.isoformat()
    except Exception:
        m["meeting_time_display"] = m.get("meeting_time", "")
        m["meeting_time_iso"] = m.get("meeting_time", "")
    return m


def _brief_from_db(brief_data: dict) -> Brief:
    return Brief(
        meeting_id=brief_data["meeting_id"],
        company=brief_data["company"],
        contact_name=brief_data["contact_name"],
        generated_at=datetime.fromisoformat(brief_data["generated_at"]),
        company_overview=brief_data["company_overview"],
        recent_news=brief_data["recent_news"],
        crm_context=brief_data["crm_context"],
        talking_points=brief_data["talking_points"],
        pain_points=brief_data["pain_points"],
        conversation_angle=brief_data["conversation_angle"],
    )


# ─── HTML Routes ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None),
):
    now = datetime.now()
    active_year  = year or now.year
    active_month = month

    meetings = get_all_meetings(year=active_year, month=active_month)
    meetings = [_meeting_to_display(m) for m in meetings]
    periods  = get_meeting_years_months()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "meetings":     meetings,
            "periods":      periods,
            "active_year":  active_year,
            "active_month": active_month,
            "current_year": now.year,
        },
    )


@app.get("/meetings/{meeting_id}/brief", response_class=HTMLResponse)
def brief_page(request: Request, meeting_id: str):
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting = _meeting_to_display(meeting)
    brief = get_brief_by_meeting_id(meeting_id)
    return templates.TemplateResponse(
        request=request,
        name="brief.html",
        context={"meeting": meeting, "brief": brief},
    )


# ─── API Routes ────────────────────────────────────────────────────────────────

@app.get("/api/meetings")
def api_get_meetings():
    meetings = get_all_meetings()
    return {"meetings": meetings, "count": len(meetings)}


@app.get("/api/meetings/{meeting_id}")
def api_get_meeting(meeting_id: str):
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@app.post("/meetings/{meeting_id}/generate-brief")
def generate_brief_endpoint(meeting_id: str):
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    update_meeting_brief_status(meeting_id, "generating")
    try:
        meeting_time = datetime.fromisoformat(meeting["meeting_time"])
        brief = generate_brief(
            meeting_id=meeting_id,
            contact_name=meeting["contact_name"],
            company=meeting["company"],
            meeting_time=meeting_time,
        )
        brief_dict = brief.dict()
        brief_dict["generated_at"] = brief.generated_at.isoformat()
        save_brief(brief_dict)
        update_meeting_brief_status(meeting_id, "ready")
        return {"status": "success", "message": "Brief generated successfully"}
    except Exception as e:
        update_meeting_brief_status(meeting_id, "failed")
        raise HTTPException(status_code=500, detail=f"Brief generation failed: {str(e)}")


@app.post("/meetings/{meeting_id}/update-stage")
def update_deal_stage(meeting_id: str, stage: str = Query(...)):
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    valid = {"Discovery", "Proposal", "Negotiation", "Closing", "Won", "Lost"}
    if stage not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {', '.join(sorted(valid))}")
    update_meeting_stage(meeting_id, stage)
    return {"status": "success", "deal_stage": stage}


class AutoBriefRequest(BaseModel):
    auto_brief: bool
    notify_email: str = ""


@app.post("/meetings/{meeting_id}/auto-brief")
def set_auto_brief(meeting_id: str, req: AutoBriefRequest):
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    update_meeting_auto_brief(meeting_id, req.auto_brief, req.notify_email)
    return {"status": "success", "auto_brief": req.auto_brief, "notify_email": req.notify_email}


@app.post("/meetings/{meeting_id}/send-brief")
def send_brief_email(meeting_id: str, email_to: str = Query(...)):
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    brief_data = get_brief_by_meeting_id(meeting_id)
    if not brief_data:
        raise HTTPException(status_code=404, detail="No brief found. Generate a brief first.")
    brief = _brief_from_db(brief_data)
    success = send_email_notification(brief, email_to)
    return {"status": "sent" if success else "fallback", "email": email_to}


@app.post("/api/notify")
def send_notification(req: NotificationRequest):
    meeting = get_meeting_by_id(req.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    brief_data = get_brief_by_meeting_id(req.meeting_id)
    if not brief_data:
        raise HTTPException(status_code=404, detail="No brief found. Generate a brief first.")
    brief = _brief_from_db(brief_data)
    success = notify(brief, channel=req.channel, email_to=req.email_to)
    return {"status": "sent" if success else "fallback", "channel": req.channel}


@app.post("/api/sync-calendar")
def sync_calendar():
    if not is_google_calendar_configured():
        raise HTTPException(status_code=400, detail="credentials.json not found.")
    try:
        meetings = fetch_upcoming_from_google()
        upsert_meetings_from_calendar(meetings)
        return {"status": "success", "synced": len(meetings)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calendar sync failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
