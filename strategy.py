from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from agent import CompanyProfile


load_dotenv()


# ============================================================
# OUTPUT SCHEMAS
# ============================================================

class MarketingObservation(BaseModel):
    observation: str
    implication: str
    supporting_evidence: list[str] = Field(default_factory=list)


class LeadGenerationOpportunity(BaseModel):
    opportunity: str
    rationale: str
    suggested_approach: str
    supporting_evidence: list[str] = Field(default_factory=list)


class AutomationOpportunity(BaseModel):
    process: str
    automation_idea: str
    expected_benefit: str
    supporting_evidence: list[str] = Field(default_factory=list)


class RecommendedAction(BaseModel):
    action: str
    reason: str
    expected_outcome: str


class BusinessStrategy(BaseModel):
    marketing_observations: list[MarketingObservation]
    lead_generation_opportunities: list[LeadGenerationOpportunity]
    automation_opportunities: list[AutomationOpportunity]
    recommended_actions: list[RecommendedAction]


# ============================================================
# MODEL
# ============================================================

model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)

structured_model = model.with_structured_output(
    BusinessStrategy
)


# ============================================================
# LANGFUSE
# ============================================================

langfuse = get_client()
langfuse_handler = CallbackHandler()


# ============================================================
# STRATEGY
# ============================================================

def generate_strategy(
    company_profile: CompanyProfile,
    validation_issues: list[str] | None = None,
) -> BusinessStrategy:

    validation_issues = validation_issues or []

    evidence_text = "\n".join(
        (
            f"- {item.claim}\n"
            f"  Source: {item.source_url}"
        )
        for item in company_profile.evidence
    )

    retry_feedback = ""

    if validation_issues:
        retry_feedback = f"""
The previous strategy failed validation.

Fix these issues:

{chr(10).join(
    f"- {issue}"
    for issue in validation_issues
)}
"""

    prompt = f"""
You are a business growth strategist.

Analyze the researched company below.

Do not invent facts.

Clearly distinguish:
- Evidence-supported observations
- Strategic inferences

COMPANY

Name:
{company_profile.company_name}

Industry:
{company_profile.industry}

Description:
{company_profile.description}

Offer:
{company_profile.offer}

Target Audience:
{company_profile.target_audience}

Problem Solved:
{company_profile.problem_solved}

Business Model:
{company_profile.business_model}

SUPPORTING EVIDENCE

{evidence_text}

Generate:

1. Marketing observations
2. Lead generation opportunities
3. Automation opportunities
4. Recommended actions

Requirements:

- Every opportunity must be connected to the researched business.
- Do not invent company capabilities.
- Do not present speculation as fact.
- Supporting evidence should actually relate to the claim.
- Produce practical recommendations.

{retry_feedback}
"""

    return structured_model.invoke(
        prompt,
        config={
            "callbacks": [langfuse_handler],
            "run_name": "business-strategy-analysis",
        },
    )