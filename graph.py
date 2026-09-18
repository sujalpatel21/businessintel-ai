from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from agent import agent
from strategy import generate_strategy

from validation import (
    validate_company_profile,
    validate_strategy,
)

from report import (
    FinalReport,
    build_final_report,
    validate_final_report,
    save_markdown_report,
)


class BusinessState(TypedDict, total=False):
    website: str
    business_goal: str

    company_profile: object
    strategy: object
    final_report: FinalReport

    validation_passed: bool
    validation_issues: list[str]

    strategy_validation_passed: bool
    strategy_validation_issues: list[str]

    final_report_valid: bool
    final_report_issues: list[str]

    research_attempts: int
    strategy_attempts: int


langfuse = get_client()
langfuse_handler = CallbackHandler()


def research_node(state: BusinessState):

    attempts = state.get(
        "research_attempts",
        0,
    ) + 1

    validation_issues = state.get(
        "validation_issues",
        [],
    )

    retry_context = ""

    if validation_issues:
        retry_context = f"""
Previous research failed validation.

Fix these issues:

{chr(10).join(
    f"- {issue}"
    for issue in validation_issues
)}
"""

    user_request = f"""
Research this company.

Website:
{state["website"]}

Business goal:
{state["business_goal"]}

Use the website crawler for first-party information.

Use web search for external context.

Do not invent facts.

Include supporting evidence.

{retry_context}
"""

    result = agent.invoke(
        {
            "messages": [
                ("user", user_request)
            ]
        }
    )

    return {
        "company_profile": result["structured_response"],
        "research_attempts": attempts,
    }


def validation_node(state: BusinessState):

    passed, issues = validate_company_profile(
        profile=state["company_profile"],
        website=state["website"],
    )

    return {
        "validation_passed": passed,
        "validation_issues": issues,
    }


def route_after_research_validation(
    state: BusinessState,
):

    if state.get(
        "validation_passed",
        False,
    ):
        return "strategy"

    if state.get(
        "research_attempts",
        0,
    ) >= 2:
        return "strategy"

    return "research"


def strategy_node(state: BusinessState):

    attempts = state.get(
        "strategy_attempts",
        0,
    ) + 1

    strategy = generate_strategy(
        company_profile=state["company_profile"],
        validation_issues=state.get(
            "strategy_validation_issues",
            [],
        ),
    )

    return {
        "strategy": strategy,
        "strategy_attempts": attempts,
    }


def strategy_validation_node(
    state: BusinessState,
):

    passed, issues = validate_strategy(
        state["strategy"]
    )

    return {
        "strategy_validation_passed": passed,
        "strategy_validation_issues": issues,
    }


def route_after_strategy_validation(
    state: BusinessState,
):

    if state.get(
        "strategy_validation_passed",
        False,
    ):
        return "final_report"

    if state.get(
        "strategy_attempts",
        0,
    ) >= 2:
        return "final_report"

    return "strategy"


def final_report_node(
    state: BusinessState,
):

    report = build_final_report(
        company_profile=state["company_profile"],
        business_strategy=state["strategy"],
    )

    passed, issues = validate_final_report(
        report
    )

    return {
        "final_report": report,
        "final_report_valid": passed,
        "final_report_issues": issues,
    }


builder = StateGraph(BusinessState)

builder.add_node(
    "research",
    research_node,
)

builder.add_node(
    "validate_research",
    validation_node,
)

builder.add_node(
    "strategy",
    strategy_node,
)

builder.add_node(
    "validate_strategy",
    strategy_validation_node,
)

builder.add_node(
    "final_report",
    final_report_node,
)

builder.add_edge(
    START,
    "research",
)

builder.add_edge(
    "research",
    "validate_research",
)

builder.add_conditional_edges(
    "validate_research",
    route_after_research_validation,
    {
        "research": "research",
        "strategy": "strategy",
    },
)

builder.add_edge(
    "strategy",
    "validate_strategy",
)

builder.add_conditional_edges(
    "validate_strategy",
    route_after_strategy_validation,
    {
        "strategy": "strategy",
        "final_report": "final_report",
    },
)

builder.add_edge(
    "final_report",
    END,
)


checkpointer = InMemorySaver()

graph = builder.compile(
    checkpointer=checkpointer,
)


def run_business_analysis(
    website: str,
    business_goal: str,
    thread_id: str,
):

    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "callbacks": [
            langfuse_handler,
        ],
        "run_name": "business-intel-workflow",
    }

    return graph.invoke(
        {
            "website": website,
            "business_goal": business_goal,
            "research_attempts": 0,
            "strategy_attempts": 0,
        },
        config=config,
    )


def save_report(result):

    if not result.get("final_report"):
        return None

    return save_markdown_report(
        result["final_report"]
    )


def shutdown_observability():

    langfuse.shutdown()