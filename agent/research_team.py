"""
Research Team - Phase 1 of Multi-Agent Workflow

Implements parallel research from multiple data sources:
- FundamentalAnalyst: AlphaEngine (业绩会纪要, 研报)
- IndustryAnalyst: Expert interviews (专家访谈)
- SentimentAnalyst: Social media (Twitter, Substack)
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import (
    ResearchReport, SourceGroup, KeyFact, DataPoint,
    SourceReference, Sentiment, DataConflict, TimelineEvent
)
from .prompts import (
    FUNDAMENTAL_ANALYST_PROMPT,
    INDUSTRY_ANALYST_PROMPT,
    SENTIMENT_ANALYST_PROMPT,
    format_documents_for_prompt
)
from .kb_client import get_kb_client, is_demo_mode


# =============================================================================
# TrackedDocument - Document with source tracking
# =============================================================================

@dataclass
class TrackedDocument:
    """A document with full source tracking for attribution."""
    file_id: int
    title: str
    source_type: str
    date: str
    content: str
    url: Optional[str] = None
    author: Optional[str] = None
    is_mock: bool = False  # 标记是否为模拟数据

    def to_source_reference(self) -> SourceReference:
        """Convert to SourceReference for use in reports."""
        return SourceReference(
            source_type=self.source_type,
            title=self.title,
            date=self.date,
            url=self.url,
            file_id=self.file_id if not self.is_mock else None,  # mock数据不传file_id
            preview=self.content[:200] if self.content else None
        )


# =============================================================================
# Mock Data for Demo Mode
# =============================================================================

def get_mock_documents(query: str, source_type: str) -> List[TrackedDocument]:
    """Get mock documents for demo mode based on query and source type.

    Uses centralized mock data from mock/mock_data.py for comprehensive coverage.
    """
    # 延迟导入以避免循环导入
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mock.mock_data import get_mock_search_results

    # 使用集中化的 mock 数据
    mock_results = get_mock_search_results(query)

    if not mock_results:
        return []

    documents = []

    for item in mock_results:
        item_source = item.get("source_type", "").lower()

        # 如果 source_type 是 "all"，包含所有文档
        should_include = (source_type == "all")

        # 否则根据 source_type 匹配数据
        if not should_include:
            if source_type == "alpha_engine":
                should_include = any(s in item_source for s in ["alphaengine", "alpha", "业绩", "研报", "acecamptech"])
            elif source_type == "expert_interview":
                should_include = "专家访谈" in item_source or "expert" in item_source.lower()
            elif source_type == "social_media":
                should_include = any(s in item_source for s in ["twitter", "推文", "substack"])

        if should_include:
            documents.append(TrackedDocument(
                file_id=item.get("file_id", 0),
                title=item.get("title", ""),
                source_type=item.get("source_type", source_type),
                date=item.get("date", ""),
                content=item.get("content", ""),
                url=item.get("url"),
                author=item.get("author"),
                is_mock=True
            ))

    return documents


# =============================================================================
# Research Analysts
# =============================================================================

class BaseAnalyst:
    """Base class for research analysts."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.kb_client = get_kb_client()

    def search_documents(self, query: str, source_type: str) -> List[TrackedDocument]:
        """Search for relevant documents."""
        if is_demo_mode() or not self.kb_client:
            return get_mock_documents(query, source_type)

        # Real KB search implementation
        try:
            # 不传 source 过滤，让 KB 返回所有匹配的文档
            # KB 的 source 字段值（如 "Substack-fomosoc", "AceCampTech"）与我们的分类不同
            results = self.kb_client.list_files(q=query, page_size=10)
            docs = []
            for item in results.get("results", []):
                # KB 返回的字段可能是 file_name 而不是 title
                title = item.get("title") or item.get("file_name", "")
                # 获取文档内容 - 可能需要额外请求
                content = item.get("content") or item.get("preview") or ""

                docs.append(TrackedDocument(
                    file_id=item.get("id", 0),
                    title=title,
                    source_type=item.get("source", source_type),
                    date=item.get("publish_date") or item.get("uploaded_at", ""),
                    content=content,
                    url=item.get("preview_url") or item.get("url"),
                    is_mock=False  # Real KB data
                ))
            return docs
        except Exception as e:
            print(f"KB search failed: {e}, falling back to mock data")
            return get_mock_documents(query, source_type)


