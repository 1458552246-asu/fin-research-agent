"""
Phase 2: Debate Team

Contains Bull vs Bear debate workflow:
- BullAnalyst: Constructs bullish arguments
- BearAnalyst: Constructs bearish arguments
- Moderator: Summarizes consensus and disputes
"""

import json
import re
from typing import List, Dict, Any, Optional, Callable
from dataclasses import asdict

from .models import (
    DebateResult, Argument, DebateRound, DebateExchange,
    ResearchReport, SourceReference, Sentiment
)
from .prompts import (
    BULL_ANALYST_PROMPT,
    BEAR_ANALYST_PROMPT,
    DEBATE_CROSS_EXAM_PROMPT,
    MODERATOR_PROMPT,
    format_key_facts_for_prompt,
    format_arguments_for_prompt,
)
from .config import Config


class LLMClient:
    """Simple LLM client for debate prompts."""

    def __init__(self):
        self.api_key = Config.LLM_API_KEY
        self.base_url = Config.LLM_BASE_URL
        self.model = Config.LLM_MODEL

    def chat(self, prompt: str, system: str = None) -> str:
        """Send a chat completion request."""
        if not self.api_key:
            return self._mock_response(prompt)

        try:
            import openai
            import httpx
            # Create custom httpx client to avoid 'proxies' parameter issue with httpx 0.28+
            http_client = httpx.Client(timeout=60.0)
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=http_client
            )

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4,  # Slightly higher for debate creativity
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM API error: {e}")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Return mock response based on query content and role."""
        # 从 prompt 中提取【用户问题】部分来判断公司
        # prompt 格式：...【用户问题】\n{query}\n\n【研究报告摘要】...
        import re
        query_match = re.search(r'【用户问题】\s*\n(.+?)\n', prompt)
        query_text = query_match.group(1).lower() if query_match else prompt.lower()

        # 基于用户问题判断公司
        is_nvidia = "nvidia" in query_text or "英伟达" in query_text or "nvda" in query_text
        is_hbm = "hbm" in query_text or "海力士" in query_text or "存储" in query_text
        is_dell = "dell" in query_text or "戴尔" in query_text

        # 用 prompt 开头的角色定义来判断是 Bull 还是 Bear
        # 不能简单用 "看多" in prompt，因为 Bear prompt 也包含"预判可能的看多质疑"
        prompt_start = prompt[:100]  # 只看开头100字
        is_bull_role = "看多研究员" in prompt_start or "Bull Analyst" in prompt_start
        is_bear_role = "看空研究员" in prompt_start or "Bear Analyst" in prompt_start

        if is_bull_role:
            if is_nvidia:
                return json.dumps({
                    "opening_statement": "NVIDIA是AI时代最确定的赢家，CUDA生态护城河深厚",
                    "arguments": [
                        {
                            "point": "数据中心收入同比增长427%，超预期",
                            "evidence": "FY2026 Q1业绩会：数据中心收入$26.3B",
                            "source": "NVIDIA FY2026 Q1 Earnings Call",
                            "strength": 0.95
                        },
                        {
                            "point": "Blackwell需求远超供应，供不应求持续到年底",
                            "evidence": "管理层明确表示供不应求状态将持续到2026年底",
                            "source": "NVIDIA FY2026 Q1 Earnings Call",
                            "strength": 0.9
                        },
                        {
                            "point": "毛利率维持在75%以上的超高水平",
                            "evidence": "本季度毛利率76.4%，预计下季度维持在75%以上",
                            "source": "NVIDIA FY2026 Q1 Earnings Call",
                            "strength": 0.85
                        }
                    ],
                    "key_bullish_factors": ["AI需求持续爆发", "CUDA生态护城河", "定价权强大"]
                }, ensure_ascii=False)
            elif is_hbm:
                return json.dumps({
                    "opening_statement": "HBM是AI芯片的核心瓶颈，供需严重失衡利好龙头",
                    "arguments": [
                        {
                            "point": "HBM收入同比增长320%，增速惊人",
                            "evidence": "SK海力士业绩会：HBM收入同比增长320%",
                            "source": "SK海力士 2026 Q1 业绩会",
                            "strength": 0.9
                        },
                        {
                            "point": "HBM毛利率超过50%，远超传统DRAM",
                            "evidence": "HBM毛利率超过50%，远高于传统DRAM的25%",
                            "source": "SK海力士 2026 Q1 业绩会",
                            "strength": 0.85
                        },
                        {
                            "point": "客户订单排到2027年Q1，需求确定性极高",
                            "evidence": "HBM3E产能满载，客户订单排到2027年Q1",
                            "source": "SK海力士 2026 Q1 业绩会",
                            "strength": 0.9
                        }
                    ],
                    "key_bullish_factors": ["供需严重失衡", "高毛利率", "订单能见度高"]
                }, ensure_ascii=False)
            else:  # Dell default
                return json.dumps({
                    "opening_statement": "AI服务器业务增长强劲，订单积压创历史新高",
                    "arguments": [
                        {
                            "point": "AI服务器收入同比增长87%，超预期",
                            "evidence": "FY2026 Q1业绩会：AI服务器收入$4.5B，同比+87%",
                            "source": "Dell FY2026 Q1 Earnings Call",
                            "strength": 0.9
                        },
                        {
                            "point": "订单积压$5.4B创历史新高，需求确定性强",
                            "evidence": "管理层披露Backlog达到$5.4B",
                            "source": "Dell FY2026 Q1 Earnings Call",
                            "strength": 0.85
                        }
                    ],
                    "key_bullish_factors": ["AI需求强劲", "订单能见度高", "NVIDIA核心合作伙伴"]
                }, ensure_ascii=False)

        elif is_bear_role:
            if is_nvidia:
                return json.dumps({
                    "opening_statement": "估值过高，竞争加剧，客户自研芯片是长期威胁",
                    "arguments": [
                        {
                            "point": "当前P/E约35x，估值已处于历史高位",
                            "evidence": "SemiAnalysis指出估值已较高，P/E约35x",
                            "source": "SemiAnalysis Newsletter",
                            "strength": 0.8
                        },
                        {
                            "point": "大客户自研芯片(TPU/Trainium)是长期威胁",
                            "evidence": "Google TPU、Amazon Trainium持续发展",
                            "source": "SemiAnalysis Newsletter",
                            "strength": 0.75
                        },
                        {
                            "point": "中国市场受限制，地缘政治风险持续",
                            "evidence": "中国市场收入占比下降至5%",
                            "source": "NVIDIA FY2026 Q1 Earnings Call",
                            "strength": 0.7
                        }
                    ],
                    "key_bearish_factors": ["估值偏高", "客户自研芯片威胁", "地缘政治风险"]
                }, ensure_ascii=False)
            elif is_hbm:
                return json.dumps({
                    "opening_statement": "2027年产能大释放可能导致供过于求，价格战风险",
                    "arguments": [
                        {
                            "point": "2027年产能大释放可能导致价格战",
                            "evidence": "专家访谈：2027年产能释放后可能会有价格压力",
                            "source": "HBM产业链专家访谈",
                            "strength": 0.85
                        },
                        {
                            "point": "HBM3E良率仅80-85%，低于上一代",
                            "evidence": "HBM3E的良率普遍在80-85%，比HBM3的90%要低",
                            "source": "HBM产业链专家访谈",
                            "strength": 0.8
                        },
                        {
                            "point": "HBM4量产至少要到2027年，技术迭代风险",
                            "evidence": "HBM4要用混合键合技术，量产至少要到2027年",
                            "source": "HBM产业链专家访谈",
                            "strength": 0.75
                        }
                    ],
                    "key_bearish_factors": ["产能释放风险", "良率问题", "技术迭代压力"]
                }, ensure_ascii=False)
            else:  # Dell default
                return json.dumps({
                    "opening_statement": "毛利率承压严重，传统业务持续下滑",
                    "arguments": [
                        {
                            "point": "GPU服务器毛利率仅12-15%，远低于传统业务",
                            "evidence": "专家访谈：GPU服务器毛利率仅12-15%，远低于传统服务器18-22%",
                            "source": "Dell前供应链高管访谈",
                            "strength": 0.9
                        },
                        {
                            "point": "传统PC业务持续萎缩，同比下降12%",
                            "evidence": "财报数据：传统服务器和PC业务同比下降12%",
                            "source": "Dell FY2026 Q1 Earnings Call",
                            "strength": 0.85
                        },
                        {
                            "point": "对NVIDIA没有议价能力，利润被挤压",
                            "evidence": "专家：NVIDIA说多少就是多少，Dell没有议价能力",
                            "source": "Dell前供应链高管访谈",
                            "strength": 0.8
                        }
                    ],
                    "key_bearish_factors": ["毛利率压力", "传统业务下滑", "对上游无议价权"]
                }, ensure_ascii=False)

        else:  # Moderator
            if is_nvidia:
                return json.dumps({
                    "consensus": ["AI需求持续强劲，NVIDIA是最大受益者", "CUDA生态系统护城河深厚"],
                    "disputes": ["当前估值是否已充分反映增长预期", "客户自研芯片的长期威胁程度"],
                    "bull_bear_ratio": 0.7,
                    "summary": "整体偏多。NVIDIA的技术领先地位和需求确定性获得共识，但估值和长期竞争格局是核心分歧点。"
                }, ensure_ascii=False)
            elif is_hbm:
                return json.dumps({
                    "consensus": ["HBM供需严重失衡，短期价格坚挺", "SK海力士技术领先地位明确"],
                    "disputes": ["2027年产能释放后的价格走势", "良率能否持续提升"],
                    "bull_bear_ratio": 0.6,
                    "summary": "中性偏多。短期供需失衡确定，但2027年产能释放是核心风险点。"
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "consensus": ["AI服务器增长确定性高", "订单积压创历史新高"],
                    "disputes": ["毛利率能否改善", "竞争格局能否稳定"],
                    "bull_bear_ratio": 0.55,
                    "summary": "中性偏多。AI服务器增长获得共识，但毛利率压力和竞争加剧是核心分歧。"
                }, ensure_ascii=False)


