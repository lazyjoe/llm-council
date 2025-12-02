"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
TOP_MODELS = [
    "gpt-5.1",
    "gemini-3-pro-preview",
    "claude-opus-4-5",
    "grok-4",
]

TEST_MODELS = [
    "grok-4.1-fast",
    # "omni-moderation-latest",
    'glm-4.5-air:free',
    "glm-4.5-flash",
    'ernie-4.5-0.3b',
    # "gemma-3n-e4b-it:free",
]

# COUNCIL_MODELS = TEST_MODELS
COUNCIL_MODELS = TOP_MODELS

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "gemini-3-pro-preview"
# CHAIRMAN_MODEL = "grok-4.1-fast"

# OpenRouter API endpoint
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL")

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Directory for deleted conversations
DELETED_DIR = "data/deleted"
