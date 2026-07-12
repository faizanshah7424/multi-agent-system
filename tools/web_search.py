import urllib.request
import urllib.parse
import re
from pydantic import BaseModel, Field
from tools.base import BaseTool
from core.logging import get_logger

logger = get_logger("WebSearchTool")


class WebSearchInput(BaseModel):
    query: str = Field(..., description="The query string to search for on the web.")
    max_results: int = Field(
        default=5, description="The maximum number of search results to return."
    )


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Searches the web for up-to-date information on a given topic, "
        "returning titles and snippets from search results."
    )
    args_schema: type[BaseModel] = WebSearchInput

    def execute(self, query: str, max_results: int = 5) -> str:
        logger.info(f"Searching the web for: '{query}'")

        try:
            # DuckDuckGo HTML-only search endpoint
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            # Use a standard browser User-Agent to avoid scraping blocks
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=8.0) as response:
                html_content = response.read().decode("utf-8", errors="ignore")

            # Extract links and snippets via regex to avoid extra package dependencies
            # DDG HTML search results are wrapped in result blocks
            # Look for class="result__a" for title/link and class="result__snippet" for text
            titles_matches = re.findall(
                r'<a class="result__a"[^>]*>(.*?)</a>', html_content, re.DOTALL
            )
            snippets_matches = re.findall(
                r'<a class="result__snippet"[^>]*>(.*?)</a>', html_content, re.DOTALL
            )

            if not titles_matches:
                # If HTML layout changed or scraping is blocked, return a friendly mock search result warning
                logger.warning(
                    "Scraping returned zero search results. Falling back to local index message."
                )
                return (
                    f"Search results for: '{query}'\n"
                    "Note: Web search scraper was blocked or returned no results. "
                    "Please rely on internal knowledge or double check the query syntax."
                )

            results = []
            count = min(len(titles_matches), len(snippets_matches), max_results)

            for i in range(count):
                # Strip HTML tags from titles and snippets
                title = re.sub(r"<[^>]+>", "", titles_matches[i]).strip()
                snippet = re.sub(r"<[^>]+>", "", snippets_matches[i]).strip()

                # Unescape HTML entities
                title = (
                    urllib.parse.unquote(title)
                    .replace("&amp;", "&")
                    .replace("&quot;", '"')
                    .replace("&#x27;", "'")
                )
                snippet = (
                    urllib.parse.unquote(snippet)
                    .replace("&amp;", "&")
                    .replace("&quot;", '"')
                    .replace("&#x27;", "'")
                )

                results.append(
                    f"Result #{i+1}\n" f"Title: {title}\n" f"Summary: {snippet}\n"
                )

            return "\n".join(results)

        except Exception as e:
            logger.error(f"Search request failed: {str(e)}")
            return f"Error: Web search failed to connect or fetch results: {str(e)}"
