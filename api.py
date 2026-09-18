from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from graph import (
    run_business_analysis,
    save_report,
    shutdown_observability,
)


app = FastAPI(
    title="BusinessIntel AI",
    description="AI-powered business research and strategy API",
    version="1.0.0",
)


# Allow the frontend to communicate with the API.
# We can restrict this to the final Vercel domain later.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BusinessRequest(BaseModel):
    website: HttpUrl
    business_goal: str


@app.get("/")
def root():
    return {
        "name": "BusinessIntel AI",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post("/analyze")
def analyze_business(request: BusinessRequest):

    import uuid

    thread_id = f"business-{uuid.uuid4().hex}"

    try:
        result = run_business_analysis(
            website=str(request.website),
            business_goal=request.business_goal,
            thread_id=thread_id,
        )

        report = result.get("final_report")

        if report is None:
            return {
                "success": False,
                "error": "Final report was not generated.",
            }

        report_path = save_report(result)

        return {
            "success": True,
            "company_profile": report.company_profile.model_dump(),
            "business_strategy": report.business_strategy.model_dump(),
            "report_file": str(report_path),
        }

    except Exception as error:

        return {
            "success": False,
            "error_type": type(error).__name__,
            "error": str(error),
        }


@app.on_event("shutdown")
def shutdown():
    shutdown_observability()