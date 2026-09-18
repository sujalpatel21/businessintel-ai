from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.agents.middleware import (
    before_model,
    after_model,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilyCrawl, TavilySearch

from langfuse import get_client
from langfuse.langchain import CallbackHandler


load_dotenv()


# ============================================================
# OUTPUT SCHEMA
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

    evidence: list[Evidence] = Field(
        description=(
            "Important claims and supporting sources. "
            "Include at least one first-party and one external source."
        )
    )


# ============================================================
# MODEL
# ============================================================

model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)


# ============================================================
# TOOLS
# ============================================================

website_crawler = TavilyCrawl(
    max_depth=1,
    max_breadth=10,
    limit=10,
    extract_depth="basic",
    format="markdown",
    allow_external=False,
)

web_search = TavilySearch(
    max_results=5,
    topic="general",
    search_depth="advanced",
    include_raw_content=True,
)


# ============================================================
# MIDDLEWARE
# ============================================================

@before_model
def research_context(state, runtime):

    messages = state.get(
        "messages",
        [],
    )

    print(
        f"[before_model] "
        f"{len(messages)} messages in agent state"
    )

    return None


@after_model
def inspect_model_response(state, runtime):

    messages = state.get(
        "messages",
        [],
    )

    if messages:

        latest_message = messages[-1]

        print(
            "[after_model] "
            f"Model returned: "
            f"{type(latest_message).__name__}"
        )

    return None


# ============================================================
# AGENT
# ============================================================

system_prompt = """
You are a business research agent.

Research the company before producing the final profile.

Use:

1. Website crawler
   - First-party company information.

2. Web search
   - External company and market information.

Rules:

- Do not invent facts.
- Include at least one first-party source.
- Include at least one external source.
- Use exact source URLs.
- Evidence must support the associated claim.
"""


agent = create_agent(
    model=model,
    tools=[
        website_crawler,
        web_search,
    ],
    system_prompt=system_prompt,
    response_format=CompanyProfile,
    middleware=[
        research_context,
        inspect_model_response,
    ],
)


# ============================================================
# LANGFUSE
# ============================================================

langfuse = get_client()
langfuse_handler = CallbackHandler()