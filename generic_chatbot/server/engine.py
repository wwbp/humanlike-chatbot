from kani import Kani
from kani.engines.openai import OpenAIEngine
from kani.engines.anthropic import AnthropicEngine
import os

# Initialize the engine
def initialize_engine(config):
    model_config = config.get("default_model_config", {})
    model_type = model_config.get("type")
    model_id = model_config.get("model_id")
    api_key = os.getenv("api_key")

    if model_type == "OpenAI":
        return OpenAIEngine(api_key=api_key, model=model_id)
    elif model_type == "Anthropic":
        return AnthropicEngine(api_key=api_key, model=model_id)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
