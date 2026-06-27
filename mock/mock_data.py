"""Mock data for demo mode - pre-built responses for common queries."""

import sys
from pathlib import Path
from typing import Dict, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.bull_bear_analyzer import BullBearAnalysis, Viewpoint


# =============================================================================
# Mock Search Results for Demo Queries
# =============================================================================

MOCK_SEARCH_RESULTS = {
    "dell": [
        {
            "file_id": 1001,
            "title": "Dell Technologies FY25 Q3业绩说明会纪要",
            "source_type": "AlphaEngine",
            "date": "2025-03-15",
            "author": "Dell IR",
            "content": """Dell在AI服务器领域表现强劲，ISG收入同比增长34%达到115亿美元。
AI优化服务器pipeline达到38亿美元，环比增长50%。管理层上调全年AI服务器收入指引至150亿美元。
但传统PC业务持续承压，CSG收入同比下降8%。""",
            "snippet": "AI服务器pipeline达38亿美元，环比增50%，全年指引上调至150亿"
        },
        {
            "file_id": 1002,
            "title": "服务器产业链专家访谈 - AI Server供应链动态",
            "source_type": "久谦中台",
            "date": "2025-03-18",
            "author": "服务器行业专家",
            "content": """Dell在AI服务器市场份额提升明显，主要受益于与NVIDIA的深度合作。
但需要关注的风险：1）GPU供应仍然紧张，交付周期长；2）AI服务器毛利率低于传统服务器；
3）竞争加剧，HPE和联想都在抢市场。专家判断Dell短期受益但中长期竞争压力大。""",
            "snippet": "Dell AI服务器份额提升，但毛利率承压，中长期竞争压力大"
        },
        {
            "file_id": 1003,
            "title": "PC市场2025展望 - 换机周期延后",
            "source_type": "AceCampTech",
            "date": "2025-03-10",
            "author": "TMT研究团队",
            "content": """全球PC市场持续低迷，2024年出货量同比下降5%。企业换机周期因宏观不确定性延后。
AI PC虽然是新概念，但实际需求有限，渗透率不及预期。Dell作为企业PC主要供应商，
短期面临去库存压力，但长期看企业数字化趋势不变。""",
            "snippet": "PC市场低迷，AI PC渗透率不及预期，Dell面临去库存压力"
        },
        {
            "file_id": 1004,
            "title": "@MichaelDell关于AI战略的推文",
            "source_type": "Twitter推文",
            "date": "2025-03-20",
            "author": "MichaelDell",
            "content": """Just announced: Dell AI Factory now powers 85% of Fortune 100 companies'
AI infrastructure. The enterprise AI revolution is just beginning. $DELL""",
            "snippet": "Dell AI Factory覆盖85%财富100强企业AI基础设施"
        }
    ],

    "hbm": [
        {
            "file_id": 2001,
            "title": "HBM产业链深度调研 - 2025扩产计划",
            "source_type": "久谦中台",
            "date": "2025-03-12",
            "author": "存储行业专家",
            "content": """SK海力士2025年HBM产能计划扩产80%，主要用于HBM3E。三星计划扩产60%但良率仍有差距。
美光扩产较为保守，约40%。整体看HBM供需仍然紧张，价格维持高位。
专家预计2025年HBM3E占比将达到70%，HBM4预计2026年量产。""",
            "snippet": "SK海力士HBM扩产80%，三星60%，美光40%，供需仍紧张"
        },
        {
            "file_id": 2002,
            "title": "SK Hynix 2025 HBM Strategy Update",
            "source_type": "AlphaEngine",
            "date": "2025-03-08",
            "author": "SK Hynix IR",
            "content": """SK Hynix confirmed 2025 HBM capacity expansion of 80% YoY.
HBM3E now accounts for 60% of total HBM revenue. NVIDIA remains primary customer with
multi-year supply agreement. Company expects HBM to contribute 30% of total DRAM revenue by 2026.""",
            "snippet": "SK Hynix确认2025年HBM产能扩80%，HBM3E占收入60%"
        },
        {
            "file_id": 2003,
            "title": "存储芯片价格与供需分析",
            "source_type": "AceCampTech",
            "date": "2025-03-05",
            "author": "半导体研究团队",
            "content": """HBM价格持续上涨，HBM3E合约价环比上涨15%。主要驱动因素：
1）AI算力需求持续超预期；2）先进封装产能瓶颈；3）三大厂商扩产节奏不一。
风险点：如果AI资本开支放缓，HBM可能面临供过于求风险，但短期内概率较低。""",
            "snippet": "HBM3E价格环比涨15%，AI需求超预期，封装产能瓶颈"
        }
    ],

    "光模块": [
        {
            "file_id": 3001,
            "title": "光模块行业2025趋势展望",
            "source_type": "久谦中台",
            "date": "2025-03-14",
            "author": "光通信专家",
            "content": """800G光模块进入规模出货期，1.6T预计2025H2开始小批量。
中际旭创、新易盛等国内厂商份额持续提升，但面临美国关税风险。
技术路线上，LPO（线性直驱）渐成主流，可降低功耗20%。
专家判断光模块行业景气度将持续到2026年。""",
            "snippet": "800G规模出货，1.6T 2025H2小批量，LPO成主流技术路线"
        },
        {
            "file_id": 3002,
            "title": "AI数据中心光互联技术演进",
            "source_type": "AceCampTech",
            "date": "2025-03-11",
            "author": "数据中心研究团队",
            "content": """AI大模型训练推动数据中心互联带宽需求激增。800G向1.6T演进加速，
硅光技术在短距离场景渗透率提升。CPO（共封装光学）长期看好但短期成熟度不足。
国内厂商在成本和交付上有优势，但高端DSP芯片仍依赖进口。""",
            "snippet": "800G向1.6T演进加速，硅光渗透率提升，国内厂商成本优势明显"
        },
        {
            "file_id": 3003,
            "title": "光模块供应链专家访谈",
            "source_type": "久谦中台",
            "date": "2025-03-16",
            "author": "光模块行业专家",
            "content": """当前光模块产能利用率维持在85%以上，订单可见度达到6个月。
但需要关注的风险：1）下游云厂商资本开支节奏变化；2）美国对中国厂商的限制；
3）价格竞争加剧导致毛利率下滑。整体看2025年仍是景气年份。""",
            "snippet": "产能利用率85%+，订单可见度6个月，2025仍是景气年份"
        }
    ]
}


