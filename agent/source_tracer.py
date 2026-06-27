"""Source tracer - generates human-readable source citations."""

from typing import Dict, List
from .config import KB_ID_TO_NAME


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

        # Build description based on source type
        if source_type == "Twitter推文":
            description = f"@{author} · {date}"
        elif source_type in ("久谦中台", "专家访谈"):
            description = f"久谦中台 · 专家访谈 · {date}《{title}》"
        elif source_type in ("AlphaEngine", "研报"):
            description = f"AlphaEngine · {author} · {date}《{title}》"
        elif source_type == "AceCampTech":
            description = f"AceCampTech · {author} · {date}《{title}》"
        elif source_type == "Substack":
            description = f"Substack · {author} · {date}《{title}》"
        else:
            description = f"{source_type} · {date}《{title}》"

        # Build preview URL (demo mode uses placeholder)
        if file_id:
            url = f"#preview-{file_id}"  # In production: actual preview URL
        else:
            url = source.get("url", "#")

        return {
            "description": description,
            "title": title,
            "snippet": snippet if len(snippet) < 200 else snippet[:197] + "...",
            "source_type": source_type,
            "date": date,
            "file_id": file_id,
            "url": url,
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
