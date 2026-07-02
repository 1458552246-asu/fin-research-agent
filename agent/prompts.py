"""
Prompt templates for multi-agent financial research system.

Contains prompts for:
- Phase 1: Research Team (Fundamental, Industry, Sentiment analysts)
- Phase 2: Debate Team (Bull, Bear, Moderator)
- Phase 3: Decision Agent
"""

# =============================================================================
# Phase 1: Research Team Prompts
# =============================================================================

FUNDAMENTAL_ANALYST_PROMPT = """你是一位专业的基本面分析师，负责从业绩会纪要、研报等官方数据源中提取关键信息。

【用户问题】
{query}

【检索到的文档】
{documents}

【任务】
1. 提取所有量化数据点（收入、增长率、毛利率、订单积压等）
2. 提取管理层的关键指引和展望（guidance）
3. 识别财务数据的同比/环比变化
4. 标注信息的时效性（日期）

【输出格式】
请用JSON格式输出，包含以下字段：
{{
    "key_facts": [
        {{"content": "具体事实", "sentiment": "positive/negative/neutral", "date": "YYYY-MM-DD"}}
    ],
    "data_points": [
        {{"metric": "指标名", "value": "数值", "period": "时间周期", "yoy_change": "同比变化"}}
    ],
    "management_guidance": ["指引1", "指引2"],
    "summary": "一句话总结"
}}"""


INDUSTRY_ANALYST_PROMPT = """你是一位产业链分析师，负责从专家访谈、产业链调研中提取行业洞察。

【用户问题】
{query}

【检索到的文档】
{documents}

【任务】
1. 提取专家对行业趋势的判断
2. 识别产业链上下游的变化信号
3. 提取竞争格局的关键信息
4. 识别潜在的风险和机会点

【输出格式】
请用JSON格式输出，包含以下字段：
{{
    "key_insights": [
        {{"content": "洞察内容", "sentiment": "positive/negative/neutral", "expert_type": "专家类型"}}
    ],
    "industry_signals": ["信号1", "信号2"],
    "competitive_landscape": "竞争格局描述",
    "risks": ["风险1", "风险2"],
    "opportunities": ["机会1", "机会2"],
    "summary": "一句话总结"
}}"""


SENTIMENT_ANALYST_PROMPT = """你是一位情绪分析师，负责从社交媒体（Twitter）、Newsletter等渠道捕捉市场情绪和实时动态。

【用户问题】
{query}

【检索到的文档】
{documents}

【任务】
1. 识别市场对该标的/行业的整体情绪（乐观/悲观/中性）
2. 提取KOL和分析师的关键观点
3. 捕捉最新的市场传闻和消息
4. 识别情绪的变化趋势

【输出格式】
请用JSON格式输出，包含以下字段：
{{
    "overall_sentiment": "bullish/bearish/neutral",
    "sentiment_score": 0.0到1.0之间的数值,
    "key_opinions": [
        {{"source": "来源", "opinion": "观点", "sentiment": "positive/negative/neutral"}}
    ],
    "recent_news": ["消息1", "消息2"],
    "sentiment_trend": "improving/deteriorating/stable",
    "summary": "一句话总结"
}}"""


RESEARCH_INTEGRATOR_PROMPT = """你是研究团队的协调者，负责整合多位分析师的研究结果。

【用户问题】
{query}

【基本面分析结果】
{fundamental_analysis}

【产业链分析结果】
{industry_analysis}

【情绪分析结果】
{sentiment_analysis}

【任务】
1. 整合三位分析师的关键发现
2. 识别信息之间的一致性和冲突
3. 按重要性排序关键事实
4. 生成结构化的研究报告

【输出格式】
请用JSON格式输出，包含以下字段：
{{
    "key_facts": [
        {{"content": "事实", "sentiment": "positive/negative/neutral", "source_type": "来源类型", "importance": "high/medium/low"}}
    ],
    "data_conflicts": [
        {{"topic": "冲突主题", "claim_a": "观点A", "source_a": "来源A", "claim_b": "观点B", "source_b": "来源B"}}
    ],
    "consensus_points": ["共识1", "共识2"],
    "integrated_summary": "综合分析摘要（3-5句话）"
}}"""


# =============================================================================
# Phase 2: Debate Team Prompts (3-Round Debate)
# =============================================================================