class BullAnalyst:
    """Constructs bullish investment arguments."""

    def __init__(self):
        self.name = "看多研究员"
        self.llm = LLMClient()

    def generate_arguments(
        self,
        query: str,
        research_report: ResearchReport,
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """Generate bullish arguments based on research report."""
        if progress_callback:
            progress_callback(f"🐂 {self.name}正在构建看多论点...")

        # Prepare research summary
        research_summary = self._format_research_summary(research_report)
        key_facts = format_key_facts_for_prompt([
            {"content": f.content, "sentiment": f.sentiment.value}
            for f in research_report.key_facts
        ])

        prompt = BULL_ANALYST_PROMPT.format(
            query=query,
            research_summary=research_summary,
            key_facts=key_facts
        )

        response = self.llm.chat(prompt)
        result = self._parse_response(response)

        if progress_callback:
            num_args = len(result.get("arguments", []))
            progress_callback(f"✓ {self.name}提出了 {num_args} 个看多论点")

        return result

    def _format_research_summary(self, report: ResearchReport) -> str:
        """Format research report for prompt."""
        summary_parts = []
        for source_group in report.sources:
            if source_group.findings:
                summary_parts.append(f"【{source_group.source_name}】")
                for finding in source_group.findings[:5]:  # Limit findings
                    summary_parts.append(f"  • {finding}")
        return "\n".join(summary_parts)

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        return {"raw_response": response, "arguments": []}


class BearAnalyst:
    """Constructs bearish investment arguments."""

    def __init__(self):
        self.name = "看空研究员"
        self.llm = LLMClient()

    def generate_arguments(
        self,
        query: str,
        research_report: ResearchReport,
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """Generate bearish arguments based on research report."""
        if progress_callback:
            progress_callback(f"🐻 {self.name}正在构建看空论点...")

        # Prepare research summary
        research_summary = self._format_research_summary(research_report)
        key_facts = format_key_facts_for_prompt([
            {"content": f.content, "sentiment": f.sentiment.value}
            for f in research_report.key_facts
        ])

        prompt = BEAR_ANALYST_PROMPT.format(
            query=query,
            research_summary=research_summary,
            key_facts=key_facts
        )

        response = self.llm.chat(prompt)
        result = self._parse_response(response)

        if progress_callback:
            num_args = len(result.get("arguments", []))
            progress_callback(f"✓ {self.name}提出了 {num_args} 个看空论点")

        return result

    def _format_research_summary(self, report: ResearchReport) -> str:
        """Format research report for prompt."""
        summary_parts = []
        for source_group in report.sources:
            if source_group.findings:
                summary_parts.append(f"【{source_group.source_name}】")
                for finding in source_group.findings[:5]:
                    summary_parts.append(f"  • {finding}")
        return "\n".join(summary_parts)

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        return {"raw_response": response, "arguments": []}


class Moderator:
    """Moderates the debate and summarizes results."""

    def __init__(self):
        self.name = "研究经理"
        self.llm = LLMClient()

    def summarize_debate(
        self,
        query: str,
        bull_result: Dict[str, Any],
        bear_result: Dict[str, Any],
        debate_exchanges: List[Dict] = None,
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """Summarize the debate and identify consensus/disputes."""
        if progress_callback:
            progress_callback(f"⚖️ {self.name}正在总结辩论...")

        bull_args = format_arguments_for_prompt(bull_result.get("arguments", []))
        bear_args = format_arguments_for_prompt(bear_result.get("arguments", []))
        exchanges_str = json.dumps(debate_exchanges or [], ensure_ascii=False, indent=2)

        prompt = MODERATOR_PROMPT.format(
            query=query,
            bull_arguments=bull_args,
            bear_arguments=bear_args,
            debate_exchanges=exchanges_str
        )

        response = self.llm.chat(prompt)
        result = self._parse_response(response)

        if progress_callback:
            ratio = result.get("bull_bear_ratio", 0.5)
            stance = "偏多" if ratio > 0.55 else "偏空" if ratio < 0.45 else "中性"
            progress_callback(f"✓ {self.name}总结完成: {stance}")

        return result

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        return {
            "consensus": [],
            "disputes": [],
            "bull_bear_ratio": 0.5,
            "summary": response[:500] if response else "辩论总结"
        }


class DebateTeam:
    """
    Coordinates the debate workflow.

    Debate Flow:
    1. Opening Statements: Bull and Bear each present arguments
    2. Cross Examination: Each side challenges the other (optional)
    3. Moderator Summary: Identify consensus, disputes, and ratio

    【重要】每个论点必须有完整的来源溯源，包含：
    - 来源类型、文档标题、文档ID、日期
    - 原文内容（不是摘要！）
    """

    def __init__(self):
        self.bull_analyst = BullAnalyst()
        self.bear_analyst = BearAnalyst()
        self.moderator = Moderator()
        self.llm = LLMClient()

    def debate(
        self,
        research_report: ResearchReport,
        enable_cross_exam: bool = False,
        progress_callback: Callable = None
    ) -> DebateResult:
        """
        Execute debate workflow.

        Args:
            research_report: Output from Research Team
            enable_cross_exam: Whether to include cross-examination rounds
            progress_callback: Optional function to report progress

        Returns:
            DebateResult with bull/bear arguments and summary
        """
        query = research_report.query

        if progress_callback:
            progress_callback("⚔️ Phase 2: 多空辩论开始...")

        result = DebateResult(query=query)

        # 构建文档索引，用于后续论点的来源溯源
        self._document_index = self._build_document_index(research_report)

        # Round 0: Opening Statements
        if progress_callback:
            progress_callback("📢 开场陈述...")

        bull_result = self.bull_analyst.generate_arguments(
            query, research_report, progress_callback
        )
        bear_result = self.bear_analyst.generate_arguments(
            query, research_report, progress_callback
        )

        # Convert to Argument objects with full source tracking
        result.bull_arguments = self._convert_arguments(
            bull_result.get("arguments", []),
            "bull",
            research_report
        )
        result.bear_arguments = self._convert_arguments(
            bear_result.get("arguments", []),
            "bear",
            research_report
        )

        # Record opening round
        opening_round = DebateRound(
            round_num=0,
            round_type="opening",
            exchanges=[
                DebateExchange(
                    round_num=0,
                    speaker="bull",
                    statement=bull_result.get("opening_statement", "看多观点陈述")
                ),
                DebateExchange(
                    round_num=0,
                    speaker="bear",
                    statement=bear_result.get("opening_statement", "看空观点陈述")
                )
            ]
        )
        result.debate_rounds.append(opening_round)

        # Optional: Cross Examination Rounds
        debate_exchanges = []
        if enable_cross_exam:
            if progress_callback:
                progress_callback("🔄 交叉质询...")

            cross_exam = self._run_cross_examination(
                query, bull_result, bear_result, progress_callback
            )
            if cross_exam:
                result.debate_rounds.append(cross_exam)
                debate_exchanges = [
                    {"speaker": ex.speaker, "statement": ex.statement}
                    for ex in cross_exam.exchanges
                ]

        # Moderator Summary
        if progress_callback:
            progress_callback("📋 研究经理总结...")

        moderator_result = self.moderator.summarize_debate(
            query, bull_result, bear_result, debate_exchanges, progress_callback
        )

        result.consensus = moderator_result.get("consensus", [])
        result.disputes = moderator_result.get("disputes", [])
        result.bull_bear_ratio = moderator_result.get("bull_bear_ratio", 0.5)
        result.moderator_summary = moderator_result.get("summary", "")

        if progress_callback:
            progress_callback("✅ Phase 2 完成: 多空辩论结束")

        return result

    def _build_document_index(self, research_report: ResearchReport) -> Dict[str, Dict]:
        """
        从研究报告构建文档索引，用于论点的来源溯源。

        Returns:
            Dict mapping keywords/phrases to document info with full content
        """
        index = {}
        for source_group in research_report.sources:
            for doc in source_group.raw_documents:
                # 存储完整文档信息
                doc_info = {
                    "file_id": doc.get("file_id"),
                    "title": doc.get("title", ""),
                    "source_type": doc.get("source_type", source_group.source_name),
                    "date": doc.get("date", ""),
                    "content": doc.get("content", ""),  # 完整原文！
                    "url": doc.get("url", "")
                }
                # 用标题作为索引
                if doc_info["title"]:
                    index[doc_info["title"].lower()] = doc_info
                # 也用来源类型作为索引
                index[doc_info["source_type"].lower()] = doc_info
        return index

    def _find_source_for_argument(
        self,
        arg_dict: Dict,
        research_report: ResearchReport
    ) -> Optional[SourceReference]:
        """
        为论点找到对应的来源文档，包含完整原文。

        Args:
            arg_dict: 论点字典，可能包含 source, evidence 等字段
            research_report: 研究报告

        Returns:
            带有完整原文的 SourceReference
        """
        evidence = arg_dict.get("evidence", "").lower()
        source_hint = arg_dict.get("source", "").lower()

        # 尝试从文档索引中匹配
        best_match = None
        for key, doc_info in self._document_index.items():
            if key in evidence or key in source_hint:
                best_match = doc_info
                break
            # 检查内容是否包含证据关键词
            content = doc_info.get("content", "").lower()
            if evidence and any(word in content for word in evidence.split()[:3] if len(word) > 2):
                best_match = doc_info
                break

        if best_match:
            return SourceReference(
                source_type=best_match.get("source_type", ""),
                title=best_match.get("title", ""),
                date=best_match.get("date", ""),
                url=best_match.get("url", ""),
                file_id=best_match.get("file_id"),
                preview=best_match.get("content", "")  # 完整原文！
            )

        # 如果没有匹配，尝试从 key_facts 中找
        for fact in research_report.key_facts:
            if fact.source and fact.content.lower() in evidence:
                return fact.source

        return None

    def _convert_arguments(
        self,
        arg_list: List[Dict],
        side: str,
        research_report: ResearchReport
    ) -> List[Argument]:
        """Convert dict arguments to Argument objects with full source tracking."""
        arguments = []
        for arg_dict in arg_list:
            if isinstance(arg_dict, dict):
                # 尝试找到对应的完整来源
                source_ref = self._find_source_for_argument(arg_dict, research_report)

                # 如果没找到，创建一个基本的来源引用
                if not source_ref and arg_dict.get("source"):
                    source_ref = SourceReference(
                        source_type=arg_dict.get("source", side),
                        title=arg_dict.get("source", ""),
                        preview=arg_dict.get("evidence", "")  # 至少保留证据作为参考
                    )

                arguments.append(Argument(
                    point=arg_dict.get("point", ""),
                    evidence=arg_dict.get("evidence", ""),
                    source=source_ref,
                    strength=arg_dict.get("strength", 0.7),
                    rebuttal=arg_dict.get("potential_rebuttal")
                ))
        return arguments

    def _run_cross_examination(
        self,
        query: str,
        bull_result: Dict,
        bear_result: Dict,
        progress_callback: Callable = None
    ) -> Optional[DebateRound]:
        """Run cross-examination round."""
        exchanges = []

        # Bull challenges Bear
        bull_challenge_prompt = DEBATE_CROSS_EXAM_PROMPT.format(
            role="看多研究员",
            role_description="Bull Analyst",
            opponent_role="看空研究员",
            opponent_arguments=format_arguments_for_prompt(bear_result.get("arguments", [])),
            your_arguments=format_arguments_for_prompt(bull_result.get("arguments", []))
        )
        bull_challenge = self.llm.chat(bull_challenge_prompt)

        try:
            bull_parsed = json.loads(re.search(r'\{[\s\S]*\}', bull_challenge).group())
            for rebuttal in bull_parsed.get("rebuttals", [])[:2]:
                exchanges.append(DebateExchange(
                    round_num=1,
                    speaker="bull",
                    statement=f"质疑: {rebuttal.get('challenge', '')} | 反证: {rebuttal.get('counter_evidence', '')}",
                    is_rebuttal=True,
                    targets_argument=rebuttal.get("targets")
                ))
        except Exception:
            exchanges.append(DebateExchange(
                round_num=1,
                speaker="bull",
                statement=bull_challenge[:300],
                is_rebuttal=True
            ))

        # Bear challenges Bull
        bear_challenge_prompt = DEBATE_CROSS_EXAM_PROMPT.format(
            role="看空研究员",
            role_description="Bear Analyst",
            opponent_role="看多研究员",
            opponent_arguments=format_arguments_for_prompt(bull_result.get("arguments", [])),
            your_arguments=format_arguments_for_prompt(bear_result.get("arguments", []))
        )
        bear_challenge = self.llm.chat(bear_challenge_prompt)

        try:
            bear_parsed = json.loads(re.search(r'\{[\s\S]*\}', bear_challenge).group())
            for rebuttal in bear_parsed.get("rebuttals", [])[:2]:
                exchanges.append(DebateExchange(
                    round_num=1,
                    speaker="bear",
                    statement=f"质疑: {rebuttal.get('challenge', '')} | 反证: {rebuttal.get('counter_evidence', '')}",
                    is_rebuttal=True,
                    targets_argument=rebuttal.get("targets")
                ))
        except Exception:
            exchanges.append(DebateExchange(
                round_num=1,
                speaker="bear",
                statement=bear_challenge[:300],
                is_rebuttal=True
            ))

        return DebateRound(
            round_num=1,
            round_type="cross_examination",
            exchanges=exchanges
        )


# Convenience function
def run_debate(
    research_report: ResearchReport,
    enable_cross_exam: bool = False,
    progress_callback: Callable = None
) -> DebateResult:
    """Run debate team workflow."""
    team = DebateTeam()
    return team.debate(research_report, enable_cross_exam, progress_callback)
