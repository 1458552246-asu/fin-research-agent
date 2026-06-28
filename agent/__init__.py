"""Fin Research Agent - Multi-source financial research assistant with Bull/Bear analysis."""

__version__ = "3.0.0"

# Core models
from .models import (
    ResearchReport, DebateResult, Decision, WorkflowState,
    Recommendation, Sentiment, SourceType,
    KeyFact, DataPoint, Argument, SourceReference
)

# Phase modules
from .research_team import ResearchTeam, run_research
from .debate_team import DebateTeam, run_debate
from .decision_agent import DecisionAgent, make_decision

# Main orchestrator
from .orchestrator import Orchestrator, analyze, analyze_streaming

# ReAct Agent & Tools
from .react_agent import ReActAgent, AgentStep, AgentOutput
from .tools import BaseTool, ToolResult, get_all_tools, get_tool_by_name

# Config
from .config import Config, KB_ID_TO_NAME, KB_NAME_TO_ID

# KB client
from .kb_client import KBClient, get_kb_client, is_demo_mode

__all__ = [
    # Models
    "ResearchReport", "DebateResult", "Decision", "WorkflowState",
    "Recommendation", "Sentiment", "SourceType",
    "KeyFact", "DataPoint", "Argument", "SourceReference",
    # Teams
    "ResearchTeam", "DebateTeam", "DecisionAgent", "Orchestrator",
    # ReAct Agent & Tools
    "ReActAgent", "AgentStep", "AgentOutput",
    "BaseTool", "ToolResult", "get_all_tools", "get_tool_by_name",
    # Functions
    "run_research", "run_debate", "make_decision", "analyze", "analyze_streaming",
    # Config
    "Config", "KB_ID_TO_NAME", "KB_NAME_TO_ID",
    # KB
    "KBClient", "get_kb_client", "is_demo_mode",
]
