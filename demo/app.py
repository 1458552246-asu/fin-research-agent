"""
Fin Research Agent - Streamlit Application

Multi-Agent Financial Research Assistant with:
- Phase 1: Research Team (parallel multi-source information gathering)
- Phase 2: Debate Team (Bull vs Bear structured debate)
- Phase 3: Decision Agent (investment recommendation with confidence)
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.config import Config, KB_ID_TO_NAME

# Reload config to pick up Streamlit Cloud secrets
Config.reload()

from agent.orchestrator import Orchestrator
from agent.models import (
    ResearchReport, DebateResult, Decision,
    Recommendation, Sentiment, WorkflowState
)
from agent.react_agent import AgentStep, AgentOutput
from agent.sentiment_monitor import get_market_sentiment, get_cache_age
from agent.subscription_manager import get_subscription_manager

# Page config
st.set_page_config(
    page_title="Fin Research Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state early to avoid "SessionInfo before initialized" error
if "query" not in st.session_state:
    st.session_state.query = ""
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False

# Custom CSS for modern agent-style UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 1rem;
    }
    /* Phase status boxes */
    .phase-box {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        background: white;
    }
    .phase-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .phase-active {
        border-left: 4px solid #2196f3;
        background: linear-gradient(to right, #e3f2fd, white);
    }
    .phase-complete {
        border-left: 4px solid #4caf50;
        background: linear-gradient(to right, #e8f5e9, white);
    }
    /* Bull/Bear styling */
    .bull-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .bear-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .neutral-box {
        background-color: #fff8e1;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    /* Source tags */
    .source-tag {
        background-color: #e3f2fd;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-right: 8px;
    }
    /* Confidence meter */
    .confidence-meter {
        background: #e0e0e0;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
        margin: 8px 0;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    .confidence-high { background: linear-gradient(to right, #4caf50, #81c784); }
    .confidence-mid { background: linear-gradient(to right, #ff9800, #ffb74d); }
    .confidence-low { background: linear-gradient(to right, #9e9e9e, #bdbdbd); }
    /* Decision card */
    .decision-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 1.5rem;
        color: white;
        margin: 1rem 0;
    }
    .decision-recommendation {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    /* Debate exchange */
    .debate-exchange {
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    .debate-bull { border-left: 4px solid #4caf50; background: #f1f8e9; }
    .debate-bear { border-left: 4px solid #f44336; background: #fce4ec; }
    /* Stance badge */
    .stance-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: bold;
        margin-left: 8px;
    }
    .stance-bullish { background-color: #c8e6c9; color: #2e7d32; }
    .stance-bearish { background-color: #ffcdd2; color: #c62828; }
    .stance-neutral { background-color: #fff9c4; color: #f57f17; }
    /* Progress log */
    .progress-log {
        font-family: monospace;
        font-size: 0.85rem;
        background: #263238;
        color: #aed581;
        padding: 1rem;
        border-radius: 8px;
        max-height: 200px;
        overflow-y: auto;
    }
    /* Sentiment box */
    .sentiment-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        color: white;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# UI Helper Functions
# =============================================================================

def get_recommendation_color(rec: Recommendation) -> str:
    """Get color for recommendation badge."""
    colors = {
        Recommendation.STRONG_BUY: "#2e7d32",
        Recommendation.BUY: "#4caf50",
        Recommendation.HOLD: "#ff9800",
        Recommendation.SELL: "#f44336",
        Recommendation.STRONG_SELL: "#c62828",
    }
    return colors.get(rec, "#757575")


def get_confidence_class(confidence: float) -> str:
    """Get CSS class for confidence level."""
    if confidence >= 70:
        return "confidence-high"
    elif confidence >= 50:
        return "confidence-mid"
    return "confidence-low"


def render_source_group(source_group):
    """Render a source group with full source tracing including original text."""
    doc_count = len(source_group.raw_documents) if source_group.raw_documents else len(source_group.findings)

    # 蓝色背景条 - 来源类型和文档数量
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1565c0 0%, #1976d2 100%); border-radius: 8px; padding: 12px 16px; margin: 15px 0 10px 0;">
        <span style="font-weight: 600; color: white; font-size: 1rem;">📚 {source_group.source_name} ({doc_count} 条文档)</span>
    </div>
    """, unsafe_allow_html=True)

    if source_group.raw_documents:
        for doc in source_group.raw_documents:
            file_id = doc.get("file_id", "")
            title = doc.get("title", doc.get("file_name", "未知标题"))
            source_type = doc.get("source_type", source_group.source_name)
            date = doc.get("date", "")
            content = doc.get("content", "")

            # 文档标题行：【来源类型】标题 · 日期 (ID: xxx)
            header = f"**【{source_type}】{title}**"
            if date:
                header += f" · {date}"
            if file_id:
                header += f" (ID: {file_id})"
            st.markdown(header)

            # 灰色内容框 - 文档摘要
            # 判断 content 是否为有效内容（不是空的或仅是文件名占位符）
            is_placeholder = not content or content.startswith("文档:") or len(content.strip()) < 20

            if not is_placeholder:
                # 显示摘要（截取前 300 字符）
                summary = content[:300] + "..." if len(content) > 300 else content
                st.markdown(f"""
                <div style="background: #f5f5f5; border-radius: 8px; padding: 15px 20px; margin: 10px 0; border: 1px solid #e0e0e0;">
                    <div style="color: #666; margin-bottom: 8px; font-size: 0.85rem;">📄 文档摘要:</div>
                    <div style="white-space: pre-wrap; color: #333; line-height: 1.6;">{summary}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 内容为空或是占位符，显示友好提示
                st.markdown(f"""
                <div style="background: #f5f5f5; border-radius: 8px; padding: 12px 16px; margin: 10px 0; border: 1px solid #e0e0e0;">
                    <div style="color: #888; font-size: 0.9rem;">📄 点击下方链接查看文档完整内容</div>
                </div>
                """, unsafe_allow_html=True)

            # 🔗 在知识库中查看原文 链接
            # 使用 source_tracer 的统一 URL 生成
            from agent.source_tracer import get_preview_url
            is_mock = doc.get("is_mock", False)
            if file_id and not is_mock:
                preview_url = get_preview_url(file_id)
                st.markdown(f"🔗 [在知识库中查看原文]({preview_url})")

            st.markdown("---")
    else:
        # 兼容旧格式
        for finding in source_group.findings:
            st.markdown(f"• {finding}")


def render_argument(arg, is_bull: bool):
    """Render a debate argument with full source tracing."""
    from agent.source_tracer import get_preview_url

    box_class = "bull-box" if is_bull else "bear-box"
    emoji = "📈" if is_bull else "📉"

    # 来源溯源信息
    source_info = ""
    preview_url = ""
    original_text = ""
    is_mock = False
    if arg.source:
        source_type = arg.source.source_type or "分析"
        source_title = arg.source.title or ""
        source_date = arg.source.date or ""
        file_id = arg.source.file_id or ""
        original_text = arg.source.preview or ""  # 原文内容

        # 判断是否为 mock 数据（通过 file_id 是否存在来判断）
        is_mock = not file_id

        source_header = f"📌 来源: 【{source_type}】"
        if source_title:
            source_header += f" {source_title}"
        if source_date:
            source_header += f" · {source_date}"
        if file_id:
            source_header += f" (ID: {file_id})"
            # 使用统一的 URL 生成函数
            preview_url = get_preview_url(file_id)
        source_info = f'<div style="color: #1976d2; font-size: 0.8rem; margin-top: 8px;">{source_header}</div>'
    else:
        source_info = '<div style="color: #888; font-size: 0.8rem; margin-top: 8px;">📌 来源: 分析推断</div>'

    # 主体内容渲染 (不包含原文，原文用 Streamlit expander)
    st.markdown(f"""
    <div class="{box_class}">
        <div style="margin-bottom: 8px;">{emoji} <strong>{arg.point}</strong></div>
        <div style="color: #666; font-size: 0.9rem;">{arg.evidence}</div>
        {source_info}
        <div style="margin-top: 4px;">
            <span style="color: #888; font-size: 0.85rem;">论点强度: {arg.strength:.0%}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 原文展示 - 使用 Streamlit 原生 expander 而非 HTML details
    if original_text:
        display_text = original_text[:500] + ("..." if len(original_text) > 500 else "")
        with st.expander("📄 查看原文依据", expanded=False):
            st.text(display_text)
            if preview_url:
                st.markdown(f"🔗 [在知识库中查看完整原文]({preview_url})")


def render_decision_card(decision: Decision):
    """Render the final decision card."""
    rec_color = get_recommendation_color(decision.recommendation)
    conf_class = get_confidence_class(decision.confidence)

    st.markdown(f"""
    <div class="decision-card">
        <div class="decision-recommendation">
            {decision.recommendation_emoji()} {decision.recommendation.value}
        </div>
        <div style="margin-bottom: 1rem;">
            <strong>置信度:</strong> {decision.confidence:.0f}%
            <div class="confidence-meter">
                <div class="confidence-fill {conf_class}" style="width: {decision.confidence}%;"></div>
            </div>
        </div>
        <div style="opacity: 0.9;">
            {decision.rationale}
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# Main Analysis Workflow
# =============================================================================

def run_agent_workflow(query: str):
    """Run the full multi-agent workflow with live progress updates."""
    orchestrator = Orchestrator()
    progress_log = []

    def update_progress(msg_or_analyst: str, status: str = None):
        """Progress callback that handles both single-arg and two-arg calls."""
        if status is not None:
            msg = f"{msg_or_analyst}: {status}"
        else:
            msg = msg_or_analyst
        progress_log.append(msg)

    # Phase 0: ReAct Agent Reasoning
    agent_steps = []

    def on_react_step(step: AgentStep):
        agent_steps.append(step)

    with st.status("🧠 Agent 推理中...", expanded=True) as status:
        st.write("🤔 分析问题，规划信息收集策略...")
        agent_output = orchestrator.run_react_phase(query, on_step=on_react_step)
        st.write(f"✅ 完成 {len(agent_output.steps)} 步推理，确定信息收集方向")
        status.update(label=f"✅ Agent 推理完成 ({len(agent_output.steps)} 步)", state="complete")

    # Display ReAct Thinking Process
    with st.expander("🧠 Agent 推理过程 (Thought → Action → Observation)", expanded=True):
        for step in agent_output.steps:
            st.markdown(f"**Step {step.step_num}**")
            st.markdown(f"💭 **Thought:** {step.thought}")
            action_params = ", ".join(f'{k}="{v}"' for k, v in step.action_input.items()) if step.action_input else ""
            st.markdown(f"🔧 **Action:** `{step.action}({action_params})`")
            st.markdown(f"👁 **Observation:** {step.observation}")
            st.divider()

    # Phase 1: Build Research Report from Agent output
    with st.status("📋 Phase 1: 多源信息检索...", expanded=True) as status:
        st.write("🔬 基本面分析师检索 AlphaEngine (业绩会/研报)...")
        st.write("🏭 产业链分析师检索 专家访谈 (久谦中台)...")
        st.write("📱 情绪分析师检索 Twitter/Substack/AceCamp...")

        research_report = orchestrator.build_report_from_agent(agent_output, query)

        source_names = [s.source_name for s in research_report.sources]
        st.write(f"✅ 找到 {research_report.total_sources_found} 条相关信息")
        st.write(f"📚 来源: {', '.join(source_names)}")
        status.update(label=f"✅ Phase 1 完成: 收集 {research_report.total_sources_found} 条信息", state="complete")

    # Display Research Summary immediately after Phase 1
    with st.expander("📊 多源信息汇总 (按来源分类)", expanded=True):
        if research_report.sources:
            for source_group in research_report.sources:
                render_source_group(source_group)

        if research_report.data_conflicts:
            st.warning("⚠️ 发现数据冲突:")
            for conflict in research_report.data_conflicts:
                st.markdown(f"- **{conflict.topic}**: {conflict.claim_a} vs {conflict.claim_b}")

    # Phase 2: Debate
    with st.status("⚔️ Phase 2: 多空辩论...", expanded=True) as status:
        st.write("🐂 看多研究员构建论点...")
        st.write("🐻 看空研究员构建论点...")
        st.write("⚖️ 研究经理总结辩论...")

        debate_result = orchestrator.debate_team.debate(
            research_report,
            enable_cross_exam=False,
            progress_callback=update_progress
        )

        ratio = debate_result.bull_bear_ratio
        stance = "偏多" if ratio > 0.55 else "偏空" if ratio < 0.45 else "中性"
        st.write(f"✅ 辩论完成 - 多空比: {ratio:.0%}, 结论: {stance}")
        status.update(label="✅ Phase 2 完成: 多空辩论", state="complete")

    # Display Debate immediately after Phase 2
    st.markdown("### ⚔️ Bull vs Bear 辩论")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🐂 看多论点")
        for arg in debate_result.bull_arguments:
            render_argument(arg, is_bull=True)

    with col2:
        st.markdown("#### 🐻 看空论点")
        for arg in debate_result.bear_arguments:
            render_argument(arg, is_bull=False)

    # Moderator Summary
    if debate_result.moderator_summary:
        st.markdown("#### ⚖️ 研究经理总结")
        st.markdown(f"""
        <div class="neutral-box">
            {debate_result.moderator_summary}
        </div>
        """, unsafe_allow_html=True)

    # Consensus & Disputes
    if debate_result.consensus:
        st.markdown("**共识点:**")
        for c in debate_result.consensus:
            st.markdown(f"- ✓ {c}")

    if debate_result.disputes:
        st.markdown("**核心分歧:**")
        for d in debate_result.disputes:
            st.markdown(f"- ❓ {d}")

    # Phase 3: Decision
    with st.status("📈 Phase 3: 生成投资建议...", expanded=True) as status:
        st.write("🤖 综合分析研究和辩论结果...")
        st.write("📊 计算置信度...")
        st.write("🎯 生成投资建议...")

        decision = orchestrator.decision_agent.decide(
            research_report,
            debate_result,
            update_progress
        )

        st.write(f"✅ 建议: {decision.recommendation.value} (置信度 {decision.confidence:.0f}%)")
        status.update(label="✅ Phase 3 完成: 投资建议", state="complete")

    # Display Decision immediately after Phase 3
    st.markdown("### 📈 投资建议")

    render_decision_card(decision)

    # Detailed Analysis
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**⚠️ 关键风险:**")
        for risk in decision.key_risks:
            st.markdown(f"- {risk}")

        st.markdown("**🎯 潜在催化剂:**")
        for cat in decision.catalysts:
            st.markdown(f"- {cat}")

    with col2:
        st.markdown("**📊 建议跟踪指标:**")
        for metric in decision.tracking_metrics:
            direction_emoji = {"上升": "📈", "下降": "📉", "稳定": "➡️"}.get(metric.target_direction, "")
            st.markdown(f"- {direction_emoji} {metric.metric_name} ({metric.importance})")

        st.markdown(f"**⏱️ 投资时间窗口:** {decision.time_horizon}")

    # Full Thesis
    if decision.thesis_summary:
        with st.expander("📝 完整投资论点", expanded=False):
            st.markdown(decision.thesis_summary)

    # Progress Log (collapsed)
    with st.expander("🔧 执行日志", expanded=False):
        st.markdown(f"""
        <div class="progress-log">
        {'<br>'.join(progress_log)}
        </div>
        """, unsafe_allow_html=True)

    return research_report, debate_result, decision


# =============================================================================
# Sentiment Panel
# =============================================================================

def render_sentiment_panel():
    """Render the WSB market sentiment panel."""
    col1, col2 = st.columns([4, 1])

    with col2:
        refresh_btn = st.button("🔄 刷新", key="refresh_sentiment")

    sentiment = get_market_sentiment(force_refresh=refresh_btn)
    cache_age = get_cache_age()

    with col1:
        if sentiment.error:
            st.warning(f"情绪数据获取异常: {sentiment.error}")

        bull_pct = sentiment.bullish_percent
        st.markdown(f"""
        <div class="sentiment-box">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span>🐂 Bullish {bull_pct:.0f}%</span>
                <span>🐻 Bearish {sentiment.bearish_percent:.0f}%</span>
            </div>
            <div style="background: #ffffff30; height: 20px; border-radius: 10px; overflow: hidden;">
                <div style="background: #4caf50; height: 100%; width: {bull_pct}%; float: left;"></div>
                <div style="background: #f44336; height: 100%; width: {sentiment.bearish_percent}%; float: left;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Summary
    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        st.markdown("**🔥 热门话题**")
        topics = sentiment.hot_topics or [
            "NVIDIA业绩超预期，AI需求持续强劲",
            "美联储降息预期升温",
            "科技股估值分化"
        ]
        for i, topic in enumerate(topics[:5], 1):
            st.markdown(f"{i}. {topic}")

    with summary_col2:
        st.markdown("**📈 热门个股**")
        tickers = sentiment.top_tickers or [
            {"symbol": "NVDA", "change": "+5.2%"},
            {"symbol": "TSLA", "change": "-2.1%"},
            {"symbol": "AMD", "change": "+3.8%"}
        ]
        for t in tickers[:6]:
            change = t.get("change", "")
            color = "🟢" if change.startswith("+") else "🔴" if change.startswith("-") else "⚪"
            st.markdown(f"{color} **${t['symbol']}** {change}")

    update_text = f"更新于 {cache_age} 分钟前" if cache_age >= 0 else "首次加载"
    wsb_url = "https://sellthenews.org/wsb/daily?truthShowAll=1"
    st.caption(f"数据来源: [WSB市场情绪]({wsb_url}) · {update_text}")


# =============================================================================
# Subscription Tab
# =============================================================================

def render_subscription_tab():
    """Render the subscription management tab."""
    manager = get_subscription_manager(use_mock=Config.use_mock())

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📢 社交媒体订阅管理")
    with col2:
        add_btn = st.button("+ 新建订阅", type="primary", use_container_width=True)

    if add_btn or st.session_state.get("show_add_form"):
        st.session_state.show_add_form = True

        with st.form("add_subscription"):
            st.markdown("### 新建订阅")

            form_col1, form_col2 = st.columns(2)
            with form_col1:
                platform = st.selectbox(
                    "平台",
                    options=["twitter", "substack"],
                    format_func=lambda x: {"twitter": "𝕏 Twitter", "substack": "📰 Substack"}[x]
                )
                screen_name = st.text_input("账号名称", placeholder="如: elonmusk")

            with form_col2:
                keywords = st.text_input("过滤关键词 (逗号分隔)", placeholder="如: Tesla, FSD, AI")
                notify_email = st.text_input("通知邮箱 *", placeholder="analyst@example.com")

            submit_col1, submit_col2 = st.columns(2)
            with submit_col1:
                submitted = st.form_submit_button("创建订阅", type="primary", use_container_width=True)
            with submit_col2:
                cancelled = st.form_submit_button("取消", use_container_width=True)

            if submitted:
                if not screen_name or not notify_email:
                    st.error("账号名称和通知邮箱为必填项")
                else:
                    try:
                        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else None
                        manager.create_subscription(
                            platform=platform,
                            screen_name=screen_name,
                            filter_keywords=keyword_list,
                            notify_emails=[notify_email]
                        )
                        st.success(f"订阅 @{screen_name} 创建成功!")
                        st.session_state.show_add_form = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"创建失败: {e}")

            if cancelled:
                st.session_state.show_add_form = False
                st.rerun()

    st.divider()

    # List subscriptions
    try:
        result = manager.list_subscriptions()
        subscriptions = result.get("subscriptions", result.get("results", []))

        # Filter out YouTube subscriptions
        subscriptions = [s for s in subscriptions if s.get("platform") != "youtube"]

        if not subscriptions:
            st.info("暂无订阅，点击「新建订阅」添加")
        else:
            for sub_data in subscriptions:
                sub = manager.parse_subscription(sub_data)
                platform_icon = {"twitter": "𝕏", "substack": "📰"}.get(sub.platform, "📱")

                # 使用更紧凑的卡片式布局
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        # 状态标记 + 平台账号
                        if sub.status == "active":
                            status_badge = "🟢"
                        else:
                            status_badge = "⚪"
                        st.markdown(f"{status_badge} **{platform_icon} {sub.platform.title()}** · @{sub.screen_name}")

                    with col2:
                        if sub.filter_keywords:
                            keywords_text = ", ".join(sub.filter_keywords[:3])
                            if len(sub.filter_keywords) > 3:
                                keywords_text += f" +{len(sub.filter_keywords) - 3}"
                            st.caption(f"关键词: {keywords_text}")

                    with col3:
                        btn_label = "暂停" if sub.status == "active" else "启用"
                        if st.button(btn_label, key=f"toggle_{sub.id}", use_container_width=True):
                            try:
                                manager.toggle_subscription(sub.id)
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))

                    st.divider()

    except Exception as e:
        st.error(f"获取订阅列表失败: {e}")


