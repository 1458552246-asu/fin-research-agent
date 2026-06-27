"""
WSB Market Sentiment Monitor

Fetches and parses sentiment data from sellthenews.org/wsb/daily
"""

import time
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup


@dataclass
class SentimentData:
    """Market sentiment data structure."""
    bullish_percent: float = 50.0
    bearish_percent: float = 50.0
    top_tickers: List[Dict[str, str]] = field(default_factory=list)  # [{"symbol": "GME", "change": "+15%"}]
    hot_topics: List[str] = field(default_factory=list)
    last_updated: str = ""
    source_url: str = "https://sellthenews.org/wsb/daily?truthShowAll=1"
    error: Optional[str] = None


class SentimentMonitor:
    """WSB sentiment monitor with caching."""

    CACHE_TTL_SECONDS = 900  # 15 minutes
    SOURCE_URL = "https://sellthenews.org/wsb/daily?truthShowAll=1"

    def __init__(self):
        self._cache: Optional[SentimentData] = None
        self._cache_time: float = 0

    def get_sentiment(self, force_refresh: bool = False) -> SentimentData:
        """Get current market sentiment with caching."""
        now = time.time()

        # Return cached data if still valid
        if not force_refresh and self._cache and (now - self._cache_time) < self.CACHE_TTL_SECONDS:
            return self._cache

        # Fetch fresh data
        try:
            data = self._fetch_and_parse()
            self._cache = data
            self._cache_time = now
            return data
        except Exception as e:
            # Return error data but keep old cache if available
            error_data = SentimentData(error=str(e))
            if self._cache:
                self._cache.error = f"刷新失败: {str(e)}"
                return self._cache
            return error_data

    def _fetch_and_parse(self) -> SentimentData:
        """Fetch and parse sentiment data from sellthenews.org."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(self.SOURCE_URL, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        data = SentimentData(
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M"),
            source_url=self.SOURCE_URL
        )

        # Parse bullish/bearish percentages
        self._parse_sentiment_ratio(soup, data)

        # Parse top tickers
        self._parse_top_tickers(soup, data)

        # Parse hot topics
        self._parse_hot_topics(soup, data)

        return data

    def _parse_sentiment_ratio(self, soup: BeautifulSoup, data: SentimentData):
        """Parse bullish/bearish sentiment ratio."""
        # Look for sentiment indicators in the page
        # Common patterns: "Bulls: 67%" or "Bullish 67%" or percentage bars

        text = soup.get_text()

        # Try to find bullish percentage
        bull_patterns = [
            r'[Bb]ull(?:ish)?[:\s]+(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*[Bb]ull(?:ish)?',
        ]

        bear_patterns = [
            r'[Bb]ear(?:ish)?[:\s]+(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*[Bb]ear(?:ish)?',
        ]

        for pattern in bull_patterns:
            match = re.search(pattern, text)
            if match:
                data.bullish_percent = float(match.group(1))
                data.bearish_percent = 100 - data.bullish_percent
                return

        for pattern in bear_patterns:
            match = re.search(pattern, text)
            if match:
                data.bearish_percent = float(match.group(1))
                data.bullish_percent = 100 - data.bearish_percent
                return

        # Look for sentiment bars or gauges
        sentiment_elements = soup.find_all(class_=re.compile(r'sentiment|bull|bear', re.I))
        for elem in sentiment_elements:
            style = elem.get('style', '')
            # Try to extract width percentage from style
            width_match = re.search(r'width[:\s]*(\d+(?:\.\d+)?)\s*%', style)
            if width_match:
                if 'bull' in elem.get('class', [''])[0].lower():
                    data.bullish_percent = float(width_match.group(1))
                    data.bearish_percent = 100 - data.bullish_percent
                    return

    def _parse_top_tickers(self, soup: BeautifulSoup, data: SentimentData):
        """Parse top mentioned tickers."""
        tickers = []

        # Look for ticker symbols (usually 1-5 uppercase letters)
        # Common containers: tables, lists, cards

        # Try to find ticker tables or lists
        ticker_containers = soup.find_all(['table', 'ul', 'ol', 'div'],
                                          class_=re.compile(r'ticker|stock|symbol|mention', re.I))

        for container in ticker_containers:
            # Look for ticker symbols
            ticker_pattern = r'\b([A-Z]{1,5})\b'
            cells = container.find_all(['td', 'li', 'span', 'a'])

            for cell in cells[:20]:  # Limit to first 20 elements
                text = cell.get_text(strip=True)
                # Skip if too long (not a ticker)
                if len(text) > 10:
                    continue

                match = re.match(ticker_pattern, text)
                if match:
                    symbol = match.group(1)
                    # Skip common non-tickers
                    if symbol in ['THE', 'AND', 'FOR', 'ARE', 'USD', 'ETF']:
                        continue

                    # Try to find associated change percentage
                    change = ""
                    next_elem = cell.find_next_sibling()
                    if next_elem:
                        change_match = re.search(r'([+-]?\d+(?:\.\d+)?)\s*%', next_elem.get_text())
                        if change_match:
                            change = f"{change_match.group(1)}%"

                    tickers.append({"symbol": symbol, "change": change})

        # If no structured tickers found, try to extract from page text
        if not tickers:
            text = soup.get_text()
            # Find common stock tickers with $ prefix
            dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
            for symbol in dollar_tickers[:10]:
                if symbol not in ['USD', 'ETF']:
                    tickers.append({"symbol": symbol, "change": ""})

        # Remove duplicates while preserving order
        seen = set()
        unique_tickers = []
        for t in tickers:
            if t["symbol"] not in seen:
                seen.add(t["symbol"])
                unique_tickers.append(t)

        data.top_tickers = unique_tickers[:10]  # Top 10

    def _parse_hot_topics(self, soup: BeautifulSoup, data: SentimentData):
        """Parse hot discussion topics."""
        topics = []

        # Look for topic/title elements
        topic_elements = soup.find_all(['h2', 'h3', 'h4', 'a'],
                                       class_=re.compile(r'title|topic|headline|post', re.I))

        for elem in topic_elements[:10]:
            text = elem.get_text(strip=True)
            # Clean up and validate
            if 10 < len(text) < 200:  # Reasonable topic length
                # Remove excessive whitespace
                text = ' '.join(text.split())
                topics.append(text)

        # Also look for post titles in Reddit-style layouts
        if not topics:
            post_titles = soup.find_all(class_=re.compile(r'post.*title|title.*post', re.I))
            for title in post_titles[:10]:
                text = title.get_text(strip=True)
                if 10 < len(text) < 200:
                    text = ' '.join(text.split())
                    topics.append(text)

        data.hot_topics = topics[:5]  # Top 5 topics

    def get_cache_age_minutes(self) -> int:
        """Get cache age in minutes."""
        if not self._cache_time:
            return -1
        return int((time.time() - self._cache_time) / 60)


# Global instance for caching
_monitor = SentimentMonitor()


def get_market_sentiment(force_refresh: bool = False) -> SentimentData:
    """Get current WSB market sentiment (cached)."""
    return _monitor.get_sentiment(force_refresh)


def get_cache_age() -> int:
    """Get cache age in minutes (-1 if no cache)."""
    return _monitor.get_cache_age_minutes()
