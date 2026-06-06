"""
Google Calendar integration for BriefAI.

On first run, opens a browser for Google OAuth consent and saves token.json.
Subsequent runs use the saved token (auto-refreshed when expired).

Place credentials.json in the briefai/ directory (same folder as main.py).
"""

import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent          # briefai/
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Known company domain → display name mappings (extend as needed)
DOMAIN_MAP = {
    "infosys.com":    "Infosys Limited",
    "tcs.com":        "Tata Consultancy Services",
    "wipro.com":      "Wipro Technologies",
    "accenture.com":  "Accenture",
    "ibm.com":        "IBM",
    "microsoft.com":  "Microsoft",
    "google.com":     "Google",
    "amazon.com":     "Amazon",
    "salesforce.com": "Salesforce",
    "oracle.com":     "Oracle",
}


def _domain_to_company(email: str) -> str:
    """Derive a company name from an email address domain."""
    try:
        domain = email.split("@")[1].lower()
        if domain in DOMAIN_MAP:
            return DOMAIN_MAP[domain]
        # Strip TLD and capitalise: john@some-corp.com → Some Corp
        name = domain.split(".")[0]
        name = re.sub(r"[-_]", " ", name).title()
        return name
    except Exception:
        return "Unknown Company"


def _get_credentials():
    """Return valid Google OAuth2 credentials, running the auth flow if needed."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise ImportError(
            "Google Calendar libraries not installed. "
            "Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        )

    creds: Optional[object] = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_FILE}. "
                    "Download it from Google Cloud Console and place it in the briefai/ folder."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as fh:
            fh.write(creds.to_json())

    return creds


def _parse_event(event: dict) -> Optional[dict]:
    """Convert a Google Calendar event dict into a BriefAI meeting dict."""
    try:
        start = event.get("start", {})
        dt_str = start.get("dateTime") or start.get("date")
        if not dt_str:
            return None

        meeting_time = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        # Convert to local naive datetime for consistent storage
        meeting_time = meeting_time.astimezone().replace(tzinfo=None)

        # Determine contact name and company from attendees
        attendees = event.get("attendees", [])
        organizer = event.get("organizer", {})

        contact_name = "Unknown Contact"
        company = "Unknown Company"

        # Pick the first external attendee (not self)
        self_email = organizer.get("email", "")
        for att in attendees:
            if att.get("self"):
                continue
            name = att.get("displayName") or att.get("email", "").split("@")[0].replace(".", " ").title()
            contact_name = name
            company = _domain_to_company(att.get("email", ""))
            break

        # Fall back to organizer if no external attendee found
        if contact_name == "Unknown Contact" and organizer:
            contact_name = organizer.get("displayName") or organizer.get("email", "Unknown")
            company = _domain_to_company(organizer.get("email", ""))

        summary = event.get("summary", "Untitled Meeting")
        description = event.get("description", "") or ""

        # If company resolved to a personal email provider, use the meeting title instead
        personal_domains = {"gmail.com", "googlemail.com", "yahoo.com", "outlook.com",
                            "hotmail.com", "icloud.com", "protonmail.com"}
        all_attendee_emails = [a.get("email", "") for a in attendees] + [organizer.get("email", "")]
        all_external = [e for e in all_attendee_emails if not e.endswith(tuple(personal_domains))]
        if company in ("Gmail", "Yahoo", "Outlook", "Hotmail", "Icloud", "Protonmail", "Unknown Company"):
            if all_external:
                company = _domain_to_company(all_external[0])
            else:
                # Last resort: derive from the meeting title
                company = summary

        # Stable deterministic ID from Google event ID
        meeting_id = "gcal_" + hashlib.md5(event.get("id", summary).encode()).hexdigest()[:10]

        return {
            "id": meeting_id,
            "contact_name": contact_name,
            "company": company,
            "meeting_time": meeting_time.strftime("%Y-%m-%d %H:%M:%S"),
            "deal_stage": "Discovery",       # Default; override via CRM enrichment
            "notes": (description[:200] if description else summary),
            "brief_status": "pending",
            "gcal_event_id": event.get("id", ""),
            "gcal_summary": summary,
        }
    except Exception as e:
        print(f"[calendar] Skipping event due to parse error: {e}")
        return None


def fetch_upcoming_from_google(max_results: int = 20) -> List[dict]:
    """
    Fetch upcoming meetings from Google Calendar.
    Returns a list of meeting dicts ready to be upserted into the DB.
    """
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "Google Calendar libraries not installed. "
            "Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        )

    creds = _get_credentials()
    service = build("calendar", "v3", credentials=creds)

    now_utc = datetime.now(timezone.utc).isoformat()

    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now_utc,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = result.get("items", [])
    meetings = []
    for ev in events:
        parsed = _parse_event(ev)
        if parsed:
            meetings.append(parsed)

    print(f"[calendar] Fetched {len(meetings)} upcoming meetings from Google Calendar.")
    return meetings


def is_google_calendar_configured() -> bool:
    """Return True if credentials.json or token.json is present."""
    return CREDENTIALS_FILE.exists() or TOKEN_FILE.exists()
