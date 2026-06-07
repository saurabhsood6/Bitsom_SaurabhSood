"""News aggregation agent for BriefAI — fetches and summarizes company news."""

import os
from datetime import datetime, timedelta
from typing import List

import requests

from models.schemas import NewsArticle

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

MOCK_NEWS_DATA: dict[str, List[NewsArticle]] = {
    "Infosys Limited": [
        NewsArticle(
            title="Infosys Expands AI-First Cloud Migration Practice",
            summary="Infosys announced a major expansion of its AI-first cloud migration services, targeting Fortune 500 clients with a new accelerator framework that reduces migration time by 40%.",
            source="Economic Times",
            published_at=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            url="https://example.com/infosys-ai-cloud",
        ),
        NewsArticle(
            title="Infosys Q3 Revenue Beats Estimates, Raises FY25 Guidance",
            summary="Infosys reported Q3 revenue of $4.66B, beating analyst estimates by 2.1%. The company raised its full-year revenue growth guidance to 4.5-5% in constant currency, citing strong deal wins in North America and Europe.",
            source="Bloomberg",
            published_at=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            url="https://example.com/infosys-q3",
        ),
        NewsArticle(
            title="Infosys Partners with Microsoft on Generative AI Solutions",
            summary="Infosys and Microsoft deepened their strategic partnership to co-develop generative AI solutions for enterprise clients, with a focus on SAP modernization and supply chain automation.",
            source="Reuters",
            published_at=(datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
            url="https://example.com/infosys-msft",
        ),
    ],
    "Tata Consultancy Services": [
        NewsArticle(
            title="TCS Wins $500M Digital Transformation Deal with European Bank",
            summary="TCS secured a landmark $500 million deal with a major European bank to lead a 5-year digital core transformation, including cloud migration, data platform modernization, and AI-driven customer experience.",
            source="Financial Times",
            published_at=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            url="https://example.com/tcs-bank-deal",
        ),
        NewsArticle(
            title="TCS Launches AI.Cloud Unit to Accelerate Enterprise Adoption",
            summary="TCS announced the launch of its dedicated AI.Cloud business unit, combining over 60,000 AI-trained professionals and a suite of proprietary accelerators to help enterprises scale AI adoption.",
            source="Mint",
            published_at=(datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
            url="https://example.com/tcs-aicloud",
        ),
        NewsArticle(
            title="TCS Named Leader in Gartner Magic Quadrant for IT Services",
            summary="TCS was positioned as a Leader in the 2025 Gartner Magic Quadrant for IT Services for the 8th consecutive year, recognized for execution capability and AI-driven service delivery.",
            source="Business Standard",
            published_at=(datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
            url="https://example.com/tcs-gartner",
        ),
    ],
    "Wipro Technologies": [
        NewsArticle(
            title="Wipro Acquires AI Startup to Bolster Data Science Platform",
            summary="Wipro completed acquisition of an AI-native data science startup, adding 150+ AI specialists and a proprietary MLOps platform to its engineering portfolio.",
            source="TechCrunch",
            published_at=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            url="https://example.com/wipro-acquisition",
        ),
        NewsArticle(
            title="Wipro's New CEO Outlines 'AI-First' Transformation Strategy",
            summary="Wipro's new CEO presented a bold AI-first strategy at the annual investor day, committing $1B in AI investment over 3 years and targeting 20% of revenue from AI-native services by 2027.",
            source="CNBC",
            published_at=(datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
            url="https://example.com/wipro-ai-strategy",
        ),
        NewsArticle(
            title="Wipro Reports Modest Q3 Growth, Sees Recovery in BFSI Segment",
            summary="Wipro reported 1.8% QoQ revenue growth in Q3, with notable recovery in the BFSI vertical. Management signaled improving deal pipeline with large deal wins up 35% year-over-year.",
            source="Reuters",
            published_at=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            url="https://example.com/wipro-q3",
        ),
    ],
    "Accenture": [
        NewsArticle(
            title="Accenture Reports Record $3.9B in New AI Bookings This Quarter",
            summary="Accenture reported a record $3.9 billion in new AI-related bookings this quarter, with generative AI services now representing 15% of total new bookings, up from 6% last year.",
            source="Wall Street Journal",
            published_at=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            url="https://example.com/accenture-ai-bookings",
        ),
        NewsArticle(
            title="Accenture Expands Workforce to 50,000 AI Specialists",
            summary="Accenture announced plans to expand its AI specialist workforce to 50,000 by end of 2025, through a combination of new hiring and reskilling of existing employees.",
            source="Bloomberg",
            published_at=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            url="https://example.com/accenture-workforce",
        ),
        NewsArticle(
            title="Accenture Named Preferred Partner for AWS Generative AI",
            summary="AWS named Accenture as its preferred generative AI partner for enterprise deployments, a designation expected to drive significant co-selling opportunities across industry verticals.",
            source="Forbes",
            published_at=(datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
            url="https://example.com/accenture-aws",
        ),
    ],
    "IBM": [
        NewsArticle(
            title="IBM Reports Strong Hybrid Cloud and AI Revenue Growth",
            summary="IBM posted 7% growth in its hybrid cloud and AI segment, driven by adoption of the watsonx AI platform and strong consulting demand for enterprise AI transformation projects.",
            source="Reuters",
            published_at=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            url="https://example.com/ibm-cloud-ai",
        ),
        NewsArticle(
            title="IBM Expands watsonx AI Platform with New Governance Features",
            summary="IBM announced major governance and compliance features for its watsonx platform, targeting regulated industries like banking, healthcare and government where AI explainability is mandatory.",
            source="ZDNet",
            published_at=(datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
            url="https://example.com/ibm-watsonx",
        ),
        NewsArticle(
            title="IBM and SAP Deepen Partnership for AI-Powered ERP Modernisation",
            summary="IBM and SAP announced a deepened partnership to help enterprises migrate to SAP S/4HANA using IBM's hybrid cloud infrastructure and AI-powered migration accelerators.",
            source="Financial Times",
            published_at=(datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
            url="https://example.com/ibm-sap",
        ),
    ],
    "HCL Technologies": [
        NewsArticle(
            title="HCL Tech Wins $200M Digital Engineering Deal with US Manufacturer",
            summary="HCL Technologies secured a $200M, 5-year digital engineering and IoT transformation deal with a leading US industrial manufacturer, expanding its manufacturing vertical footprint.",
            source="Business Standard",
            published_at=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            url="https://example.com/hcl-manufacturing",
        ),
        NewsArticle(
            title="HCLTech Launches AI Force Platform for Enterprise Automation",
            summary="HCL Technologies unveiled AI Force, its unified AI automation platform combining generative AI, RPA and intelligent document processing, targeting cost reduction of 30–40% for enterprise back-office operations.",
            source="Economic Times",
            published_at=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            url="https://example.com/hcl-aiforce",
        ),
        NewsArticle(
            title="HCL Tech Q3 Revenue Grows 5.6%, Raises Annual Guidance",
            summary="HCL Technologies reported Q3 revenue of $3.3B, up 5.6% YoY in constant currency, and raised its FY guidance to 6–7% growth, citing strong momentum in engineering services and cloud-native application development.",
            source="Mint",
            published_at=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            url="https://example.com/hcl-q3",
        ),
    ],
}


def _fetch_from_newsapi(company: str) -> List[NewsArticle]:
    """Fetch real news from NewsAPI."""
    if not NEWSAPI_KEY:
        print(f"[NewsAggregator] NEWSAPI_KEY is not set — skipping live fetch for '{company}', using mock data.")
        return []

    try:
        # Free-tier NewsAPI plans only index articles with some delay, so requesting
        # the last 24h often returns zero results — go back a bit further instead.
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": company,
            "from": from_date,
            "sortBy": "publishedAt",
            "pageSize": 5,
            "language": "en",
            "apiKey": NEWSAPI_KEY,
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            try:
                detail = response.json().get("message", response.text)
            except Exception:
                detail = response.text
            print(f"[NewsAggregator] NewsAPI returned HTTP {response.status_code} for '{company}': {detail}. Using mock data.")
            return []

        data = response.json()
        if data.get("status") != "ok":
            print(f"[NewsAggregator] NewsAPI error for '{company}': {data.get('message', data)}. Using mock data.")
            return []

        articles = []
        for art in data.get("articles", []):
            articles.append(
                NewsArticle(
                    title=art.get("title", "No title"),
                    summary=art.get("description") or (art.get("content") or "")[:300],
                    source=art.get("source", {}).get("name", "Unknown"),
                    published_at=art.get("publishedAt", "")[:10],
                    url=art.get("url", ""),
                )
            )

        if not articles:
            print(f"[NewsAggregator] NewsAPI returned 0 articles for '{company}'. Using mock data.")

        return articles
    except Exception as e:
        print(f"[NewsAggregator] NewsAPI fetch failed for '{company}': {e}. Using mock data.")
        return []


def get_company_news(company: str) -> List[NewsArticle]:
    """Fetch recent news for a company. Falls back to mock data if no API key."""
    live_articles = _fetch_from_newsapi(company)
    if live_articles:
        return live_articles

    # Fallback: check mock data; if not found, generate generic mock articles
    if company in MOCK_NEWS_DATA:
        return MOCK_NEWS_DATA[company]

    return [
        NewsArticle(
            title=f"{company} Continues Digital Transformation Initiatives",
            summary=f"{company} has been actively investing in technology modernization and AI adoption as part of its strategic growth plan.",
            source="Industry News",
            published_at=datetime.now().strftime("%Y-%m-%d"),
        ),
        NewsArticle(
            title=f"{company} Expands Strategic Partnerships",
            summary=f"{company} recently announced new strategic partnerships aimed at accelerating innovation and expanding market reach.",
            source="Business Wire",
            published_at=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        ),
        NewsArticle(
            title=f"{company} Reports Strong Quarterly Performance",
            summary=f"{company} posted solid quarterly results, beating analyst expectations and raising full-year guidance on the back of strong enterprise demand.",
            source="Market Watch",
            published_at=(datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
        ),
    ]
