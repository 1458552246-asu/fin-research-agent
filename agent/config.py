"""Configuration management - all sensitive data from environment variables."""

import os
from pathlib import Path

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # dotenv not installed, use environment variables directly


def _get_secret(key: str, default: str = "") -> str:
    """Get a config value from env vars or Streamlit Cloud secrets."""
    # 1. Try os.getenv first (works locally with .env)
    val = os.getenv(key, "")
    if val:
        return val

    # 2. Try Streamlit secrets (works on Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass

    return default


class Config:
    """Application configuration from environment variables."""

    # LLM API for Bull/Bear analysis (OpenAI-compatible)
    LLM_API_KEY = _get_secret("LLM_API_KEY")
    LLM_BASE_URL = _get_secret("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL = _get_secret("LLM_MODEL", "claude-sonnet-4-20250514")

    # Legacy support for ANTHROPIC_API_KEY
    ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")

    # Knowledge Base API (production)
    KB_API_BASE_URL = _get_secret("KB_API_BASE_URL")
    KB_USERNAME = _get_secret("KB_API_USERNAME")
    KB_PASSWORD = _get_secret("KB_API_PASSWORD")

    # Demo mode - use mock data
    DEMO_MODE = _get_secret("DEMO_MODE", "false").lower() == "true"

    @classmethod
    def reload(cls):
        """Reload config (useful after secrets become available)."""
        cls.LLM_API_KEY = _get_secret("LLM_API_KEY")
        cls.LLM_BASE_URL = _get_secret("LLM_BASE_URL", "https://api.openai.com/v1")
        cls.LLM_MODEL = _get_secret("LLM_MODEL", "claude-sonnet-4-20250514")
        cls.ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")
        cls.KB_API_BASE_URL = _get_secret("KB_API_BASE_URL")
        cls.KB_USERNAME = _get_secret("KB_API_USERNAME")
        cls.KB_PASSWORD = _get_secret("KB_API_PASSWORD")
        cls.DEMO_MODE = _get_secret("DEMO_MODE", "false").lower() == "true"

    @classmethod
    def is_production_ready(cls) -> bool:
        """Check if production KB API is configured."""
        return bool(cls.KB_API_BASE_URL and cls.KB_USERNAME and cls.KB_PASSWORD)

    @classmethod
    def has_llm_api(cls) -> bool:
        """Check if LLM API is configured."""
        return bool(cls.LLM_API_KEY or cls.ANTHROPIC_API_KEY)

    @classmethod
    def use_mock(cls) -> bool:
        """Determine whether to use mock data."""
        if cls.DEMO_MODE:
            return True
        return not cls.is_production_ready()


# Default Knowledge Base IDs (for reference)
DEFAULT_KB_IDS = [17, 18, 19, 21, 28]

# KB name mapping
KB_ID_TO_NAME = {
    17: "专家访谈",      # Expert interviews
    18: "Twitter推文",   # Social media
    19: "AceCampTech",  # Research articles
    21: "Substack",     # Newsletters
    28: "AlphaEngine",  # Reports & earnings
}

KB_NAME_TO_ID = {v: k for k, v in KB_ID_TO_NAME.items()}

# User-friendly KB keywords
KB_KEYWORD_MAP = {
    "expert": 17, "专家": 17, "访谈": 17,
    "twitter": 18, "推特": 18, "x": 18,
    "acecamp": 19, "ace": 19,
    "substack": 21, "newsletter": 21,
    "alpha": 28, "研报": 28, "report": 28,
}
