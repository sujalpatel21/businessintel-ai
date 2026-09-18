from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from research import research_business


load_dotenv()


# ============================================================
# DATA MODELS
# ============================================================

class Evidence(BaseModel):
    source_title: str
    source_url: str
    claim: str


class CompanyProfile(BaseModel):
    company_name: str
    industry: str
    description: str
    offer: str
    target_audience: str
    problem_solved: str
    business_model: str
    evidence: list[Evidence] = Field(default_factory=list)


# ============================================================
# MODEL + OBSERVABILITY
# ============================================================

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)

structured_model = model.with_structured_output(
    CompanyProfile
)

langfuse = get_client()
langfuse_handler = CallbackHandler()


# ============================================================
# CONTEXT BUILDER
# ============================================================

def build_research_context(research):
    sections = []

    for index, page in enumerate(research.website_pages, start=1):
        sections.append(
            f"""
FIRST-PARTY SOURCE {index}

URL:
{page.url}

CONTENT:
{page.content[:5000]}
"""
        )

    for index, result in enumerate(research.search_results, start=1):
        sections.append(
            f"""
EXTERNAL SOURCE {index}

TITLE:
{result.title}

URL:
{result.url}

CONTENT:
{result.content[:4000]}
"""
        )

    return "\n".join(sections)


# ============================================================
# ANALYSIS
# ============================================================

def analyze_company(research):

    research_context = build_research_context(research)

    prompt = f"""
You are a business research analyst.

Analyze the company using ONLY the research evidence provided below.

Do not invent facts.

When a fact is uncertain or not supported by the evidence,
state that uncertainty rather than guessing.

Your job is to identify:

1. Company name
2. Industry
3. What the company does
4. Main offer
5. Target audience
6. Problem solved
7. Business model

For every important claim, add supporting evidence.

The evidence source must use the exact URL provided in the research.

RESEARCH EVIDENCE:

{research_context}
"""

    return structured_model.invoke(
        prompt,
        config={
            "callbacks": [langfuse_handler],
            "run_name": "company-profile-analysis",
        },
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    url = "https://www.hubspot.com/"

    research = research_business(
        url=url,
        search_query="HubSpot target audience business model"
    )

    company_profile = analyze_company(research)

    print("\n===== COMPANY PROFILE =====\n")

    print(
        company_profile.model_dump_json(
            indent=2
        )
    )

    langfuse.flush()