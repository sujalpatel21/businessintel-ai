from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_tavily import TavilyCrawl, TavilySearch
from langfuse import get_client
from langfuse.langchain import CallbackHandler


load_dotenv()


# ============================================================
# DATA MODELS
# ============================================================

class WebsitePage(BaseModel):
    url: str
    content: str


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: float | None = None


class ResearchBundle(BaseModel):
    base_url: str
    website_pages: list[WebsitePage] = Field(default_factory=list)
    search_results: list[SearchResult] = Field(default_factory=list)


# ============================================================
# OBSERVABILITY
# ============================================================

langfuse = get_client()
langfuse_handler = CallbackHandler()


# ============================================================
# TAVILY
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
# RAW RESEARCH
# ============================================================

def crawl_website(url: str):
    return website_crawler.invoke(
        {"url": url},
        config={
            "callbacks": [langfuse_handler],
            "run_name": "tavily-website-crawl",
        },
    )


def search_web(query: str):
    return web_search.invoke(
        {"query": query},
        config={
            "callbacks": [langfuse_handler],
            "run_name": "tavily-web-search",
        },
    )


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_research(
    base_url: str,
    crawl_result: dict,
    search_result: dict,
) -> ResearchBundle:

    website_pages = []

    for page in crawl_result.get("results", []):
        content = page.get("raw_content", "")

        if content:
            website_pages.append(
                WebsitePage(
                    url=page.get("url", ""),
                    content=content,
                )
            )

    search_results = []

    for result in search_result.get("results", []):
        content = result.get("raw_content") or result.get("content", "")

        search_results.append(
            SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                content=content,
                score=result.get("score"),
            )
        )

    return ResearchBundle(
        base_url=base_url,
        website_pages=website_pages,
        search_results=search_results,
    )


# ============================================================
# RESEARCH PIPELINE
# ============================================================

def research_business(url: str, search_query: str) -> ResearchBundle:

    crawl_result = crawl_website(url)

    search_result = search_web(search_query)

    return normalize_research(
        base_url=url,
        crawl_result=crawl_result,
        search_result=search_result,
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

    print("\n===== RESEARCH SUMMARY =====\n")

    print("Base URL:", research.base_url)

    print(
        "Website pages:",
        len(research.website_pages)
    )

    print(
        "Search results:",
        len(research.search_results)
    )

    print("\n--- Website Sources ---")

    for page in research.website_pages:
        print(page.url)

    print("\n--- External Sources ---")

    for result in research.search_results:
        print(result.title)
        print(result.url)

    langfuse.flush()