# =============================================================================
# Main
# =============================================================================

def main():
    # Header
    st.markdown('<div class="main-header">📊 Fin Research Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">多 Agent 金融研究助手 · ReAct 推理 → 多源研究 → 多空辩论 → 投资决策</div>', unsafe_allow_html=True)

    # Market Sentiment
    with st.container():
        st.markdown("### 🎭 市场情绪")
        render_sentiment_panel()

    st.divider()

    # Sidebar
    with st.sidebar:
        st.header("🔧 配置")

        if Config.use_mock():
            st.caption("🎭 Demo 模式 · 预置数据")
        else:
            st.success("🚀 **生产模式**\n\n已连接真实数据源")

        st.divider()

        st.header("🤖 Agent 架构")
        st.markdown("""
        **Phase 0: ReAct 推理引擎**
        - 分析问题意图
        - 动态选择工具 (Tool)
        - 多步推理收集信息

        **Phase 1: 研究报告**
        - 多源信息整合
        - 按来源分类归档
        - 关键事实提取

        **Phase 2: 辩论团队**
        - 看多研究员 (Bull Analyst)
        - 看空研究员 (Bear Analyst)
        - 研究经理 (Moderator)

        **Phase 3: 决策 Agent**
        - 综合判断 + 置信度
        - 风险 & 催化剂分析
        """)

        st.divider()

        st.header("📚 数据源")
        for kb_name in KB_ID_TO_NAME.values():
            st.markdown(f"- {kb_name}")

    # Main content with tabs
    tab1, tab2, tab3 = st.tabs(["📊 研究分析", "📢 订阅管理", "ℹ️ 关于项目"])

    with tab1:
        # Query input
        col1, col2 = st.columns([3, 1])

        with col1:
            query = st.text_input(
                "输入你的研究问题",
                value=st.session_state.get("query", ""),
                placeholder="例如：Dell未来业绩怎么看？NVIDIA业绩会关键指引？",
                key="query_input"
            )

        with col2:
            analyze_btn = st.button("🚀 启动分析", type="primary", use_container_width=True)

        # Quick query buttons
        st.markdown("**快速提问：**")
        quick_cols = st.columns(4)
        quick_queries = [
            ("Dell业绩", "Dell未来业绩怎么看"),
            ("NVIDIA业绩会", "NVIDIA最新业绩会关键指引"),
            ("HBM扩产", "HBM产能扩张节奏"),
            ("AI服务器", "AI服务器市场竞争格局"),
        ]

        for i, (label, q) in enumerate(quick_queries):
            with quick_cols[i]:
                if st.button(label, use_container_width=True):
                    st.session_state.query = q
                    st.session_state.run_analysis = True
                    st.rerun()

        # Run analysis - triggered by button or quick query
        should_run = (analyze_btn and query) or st.session_state.get("run_analysis", False)
        if should_run:
            run_query = query or st.session_state.get("query", "")
            # Clear the trigger flag
            if "run_analysis" in st.session_state:
                del st.session_state["run_analysis"]
            if run_query:
                st.divider()
                run_agent_workflow(run_query)
            else:
                st.warning("请输入研究问题")
        elif analyze_btn and not query:
            st.warning("请输入研究问题")

    with tab2:
        render_subscription_tab()

    with tab3:
        render_about_tab()