# =============================================================================
# Mock Bull/Bear Analysis Results
# =============================================================================

def get_mock_analysis(query: str, search_results: List[Dict]) -> BullBearAnalysis:
    """Get pre-built Bull/Bear analysis for demo queries."""

    query_lower = query.lower()

    # Dell analysis
    if "dell" in query_lower or "戴尔" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="AI服务器业务强劲增长，pipeline达38亿美元环比增50%，全年指引上调至150亿",
                    source="Dell FY25 Q3业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2025-03-15",
                    confidence="高"
                ),
                Viewpoint(
                    content="Dell AI Factory已覆盖85%财富100强企业AI基础设施，企业AI市场领先地位稳固",
                    source="@MichaelDell推文",
                    source_type="Twitter推文",
                    source_date="2025-03-20",
                    confidence="中"
                ),
                Viewpoint(
                    content="与NVIDIA深度合作，在AI服务器市场份额持续提升",
                    source="服务器产业链专家访谈",
                    source_type="久谦中台",
                    source_date="2025-03-18",
                    confidence="高"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="传统PC业务持续承压，CSG收入同比下降8%，AI PC渗透率不及预期",
                    source="PC市场2025展望",
                    source_type="AceCampTech",
                    source_date="2025-03-10",
                    confidence="高"
                ),
                Viewpoint(
                    content="AI服务器毛利率低于传统服务器，GPU供应紧张导致交付周期长",
                    source="服务器产业链专家访谈",
                    source_type="久谦中台",
                    source_date="2025-03-18",
                    confidence="高"
                ),
                Viewpoint(
                    content="竞争加剧，HPE、联想都在抢AI服务器市场，中长期竞争压力大",
                    source="服务器产业链专家访谈",
                    source_type="久谦中台",
                    source_date="2025-03-18",
                    confidence="中"
                ),
            ],
            synthesis="Dell在AI服务器领域表现亮眼，受益于与NVIDIA的深度合作和企业AI需求爆发。但传统PC业务持续拖累，且AI服务器毛利率较低、竞争加剧是中长期风险。综合来看，短期受益AI浪潮，但需关注业务结构优化进度。",
            overall_stance="中性偏多",
            key_factors=[
                "AI服务器pipeline增长和订单可见度",
                "传统PC业务何时见底",
                "AI服务器毛利率能否改善",
                "竞争格局变化"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("dell", [])
        )

    # HBM analysis
    if "hbm" in query_lower or "高带宽内存" in query_lower or "海力士" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="SK海力士2025年HBM产能扩产80%，三星60%，供需维持紧张，价格高位运行",
                    source="HBM产业链深度调研",
                    source_type="久谦中台",
                    source_date="2025-03-12",
                    confidence="高"
                ),
                Viewpoint(
                    content="HBM3E合约价环比上涨15%，AI算力需求持续超预期支撑价格",
                    source="存储芯片价格与供需分析",
                    source_type="AceCampTech",
                    source_date="2025-03-05",
                    confidence="高"
                ),
                Viewpoint(
                    content="SK Hynix与NVIDIA签订多年供应协议，HBM收入占比预计2026年达30%",
                    source="SK Hynix Strategy Update",
                    source_type="AlphaEngine",
                    source_date="2025-03-08",
                    confidence="高"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="三星HBM良率仍有差距，若追赶成功可能加剧供给压力",
                    source="HBM产业链深度调研",
                    source_type="久谦中台",
                    source_date="2025-03-12",
                    confidence="中"
                ),
                Viewpoint(
                    content="先进封装产能瓶颈可能限制HBM出货量，CoWoS产能紧张",
                    source="存储芯片价格与供需分析",
                    source_type="AceCampTech",
                    source_date="2025-03-05",
                    confidence="中"
                ),
                Viewpoint(
                    content="如果AI资本开支放缓，HBM可能面临供过于求风险",
                    source="存储芯片价格与供需分析",
                    source_type="AceCampTech",
                    source_date="2025-03-05",
                    confidence="低"
                ),
            ],
            synthesis="HBM市场受AI算力需求驱动，三大厂商扩产节奏明确（SK海力士80%、三星60%、美光40%），但供需仍然紧张，价格维持高位。SK海力士凭借与NVIDIA的深度绑定保持领先。主要风险在于封装产能瓶颈和远期AI需求不确定性。",
            overall_stance="看多",
            key_factors=[
                "AI算力资本开支节奏",
                "三星HBM良率追赶进度",
                "先进封装产能扩张速度",
                "HBM4量产时间表"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("hbm", [])
        )

    # 光模块 analysis
    if "光模块" in query_lower or "光通信" in query_lower or "transceiver" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="800G光模块进入规模出货期，1.6T预计2025H2小批量，行业景气度持续到2026年",
                    source="光模块行业2025趋势展望",
                    source_type="久谦中台",
                    source_date="2025-03-14",
                    confidence="高"
                ),
                Viewpoint(
                    content="产能利用率维持85%以上，订单可见度达到6个月，需求旺盛",
                    source="光模块供应链专家访谈",
                    source_type="久谦中台",
                    source_date="2025-03-16",
                    confidence="高"
                ),
                Viewpoint(
                    content="国内厂商在成本和交付上有优势，中际旭创、新易盛等份额持续提升",
                    source="AI数据中心光互联技术演进",
                    source_type="AceCampTech",
                    source_date="2025-03-11",
                    confidence="中"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="美国对中国厂商的限制风险，关税政策不确定性",
                    source="光模块行业2025趋势展望",
                    source_type="久谦中台",
                    source_date="2025-03-14",
                    confidence="中"
                ),
                Viewpoint(
                    content="价格竞争加剧可能导致毛利率下滑",
                    source="光模块供应链专家访谈",
                    source_type="久谦中台",
                    source_date="2025-03-16",
                    confidence="中"
                ),
                Viewpoint(
                    content="高端DSP芯片仍依赖进口，供应链自主可控存在短板",
                    source="AI数据中心光互联技术演进",
                    source_type="AceCampTech",
                    source_date="2025-03-11",
                    confidence="中"
                ),
            ],
            synthesis="光模块行业受AI数据中心建设驱动，800G规模出货、1.6T即将量产，景气度有望持续到2026年。国内厂商凭借成本和交付优势份额提升。但需关注地缘政治风险、价格竞争和核心芯片自主可控问题。",
            overall_stance="看多",
            key_factors=[
                "云厂商AI资本开支节奏",
                "1.6T光模块量产进度",
                "美国关税和出口限制政策",
                "LPO/CPO技术路线演进"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("光模块", [])
        )

    # Default fallback
    return BullBearAnalysis(
        query=query,
        bull_points=[
            Viewpoint(
                content="暂无明确看多观点，需要更多数据支持",
                source="系统提示",
                source_type="",
                source_date="",
                confidence="低"
            )
        ],
        bear_points=[
            Viewpoint(
                content="暂无明确看空观点，需要更多数据支持",
                source="系统提示",
                source_type="",
                source_date="",
                confidence="低"
            )
        ],
        synthesis="当前问题没有预置的分析数据，请尝试其他问题如：Dell未来业绩、HBM扩产比例、光模块行业趋势",
        overall_stance="中性",
        key_factors=["请尝试预置问题获取完整分析"],
        sources_used=search_results or []
    )


def get_mock_search_results(query: str) -> List[Dict]:
    """Get mock search results for a query."""
    query_lower = query.lower()

    if "dell" in query_lower or "戴尔" in query_lower:
        return MOCK_SEARCH_RESULTS["dell"]
    elif "hbm" in query_lower or "海力士" in query_lower or "扩产" in query_lower:
        return MOCK_SEARCH_RESULTS["hbm"]
    elif "光模块" in query_lower or "光通信" in query_lower:
        return MOCK_SEARCH_RESULTS["光模块"]
    else:
        return []
