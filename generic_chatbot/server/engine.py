from kani import Kani
from kani.engines.openai import OpenAIEngine
from kani.engines.anthropic import AnthropicEngine
import os

from dotenv import load_dotenv

# Load .env file from the root directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(base_dir, '..', '.env')  # Adjust for HUMANLIKE-CHATBOT root
load_dotenv(dotenv_path)

# Initialize the engine
def initialize_engine(config):
    model_config = config.get("default_model_config", {})
    model_type = model_config.get("type")
    model_id = model_config.get("model_id")

    if model_type == "OpenAI":
        api_key = os.getenv("OPENAI_API_KEY")  
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY environment variable.")
        return OpenAIEngine(api_key=api_key, model=model_id)
    
    elif model_type == "Anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Missing ANTHROPIC_API_KEY environment variable.")
        return AnthropicEngine(api_key=api_key, model=model_id)
    
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
