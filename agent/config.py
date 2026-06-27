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


class Config:
    """Application configuration from environment variables."""

    # Claude API for Bull/Bear analysis
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # Knowledge Base API (production)
    KB_API_BASE_URL = os.getenv("KB_API_BASE_URL", "")
    KB_USERNAME = os.getenv("KB_USERNAME", "")
    KB_PASSWORD = os.getenv("KB_PASSWORD", "")

    # Demo mode - use mock data
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

    @classmethod
    def is_production_ready(cls) -> bool:
        """Check if production KB API is configured."""
        return bool(cls.KB_API_BASE_URL and cls.KB_USERNAME and cls.KB_PASSWORD)

    @classmethod
    def has_llm_api(cls) -> bool:
        """Check if Claude API is configured."""
        return bool(cls.ANTHROPIC_API_KEY)

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
    17: "久谦中台",      # Expert interviews
    18: "Twitter推文",   # Social media
    19: "AceCampTech",  # Research articles
    21: "Substack",     # Newsletters
    28: "AlphaEngine",  # Reports & earnings
}

KB_NAME_TO_ID = {v: k for k, v in KB_ID_TO_NAME.items()}

# User-friendly KB keywords
KB_KEYWORD_MAP = {
    "久谦": 17, "jiuqian": 17, "expert": 17, "专家": 17,
    "twitter": 18, "推特": 18, "x": 18,
    "acecamp": 19, "ace": 19,
    "substack": 21, "newsletter": 21,
    "alpha": 28, "研报": 28, "report": 28,
}
