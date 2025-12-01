"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = [
    "gpt-5.1",
    "gemini-3-pro-preview",
    "claude-sonnet-4-5",
    "grok-4",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "gemini-3-pro-preview"

# OpenRouter API endpoint
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL")

# Data directory for conversation storage
DATA_DIR = "data/conversations"
