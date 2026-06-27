"""Source tracer - generates human-readable source citations with KB preview URLs.

Based on aichat-kb-search/runtime/source_tracer.py
Provides document source tracking and preview URL generation for KB documents.
"""

from typing import Dict, List
from .config import KB_ID_TO_NAME

# KB API base URL for preview links (same as aichat-kb-search)
KB_PREVIEW_BASE = "http://3.128.243.191:8001"


def get_preview_url(file_id: int) -> str:
    """Generate KB preview URL for a file."""
    if not file_id:
        return ""
    return f"{KB_PREVIEW_BASE}/files/preview/{file_id}/"


class SourceTracer:
    """Traces document sources and generates formatted citations."""

    def format_source(self, source: Dict) -> Dict:
        """Format a single source into a citation-ready dict.

        Args:
            source: Raw source dict with file_id, title, content, etc.

        Returns:
            Formatted dict with description, snippet, url, etc.
        """
        file_id = source.get("file_id", "")
        title = source.get("title", source.get("file_name", "未知标题"))
        source_type = source.get("source_type", "")
        date = source.get("date", source.get("uploaded_at", ""))
        author = source.get("author", "")
        snippet = source.get("snippet", source.get("content", ""))[:200]
        is_mock = source.get("is_mock", False)

        # Build description based on source type
        if source_type == "Twitter推文" or "twitter" in source_type.lower():
            description = f"@{author} · {date}"
        elif source_type in ("专家访谈", "久谦中台"):
            description = f"专家访谈 · {author} · {date}《{title}》"
        elif source_type.lower() in ("alphaengine", "alpha", "研报"):
            description = f"AlphaEngine · {author} · {date}《{title}》"
        elif source_type == "AceCampTech":
            description = f"AceCampTech · {author} · {date}《{title}》"
        elif "substack" in source_type.lower():
            description = f"Substack · {author} · {date}《{title}》"
        elif source_type == "联网搜索":
            # Web search results
            description = f"🌐 {author} · {date}《{title}》" if date else f"🌐 {author}《{title}》"
        else:
            description = f"{source_type} · {date}《{title}》"

        # Build preview URL - use real KB URL for non-mock data
        if file_id and not is_mock:
            url = get_preview_url(file_id)
        elif source.get("url"):
            url = source.get("url")
        else:
            url = ""

        return {
            "description": description,
            "title": title,
            "snippet": snippet if len(snippet) < 200 else snippet[:197] + "...",
            "source_type": source_type,
            "date": date,
            "file_id": file_id,
            "url": url,
            "is_web_source": source_type == "联网搜索",
            "is_mock": is_mock,
        }

    def format_sources(self, sources: List[Dict]) -> List[Dict]:
        """Format multiple sources."""
        seen_ids = set()
        formatted = []

        for src in sources:
            file_id = src.get("file_id", id(src))  # Use object id if no file_id
            if file_id in seen_ids:
                continue
            seen_ids.add(file_id)
            formatted.append(self.format_source(src))

        return formatted

    def group_by_type(self, sources: List[Dict]) -> Dict[str, List[Dict]]:
        """Group formatted sources by source type."""
        groups = {}
        for src in sources:
            source_type = src.get("source_type", "其他")
            if source_type not in groups:
                groups[source_type] = []
            groups[source_type].append(src)
        return groups

    def separate_kb_and_web_sources(self, sources: List[Dict]) -> tuple:
        """Separate KB sources and web search sources.

        Returns:
            Tuple of (kb_sources, web_sources)
        """
        kb_sources = []
        web_sources = []

        for src in sources:
            if src.get("is_web_source") or src.get("source_type") == "联网搜索":
                web_sources.append(src)
            else:
                kb_sources.append(src)

        return kb_sources, web_sources
