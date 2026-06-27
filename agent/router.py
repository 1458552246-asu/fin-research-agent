"""Intent router - recognizes user intent and routes to appropriate KBs."""

from typing import List, Tuple
from .config import DEFAULT_KB_IDS, KB_KEYWORD_MAP


# Intent patterns with keywords and KB priorities
INTENT_PATTERNS = {
    "earnings_call": {
        "keywords": [
            "transcript", "earnings", "业绩会", "纪要", "电话会",
            "conference call", "业绩说明会", "财报", "quarterly",
            "季度业绩", "q1", "q2", "q3", "q4", "年报",
        ],
        "kb_priority": [28, 17, 19],  # AlphaEngine -> 久谦 -> AceCamp
        "description": "业绩会/财报查询",
    },
    "expert_interview": {
        "keywords": [
            "expert", "专家", "访谈", "interview", "专家访谈",
            "调研纪要", "1x1", "专家交流", "产业链调研", "草根调研",
        ],
        "kb_priority": [17, 19, 28],  # 久谦 -> AceCamp -> AlphaEngine
        "description": "专家访谈",
    },
    "social_media": {
        "keywords": [
            "twitter", "tweet", "推文", "推特", "最新消息",
            "最新动态", "社交媒体", "substack", "newsletter",
        ],
        "kb_priority": [18, 21, 19],  # Twitter -> Substack -> AceCamp
        "description": "社交媒体/最新动态",
    },
    "research_report": {
        "keywords": [
            "report", "研报", "研究报告", "深度报告", "行业报告",
            "分析", "coverage", "评级", "目标价", "买入", "卖出",
        ],
        "kb_priority": [28, 19, 17],  # AlphaEngine -> AceCamp -> 久谦
        "description": "研报/研究分析",
    },
    "company_outlook": {
        "keywords": [
            "怎么看", "outlook", "展望", "未来", "前景",
            "业绩", "预期", "guidance", "增长", "趋势",
        ],
        "kb_priority": [28, 17, 19],  # AlphaEngine -> 久谦 -> AceCamp
        "description": "公司展望分析",
    },
    "industry_trend": {
        "keywords": [
            "行业", "industry", "趋势", "trend", "景气度",
            "周期", "格局", "产业链", "渗透率", "市场规模",
        ],
        "kb_priority": [17, 19, 28],  # 久谦 -> AceCamp -> AlphaEngine
        "description": "行业趋势",
    },
    "data_comparison": {
        "keywords": [
            "对比", "compare", "vs", "排名", "表格",
            "汇总", "各家", "分别", "数据", "指标",
        ],
        "kb_priority": DEFAULT_KB_IDS,
        "description": "数据对比/汇总",
    },
}


class IntentRouter:
    """Routes user queries to appropriate knowledge bases based on intent."""

    def __init__(self):
        self._patterns = INTENT_PATTERNS

    def detect_intent(self, query: str) -> Tuple[str, List[int], str]:
        """Detect user intent and return (intent_name, kb_priority_list, description).

        Returns:
            Tuple of (intent_name, list_of_kb_ids, human_readable_description)
        """
        query_lower = query.lower().strip()

        # Check for explicit KB specification first
        for keyword, kb_id in KB_KEYWORD_MAP.items():
            if keyword in query_lower:
                return "explicit_kb", [kb_id], f"指定知识库查询"

        # Score each intent
        scores = {}
        for intent_name, config in self._patterns.items():
            score = sum(2 for kw in config["keywords"] if kw.lower() in query_lower)
            if score > 0:
                scores[intent_name] = score

        # Return highest scoring intent
        if scores:
            best_intent = max(scores, key=scores.get)
            config = self._patterns[best_intent]
            return best_intent, config["kb_priority"], config["description"]

        # Default: general query
        return "general", DEFAULT_KB_IDS.copy(), "综合查询"


# Company name expansion for better search coverage
COMPANY_ALIASES = {
    "dell": ["Dell Technologies", "Dell", "DELL", "dell", "戴尔"],
    "nvidia": ["NVIDIA", "Nvidia", "NVDA", "nvda", "英伟达", "老黄"],
    "apple": ["Apple", "AAPL", "aapl", "苹果"],
    "microsoft": ["Microsoft", "MSFT", "msft", "微软"],
    "google": ["Google", "Alphabet", "GOOGL", "GOOG", "谷歌"],
    "meta": ["Meta", "META", "Facebook", "FB", "脸书"],
    "amazon": ["Amazon", "AMZN", "amzn", "亚马逊"],
    "tesla": ["Tesla", "TSLA", "tsla", "特斯拉"],
    "amd": ["AMD", "Advanced Micro Devices", "amd", "超威"],
    "intel": ["Intel", "INTC", "intc", "英特尔"],
    "tsmc": ["TSMC", "台积电", "TSM", "Taiwan Semiconductor"],
    "samsung": ["Samsung", "三星", "SSNLF"],
    "sk hynix": ["SK Hynix", "SK海力士", "海力士", "hynix"],
    "micron": ["Micron", "MU", "美光"],
}


def expand_company_names(query: str) -> List[str]:
    """Expand company names to all known variants for better search."""
    query_lower = query.lower()
    expanded = [query]

    for key, aliases in COMPANY_ALIASES.items():
        if key in query_lower or any(a.lower() in query_lower for a in aliases):
            # Add OR-joined variants
            or_query = " OR ".join(f'"{a}"' for a in aliases)
            expanded.append(or_query)
            break

    return expanded