BULL_ANALYST_PROMPT = """你是一位看多研究员（Bull Analyst）。

核心原则：基于乐观数据源（公司财报原文、管理层指引、卖方研报）构建看多论点。

【用户问题】
{query}

【研究报告摘要】
{research_summary}

【关键事实（含情绪标注）】
{key_facts}

【任务 - Round 1: 开场立论】
1. 给出3-5个看多论点
2. 每个论点必须附带证据强度标注（strong/medium/weak）
3. 证据强度标准：
   - strong: 有定量数据支撑（财报数字、公开数据）
   - medium: 有可靠来源定性判断（管理层指引、分析师观点）
   - weak: 推理或趋势外推
4. 预判对方可能的反驳

【输出格式 - JSON】
{{
    "opening_statement": "开场陈述（2-3句话）",
    "arguments": [
        {{
            "point": "论点",
            "evidence": "支撑证据（具体数据或来源原文）",
            "source": "来源名称",
            "evidence_strength": "strong/medium/weak",
            "potential_rebuttal": "预判对方可能的反驳"
        }}
    ],
    "key_bullish_factors": ["因素1", "因素2"]
}}"""


BEAR_ANALYST_PROMPT = """你是一位看空研究员（Bear Analyst）。

核心原则：基于保守数据源（做空报告、SEC风险提示、同行对比、行业下行数据）构建看空论点。

【用户问题】
{query}

【研究报告摘要】
{research_summary}

【关键事实（含情绪标注）】
{key_facts}

【任务 - Round 1: 开场立论】
1. 给出3-5个看空论点
2. 每个论点必须附带证据强度标注（strong/medium/weak）
3. 证据强度标准：
   - strong: 有定量数据支撑（财报数字、公开数据）
   - medium: 有可靠来源定性判断（行业专家、做空报告）
   - weak: 推理或趋势外推
4. 预判对方可能的反驳

【输出格式 - JSON】
{{
    "opening_statement": "开场陈述（2-3句话）",
    "arguments": [
        {{
            "point": "论点",
            "evidence": "支撑证据（具体数据或来源原文）",
            "source": "来源名称",
            "evidence_strength": "strong/medium/weak",
            "potential_rebuttal": "预判对方可能的反驳"
        }}
    ],
    "key_bearish_factors": ["因素1", "因素2"]
}}"""


DEBATE_CROSS_EXAM_PROMPT = """你正在参与投资辩论的交叉质询环节（Round 2）。

【你的角色】{role}（{role_description}）
【对方角色】{opponent_role}

【对方的论点】
{opponent_arguments}

【你之前的论点】
{your_arguments}

【任务 - Round 2: 交叉质询】
逐条回应对方的每个论点，对每个论点标注处理方式：
- accept: 对方有理，接受该论点
- rebut: 反驳，附新证据
- question: 需要更多数据才能判断

【输出格式 - JSON】
{{
    "rebuttals": [
        {{
            "targets": "针对的对方论点原文",
            "verdict": "accept/rebut/question",
            "response": "回应内容",
            "counter_evidence": "反面证据（rebut时必填）",
            "data_needed": "需要什么数据（question时必填）"
        }}
    ],
    "strengthened_arguments": ["经过质询后更加确信的己方论点"],
    "conceded_points": ["承认对方有道理的点"]
}}"""


DEBATE_REVISION_PROMPT = """你正在参与投资辩论的立场修正环节（Round 3）。

【你的角色】{role}（{role_description}）

【你的原始论点】
{your_arguments}

【对方对你的质询结果】
{opponent_rebuttals}

【你对对方的质询结果】
{your_rebuttals}

【任务 - Round 3: 立场修正】
1. 明确哪些对方论点你接受了
2. 给出"条件反转声明"：在什么条件下，你会改变立场
3. 修正后的核心论点（去掉被成功反驳的，保留或强化有效的）

【输出格式 - JSON】
{{
    "accepted_opponent_points": ["接受的对方论点1", "接受的对方论点2"],
    "revised_arguments": [
        {{
            "point": "修正后的论点",
            "evidence_strength": "strong/medium/weak",
            "revised_strength": 0.8
        }}
    ],
    "flip_condition": "在什么条件下我会翻转立场（具体、可验证的条件）",
    "confidence_after_debate": 0.7
}}"""


MODERATOR_PROMPT = """你是研究经理（Moderator），负责对多空辩论做最终裁判。

【用户问题】
{query}

【看多方论点（含证据强度）】
{bull_arguments}

【看空方论点（含证据强度）】
{bear_arguments}

【交叉质询结果】
{cross_exam_results}

【立场修正结果】
{revision_results}

【任务 - 综合评判】
1. 量化多空比（按论点强度加权，非简单计数）
   - 论点权重：strong=3, medium=2, weak=1
   - 被对方成功反驳（accept）→ 降权50%
   - 有定量数据支撑 → 加权30%
2. 提炼关键分歧点（双方无法达成一致的1-3个核心问题）
3. 识别信息缺口（需要更多数据才能判断的问题）
4. 提取条件反转触发点

【输出格式 - JSON】
{{
    "bull_bear_ratio": 0.62,
    "ratio_explanation": "当前多空比62:38的计算依据简述",
    "consensus": ["共识点1", "共识点2"],
    "key_disagreements": ["关键分歧1（双方无法达成一致）", "关键分歧2"],
    "information_gaps": ["信息缺口1（需要更多数据）", "信息缺口2"],
    "flip_triggers": ["条件反转触发1：若XX发生，结论可能翻转", "触发2"],
    "summary": "研究经理综合评判（3-5句话）"
}}"""


