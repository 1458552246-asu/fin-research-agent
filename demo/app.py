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
from agent.orchestrator import Orchestrator
from agent.models import (
    ResearchReport, DebateResult, Decision,
    Recommendation, Sentiment, WorkflowState
)
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
            elif is_mock:
                st.markdown("📋 *Demo 模式 - 模拟数据*")

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
            elif is_mock:
                st.markdown("📋 *Demo 模式 - 模拟数据*")


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

    # Phase 1: Research
    with st.status("📋 Phase 1: 研究团队收集信息...", expanded=True) as status:
        st.write("🔬 基本面分析师检索 AlphaEngine (业绩会/研报)...")
        st.write("🏭 产业链分析师检索 专家访谈...")
        st.write("📱 情绪分析师检索 Twitter/Substack/AceCamp...")

        research_report = orchestrator.research_team.research(query, update_progress)

        st.write(f"✅ 找到 {research_report.total_sources_found} 条相关信息")
        status.update(label="✅ Phase 1 完成: 信息收集", state="complete")

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
    st.markdown('<div class="sub-header">多 Agent 金融研究助手 · 研究团队 → 多空辩论 → 投资决策</div>', unsafe_allow_html=True)

    # Market Sentiment
    with st.container():
        st.markdown("### 🎭 市场情绪")
        render_sentiment_panel()

    st.divider()

    # Sidebar
    with st.sidebar:
        st.header("🔧 配置")

        if Config.use_mock():
            st.info("🎭 **Demo 模式**\n\n使用预置数据演示")
        else:
            st.success("🚀 **生产模式**\n\n已连接真实数据源")

        st.divider()

        st.header("🤖 Agent 架构")
        st.markdown("""
        **Phase 1: 研究团队**
        - 基本面分析师 (AlphaEngine)
        - 产业链分析师 (专家访谈)
        - 情绪分析师 (Twitter/Substack)

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
                    st.rerun()

        # Run analysis
        if analyze_btn and query:
            st.divider()
            run_agent_workflow(query)
        elif analyze_btn and not query:
            st.warning("请输入研究问题")

    with tab2:
        render_subscription_tab()

    with tab3:
        render_about_tab()


def render_about_tab():
    """Render the About Project tab with architecture and innovation highlights."""
    st.markdown("## 项目简介")
    st.markdown("""
    **Fin Research Agent** 是一个面向专业投研团队的金融数据分析 Agent，对接业绩会纪要、专家访谈、研报、社交媒体等多源数据，
    通过意图识别自动路由到最相关的信息源，用两步检索策略解决金融文档检索难题，并对多源信息做交叉验证、矛盾标注和时效性判断，
    最终以来源可追溯的方式输出结论，形成可沉淀的研究底稿。
    """)

    st.markdown("---")

    # 核心痛点
    st.markdown("## 解决的核心痛点")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **专业投研团队的困境**
        - ❌ **信息极度分散**: 业绩会在一个平台、专家观点在另一个平台、社交媒体又在别处
        - ❌ **效率低且易遗漏**: 多渠道切换、人工比对，关键信息容易遗漏
        - ❌ **时效性风险**: 上季度结论可能已被最新业绩推翻
        - ❌ **矛盾难处理**: 不同来源判断相反，缺乏系统化处理手段
        """)
    with col2:
        st.markdown("""
        **我们的方案**
        - ✅ **5 类数据源统一检索**: 一次对话完成全流程
        - ✅ **意图识别 + 智能路由**: 自动选择最佳数据源
        - ✅ **两步检索策略**: 宽召回 + 精准回答
        - ✅ **矛盾标注 + 交叉验证**: 系统化处理信息冲突
        - ✅ **来源可追溯**: 形成可沉淀的研究底稿
        """)

    st.markdown("---")

    # 为什么是 Agent
    st.markdown("## 为什么是 AI Agent？")
    st.markdown("""
    这个场景天然需要 Agent 能力——**不是单轮问答，而是需要自主规划检索路径、跨多个数据源执行操作、对结果做推理整合**。
    """)

    why_col1, why_col2 = st.columns(2)
    with why_col1:
        st.markdown("""
        **传统搜索工具**
        - 只能逐个平台查询
        - 需要人工判断去哪查
        - 结果需要人工比对
        - 无法处理信息冲突
        """)
    with why_col2:
        st.markdown("""
        **AI Agent**
        - 一次对话完成全流程
        - 自动识别意图，路由到最佳数据源
        - 自动交叉验证，标注矛盾
        - 结构化输出多空观点，辅助决策
        """)

    st.info("**Agent 完整决策链路**: 判断意图 → 多源检索 → 交叉验证 → 矛盾标注 → 结构化输出")

    st.markdown("---")

    # 技术架构图
    st.markdown("## Multi-Agent 架构")
    st.markdown("采用 **3 阶段 7 Agent** 协作模式，模拟真实投研团队工作流：")
    st.code("""
┌──────────────────────────────────────────────────────────────────────┐
│                      Orchestrator (工作流编排)                        │
├──────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │
│  │ Research    │  │ Debate      │  │ Decision    │                   │
│  │ Team        │→│ Team        │→│ Agent       │                   │
│  │ (3 Agents)  │  │ (3 Agents)  │  │ (1 Agent)   │                   │
│  └─────────────┘  └─────────────┘  └─────────────┘                   │
│                                                                      │
│  Phase 1: 研究团队          Phase 2: 辩论团队        Phase 3: 决策     │
│  - 基本面分析师             - 看多研究员            - 综合判断        │
│  - 产业链分析师             - 看空研究员            - 风险分析        │
│  - 情绪分析师               - 研究经理              - 置信度评估      │
└──────────────────────────────────────────────────────────────────────┘
    """, language=None)

    st.markdown("---")

    # 核心创新点
    st.markdown("## 核心创新点")

    inno_col1, inno_col2 = st.columns(2)
    with inno_col1:
        st.markdown("""
        ### 1. 多源异构数据融合
        对接 **5 类金融信息源**：
        - 专家访谈（一手信息）
        - AlphaEngine（研报/业绩会）
        - Twitter（实时舆情）
        - Substack（深度 Newsletter）
        - AceCampTech（社区调研）

        ### 2. 两步检索策略
        解决金融文档「标题与内容弱关联」的检索难题：
        - **Stage 1**: 宽召回，最大化召回相关文档
        - **Stage 2**: 精准回答，定位答案
        """)

    with inno_col2:
        st.markdown("""
        ### 3. 意图识别 + 智能路由
        根据问题类型自动选择最优数据源：
        - 业绩会查询 → AlphaEngine
        - 专家观点 → 专家访谈
        - 行业趋势 → 专家访谈 + AceCamp
        - 实时舆情 → Twitter + Substack

        ### 4. 矛盾识别与交叉验证
        - 时效性判断：标注过时结论
        - 矛盾标注：明确标注分歧点
        - 交叉验证：多源信息互相印证
        """)

    st.markdown("---")

    # 目标用户
    st.markdown("## 目标用户")

    st.markdown("### 核心用户：买方投研团队（资管/基金公司）")
    st.markdown("""
    | 维度 | 内容 |
    |------|------|
    | **谁** | 基金公司/资管公司的研究员、分析师、基金经理助理 |
    | **什么情况下** | 投资决策前的信息收集、持仓公司定期跟踪、行业专题研究 |
    | **干什么** | 快速整合业绩会、专家访谈、研报、舆情等多源信息，识别市场分歧点，形成可溯源的研究底稿 |
    | **核心价值** | 研究效率提升 3-5 倍，避免遗漏关键信息，降低决策失误 |
    """)
    st.info("**典型场景**: 某基金持仓 Dell，财报发布后，研究员需要在 1 小时内整合业绩会纪要、卖方研报、专家访谈、Twitter 舆情，形成多空观点对比，供基金经理决策。")

    st.markdown("### 次要用户：卖方研究部门（券商/投行）")
    st.markdown("""
    | 维度 | 内容 |
    |------|------|
    | **谁** | 券商研究所的行业研究员 |
    | **什么情况下** | 撰写深度研报前、覆盖新公司时、行业重大事件发生时 |
    | **干什么** | 快速了解市场已有观点、识别观点分歧、找到差异化切入点 |
    | **核心价值** | 缩短研报准备周期，提供差异化观点依据 |
    """)

    st.markdown("### 潜在用户：金融数据服务商")
    st.markdown("""
    Wind/Bloomberg/同花顺等金融信息终端，可将 Agent 能力作为增值模块嵌入现有产品，提升竞争力。
    """)

    st.markdown("---")

    # 技术栈
    st.markdown("## 技术栈")
    st.markdown("""
    | 组件 | 技术选型 |
    |------|----------|
    | 前端 | Streamlit |
    | LLM | Claude (Anthropic) |
    | 知识库 | 自建向量检索 |
    | 架构模式 | Multi-Agent Orchestration |
    """)


if __name__ == "__main__":
    main()
