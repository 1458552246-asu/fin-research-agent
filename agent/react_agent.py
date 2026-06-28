"""
ReAct Agent - Reasoning + Acting Engine.

Implements the Thought -> Action -> Observation loop for intelligent
information gathering. The agent analyzes the query, selects appropriate
tools, executes them, and decides when it has enough information.

Supports both real LLM-driven reasoning and mock mode for demos.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import json
import re

from .tools import BaseTool, ToolResult, get_all_tools, get_tool_by_name, get_tools_description
from .config import Config


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class AgentStep:
    """A single step in the ReAct reasoning loop."""
    step_num: int
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: str


@dataclass
class AgentOutput:
    """Final output from the ReAct Agent."""
    query: str
    steps: List[AgentStep] = field(default_factory=list)
    final_answer: str = ""
    collected_documents: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True


# =============================================================================
# Mock Reasoning Chains (for Demo Mode)
# =============================================================================

def _get_mock_reasoning_chain(query: str) -> List[AgentStep]:
    """Generate pre-built reasoning chains for demo mode."""
    query_lower = query.lower()

    # NVIDIA / GPU related
    if any(kw in query_lower for kw in ["nvidia", "nvda", "英伟达", "黄仁勋"]):
        return [
            AgentStep(
                step_num=1,
                thought="User is asking about NVIDIA. I should first search the knowledge base for earnings call transcripts and research reports to get fundamental data.",
                action="kb_search",
                action_input={"query": "NVIDIA earnings revenue guidance", "source_filter": "alpha_engine"},
                observation="Found 2 documents: NVIDIA FY2028 Q1 earnings call (revenue $30B+, data center $26.3B +73% YoY), GPU pricing analysis report."
            ),
            AgentStep(
                step_num=2,
                thought="Good fundamental data found. Now I need supply chain perspective - let me search expert interviews for insights on Blackwell production and capacity constraints.",
                action="kb_search",
                action_input={"query": "NVIDIA Blackwell supply chain capacity", "source_filter": "expert_interview"},
                observation="Found 1 document: Supply chain expert interview - Blackwell yield at 85%, CoWoS is main bottleneck, supply tight through 2026H1."
            ),
            AgentStep(
                step_num=3,
                thought="I have fundamental and supply chain data. Let me also check social media sentiment to understand market mood and any contrarian signals.",
                action="kb_search",
                action_input={"query": "NVIDIA AI infrastructure", "source_filter": "social_media"},
                observation="Found 2 documents: Jensen Huang tweet about sovereign AI demand from 30+ countries; GPU market competition analysis from AceCampTech."
            ),
            AgentStep(
                step_num=4,
                thought="I now have comprehensive multi-source coverage: earnings data, supply chain expert views, and social sentiment. Let me check current market sentiment to complete the picture.",
                action="market_sentiment",
                action_input={},
                observation="Market Sentiment: Bullish 62% / Bearish 38%. Hot topics: NVIDIA earnings beat, AI infrastructure spending, Fed rate expectations."
            ),
        ]

    # Dell related
    if any(kw in query_lower for kw in ["dell", "戴尔"]):
        return [
            AgentStep(
                step_num=1,
                thought="User is asking about Dell. I'll start with earnings data to understand the ISG (server) business performance and AI server traction.",
                action="kb_search",
                action_input={"query": "Dell ISG revenue AI server", "source_filter": "alpha_engine"},
                observation="Found 1 document: Dell FY26 Q1 earnings - ISG revenue +42% to $12.8B, AI server backlog $4.2B (+25% QoQ), but ISG margin dropped to 18.5%."
            ),
            AgentStep(
                step_num=2,
                thought="The margin decline is concerning. Let me get expert perspective on Dell's competitive position and whether the margin pressure is structural or temporary.",
                action="kb_search",
                action_input={"query": "Dell AI server margin competition", "source_filter": "expert_interview"},
                observation="Found 1 document: Expert interview - Dell's AI server share growing via NVIDIA partnership, but margins lower than traditional servers. HPE and Lenovo competing aggressively."
            ),
            AgentStep(
                step_num=3,
                thought="I have the bull case (revenue growth, AI server demand) and bear case (margin pressure, competition). Let me also check the PC business outlook since it's important for Dell.",
                action="kb_search",
                action_input={"query": "Dell PC AI PC market outlook", "source_filter": "all"},
                observation="Found 2 documents: AI PC market analysis (enterprise refresh cycle starting, Dell CSG may bottom in H2), Michael Dell tweet about AI Factory powering 85% of Fortune 100."
            ),
        ]

    # HBM related
    if any(kw in query_lower for kw in ["hbm", "海力士", "扩产", "高带宽"]):
        return [
            AgentStep(
                step_num=1,
                thought="User is asking about HBM capacity expansion. I should first look at SK Hynix earnings for production data and expansion plans.",
                action="kb_search",
                action_input={"query": "SK Hynix HBM production capacity expansion", "source_filter": "alpha_engine"},
                observation="Found 1 document: SK Hynix 2026 Q1 earnings - HBM revenue +320% YoY, 35% of DRAM revenue, 80% capacity expansion planned for 2026."
            ),
            AgentStep(
                step_num=2,
                thought="Good production data. Now I need technical perspective on yield challenges and competition from Samsung. Let me search expert interviews.",
                action="kb_search",
                action_input={"query": "HBM yield HBM4 technology competition Samsung", "source_filter": "expert_interview"},
                observation="Found 1 document: Industry expert interview - HBM3E yield at 80-85%, HBM4 requires Hybrid Bonding (new process), mass production earliest 2027. SK Hynix leads Samsung by 6-9 months."
            ),
            AgentStep(
                step_num=3,
                thought="I have supply-side data. Let me check demand-side signals and pricing trends from social/research sources.",
                action="kb_search",
                action_input={"query": "HBM demand pricing supply", "source_filter": "social_media"},
                observation="Found 2 documents: Twitter analysis - HBM supply-demand gap widening, contract price +8-10% QoQ; Substack deep dive - HBM is most certain growth point in memory industry."
            ),
        ]

    # KKR / Alternative Asset Management
    if any(kw in query_lower for kw in ["kkr", "apollo", "blackstone", "资管", "另类"]):
        return [
            AgentStep(
                step_num=1,
                thought="User is asking about alternative asset managers. I should compare KKR, Apollo, and Blackstone's latest earnings to understand relative performance.",
                action="kb_search",
                action_input={"query": "KKR Apollo Blackstone", "source_filter": "all"},
                observation="Found 3 documents: KKR (FRE $1.23B +18%, AUM $601B), Apollo (FRE $520M +12%, AUM $671B), Blackstone (FRE $1.35B +15%, AUM $1.1T)."
            ),
            AgentStep(
                step_num=2,
                thought="Good financial comparison. Let me get industry expert perspective on competitive dynamics and outlook.",
                action="kb_search",
                action_input={"query": "资管行业", "source_filter": "expert_interview"},
                observation="Found 1 document: Expert interview - KKR fastest growth, Apollo strongest in credit, Blackstone largest scale. Private credit and infrastructure are key growth drivers. M&A expected to recover H2 2026."
            ),
            AgentStep(
                step_num=3,
                thought="I have sufficient data to compare the three firms. The key differentiators are clear: KKR (growth), Apollo (credit/insurance synergy), Blackstone (scale/brand).",
                action="market_sentiment",
                action_input={},
                observation="Market Sentiment: Bullish 58% / Bearish 42%. Financial sector sentiment neutral to slightly positive."
            ),
        ]

    # Tesla / FSD / xAI
    if any(kw in query_lower for kw in ["tesla", "特斯拉", "musk", "马斯克", "fsd", "xai"]):
        return [
            AgentStep(
                step_num=1,
                thought="User is asking about Tesla. Let me search for the latest earnings data including FSD progress and Robotaxi timeline.",
                action="kb_search",
                action_input={"query": "Tesla earnings FSD Robotaxi", "source_filter": "alpha_engine"},
                observation="Found 1 document: Tesla 2026Q1 earnings - Auto revenue -5%, margin 16.8%, FSD V13 reached 3B miles, Robotaxi targeting end of 2026 in select cities."
            ),
            AgentStep(
                step_num=2,
                thought="The auto business is declining while FSD/Robotaxi is the key narrative. Let me get expert assessment of FSD's actual technical level.",
                action="kb_search",
                action_input={"query": "Tesla FSD autonomous driving level assessment", "source_filter": "expert_interview"},
                observation="Found 1 document: Expert interview - FSD V13 shows clear improvement but still gap to L4. Extreme weather performance poor, intervention rate higher than Waymo. Robotaxi timeline likely delayed to mid-2026."
            ),
            AgentStep(
                step_num=3,
                thought="There's a clear divergence between Musk's narrative and expert assessment. Let me check social media and valuation analysis for market positioning.",
                action="kb_search",
                action_input={"query": "Tesla valuation FSD Robotaxi xAI", "source_filter": "all"},
                observation="Found 2 documents: Musk tweet about FSD V13.2 and Grok 3; Valuation analysis shows 50% of Tesla's value depends on FSD/Robotaxi - significant downside risk if delayed."
            ),
        ]

    # TSMC / CoWoS
    if any(kw in query_lower for kw in ["tsmc", "台积电", "cowos", "封装"]):
        return [
            AgentStep(
                step_num=1,
                thought="User is asking about TSMC's advanced packaging. Let me search for CoWoS capacity data from earnings.",
                action="kb_search",
                action_input={"query": "TSMC CoWoS capacity expansion 2026", "source_filter": "alpha_engine"},
                observation="Found 1 document: TSMC 2026Q1 earnings - CoWoS capacity doubling in 2026 but still can't meet demand, orders visible through 2027."
            ),
            AgentStep(
                step_num=2,
                thought="Management guidance is optimistic. Let me get expert view on actual execution risk.",
                action="kb_search",
                action_input={"query": "CoWoS packaging supply bottleneck expansion", "source_filter": "expert_interview"},
                observation="Found 1 document: Expert interview - Actual expansion may only reach 80-90%, constrained by equipment delivery delays and skilled worker shortage. Tight supply through end of 2026."
            ),
            AgentStep(
                step_num=3,
                thought="Clear picture: strong demand, dominant market position, but execution risk on capacity expansion. Let me check competitive landscape.",
                action="kb_search",
                action_input={"query": "CoWoS competition market share Samsung", "source_filter": "all"},
                observation="Found 2 documents: CoWoS market share >90%, Samsung 2+ years behind; Morris Chang tweet about unprecedented AI demand."
            ),
        ]

    # Anthropic / Claude
    if any(kw in query_lower for kw in ["anthropic", "claude"]):
        return [
            AgentStep(
                step_num=1,
                thought="User is asking about Anthropic. Let me search for the latest funding and valuation data.",
                action="kb_search",
                action_input={"query": "Anthropic funding valuation ARR", "source_filter": "all"},
                observation="Found 2 documents: Anthropic raising at $40-50B valuation, ARR reportedly $1B; Claude used by 50% of Fortune 500."
            ),
            AgentStep(
                step_num=2,
                thought="Let me get expert perspective on whether the valuation is justified and competitive positioning.",
                action="kb_search",
                action_input={"query": "Anthropic competition AI model market", "source_filter": "expert_interview"},
                observation="Found 2 documents: Expert says 40-50x ARR is aggressive but in-line with AI hype; Claude 3.5 leads in reasoning/coding but burns cash fast, lacks distribution channels."
            ),
        ]

    # SMCI
    if any(kw in query_lower for kw in ["smci", "超微", "super micro"]):
        return [
            AgentStep(
                step_num=1,
                thought="User is asking about SMCI - this is primarily an audit/governance risk question. Let me find the latest on audit status.",
                action="kb_search",
                action_input={"query": "SMCI audit BDO financial report", "source_filter": "alpha_engine"},
                observation="Found 1 document: SMCI hired BDO as new auditor, targeting June completion, company states no material fraud."
            ),
            AgentStep(
                step_num=2,
                thought="The audit timeline is critical. Let me get supply chain expert view on whether the business fundamentals are real.",
                action="kb_search",
                action_input={"query": "SMCI business AI server supply chain", "source_filter": "expert_interview"},
                observation="Found 1 document: Expert confirms SMCI's core AI server business is real with close NVIDIA ties, but governance is weak and customers may shift orders to Dell/HPE due to uncertainty."
            ),
            AgentStep(
                step_num=3,
                thought="Let me also check the short seller's thesis and social media for risk signals.",
                action="kb_search",
                action_input={"query": "SMCI Hindenburg short delisting risk", "source_filter": "all"},
                observation="Found 2 documents: Hindenburg allegations partially supported but 'fraud' conclusion too strong; Twitter warning that June deadline is critical for NASDAQ listing."
            ),
        ]

    # Fed / Interest Rate
    if any(kw in query_lower for kw in ["fed", "美联储", "降息", "利率"]):
        return [
            AgentStep(
                step_num=1,
                thought="User is asking about Fed rate impact. Let me find the latest FOMC meeting summary.",
                action="kb_search",
                action_input={"query": "Fed FOMC rate cut 2026", "source_filter": "alpha_engine"},
                observation="Found 1 document: Fed held rates but signaled 1-2 cuts in H2 2026. September cut probability at 70%. Year-end rate target 4.5-4.75%."
            ),
            AgentStep(
                step_num=2,
                thought="Now let me understand the differential impact on tech stocks - NVDA, MSFT, GOOGL have different rate sensitivities.",
                action="kb_search",
                action_input={"query": "tech stocks interest rate sensitivity NVDA MSFT GOOGL", "source_filter": "all"},
                observation="Found 2 documents: NVDA least sensitive (earnings-driven), MSFT medium (cloud benefits from IT spending recovery), GOOGL most sensitive (ad spend correlated with macro). 25bp cut = 3-5% sector valuation boost."
            ),
            AgentStep(
                step_num=3,
                thought="Let me also check what tech CFOs are saying about rate impact on their business.",
                action="kb_search",
                action_input={"query": "tech CFO rate impact AI demand", "source_filter": "expert_interview"},
                observation="Found 1 document: NVIDIA CFO says AI demand unrelated to rates; Microsoft CFO says rate cuts would boost SMB cloud spending; Google CFO notes competition pressure persists regardless of rates."
            ),
        ]

    # Default fallback chain
    return [
        AgentStep(
            step_num=1,
            thought=f"Analyzing query: '{query}'. Let me search the knowledge base broadly for relevant financial information.",
            action="kb_search",
            action_input={"query": query, "source_filter": "all"},
            observation="Searching knowledge base for relevant documents..."
        ),
        AgentStep(
            step_num=2,
            thought="Let me also check market sentiment to understand the broader context.",
            action="market_sentiment",
            action_input={},
            observation="Market Sentiment: Bullish 55% / Bearish 45%. Market in neutral territory."
        ),
    ]


# =============================================================================
# ReAct Agent
# =============================================================================

class ReActAgent:
    """
    ReAct (Reasoning + Acting) Agent.

    Implements the Thought -> Action -> Observation loop to intelligently
    gather information before passing to the Debate and Decision phases.
    """

    def __init__(
        self,
        tools: Optional[List[BaseTool]] = None,
        llm_client=None,
        max_steps: int = 5
    ):
        self.tools = tools or get_all_tools()
        self.llm_client = llm_client
        self.max_steps = max_steps

    def run(
        self,
        query: str,
        on_step: Optional[Callable[[AgentStep], None]] = None
    ) -> AgentOutput:
        """
        Run the ReAct loop.

        Args:
            query: User's research question
            on_step: Optional callback for each step (for UI updates)

        Returns:
            AgentOutput with collected information and reasoning trace
        """
        if Config.has_llm_api() and not Config.use_mock():
            result = self._run_with_llm(query, on_step)
            if result.steps:
                return result
            # LLM failed (0 steps) - fall back to mock reasoning with real tool execution
        return self._run_mock(query, on_step)

    def _run_mock(
        self,
        query: str,
        on_step: Optional[Callable[[AgentStep], None]] = None
    ) -> AgentOutput:
        """Run with pre-built reasoning chains (demo mode)."""
        steps = _get_mock_reasoning_chain(query)
        collected_docs = []

        for step in steps:
            # Actually execute the tool to get real mock data
            tool = get_tool_by_name(step.action)
            if tool:
                result = tool.execute(**step.action_input)
                if result.success:
                    # Update observation with real result summary
                    step.observation = result.summary
                    # Collect documents from KB search results
                    if step.action == "kb_search":
                        collected_docs.extend(result.data)
                # If tool returned no results, keep the pre-built observation
                # (which contains a narrative summary for the demo)

            # Notify UI
            if on_step:
                on_step(step)

        return AgentOutput(
            query=query,
            steps=steps,
            final_answer=f"Completed {len(steps)}-step analysis of: {query}",
            collected_documents=collected_docs,
            success=True
        )

    def _run_with_llm(
        self,
        query: str,
        on_step: Optional[Callable[[AgentStep], None]] = None
    ) -> AgentOutput:
        """Run with real LLM-driven reasoning."""
        steps = []
        collected_docs = []
        messages = self._build_initial_messages(query)

        for step_num in range(1, self.max_steps + 1):
            # Get LLM response
            response_text = self._call_llm(messages)

            # Parse thought and action
            thought, action, action_input, is_final = self._parse_response(response_text)

            if is_final:
                # Agent decided it has enough info
                break

            # Execute tool
            tool = get_tool_by_name(action)
            if tool:
                result = tool.execute(**action_input)
                observation = result.summary
                if action == "kb_search" and result.success:
                    collected_docs.extend(result.data)
            else:
                observation = f"Error: Tool '{action}' not found. Available tools: {[t.name for t in self.tools]}"

            step = AgentStep(
                step_num=step_num,
                thought=thought,
                action=action,
                action_input=action_input,
                observation=observation
            )
            steps.append(step)

            if on_step:
                on_step(step)

            # Add to conversation
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"Observation: {observation}"})

        return AgentOutput(
            query=query,
            steps=steps,
            final_answer=f"Completed {len(steps)}-step analysis of: {query}",
            collected_documents=collected_docs,
            success=True
        )

    def _build_initial_messages(self, query: str) -> List[Dict[str, str]]:
        """Build the initial prompt for the LLM."""
        tools_desc = get_tools_description()

        system_prompt = f"""You are a financial research agent. Your goal is to gather comprehensive information to answer the user's question.

