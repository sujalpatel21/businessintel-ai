# BusinessIntel AI Architecture

## 1. System Overview

BusinessIntel AI is a web application that converts a company website and a business goal into a structured, evidence-backed business strategy.

The production system is split into two deployable services:

```text
┌───────────────────────────────────────┐
│              Vercel                   │
│         React + Vite Frontend         │
└───────────────────┬───────────────────┘
                    │
                    │ POST /analyze
                    ▼
┌───────────────────────────────────────┐
│              Render                   │
│          FastAPI Backend              │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│           LangGraph Workflow          │
│                                       │
│ Research → Validation → Strategy →    │
│ Validation → Final Report             │
└───────────────┬───────────┬───────────┘
                │           │
                ▼           ▼
        Tavily Research   Gemini
                │
                ▼
        Langfuse Tracing
```

## 2. Request Lifecycle

A user submits:

```json
{
  "website": "https://company.com",
  "business_goal": "Find opportunities to improve lead generation."
}
```

The request flows through the following stages.

### Stage 1 — Frontend

The React application collects:

- Company website
- Business goal

The frontend sends a JSON `POST /analyze` request to the deployed FastAPI service.

Production frontend:

```text
https://frontend-pink-omega-62.vercel.app
```

### Stage 2 — FastAPI

The backend validates the incoming request with Pydantic:

```python
class BusinessRequest(BaseModel):
    website: HttpUrl
    business_goal: str
```

FastAPI then creates a unique workflow thread ID and starts the LangGraph workflow.

Backend:

```text
https://businessintel-ai.onrender.com
```

## 3. LangGraph State

The workflow uses a typed state object containing the major artifacts produced during execution.

Core state:

```text
website
business_goal
company_profile
strategy
final_report
validation_passed
validation_issues
strategy_validation_passed
strategy_validation_issues
final_report_valid
final_report_issues
research_attempts
strategy_attempts
```

This allows each node to operate on the outputs of previous nodes without tightly coupling the implementation.

## 4. Research Node

The research node asks the agent to investigate the target company.

Research instructions include:

- Use the website crawler for first-party information.
- Use web search for external context.
- Do not invent facts.
- Include supporting evidence.

The agent uses:

- Google Gemini
- Tavily crawl
- Tavily web search
- Structured Pydantic output

The output is a `CompanyProfile`.

## 5. Company Profile

The structured company profile contains:

```text
company_name
industry
description
offer
target_audience
problem_solved
business_model
evidence[]
```

Each evidence item contains:

```text
source_title
source_url
claim
```

This makes the research data directly usable by later workflow stages and the frontend.

## 6. Research Validation

The research validation node checks the company profile.

It verifies:

- Required company fields are present.
- At least three evidence items exist.
- Evidence URLs are valid.
- At least one source is first-party.
- At least one source is external.

Routing:

```text
                    ┌──────────────┐
                    │   Research   │
                    └──────┬───────┘
                           ▼
                  ┌──────────────────┐
                  │ Research         │
                  │ Validation       │
                  └───────┬──────────┘
                     pass │ fail
                          /                          /                           ▼     ▼
                   Strategy  Research
                              retry
```

The workflow allows a limited retry rather than adding an unlimited loop.

## 7. Strategy Generation

The strategy stage takes the structured company profile and generates a business strategy.

The output contains:

### Marketing observations

Business observations and their implications.

### Lead generation opportunities

Potential opportunities with rationale, suggested approach, and supporting evidence.

### Automation opportunities

Business processes that could benefit from automation, plus expected benefits and supporting evidence.

### Recommended actions

Concrete actions, reasons, and expected outcomes.

## 8. Strategy Validation

The strategy validation node checks that:

- All strategy sections are populated.
- Lead-generation opportunities include supporting evidence.
- Automation opportunities include supporting evidence.

Routing follows the same limited-retry pattern used by research validation.

## 9. Final Report

The final report combines:

```text
CompanyProfile
        +
BusinessStrategy
        =
FinalReport
```

The report renderer produces Markdown containing:

