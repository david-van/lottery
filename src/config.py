"""Runtime configuration and path constants."""

import os
from pathlib import Path

# Project root is the parent of src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Output directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_CSV_PATH = DATA_DIR / "raw_matches.csv"
NORMALIZED_CSV_PATH = DATA_DIR / "normalized_matches.csv"

# Prompt assets
PROMPT_TEMPLATE_PATH = PROJECT_ROOT / "prompt_template.txt"

# API endpoints
MATCH_LIST_API = "https://webapi.sporttery.cn/gateway/uniform/football/league/getMatchResultV1.qry"
ODDS_DETAIL_API = "https://webapi.sporttery.cn/gateway/jc/football/getFixedBonusV1.qry"

# HTTP defaults
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
)
HTTP_TIMEOUT = 30  # seconds

# LLM configuration (provider-agnostic, credentials from env)
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "")

# OpenAI-specific configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "")  # leave empty for default OpenAI endpoint


def ensure_data_dir():
    """Create the data output directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