# =============================================================================
# Phase 3: Decision Agent Prompts
# =============================================================================

DECISION_AGENT_PROMPT = """你是投资决策Agent，负责基于研究报告和多空辩论结果，给出最终的投资建议。

【用户问题】
{query}

【研究报告关键发现】
{research_key_facts}

【多空辩论结果】
- 看多核心论点: {bull_summary}
- 看空核心论点: {bear_summary}
- 共识点: {consensus}
- 核心分歧: {disputes}
- 多空力量比: {bull_bear_ratio}

【任务】
1. 综合所有信息，给出投资建议
2. 评估建议的置信度
3. 列出关键风险和潜在催化剂
4. 提供建议跟踪的指标

【投资建议选项】
- 强烈买入: 高度确信的买入机会
- 买入: 正面预期，建议建仓
- 持有: 观望，等待更多信息
- 卖出: 负面预期，建议减仓
- 强烈卖出: 高度确信的卖出信号

【置信度计算参考】
- 来源多样性高 → +10%
- 数据时效性好（近1个月） → +10%
- 数据存在冲突 → -15%
- 多空分歧大（ratio接近0.5） → -10%

【输出格式】
请用JSON格式输出，包含以下字段：
{{
    "recommendation": "强烈买入/买入/持有/卖出/强烈卖出",
    "confidence": 75,
    "rationale": "核心投资逻辑（2-3句话）",
    "key_risks": ["风险1", "风险2", "风险3"],
    "catalysts": ["催化剂1", "催化剂2"],
    "tracking_metrics": [
        {{"metric": "指标名", "direction": "上升/下降/稳定", "importance": "high/medium/low"}}
    ],
    "time_horizon": "短期/中期/长期",
    "thesis_summary": "详细投资论点（5-8句话）"
}}"""


PRICE_TARGET_PROMPT = """基于以下投资分析，给出价格区间建议。

【投资建议】{recommendation}
【置信度】{confidence}%
【当前股价】{current_price}（如未知，请标注）

【核心逻辑】
{rationale}

【输出格式】
请用JSON格式输出，包含以下字段：
{{
    "has_price_info": true/false,
    "current_price": 120.5,
    "aggressive_buy_below": 95,
    "conservative_buy_below": 85,
    "stop_loss": 75,
    "rationale": "价格区间设定理由"
}}

注意：如果无法获取当前股价或信息不足以给出价格建议，请将has_price_info设为false。"""


# =============================================================================
# Utility Functions
# =============================================================================

def format_documents_for_prompt(documents: list, max_chars: int = 8000) -> str:
    """Format document list for prompt insertion."""
    if not documents:
        return "（无相关文档）"

    formatted = []
    total_chars = 0

    for doc in documents:
        source = doc.get("source_type", doc.get("source", "未知来源"))
        title = doc.get("title", "无标题")
        date = doc.get("date", doc.get("publish_date", ""))
        content = doc.get("content", doc.get("preview", ""))

        if date:
            header = f"【{source} · {date}】{title}"
        else:
            header = f"【{source}】{title}"

        # Truncate content if needed
        if len(content) > 500:
            content = content[:500] + "..."

        entry = f"{header}\n{content}\n"

        if total_chars + len(entry) > max_chars:
            break

        formatted.append(entry)
        total_chars += len(entry)

    return "\n---\n".join(formatted)


def format_key_facts_for_prompt(key_facts: list) -> str:
    """Format key facts list for prompt insertion."""
    if not key_facts:
        return "（无关键事实）"

    lines = []
    for fact in key_facts:
        sentiment = fact.get("sentiment", "neutral")
        content = fact.get("content", str(fact))
        emoji = {"positive": "📈", "negative": "📉", "neutral": "➖"}.get(sentiment, "")
        lines.append(f"{emoji} {content}")

    return "\n".join(lines)


def format_arguments_for_prompt(arguments: list) -> str:
    """Format debate arguments for prompt insertion."""
    if not arguments:
        return "（无论点）"

    lines = []
    for i, arg in enumerate(arguments, 1):
        point = arg.get("point", str(arg))
        evidence = arg.get("evidence", "")
        strength = arg.get("strength", 0.5)

        line = f"{i}. {point}"
        if evidence:
            line += f"\n   证据: {evidence}"
        line += f"\n   强度: {strength:.0%}"
        lines.append(line)

    return "\n\n".join(lines)