class FundamentalAnalyst(BaseAnalyst):
    """Analyzes AlphaEngine data (earnings calls, research reports)."""

    def analyze(self, query: str) -> Dict[str, Any]:
        """Run fundamental analysis."""
        documents = self.search_documents(query, "alpha_engine")

        return {
            "analyst_type": "fundamental",
            "source_name": "AlphaEngine · 基本面数据",
            "documents": documents,
            "findings": [doc.content for doc in documents],
            "raw_documents": [
                {
                    "file_id": doc.file_id,
                    "title": doc.title,
                    "source_type": doc.source_type,
                    "date": doc.date,
                    "content": doc.content,
                    "url": doc.url,
                    "is_mock": doc.is_mock
                }
                for doc in documents
            ]
        }


class IndustryAnalyst(BaseAnalyst):
    """Analyzes expert interviews and industry research."""

    def analyze(self, query: str) -> Dict[str, Any]:
        """Run industry analysis."""
        documents = self.search_documents(query, "expert_interview")

        return {
            "analyst_type": "industry",
            "source_name": "专家访谈 · 产业链洞察",
            "documents": documents,
            "findings": [doc.content for doc in documents],
            "raw_documents": [
                {
                    "file_id": doc.file_id,
                    "title": doc.title,
                    "source_type": doc.source_type,
                    "date": doc.date,
                    "content": doc.content,
                    "url": doc.url,
                    "author": doc.author,
                    "is_mock": doc.is_mock
                }
                for doc in documents
            ]
        }


class SentimentAnalyst(BaseAnalyst):
    """Analyzes social media sentiment (Twitter, Substack)."""

    def analyze(self, query: str) -> Dict[str, Any]:
        """Run sentiment analysis."""
        documents = self.search_documents(query, "social_media")

        return {
            "analyst_type": "sentiment",
            "source_name": "社交媒体 · 市场情绪",
            "documents": documents,
            "findings": [doc.content for doc in documents],
            "raw_documents": [
                {
                    "file_id": doc.file_id,
                    "title": doc.title,
                    "source_type": doc.source_type,
                    "date": doc.date,
                    "content": doc.content,
                    "url": doc.url,
                    "author": doc.author,
                    "is_mock": doc.is_mock
                }
                for doc in documents
            ]
        }


# =============================================================================
# Research Team Coordinator
# =============================================================================

