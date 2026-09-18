import requests
from bs4 import BeautifulSoup


class WebsiteResearcher:

    def __init__(self, timeout=20):
        self.timeout = timeout

    def fetch_html(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response.text

    def extract_content(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")

        # Remove elements that usually don't contain useful business information
        for element in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
            "header",
        ]):
            element.decompose()

        title = ""
        if soup.title:
            title = soup.title.get_text(" ", strip=True)

        headings = []

        for heading in soup.find_all(["h1", "h2", "h3"]):
            text = heading.get_text(" ", strip=True)

            if text:
                headings.append(text)

        paragraphs = []

        for paragraph in soup.find_all("p"):
            text = paragraph.get_text(" ", strip=True)

            if text and len(text) > 20:
                paragraphs.append(text)

        return {
            "title": title,
            "headings": headings,
            "paragraphs": paragraphs,
        }

    def research(self, url: str) -> dict:
        html = self.fetch_html(url)

        content = self.extract_content(html)

        return {
            "url": url,
            **content,
        }