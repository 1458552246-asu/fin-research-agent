"""
Web Search Module

Provides fallback web search when KB results are insufficient.
Uses DuckDuckGo search (no API key required).
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup


@dataclass
class WebSearchResult:
    """A single web search result."""
    title: str
    url: str
    snippet: str
    source: str  # Domain name
    date: str = ""
    source_type: str = "联网搜索"


class WebSearcher:
    """Web search with DuckDuckGo HTML scraping."""

    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

    def search(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """Search the web for the given query."""
        try:
            response = self.session.post(
                self.SEARCH_URL,
                data={"q": query, "b": ""},
                timeout=10
            )
            response.raise_for_status()
            return self._parse_results(response.text, max_results)
        except Exception as e:
            print(f"Web search error: {e}")
            return []

    def _parse_results(self, html: str, max_results: int) -> List[WebSearchResult]:
        """Parse DuckDuckGo HTML results."""
        soup = BeautifulSoup(html, "lxml")
        results = []

        # DuckDuckGo result structure
        for result in soup.find_all("div", class_="result"):
            if len(results) >= max_results:
                break

            # Title and URL
            title_elem = result.find("a", class_="result__a")
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")

            # Clean up DuckDuckGo redirect URL
            if "uddg=" in url:
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                url = parsed.get("uddg", [url])[0]

            # Snippet
            snippet_elem = result.find("a", class_="result__snippet")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            # Extract domain
            source = self._extract_domain(url)

            # Try to extract date from snippet
            date = self._extract_date(snippet)

            results.append(WebSearchResult(
                title=title,
                url=url,
                snippet=snippet[:300] if snippet else "",
                source=source,
                date=date,
                source_type="联网搜索"
            ))

        return results

    def _extract_domain(self, url: str) -> str:
        """Extract readable domain name from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www.
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except:
            return "网络来源"

    def _extract_date(self, text: str) -> str:
        """Try to extract date from text."""
        # Common date patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # 2025-06-27
            r'(\d{4}/\d{2}/\d{2})',  # 2025/06/27
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})',  # Jun 27, 2025
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # 27 Jun 2025
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""


# Global instance
_searcher = WebSearcher()


def web_search(query: str, max_results: int = 5) -> List[WebSearchResult]:
    """
    Perform web search as fallback for KB.

    Args:
        query: Search query
        max_results: Maximum number of results to return

    Returns:
        List of WebSearchResult objects
    """
    return _searcher.search(query, max_results)


def should_trigger_web_search(kb_results: list, threshold: int = 2) -> bool:
    """
    Determine if web search should be triggered.

    Args:
        kb_results: Results from KB search
        threshold: Minimum KB results required to skip web search

    Returns:
        True if web search should be triggered
    """
    return len(kb_results) < threshold


def format_web_sources(results: List[WebSearchResult]) -> List[dict]:
    """
    Format web search results for source display.

    Returns list compatible with source_tracer format.
    """
    formatted = []
    for r in results:
        formatted.append({
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet,
            "source_type": "联网搜索",
            "description": f"{r.source} · {r.date}《{r.title}》" if r.date else f"{r.source}《{r.title}》",
            "file_id": None,  # No file_id for web results
            "author": r.source,
            "date": r.date
        })
    return formatted