1. Company Overview
2. Offer
3. Target Audience
4. Problem Solved
5. Business Model
6. Marketing Observations
7. Lead Generation Opportunities
8. Automation Opportunities
9. Recommended Actions
10. Sources & Evidence

The cloud API returns the rendered Markdown directly in the JSON response.

## 10. API Contract

### GET /

Returns basic service information.

### GET /health

Used as a lightweight health check.

Response:

```json
{
  "status": "healthy"
}
```

### POST /analyze

Request:

```json
{
  "website": "https://www.hubspot.com/",
  "business_goal": "Analyze the business model and identify opportunities to improve lead generation and automation."
}
```

Response shape:

```json
{
  "success": true,
  "company_profile": {},
  "business_strategy": {},
  "report_markdown": "..."
}
```

## 11. Observability

Langfuse is connected to the LangGraph invocation as a callback handler.

The workflow also includes lightweight model middleware hooks:

- `before_model`
- `after_model`

These hooks currently provide runtime visibility into model execution.

## 12. Deployment Architecture

### Frontend

```text
GitHub
  ↓
Vercel
  ↓
React + Vite
```

### Backend

```text
GitHub
  ↓
Render
  ↓
Docker
  ↓
Uvicorn
  ↓
FastAPI
```

### Backend container

The Docker image:

1. Uses Python as the base image.
2. Copies uv into the image.
3. Installs dependencies with `uv sync --locked`.
4. Copies the application source.
5. Exposes port `10000`.
6. Starts Uvicorn on `0.0.0.0:10000`.

## 13. Security Boundaries

The backend owns all sensitive API credentials.

The frontend only receives the public API URL through:

```text
VITE_API_URL
```

Backend credentials such as:

```text
GOOGLE_API_KEY
TAVILY_API_KEY
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY
```

remain server-side.

CORS is restricted to the production frontend domain and local development origin.

## 14. Reliability Decisions

The application deliberately uses a small number of explicit reliability mechanisms rather than a large middleware stack.

Current protections include:

- Pydantic request validation
- Structured model outputs
- Research validation
- Strategy validation
- Limited workflow retries
- Final report validation
- Health endpoint
- Langfuse tracing
- API-level exception handling

## 15. Deliberate Non-Goals

The current version intentionally does not include:

- RAG
- Vector database
- Persistent analysis history
- User authentication
- Background job queues
- Multi-tenant authorization
- Complex retry middleware

These can be added as separate engineering stages after the core system is stable.

## 16. Production Data Flow

End-to-end:

```text
User
  │
  ▼
Vercel React UI
  │
  │ HTTPS POST /analyze
  ▼
Render FastAPI
  │
  ▼
LangGraph
  │
  ├── Research Agent
  │      ├── Tavily Crawl
  │      └── Tavily Search
  │
  ├── Research Validation
  │
  ├── Strategy Generation
  │      └── Gemini
  │
  ├── Strategy Validation
  │
  └── Final Report
  │
  ▼
JSON + Markdown
  │
  ▼
Vercel UI
```

## 17. Main Components

| Component | Responsibility |
| --- | --- |
| `frontend/src/App.jsx` | User interface, API calls, report rendering, report download |
| `api.py` | HTTP API and CORS |
| `graph.py` | LangGraph workflow and state transitions |
| `agent.py` | Research agent, tools, structured company profile |
| `strategy.py` | Business strategy generation |
| `validation.py` | Research and strategy validation |
| `report.py` | Final report model, validation, Markdown rendering |
| `research.py` | Tavily research utilities |
| `Dockerfile` | Backend container build |
| `pyproject.toml` | Python project metadata and dependencies |

## 18. Engineering Goal

BusinessIntel AI is designed as a focused Agentic AI application rather than a collection of disconnected demonstrations.

The architecture emphasizes:

- Clear state transitions
- Tool-using agents
- Structured outputs
- Evidence validation
- Explicit workflow control
- Observable model execution
- API-first backend design
- Containerized deployment
- Separate frontend and backend services
