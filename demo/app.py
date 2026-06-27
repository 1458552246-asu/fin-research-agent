"""
Fin Research Agent - Streamlit Demo Application

A multi-source financial research assistant with Bull/Bear analysis.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.config import Config, KB_ID_TO_NAME
from agent.router import IntentRouter, expand_company_names
from agent.bull_bear_analyzer import BullBearAnalyzer
from agent.source_tracer import SourceTracer
from mock.mock_data import get_mock_search_results, get_mock_analysis

# Page config
st.set_page_config(
    page_title="Fin Research Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
        margin-bottom: 2rem;
    }
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
    .source-tag {
        background-color: #e3f2fd;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-right: 8px;
    }
    .confidence-high { color: #2e7d32; font-weight: bold; }
    .confidence-mid { color: #f57c00; }
    .confidence-low { color: #757575; }
    .synthesis-box {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
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
</style>
""", unsafe_allow_html=True)


def get_stance_class(stance: str) -> str:
    """Get CSS class for stance badge."""
    if "多" in stance:
        return "stance-bullish"
    elif "空" in stance:
        return "stance-bearish"
    return "stance-neutral"


def get_confidence_class(confidence: str) -> str:
    """Get CSS class for confidence level."""
    if confidence == "高":
        return "confidence-high"
    elif confidence == "中":
        return "confidence-mid"
    return "confidence-low"


def main():
    # Header
    st.markdown('<div class="main-header">📊 Fin Research Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">多源异构金融研究助手 · Bull/Bear 结构化分析</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("🔧 配置")

        # Demo mode indicator
        if Config.use_mock():
            st.info("🎭 **Demo 模式**\n\n使用预置数据演示，支持以下问题：\n- Dell未来业绩怎么看\n- HBM扩产比例\n- 光模块行业趋势")
        else:
            st.success("🚀 **生产模式**\n\n已连接真实数据源")

        st.divider()

        st.header("📚 数据源")
        for kb_id, kb_name in KB_ID_TO_NAME.items():
            st.markdown(f"- {kb_name}")

        st.divider()

        st.header("🎯 支持的意图")
        intents = ["业绩会/财报", "专家访谈", "研报分析", "行业趋势", "公司展望", "数据对比"]
        for intent in intents:
            st.markdown(f"- {intent}")

        st.divider()

        st.markdown("---")
        st.markdown("**技术架构**")
        st.markdown("""
        1. 意图识别 + KB路由
        2. 两步检索（宽+精）
        3. Bull/Bear 分析
        4. 来源溯源
        """)

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        # Query input
        query = st.text_input(
            "输入你的研究问题",
            placeholder="例如：Dell未来业绩怎么看？HBM扩产比例？光模块行业趋势？",
            key="query_input"
        )

        # Quick query buttons
        st.markdown("**快速提问：**")
        quick_cols = st.columns(3)
        with quick_cols[0]:
            if st.button("Dell未来业绩怎么看", use_container_width=True):
                st.session_state.query_input = "Dell未来业绩怎么看"
                st.rerun()
        with quick_cols[1]:
            if st.button("HBM扩产比例", use_container_width=True):
                st.session_state.query_input = "HBM扩产比例"
                st.rerun()
        with quick_cols[2]:
            if st.button("光模块行业趋势", use_container_width=True):
                st.session_state.query_input = "光模块行业趋势"
                st.rerun()

    with col2:
        analyze_btn = st.button("🔍 开始分析", type="primary", use_container_width=True)

    # Process query
    if analyze_btn and query:
        with st.spinner("正在分析..."):
            # Initialize components
            router = IntentRouter()
            analyzer = BullBearAnalyzer()
            tracer = SourceTracer()

            # Step 1: Intent detection
            intent, kb_ids, intent_desc = router.detect_intent(query)

            # Step 2: Search (mock in demo mode)
            search_results = get_mock_search_results(query)

            # Step 3: Bull/Bear analysis
            analysis = analyzer.analyze(query, search_results, use_mock=Config.use_mock())

            # Display results
            st.divider()

            # Intent and routing info
            with st.expander("🎯 意图识别 & 知识库路由", expanded=False):
                st.markdown(f"**识别意图**: {intent_desc}")
                st.markdown(f"**优先知识库**: {', '.join(KB_ID_TO_NAME.get(k, str(k)) for k in kb_ids[:3])}")
                expanded = expand_company_names(query)
                if len(expanded) > 1:
                    st.markdown(f"**Query扩展**: {expanded[1]}")

            # Bull/Bear Analysis
            st.subheader("📊 多空观点分析")

            # Stance badge
            stance_class = get_stance_class(analysis.overall_stance)
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <strong>综合判断：</strong>
                <span class="stance-badge {stance_class}">{analysis.overall_stance}</span>
            </div>
            """, unsafe_allow_html=True)

            # Two columns for Bull/Bear
            bull_col, bear_col = st.columns(2)

            with bull_col:
                st.markdown("### 🐂 看多论点")
                for point in analysis.bull_points:
                    conf_class = get_confidence_class(point.confidence)
                    st.markdown(f"""
                    <div class="bull-box">
                        <div style="margin-bottom: 8px;">{point.content}</div>
                        <div>
                            <span class="source-tag">{point.source_type}</span>
                            <span style="color: #666; font-size: 0.85rem;">{point.source}</span>
                            <span class="{conf_class}" style="float: right;">可信度: {point.confidence}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with bear_col:
                st.markdown("### 🐻 看空论点")
                for point in analysis.bear_points:
                    conf_class = get_confidence_class(point.confidence)
                    st.markdown(f"""
                    <div class="bear-box">
                        <div style="margin-bottom: 8px;">{point.content}</div>
                        <div>
                            <span class="source-tag">{point.source_type}</span>
                            <span style="color: #666; font-size: 0.85rem;">{point.source}</span>
                            <span class="{conf_class}" style="float: right;">可信度: {point.confidence}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Synthesis
            st.markdown(f"""
            <div class="synthesis-box">
                <strong>⚖️ 综合分析</strong>
                <p style="margin-top: 0.5rem;">{analysis.synthesis}</p>
            </div>
            """, unsafe_allow_html=True)

            # Key factors
            st.markdown("**🔑 关键影响因素**")
            for factor in analysis.key_factors:
                st.markdown(f"- {factor}")

            # Sources
            st.divider()
            with st.expander("📑 来源引用", expanded=True):
                sources = tracer.format_sources(analysis.sources_used)
                grouped = tracer.group_by_type(sources)

                for source_type, items in grouped.items():
                    st.markdown(f"**{source_type}**")
                    for item in items:
                        st.markdown(f"""
                        - {item['description']}
                          > {item['snippet']}
                        """)

    elif analyze_btn and not query:
        st.warning("请输入研究问题")


if __name__ == "__main__":
    main()
