"""Mock CRM connector (Salesforce/HubSpot style) for BriefAI."""

from models.schemas import CRMData

MOCK_CRM_DATA = {
    "Infosys Limited": CRMData(
        company="Infosys Limited",
        contact_name="Rajesh Kumar",
        deal_stage="Proposal",
        deal_value="$250,000",
        last_interaction="2025-01-10 — Demo call. Stakeholders impressed with cloud migration capabilities.",
        notes="Budget approved for Q1. Key decision maker is CTO Rajesh Kumar. Previous vendor contract expires March 2025. They have a 3-year digital transformation roadmap.",
        open_tasks=[
            "Send updated proposal with enterprise pricing",
            "Schedule technical deep-dive with their cloud team",
            "Provide reference customers in banking sector",
        ],
    ),
    "Tata Consultancy Services": CRMData(
        company="Tata Consultancy Services",
        contact_name="Priya Sharma",
        deal_stage="Negotiation",
        deal_value="$1,200,000",
        last_interaction="2025-01-12 — Pricing negotiation call. Requested 15% volume discount.",
        notes="Enterprise license discussion ongoing. Legal team reviewed MSA. Priya Sharma is VP of Technology Procurement with full signing authority. Competitive bid from Competitor X also in play.",
        open_tasks=[
            "Respond to discount request — check with finance",
            "Send revised MSA with agreed SLA terms",
            "Arrange executive sponsor introduction call",
        ],
    ),
    "Wipro Technologies": CRMData(
        company="Wipro Technologies",
        contact_name="Anand Mehta",
        deal_stage="Discovery",
        deal_value="TBD",
        last_interaction="2025-01-08 — Initial intro call. High-level overview of AI/ML needs.",
        notes="Early stage. Anand Mehta is Director of Innovation. Team of 200+ data scientists. Currently using open-source tooling and looking to standardize. Budget cycle starts Q2.",
        open_tasks=[
            "Send product overview deck",
            "Schedule discovery workshop with their data science leads",
            "Identify all stakeholders in the buying committee",
        ],
    ),
    "Accenture": CRMData(
        company="Accenture",
        contact_name="Sarah Johnson",
        deal_stage="Closing",
        deal_value="$3,500,000",
        last_interaction="2025-01-14 — Final contract review. Minor redlines from their legal team.",
        notes="Contract in final stages. Legal approved with two minor amendments. Sarah Johnson is Managing Director. Implementation start date targeted for Feb 1, 2025. Champion internally is their CTO.",
        open_tasks=[
            "Confirm final contract amendments are addressed",
            "Prepare onboarding plan and kickoff agenda",
            "Coordinate with professional services for implementation timeline",
        ],
    ),
}


def get_crm_data(company: str) -> CRMData:
    """Retrieve CRM data for a given company."""
    if company in MOCK_CRM_DATA:
        return MOCK_CRM_DATA[company]
    # Generic fallback for unknown companies
    return CRMData(
        company=company,
        contact_name="Unknown Contact",
        deal_stage="Discovery",
        deal_value="TBD",
        last_interaction="No recent interactions recorded",
        notes="No CRM data available for this company.",
        open_tasks=["Research company background", "Identify key stakeholders"],
    )
