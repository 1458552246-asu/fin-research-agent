"""
Tool Abstraction Layer for ReAct Agent.

Defines a standard Tool interface and concrete implementations that wrap
existing capabilities (KB search, web search, sentiment monitoring, document read).
This abstraction enables the ReAct Agent to dynamically select and execute tools.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .kb_client import get_kb_client, is_demo_mode
from .web_search import web_search, WebSearchResult
from .sentiment_monitor import get_market_sentiment, SentimentData


# =============================================================================
# Core Tool Abstractions
# =============================================================================

@dataclass
class ToolResult:
    """Result returned by a tool execution."""
    tool_name: str
    success: bool
    data: Any
    summary: str  # Human-readable summary for the LLM


class BaseTool(ABC):
    """Abstract base class for all tools."""

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        ...


# =============================================================================
# Concrete Tool Implementations
# =============================================================================

class KBSearchTool(BaseTool):
    """Search the knowledge base for financial documents."""

    name = "kb_search"
    description = (
        "Search the knowledge base for financial documents including earnings calls, "
        "expert interviews, research reports, and social media posts. "
        "Use this when you need to find information about a company or topic."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for the knowledge base"
            },
            "source_filter": {
                "type": "string",
                "description": "Optional filter: 'alpha_engine', 'expert_interview', 'social_media', or 'all'",
                "default": "all"
            }
        },
        "required": ["query"]
    }

    def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        source_filter = kwargs.get("source_filter", "all")

        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=[],
                summary="Error: No query provided"
            )

        # Use existing research_team search mechanism
        from .research_team import get_mock_documents, TrackedDocument
        import re

        kb_client = get_kb_client()

        if is_demo_mode() or not kb_client:
            docs = get_mock_documents(query, source_filter)
        else:
            try:
                results = kb_client.list_files(q=query, page_size=10)

                # If full query returns no results, try keyword extraction
                if not results.get("results"):
                    # Extract English words and Chinese keywords
                    english_words = re.findall(r'[A-Za-z]+', query)
                    chinese_keywords = []
                    for term in ['HBM', 'NVIDIA', 'Dell', 'Tesla', 'TSMC', 'KKR',
                                 'Apollo', 'CoWoS', '海力士', '存储', '产能',
                                 '业绩', '收入', '毛利', '增长', '服务器',
                                 '芯片', '资管', '特斯拉', '台积电']:
                        if term.lower() in query.lower():
                            chinese_keywords.append(term)

                    keywords = chinese_keywords + english_words
                    if not keywords:
                        keywords = [query[:3]]

                    # Try each keyword until we find results
                    for kw in keywords:
                        if len(kw) >= 2:
                            results = kb_client.list_files(q=kw, page_size=10)
                            if results.get("results"):
                                break

                docs = []
                for item in results.get("results", []):
                    title = item.get("title") or item.get("file_name", "")
                    file_id = item.get("id", 0)

                    # Fetch full content via get_file
                    content = ""
                    if file_id and kb_client:
                        try:
                            detail = kb_client.get_file(file_id)
                            file_data = detail.get("data", detail)
                            content = file_data.get("content", "")
                        except Exception:
                            pass

                    # Fallback to list-level fields
                    if not content:
                        content = item.get("content") or item.get("preview") or ""

                    # Extract date from tags
                    tags = item.get("tags", {})
                    date = tags.get("date") or item.get("publish_date") or item.get("uploaded_at", "")

                    docs.append(TrackedDocument(
                        file_id=file_id,
                        title=title,
                        source_type=item.get("source", "unknown"),
                        date=date,
                        content=content,
                        url=item.get("preview_url") or item.get("url"),
                        is_mock=False
                    ))
            except Exception as e:
                docs = get_mock_documents(query, source_filter)

        # Build summary
        if docs:
            doc_summaries = []
            for doc in docs[:5]:
                snippet = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                doc_summaries.append(f"- [{doc.source_type}] {doc.title}: {snippet}")
            summary = f"Found {len(docs)} documents:\n" + "\n".join(doc_summaries)
        else:
            summary = f"No documents found for query: '{query}'"

        return ToolResult(
            tool_name=self.name,
            success=len(docs) > 0,
            data=[{
                "file_id": doc.file_id,
                "title": doc.title,
                "source_type": doc.source_type,
                "date": doc.date,
                "content": doc.content,
                "url": doc.url,
                "is_mock": doc.is_mock
            } for doc in docs],
            summary=summary
        )


class WebSearchTool(BaseTool):
    """Search the web for recent financial news and analysis."""

    name = "web_search"
    description = (
        "Search the web for recent news, analysis, and information. "
        "Use this when KB results are insufficient or you need the latest information."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for web search"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 5
            }
        },
        "required": ["query"]
    }

    def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)

        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=[],
                summary="Error: No query provided"
            )

        # In demo mode, return mock web results
        if is_demo_mode():
            mock_results = [
                {
                    "title": f"Latest analysis: {query}",
                    "url": "https://example.com/analysis",
                    "snippet": f"Recent market analysis related to {query} shows mixed signals...",
                    "source": "financial-news.com",
                    "date": "2026-06-27"
                }
            ]
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=mock_results,
                summary=f"Web search for '{query}': Found 1 result (demo mode)"
            )

        results = web_search(query, max_results)
        data = [{
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet,
            "source": r.source,
            "date": r.date
        } for r in results]

        if results:
            summary_lines = [f"Found {len(results)} web results:"]
            for r in results[:3]:
                summary_lines.append(f"- {r.title} ({r.source})")
            summary = "\n".join(summary_lines)
        else:
            summary = f"No web results found for: '{query}'"

        return ToolResult(
            tool_name=self.name,
            success=len(results) > 0,
            data=data,
            summary=summary
        )


class SentimentTool(BaseTool):
    """Get current market sentiment data from WSB/social media."""

    name = "market_sentiment"
    description = (
        "Get current market sentiment data including bullish/bearish ratio, "
        "hot topics, and trending tickers. Use this to understand market mood."
    )
    parameters = {
        "type": "object",
        "properties": {
            "force_refresh": {
                "type": "boolean",
                "description": "Whether to force refresh cached data",
                "default": False
            }
        },
        "required": []
    }

    def execute(self, **kwargs) -> ToolResult:
        force_refresh = kwargs.get("force_refresh", False)

        sentiment = get_market_sentiment(force_refresh)

        data = {
            "bullish_percent": sentiment.bullish_percent,
            "bearish_percent": sentiment.bearish_percent,
            "top_tickers": sentiment.top_tickers,
            "hot_topics": sentiment.hot_topics,
            "last_updated": sentiment.last_updated,
            "error": sentiment.error
        }

        if sentiment.error:
            summary = f"Sentiment data (cached/default): Bullish {sentiment.bullish_percent:.0f}% / Bearish {sentiment.bearish_percent:.0f}%"
        else:
            topics_str = ", ".join(sentiment.hot_topics[:3]) if sentiment.hot_topics else "N/A"
            summary = (
                f"Market Sentiment: Bullish {sentiment.bullish_percent:.0f}% / "
                f"Bearish {sentiment.bearish_percent:.0f}%. "
                f"Hot topics: {topics_str}"
            )

        return ToolResult(
            tool_name=self.name,
            success=True,
            data=data,
            summary=summary
        )


class DocumentReadTool(BaseTool):
    """Read detailed content of a specific document by ID."""

    name = "read_document"
    description = (
        "Read the full content of a specific document from the knowledge base by file ID. "
        "Use this when you need more details about a document found in search results."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_id": {
                "type": "integer",
                "description": "The file ID of the document to read"
            }
        },
        "required": ["file_id"]
    }

    def execute(self, **kwargs) -> ToolResult:
        file_id = kwargs.get("file_id")

        if not file_id:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                summary="Error: No file_id provided"
            )

        # In demo mode, look up from mock data
        if is_demo_mode():
            from mock.mock_data import MOCK_SEARCH_RESULTS
            for category_results in MOCK_SEARCH_RESULTS.values():
                for doc in category_results:
                    if doc.get("file_id") == file_id:
                        return ToolResult(
                            tool_name=self.name,
                            success=True,
                            data=doc,
                            summary=f"Document [{doc['source_type']}] {doc['title']}: {doc['content'][:200]}..."
                        )
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                summary=f"Document with ID {file_id} not found"
            )

        # Real KB read
        kb_client = get_kb_client()
        if not kb_client:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                summary="KB client not available"
            )

        try:
            detail = kb_client.get_file(file_id)
            file_data = detail.get("data", detail)
            content = file_data.get("content", "")
            title = file_data.get("title") or file_data.get("file_name", "Unknown")

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=file_data,
                summary=f"Document '{title}': {content[:300]}..."
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                summary=f"Failed to read document {file_id}: {str(e)}"
            )


# =============================================================================
# Tool Registry
# =============================================================================

def get_all_tools() -> List[BaseTool]:
    """Get all available tools."""
    return [
        KBSearchTool(),
        WebSearchTool(),
        SentimentTool(),
        DocumentReadTool(),
    ]


def get_tool_by_name(name: str) -> Optional[BaseTool]:
    """Get a tool by its name."""
    for tool in get_all_tools():
        if tool.name == name:
            return tool
    return None


def get_tools_description() -> str:
    """Get formatted description of all tools for the LLM prompt."""
    tools = get_all_tools()
    lines = []
    for tool in tools:
        params_desc = ""
        props = tool.parameters.get("properties", {})
        required = tool.parameters.get("required", [])
        for param_name, param_info in props.items():
            req_mark = "*" if param_name in required else ""
            params_desc += f"\n    - {param_name}{req_mark}: {param_info.get('description', '')}"
        lines.append(f"- **{tool.name}**: {tool.description}{params_desc}")
    return "\n".join(lines)
