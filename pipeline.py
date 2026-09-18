from dotenv import load_dotenv

from agent import agent
from strategy import generate_strategy

from langfuse import get_client
from langfuse.langchain import CallbackHandler


load_dotenv()


langfuse = get_client()
langfuse_handler = CallbackHandler()


def run_business_analysis(
    website: str,
    business_goal: str,
):
    """
    Runs the complete Business Stategist pipeline.

    Research Agent
        ↓
    Company Profile
        ↓
    Strategy Engine
        ↓
    Business Strategy
    """

    user_request = f"""
    Research this company:

    Website:
    {website}

    Business goal:
    {business_goal}

    Research the company using the available tools.
    Gather enough evidence to understand the business before
    producing the final structured company profile.
    """

    research_result = agent.invoke(
        {
            "messages": [
                ("user", user_request)
            ]
        },
        config={
            "callbacks": [langfuse_handler],
            "run_name": "business-research-agent",
        },
    )

    company_profile = research_result["structured_response"]

    strategy = generate_strategy(
        company_profile
    )

    return {
        "company_profile": company_profile,
        "strategy": strategy,
    }


if __name__ == "__main__":

    result = run_business_analysis(
        website="https://www.hubspot.com/",
        business_goal=(
            "Understand the business and identify "
            "lead generation and automation opportunities."
        ),
    )

    print("\n===== COMPANY PROFILE =====\n")

    print(
        result["company_profile"].model_dump_json(
            indent=2
        )
    )

    print("\n===== BUSINESS STRATEGY =====\n")

    print(
        result["strategy"].model_dump_json(
            indent=2
        )
    )

    langfuse.flush()