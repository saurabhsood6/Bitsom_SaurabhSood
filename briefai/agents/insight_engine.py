"""Insight engine — identifies pain points and conversation angles for sales reps."""

from typing import List, Tuple

from models.schemas import CRMData, NewsArticle


DEAL_STAGE_PAIN_POINTS = {
    "Discovery": [
        "Unclear internal alignment on technology priorities and budget ownership",
        "Fragmented legacy tooling creating inefficiency and data silos",
    ],
    "Proposal": [
        "ROI justification required for executive stakeholder approval",
        "Competitive evaluation pressure — other vendors may be shortlisted",
    ],
    "Negotiation": [
        "Procurement process friction: multi-stakeholder approval and lengthy MSA review",
        "Budget constraints driving requests for discounts or phased implementation",
    ],
    "Closing": [
        "Implementation risk and change management concerns may delay final signature",
        "Internal champion may need executive air cover to finalize the deal",
    ],
}

DEAL_STAGE_ANGLES = {
    "Discovery": (
        "Lead with diagnostic questions to uncover the true scope of their data/AI "
        "challenges. Position your solution as a strategic enabler rather than a point tool."
    ),
    "Proposal": (
        "Anchor the conversation on measurable business outcomes and ROI. Bring a "
        "customer reference story from a similar industry to build credibility."
    ),
    "Negotiation": (
        "Shift focus from price to total value: implementation support, SLAs, and "
        "long-term partnership. Introduce an executive sponsor to elevate the conversation."
    ),
    "Closing": (
        "De-risk the final decision: offer a phased rollout or pilot milestone. Confirm "
        "implementation readiness and celebrate the shared vision to maintain momentum."
    ),
}


def extract_insights(
    crm_data: CRMData,
    news_articles: List[NewsArticle],
) -> Tuple[List[str], str]:
    """
    Derive pain points and a conversation angle from CRM data and news context.
    Returns (pain_points, conversation_angle).
    """
    deal_stage = crm_data.deal_stage
    pain_points = DEAL_STAGE_PAIN_POINTS.get(deal_stage, [
        "Unclear technology roadmap and strategic priorities",
        "Pressure to demonstrate measurable ROI from technology investments",
    ])

    # Augment pain points with news signals
    news_keywords = {
        "acquisition": "Integration complexity following recent M&A activity may create new technology standardization needs.",
        "restructur": "Organizational restructuring may introduce new decision makers and shift technology priorities.",
        "revenue": "Recent financial performance signals budget availability or tightening — tailor value proposition accordingly.",
        "partner": "New strategic partnerships may indicate openness to expanding vendor ecosystem.",
        "ai": "Active AI investment signals a receptive audience for AI-powered capabilities in your portfolio.",
        "cloud": "Active cloud migration initiatives create an immediate window for cloud-native solution positioning.",
    }

    augmented_pain_points = list(pain_points)
    for article in news_articles[:3]:
        text = (article.title + " " + article.summary).lower()
        for keyword, insight in news_keywords.items():
            if keyword in text and insight not in augmented_pain_points:
                augmented_pain_points.append(insight)
                break

    final_pain_points = augmented_pain_points[:2]
    conversation_angle = DEAL_STAGE_ANGLES.get(
        deal_stage,
        "Focus on understanding the prospect's strategic priorities and aligning your solution to their most pressing business outcomes.",
    )

    return final_pain_points, conversation_angle
