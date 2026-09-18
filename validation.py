from urllib.parse import urlparse

from agent import CompanyProfile
from strategy import BusinessStrategy


REQUIRED_COMPANY_FIELDS = [
    "company_name",
    "industry",
    "description",
    "offer",
    "target_audience",
    "problem_solved",
    "business_model",
]


def normalize_domain(url: str) -> str:
    parsed = urlparse(url)

    return (
        parsed.netloc
        .lower()
        .replace("www.", "")
        .split(":")[0]
    )


# ============================================================
# RESEARCH VALIDATION
# ============================================================

def validate_company_profile(
    profile: CompanyProfile,
    website: str,
) -> tuple[bool, list[str]]:

    issues = []

    for field in REQUIRED_COMPANY_FIELDS:

        value = getattr(
            profile,
            field,
            None,
        )

        if not value or not str(value).strip():
            issues.append(
                f"Missing required field: {field}"
            )

    if len(profile.evidence) < 3:
        issues.append(
            f"Only {len(profile.evidence)} evidence items found. "
            "At least 3 are required."
        )

    website_domain = normalize_domain(website)

    has_first_party_source = False
    has_external_source = False

    for index, evidence in enumerate(
        profile.evidence,
        start=1,
    ):

        if not evidence.source_url:
            issues.append(
                f"Evidence item {index} has no source URL."
            )
            continue

        parsed = urlparse(
            evidence.source_url
        )

        if not parsed.scheme or not parsed.netloc:
            issues.append(
                f"Evidence item {index} has an invalid source URL."
            )
            continue

        evidence_domain = normalize_domain(
            evidence.source_url
        )

        if evidence_domain == website_domain:
            has_first_party_source = True
        else:
            has_external_source = True

    if not has_first_party_source:
        issues.append(
            "No first-party source was included."
        )

    if not has_external_source:
        issues.append(
            "No external source was included."
        )

    return len(issues) == 0, issues


# ============================================================
# STRATEGY VALIDATION
# ============================================================

def validate_strategy(
    strategy: BusinessStrategy,
) -> tuple[bool, list[str]]:

    issues = []

    if not strategy.marketing_observations:
        issues.append(
            "No marketing observations were generated."
        )

    if not strategy.lead_generation_opportunities:
        issues.append(
            "No lead generation opportunities were generated."
        )

    if not strategy.automation_opportunities:
        issues.append(
            "No automation opportunities were generated."
        )

    if not strategy.recommended_actions:
        issues.append(
            "No recommended actions were generated."
        )

    for index, item in enumerate(
        strategy.lead_generation_opportunities,
        start=1,
    ):

        if not item.supporting_evidence:
            issues.append(
                f"Lead generation opportunity {index} "
                "has no supporting evidence."
            )

    for index, item in enumerate(
        strategy.automation_opportunities,
        start=1,
    ):

        if not item.supporting_evidence:
            issues.append(
                f"Automation opportunity {index} "
                "has no supporting evidence."
            )

    return len(issues) == 0, issues