def render_about_tab():
    """Render the About Project tab - synced with README v3.0."""
    # 一句话定位
    st.markdown("## 项目定位")
    st.markdown("""
    用 AI Agent 替代投研团队 **60% 的信息收集工作**：一次提问，自动从 5 类数据源收集信息、3轮结构化辩论、情景估值、输出带打分卡的投研简报。
    """)

    st.markdown("---")

    # 核心特性 v3.0
    st.markdown("## 核心特性（v3.0）")
    st.markdown("""
    | 特性 | 说明 |
    |------|------|
    | **3轮结构化辩论** | 开场→交叉质询→修正立场，加权多空比（strong=3/medium=2/weak=1） |
    | **信息充分度检查** | 6维度评分，<60%自动回退补充检索（最多1次），避免信息不足下的误判 |
    | **估值Agent** | 相对估值（P/E行业对比 + 历史分位）+ 三情景目标价 + 安全边际 |
    | **5维度决策打分卡** | 基本面30% / 估值25% / 催化剂20% / 风险15% / 动量10% |
    | **Smart Summary** | 结构化投研简报（终端文本 + JSON），适配飞书/Slack推送 |
    | **信号检测** | 11类信号模式匹配，分级为强/中/弱 |
    | **命中率记录** | JSONL持久化，3个月后自动回测，方向命中率 + 目标命中率统计 |
    """)

    st.markdown("---")

    # 场景创新性
    st.markdown("## 场景创新性")
    st.markdown("""
    **核心洞察**：投研的本质是信息差 + 判断力。AI 时代信息差消失，判断力成为稀缺资源——但研究员 60% 时间还在当"信息搬运工"。
    """)

    st.markdown("**我们不是做搜索引擎，是重构工作流：**")
    st.markdown("""
    | 维度 | 传统 AI 金融产品 | 本项目 |
    |------|-----------------|--------|
    | 架构 | 问题 → LLM → 答案 | 多源收集 → 3轮辩论 → 估值验证 → 打分决策 |
    | 定位 | AI 替代人 | AI 初级研究员，释放人的判断力 |
    | 输出 | 一个结论（黑盒） | 多空论点 + 打分卡 + 情景估值 + 来源追溯（白盒） |
    | 价值 | "给你答案" | "帮你看全，由你判断" |
    | 跟踪 | 无反馈闭环 | 3个月命中率回测，持续校准 |
    """)

    st.info("**Bull/Bear 辩论 + 交叉质询的认知价值**：投资决策最大的敌人是 confirmation bias。3轮辩论强制呈现双面观点 + 质询弱点 + 标注翻转条件，让决策者在充分信息下做判断。")

    st.markdown("---")

    # 系统架构
    st.markdown("## 系统架构（v3.0）")
    st.markdown("采用 **5 阶段 Multi-Agent Pipeline** 协作模式：")
    st.code("""
用户问题: "分析NVDA投资价值"
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Research Team (多源信息收集)                            │
│  5类数据源并行检索 → 关键事实提取 → 正负面标注                     │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 2: Debate Team (3轮结构化辩论)                             │
│  Round 1: 开场立论（Bull vs Bear）                                │
│  Round 2: 交叉质询（接受/反驳/追问）                              │
│  Round 3: 修正立场（翻转条件）                                    │
│  Moderator: 加权多空比 + 信息缺口 + 翻转触发条件                  │
│  ── 信息充分度检查（<60% 回退补充，最多1次）──                    │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 3: Valuation Agent (相对估值 + 情景分析)                    │
│  P/E vs 行业/历史 → 三情景目标价（Bull/Base/Bear）                │
│  加权目标价 + 安全边际评估                                        │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 4: Decision Agent (投资决策)                               │
│  建议(强烈买入→强烈卖出) + 置信度 + 风险 + 催化剂                 │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 5: Signal Detection + Scorecard + Smart Summary            │
│  信号分级（强/中/弱）→ 5维度打分卡 → 投研简报输出                 │
│  命中率记录系统（3个月后自动回测）                                 │
└─────────────────────────────────────────────────────────────────┘
    """, language=None)

    st.markdown("---")

    # 核心技术点
    st.markdown("## 核心技术点")
    st.markdown("""
    | 模块 | 设计要点 |
    |------|---------|
    | **统一 LLM Client** | OpenAI 兼容接口 + httpx 代理支持，支持多模型切换 |
    | **3轮辩论引擎** | Round1开场 → Round2交叉质询(accept/rebut/question) → Round3修正 + 加权比 |
    | **估值Agent** | 相对估值(P/E分位) + 三情景加权目标价，无DCF避免参数敏感 |
    | **充分度检查** | 6维评分(论点/事实/源多样性/证据质量)，阈值60%触发补充 |
    | **打分卡系统** | 5维度加权(基本面/估值/催化/风险/动量)，score→仓位映射 |
    | **信号检测** | 11类模式 + 正则匹配，分级推送策略 |
    | **命中率回测** | JSONL存储 + 90天自动评估，方向/目标两维度 |
    | **Graceful Degradation** | LLM 不可用时 fallback 到 mock 数据，保证 Demo 可用 |
    """)

    st.markdown("---")

    # 商业潜力
    st.markdown("## 商业潜力")
    st.markdown("""
    | 维度 | 判断 |
    |------|------|
    | **市场规模** | 买方投研团队人均年薪 50-100 万，效率提升 3 倍 = 巨大 ROI |
    | **需求强度** | 财报发布后 1 小时决策窗口，错过 = 错过 alpha，是刚需非 nice-to-have |
    | **时机** | LLM 推理能力刚好够用，但交叉人才稀缺，先发窗口打开 |
    | **壁垒** | 需要投研领域知识 + AI 架构能力的交叉，不是纯技术问题 |
    | **扩展** | 核心能力可横向复制到卖方研究、金融数据终端（Wind/Bloomberg）增值模块 |
    """)

    st.markdown("**目标用户路径**：买方投研团队（基金/资管）→ 卖方研究部门 → 金融数据服务商")

    st.info("**典型场景**: 某基金持仓 Dell，财报发布后，研究员需要在 1 小时内整合业绩会纪要、卖方研报、专家访谈、Twitter 舆情，形成多空观点对比，供基金经理决策。")

    st.markdown("---")

    # 技术栈
    st.markdown("## 技术栈")
    st.markdown("""
    | 层 | 选型 |
    |----|------|
    | 前端 | Streamlit |
    | LLM | Claude (通过 OpenAI 兼容接口) |
    | 知识库 | 自建 RAG API (5 类数据源) |
    | 架构 | Multi-Agent Pipeline (5 Phase) |
    | 部署 | Streamlit Cloud |
    """)


if __name__ == "__main__":
    main()
