from uuid import uuid4

from graph import (
    run_business_analysis,
    save_report,
    shutdown_observability,
)


def main():

    print()
    print("=" * 60)
    print("                    BUSINESSINTEL AI")
    print("         AI-Powered Business Research & Strategy")
    print("=" * 60)
    print()

    website = input(
        "Business website: "
    ).strip()

    business_goal = input(
        "Business goal: "
    ).strip()

    if not website:
        print("\nWebsite is required.")
        return

    if not business_goal:
        print("\nBusiness goal is required.")
        return

    thread_id = (
        f"business-{uuid4().hex}"
    )

    print()
    print("Starting business research...")
    print()

    try:

        result = run_business_analysis(
            website=website,
            business_goal=business_goal,
            thread_id=thread_id,
        )

        print()
        print("=" * 60)
        print("                     COMPLETE")
        print("=" * 60)
        print()

        print(
            "Research validation:",
            result.get(
                "validation_passed"
            ),
        )

        print(
            "Strategy validation:",
            result.get(
                "strategy_validation_passed"
            ),
        )

        print(
            "Final report validation:",
            result.get(
                "final_report_valid"
            ),
        )

        if result.get("final_report"):

            report = result["final_report"]

            print()
            print(
                "Company:",
                report.company_profile.company_name,
            )

            print(
                "Industry:",
                report.company_profile.industry,
            )

            print(
                "Lead generation opportunities:",
                len(
                    report.business_strategy
                    .lead_generation_opportunities
                ),
            )

            print(
                "Automation opportunities:",
                len(
                    report.business_strategy
                    .automation_opportunities
                ),
            )

            report_path = save_report(
                result
            )

            print()
            print(
                f"Report saved to: {report_path}"
            )

    except Exception as error:

        print()
        print("=" * 60)
        print("                       ERROR")
        print("=" * 60)
        print()

        print(
            f"{type(error).__name__}:"
        )

        print(
            str(error)
        )

    finally:

        shutdown_observability()


if __name__ == "__main__":
    main()