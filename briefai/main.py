"""BriefAI — FastAPI application entry point."""

import os
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

from agents.brief_generator import generate_brief
from db.database import (
    get_all_meetings,
    get_brief_by_meeting_id,
    get_meeting_by_id,
    init_db,
    save_brief,
    seed_meetings,
    update_meeting_brief_status,
)
from integrations.notification import notify
from models.schemas import Brief, BriefGenerationRequest, NotificationRequest

app = FastAPI(title="BriefAI", description="AI-Powered Sales Intelligence Agent", version="1.0.0")

BASE_DIR = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.on_event("startup")
def startup_event():
    init_db()
    seed_meetings()


def _meeting_to_display(m: dict) -> dict:
    """Enrich a meeting dict with display-friendly fields."""
    try:
        dt = datetime.fromisoformat(m["meeting_time"])
        m["meeting_time_display"] = dt.strftime("%b %d, %Y — %I:%M %p")
        m["meeting_time_iso"] = dt.isoformat()
    except Exception:
        m["meeting_time_display"] = m.get("meeting_time", "")
        m["meeting_time_iso"] = m.get("meeting_time", "")
    return m


# ─── HTML Routes ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    meetings = get_all_meetings()
    meetings = [_meeting_to_display(m) for m in meetings]
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"meetings": meetings},
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


@app.post("/api/notify")
def send_notification(req: NotificationRequest):
    meeting = get_meeting_by_id(req.meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    brief_data = get_brief_by_meeting_id(req.meeting_id)
    if not brief_data:
        raise HTTPException(status_code=404, detail="No brief found for this meeting. Generate a brief first.")

    brief = Brief(
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

    success = notify(brief, channel=req.channel, email_to=req.email_to)
    return {"status": "sent" if success else "fallback", "channel": req.channel}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
