"""Notification system for BriefAI — console and email delivery."""

import os
import smtplib
import textwrap
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from models.schemas import Brief


def _format_brief_text(brief: Brief) -> str:
    """Format a brief as plain text."""
    lines = [
        "=" * 60,
        f"PRE-MEETING BRIEF: {brief.company}",
        f"Contact: {brief.contact_name}",
        f"Generated: {brief.generated_at.strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        "",
        "COMPANY OVERVIEW",
        "-" * 40,
        textwrap.fill(brief.company_overview, width=72),
        "",
        "RECENT NEWS",
        "-" * 40,
    ]
    for i, news in enumerate(brief.recent_news, 1):
        lines.append(f"{i}. {news}")
    lines += [
        "",
        "CRM CONTEXT",
        "-" * 40,
        textwrap.fill(brief.crm_context, width=72),
        "",
        "TALKING POINTS",
        "-" * 40,
    ]
    for i, tp in enumerate(brief.talking_points, 1):
        lines.append(f"{i}. {tp}")
    lines += [
        "",
        "POTENTIAL PAIN POINTS",
        "-" * 40,
    ]
    for i, pp in enumerate(brief.pain_points, 1):
        lines.append(f"{i}. {pp}")
    lines += [
        "",
        "SUGGESTED CONVERSATION ANGLE",
        "-" * 40,
        textwrap.fill(brief.conversation_angle, width=72),
        "",
        "=" * 60,
    ]
    return "\n".join(lines)


def send_console_notification(brief: Brief) -> bool:
    """Print brief to console."""
    print(_format_brief_text(brief))
    return True


def send_email_notification(brief: Brief, email_to: str) -> bool:
    """Send brief via SMTP email."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        print(f"[Notification] SMTP credentials not configured. "
              f"Would send brief for {brief.company} to {email_to}")
        print(_format_brief_text(brief))
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"BriefAI: Pre-Meeting Brief — {brief.company}"
        msg["From"] = smtp_user
        msg["To"] = email_to

        text_part = MIMEText(_format_brief_text(brief), "plain")
        html_content = _format_brief_html(brief)
        html_part = MIMEText(html_content, "html")

        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, email_to, msg.as_string())

        print(f"[Notification] Brief for {brief.company} sent to {email_to}")
        return True

    except Exception as e:
        print(f"[Notification] Failed to send email: {e}")
        return False


def _format_brief_html(brief: Brief) -> str:
    """Format a brief as HTML email."""
    news_items = "".join(f"<li>{n}</li>" for n in brief.recent_news)
    talking_items = "".join(f"<li>{tp}</li>" for tp in brief.talking_points)
    pain_items = "".join(f"<li>{pp}</li>" for pp in brief.pain_points)

    return f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
    <h1 style="color: #1a56db;">Pre-Meeting Brief: {brief.company}</h1>
    <p><strong>Contact:</strong> {brief.contact_name} |
       <strong>Generated:</strong> {brief.generated_at.strftime('%Y-%m-%d %H:%M')}</p>
    <hr/>
    <h2>Company Overview</h2><p>{brief.company_overview}</p>
    <h2>Recent News</h2><ul>{news_items}</ul>
    <h2>CRM Context</h2><p>{brief.crm_context}</p>
    <h2>Talking Points</h2><ul>{talking_items}</ul>
    <h2>Potential Pain Points</h2><ul>{pain_items}</ul>
    <h2>Suggested Conversation Angle</h2><p>{brief.conversation_angle}</p>
    </body></html>
    """


def notify(brief: Brief, channel: str = "console", email_to: Optional[str] = None) -> bool:
    """Dispatch notification via specified channel."""
    if channel == "email" and email_to:
        return send_email_notification(brief, email_to)
    return send_console_notification(brief)
