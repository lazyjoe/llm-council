"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
# Read from .env if available, otherwise use defaults

model_group = "COUNCIL_MODELS"
model_group = "TEST_MODELS"

print(f"Using model group from env: {model_group}")

_council_models_env = os.getenv(model_group)
if _council_models_env:
    COUNCIL_MODELS = [m.strip() for m in _council_models_env.split(",")]
else:
    # throw exception if not set in .env
    raise ValueError("COUNCIL_MODELS env var is not set. e.g. COUNCIL_MODELS=grok-4.1-fast,glm-4.5-air:free,glm-4.5-flash,ernie-4.5-0.3b")

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = os.getenv("CHAIRMAN_MODEL", "grok-4.1-fast")
print(f"Using chairman model: {CHAIRMAN_MODEL}")

# OpenRouter API endpoint
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL")

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Directory for deleted conversations
DELETED_DIR = "data/deleted"