class ResearchTeam:
    """Coordinates multiple research analysts to produce a comprehensive report."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.kb_client = get_kb_client()

    def research(self, query: str, progress_callback=None) -> ResearchReport:
        """
        Execute research by searching KB and grouping by source.

        Args:
            query: User's research question
            progress_callback: Optional callback for progress updates

        Returns:
            ResearchReport with consolidated findings
        """
        if progress_callback:
            progress_callback("research", "searching")

        # 统一搜索一次，获取所有相关文档
        documents = self._search_all(query)

        if progress_callback:
            progress_callback("research", f"found {len(documents)} documents")

        # 按 source 分组
        source_groups = self._group_by_source(documents)

        if progress_callback:
            progress_callback("research", "completed")

        # Build research report
        return self._build_report(query, source_groups, len(documents))

    def _search_all(self, query: str) -> List[TrackedDocument]:
        """Search KB for all relevant documents."""
        if is_demo_mode() or not self.kb_client:
            # Demo mode - 使用 mock 数据
            return get_mock_documents(query, "all")

        try:
            # 提取关键词进行搜索 - 长查询可能返回 0 结果
            # 尝试用原始查询，如果没结果就提取关键词
            results = self.kb_client.list_files(q=query, page_size=20)

            if not results.get("results"):
                # 提取关键词 - 对于中文，尝试常见的金融/技术术语
                import re
                # 提取英文单词和中文词组
                english_words = re.findall(r'[A-Za-z]+', query)
                # 中文分词：简单策略，按常见词切分
                chinese_keywords = []
                for term in ['产能', '扩张', '业绩', '收入', '毛利', '增长', '下降', '风险']:
                    if term in query:
                        chinese_keywords.append(term)

                keywords = english_words + chinese_keywords
                if not keywords:
                    # 最后兜底：取前3个字符
                    keywords = [query[:3]]

                # 用关键词搜索
                for kw in keywords:
                    if len(kw) >= 2:
                        results = self.kb_client.list_files(q=kw, page_size=20)
                        if results.get("results"):
                            print(f"Search with keyword '{kw}' found {len(results.get('results', []))} results")
                            break

            docs = []
            for item in results.get("results", []):
                title = item.get("title") or item.get("file_name", "")
                file_id = item.get("id", 0)

                # 获取文档详情以获取完整内容
                content = ""
                if file_id and self.kb_client:
                    try:
                        detail = self.kb_client.get_file(file_id)
                        file_data = detail.get("data", detail)
                        content = file_data.get("content", "")
                    except Exception as e:
                        print(f"Failed to get file {file_id} content: {e}")

                # 如果获取详情失败，使用 list 返回的字段
                if not content:
                    content = item.get("content") or item.get("preview") or ""

                # 从 tags 中提取日期
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
            return docs
        except Exception as e:
            print(f"KB search failed: {e}, falling back to mock data")
            return get_mock_documents(query, "all")

    def _group_by_source(self, documents: List[TrackedDocument]) -> Dict[str, List[TrackedDocument]]:
        """Group documents by source type."""
        groups = {}
        for doc in documents:
            source = doc.source_type or "other"
            if source not in groups:
                groups[source] = []
            groups[source].append(doc)
        return groups

    def _build_report(self, query: str, source_groups: Dict[str, List[TrackedDocument]], total_docs: int) -> ResearchReport:
        """Build consolidated research report from grouped documents."""
        sources = []

        for source_type, docs in source_groups.items():
            raw_docs = [
                {
                    "file_id": doc.file_id,
                    "title": doc.title,
                    "source_type": doc.source_type,
                    "date": doc.date,
                    "content": doc.content,
                    "url": doc.url,
                    "is_mock": doc.is_mock
                }
                for doc in docs
            ]

            source_group = SourceGroup(
                source_type=source_type,
                source_name=source_type,
                date=docs[0].date if docs else None,
                findings=[doc.content for doc in docs],
                raw_documents=raw_docs
            )
            sources.append(source_group)

        # Extract key facts
        key_facts = []
        for source in sources:
            for finding in source.findings[:3]:
                sentiment = Sentiment.NEUTRAL
                if any(word in finding.lower() for word in ["增长", "上升", "强劲", "超预期", "bullish"]):
                    sentiment = Sentiment.POSITIVE
                elif any(word in finding.lower() for word in ["下降", "风险", "下滑", "压力", "bearish"]):
                    sentiment = Sentiment.NEGATIVE

                key_facts.append(KeyFact(
                    content=finding[:200] + "..." if len(finding) > 200 else finding,
                    sentiment=sentiment,
                    source=SourceReference(
                        source_type=source.source_name,
                        title=source.source_name,
                        date=source.date
                    )
                ))

        return ResearchReport(
            query=query,
            sources=sources,
            key_facts=key_facts,
            total_sources_found=total_docs,
            search_terms_used=[query]
        )


# =============================================================================
# Convenience function
# =============================================================================

def run_research(query: str, progress_callback=None) -> ResearchReport:
    """
    Convenience function to run research team.

    Args:
        query: Research question
        progress_callback: Optional progress callback

    Returns:
        ResearchReport
    """
    team = ResearchTeam()
    return team.research(query, progress_callback)
