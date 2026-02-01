"""
Configuration constants for the English Learning application.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# User data directory
USERS_DIR = PROJECT_ROOT / "users"

# Ensure users directory exists
USERS_DIR.mkdir(exist_ok=True)

# File names
USER_INFO_FILE = "user_info.txt"
API_KEY_FILE = "api_key.txt"
WORD_BANK_FILE = "word_bank.txt"
LOG_DIR = "log"

# Default values
DEFAULT_AGE = 12
DEFAULT_LEXILE = 600

# AI Provider configurations
SUPPORTED_PROVIDERS = ["anthropic", "openai", "dashscope"]

# Article generation parameters
MIN_ARTICLE_LENGTH = 150
MAX_ARTICLE_LENGTH = 250
WORD_USAGE_THRESHOLD = 0.8  # 80% of words should be used

# Question configuration
NUM_QUESTIONS = 5
QUESTION_TYPES = {
    "multiple_choice": "选择题",
    "fill_blank": "填空题",
    "true_false": "判断题"
}

# Scoring
MAX_SCORE = 100
