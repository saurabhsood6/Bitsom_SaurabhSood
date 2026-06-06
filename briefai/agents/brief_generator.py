"""Core brief generation agent for BriefAI — orchestrates all data sources and calls Claude."""

import os
from datetime import datetime
from typing import Optional

import anthropic

from agents.crm_connector import get_crm_data
from agents.insight_engine import extract_insights
from agents.news_aggregator import get_company_news
from models.schemas import Brief, CRMData, NewsArticle


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5-20251001"


def _build_prompt(
    contact_name: str,
    company: str,
    meeting_time: datetime,
    crm_data: CRMData,
    news_summaries: list[str],
    pain_points: list[str],
    conversation_angle: str,
) -> str:
    news_block = "\n".join(f"- {n}" for n in news_summaries)
    tasks_block = "\n".join(f"- {t}" for t in crm_data.open_tasks)
    pain_block = "\n".join(f"- {p}" for p in pain_points)

    return f"""You are BriefAI, an expert sales intelligence assistant. Generate a concise, actionable pre-meeting brief for an enterprise sales representative.

## Meeting Details
- Contact: {contact_name}
- Company: {company}
- Meeting Time: {meeting_time.strftime("%B %d, %Y at %I:%M %p")}

## CRM Context
- Deal Stage: {crm_data.deal_stage}
- Deal Value: {crm_data.deal_value or "TBD"}
- Last Interaction: {crm_data.last_interaction}
- Notes: {crm_data.notes}
- Open Tasks:
{tasks_block}

## Recent Company News (last 3-5 days)
{news_block}

## Identified Pain Points
{pain_block}

## Suggested Conversation Angle
{conversation_angle}

---

Generate a structured pre-meeting brief with these EXACT sections. Each section should be concise but information-dense. The entire brief should be readable in 1-2 minutes.

Respond in this exact JSON format:
{{
  "company_overview": "<2-3 sentences: what the company does, scale, strategic focus>",
  "recent_news": [
    "<key news point 1 — business implication for the sales rep>",
    "<key news point 2 — business implication for the sales rep>",
    "<key news point 3 — business implication for the sales rep>"
  ],
  "crm_context": "<2-3 sentences summarizing deal history, stakeholder dynamics, and what matters most right now>",
  "talking_points": [
    "<actionable talking point 1 tied to their current priority>",
    "<actionable talking point 2 tied to their pain points>",
    "<actionable talking point 3 tied to the deal stage>"
  ],
  "pain_points": [
    "<pain point 1 with specific evidence from news or CRM>",
    "<pain point 2 with specific evidence from news or CRM>"
  ],
  "conversation_angle": "<1-2 sentences: the single best opening angle for this specific meeting>"
}}

Return ONLY the JSON object. No markdown, no explanation, no preamble."""


def _parse_claude_response(raw: str) -> dict:
    """Parse Claude's JSON response, with robust fallback."""
    import json
    import re

    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    cleaned = cleaned.rstrip("`").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Attempt to extract JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse Claude response as JSON:\n{raw[:500]}")


def _generate_fallback_brief(
    contact_name: str,
    company: str,
    crm_data: CRMData,
    news_summaries: list[str],
    pain_points: list[str],
    conversation_angle: str,
) -> dict:
    """Fallback brief when Claude API is unavailable."""
    return {
        "company_overview": (
            f"{company} is a leading enterprise technology and services organization with a global footprint. "
            f"The company is actively investing in digital transformation and AI adoption. "
            f"Your contact {contact_name} is a key decision-maker in the current {crm_data.deal_stage} stage engagement."
        ),
        "recent_news": news_summaries[:3] if news_summaries else [
            f"{company} continues to expand its technology capabilities.",
            "Market dynamics are creating opportunities for strategic partnerships.",
            "Industry analysts highlight growing demand for AI-powered enterprise solutions.",
        ],
        "crm_context": (
            f"Currently in {crm_data.deal_stage} stage with a deal value of {crm_data.deal_value or 'TBD'}. "
            f"Last interaction: {crm_data.last_interaction}. {crm_data.notes}"
        ),
        "talking_points": [
            f"Reference the deal progress to date and confirm alignment on next steps for {crm_data.deal_stage} stage.",
            f"Address open task: {crm_data.open_tasks[0] if crm_data.open_tasks else 'Confirm stakeholder alignment'}.",
            "Demonstrate clear ROI and implementation support to build confidence in the partnership.",
        ],
        "pain_points": pain_points,
        "conversation_angle": conversation_angle,
    }


def generate_brief(
    meeting_id: str,
    contact_name: str,
    company: str,
    meeting_time: datetime,
) -> Brief:
    """
    Orchestrate all data sources and generate a structured pre-meeting brief.
    Uses Claude if API key is available, otherwise falls back to rule-based generation.
    """
    # Gather data from all sources
    crm_data = get_crm_data(company)
    news_articles = get_company_news(company)
    pain_points, conversation_angle = extract_insights(crm_data, news_articles)

    news_summaries = [
        f"{art.title} ({art.source}, {art.published_at}): {art.summary}"
        for art in news_articles[:5]
    ]

    if ANTHROPIC_API_KEY:
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            prompt = _build_prompt(
                contact_name=contact_name,
                company=company,
                meeting_time=meeting_time,
                crm_data=crm_data,
                news_summaries=news_summaries,
                pain_points=pain_points,
                conversation_angle=conversation_angle,
            )
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_response = message.content[0].text
            parsed = _parse_claude_response(raw_response)
        except Exception as e:
            print(f"[BriefGenerator] Claude API call failed: {e}. Using fallback.")
            parsed = _generate_fallback_brief(
                contact_name, company, crm_data, news_summaries, pain_points, conversation_angle
            )
            raw_response = str(parsed)
    else:
        print("[BriefGenerator] No ANTHROPIC_API_KEY set. Using fallback brief generation.")
        parsed = _generate_fallback_brief(
            contact_name, company, crm_data, news_summaries, pain_points, conversation_angle
        )
        raw_response = str(parsed)

    return Brief(
        meeting_id=meeting_id,
        company=company,
        contact_name=contact_name,
        generated_at=datetime.now(),
        company_overview=parsed.get("company_overview", ""),
        recent_news=parsed.get("recent_news", []),
        crm_context=parsed.get("crm_context", ""),
        talking_points=parsed.get("talking_points", []),
        pain_points=parsed.get("pain_points", pain_points),
        conversation_angle=parsed.get("conversation_angle", conversation_angle),
        raw_content=raw_response,
    )