You have access to the following tools:
{tools_desc}

Use the ReAct format for each step:
Thought: [Your reasoning about what to do next]
Action: [tool_name]
Action Input: {{"param1": "value1", "param2": "value2"}}

When you have gathered enough information, respond with:
Thought: I have sufficient information to provide a comprehensive analysis.
Action: FINISH
Action Input: {{}}

Guidelines:
- Search multiple source types (earnings, expert interviews, social media) for balanced coverage
- Look for both bullish and bearish signals
- Verify claims across sources when possible
- Usually 3-5 steps are sufficient
"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Research question: {query}"}
        ]

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call the LLM API."""
        import requests

        api_key = Config.LLM_API_KEY or Config.ANTHROPIC_API_KEY
        base_url = Config.LLM_BASE_URL

        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": Config.LLM_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Thought: LLM call failed ({e}), finishing with collected data.\nAction: FINISH\nAction Input: {{}}"

    def _parse_response(self, text: str) -> tuple:
        """Parse LLM response into thought, action, action_input, is_final."""
        thought = ""
        action = ""
        action_input = {}
        is_final = False

        # Extract Thought
        thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\Z)", text, re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()

        # Extract Action
        action_match = re.search(r"Action:\s*(.+?)(?=\nAction Input:|\Z)", text, re.DOTALL)
        if action_match:
            action = action_match.group(1).strip()

        # Check if finished
        if action.upper() == "FINISH":
            is_final = True
            return thought, action, action_input, is_final

        # Extract Action Input
        input_match = re.search(r"Action Input:\s*(\{.+?\})", text, re.DOTALL)
        if input_match:
            try:
                action_input = json.loads(input_match.group(1))
            except json.JSONDecodeError:
                action_input = {}

        return thought, action, action_input, is_final
