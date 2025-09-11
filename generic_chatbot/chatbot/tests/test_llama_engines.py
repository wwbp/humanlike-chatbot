"""
Condensed test to evaluate Kani engines for Llama3 integration
"""

from chatbot.models import Bot, Conversation, Model, ModelProvider
import os
import time
import psutil
import logging
from typing import Dict, Any

import django
import pytest
from asgiref.sync import sync_to_async

# Setup Django first
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "generic_chatbot.settings")
django.setup()


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


class TestLlamaEngines:
    """Condensed test for different Kani engine approaches"""

    def setUp(self):
        """Set up test data"""
        Model.get_or_create_default_models()
        self.model = Model.objects.first()
        self.bot = Bot.objects.create(
            name="test_bot_llama",
            prompt="You are a helpful assistant.",
            ai_model=self.model,
        )
        self.conversation = Conversation.objects.create(
            conversation_id="test_conversation_llama",
            bot_name=self.bot.name,
            participant_id="test_user",
            study_name="test_study",
        )

    def tearDown(self):
        """Clean up test data"""
        self.conversation.delete()
        self.bot.delete()

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_api_approach(self):
        """Test current API approach"""
        print(f"\n{'='*50}")
        print("TESTING API APPROACH (OpenAI)")
        print(f"{'='*50}")

        try:
            from kani import Kani
            from kani.engines.openai import OpenAIEngine

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {"success": False, "error": "No API key"}

            print(f"Memory before: {get_memory_usage():.1f} MB")
            start_time = time.time()

            engine = OpenAIEngine(api_key=api_key, model="gpt-3.5-turbo")
            ai = Kani(engine, system_prompt="You are a helpful assistant.")

            load_time = time.time() - start_time
            print(f"Load time: {load_time:.2f}s")
            print(f"Memory after: {get_memory_usage():.1f} MB")

            # Test conversation
            start_time = time.time()
            response = await ai.chat_round_str("Tell me a short joke.")
            response_time = time.time() - start_time

            print(f"Response time: {response_time:.2f}s")
            print(f"Response: {response[:100]}...")

            return {
                "success": True,
                "load_time": load_time,
                "response_time": response_time,
                "memory_usage": get_memory_usage(),
                "model_id": "gpt-3.5-turbo"
            }

        except Exception as e:
            print(f"API test failed: {e}")
            return {"success": False, "error": str(e)}

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_huggingface_llama3(self):
        """Test HuggingFace with proper Llama3 setup"""
        print(f"\n{'='*50}")
        print("TESTING HUGGINGFACE LLAMA3")
        print(f"{'='*50}")

        try:
            import torch
            from kani import Kani
            from kani.engines.huggingface import HuggingEngine

            print(f"Memory before: {get_memory_usage():.1f} MB")
            start_time = time.time()

            # Use Llama3 8B model
            engine = HuggingEngine(
                model_id="meta-llama/Meta-Llama-3-8B-Instruct",
                use_auth_token="",  # Hardcoded token
                model_load_kwargs={
                    "device_map": "auto",
                    "torch_dtype": torch.bfloat16
                },
                temperature=0.6,
                top_p=0.9,
                max_new_tokens=100,
            )

            load_time = time.time() - start_time
            print(f"Load time: {load_time:.2f}s")
            print(f"Memory after: {get_memory_usage():.1f} MB")

            # Test conversation
            ai = Kani(engine, system_prompt="You are a helpful assistant.")
            start_time = time.time()
            response = await ai.chat_round_str("Tell me a short joke.")
            response_time = time.time() - start_time

            print(f"Response time: {response_time:.2f}s")
            print(f"Response: {response[:100]}...")

            return {
                "success": True,
                "load_time": load_time,
                "response_time": response_time,
                "memory_usage": get_memory_usage(),
                "model_id": "meta-llama/Meta-Llama-3-8B-Instruct"
            }

        except Exception as e:
            print(f"HuggingFace test failed: {e}")
            return {"success": False, "error": str(e)}

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_llamacpp_llama3(self):
        """Test LlamaCpp with proper GGUF setup"""
        print(f"\n{'='*50}")
        print("TESTING LLAMACPP LLAMA3")
        print(f"{'='*50}")

        try:
            from kani import Kani
            from kani.engines.llamacpp import LlamaCppEngine
            from kani.engines.huggingface import ChatTemplatePromptPipeline

            print(f"Memory before: {get_memory_usage():.1f} MB")
            start_time = time.time()

            # Use Llama3 8B model
            pipeline = ChatTemplatePromptPipeline.from_pretrained(
                "meta-llama/Meta-Llama-3-8B-Instruct",
                token="")
            engine = LlamaCppEngine(
                repo_id="TheBloke/Llama-3-8B-Instruct-GGUF",
                filename="*.Q4_K_M.gguf",
                prompt_pipeline=pipeline,
                model_load_kwargs={
                    "n_gpu_layers": 0,  # CPU only for testing
                },
                temperature=0.6,
                top_p=0.9,
                max_tokens=100,  # Fixed parameter name
            )

            load_time = time.time() - start_time
            print(f"Load time: {load_time:.2f}s")
            print(f"Memory after: {get_memory_usage():.1f} MB")

            # Test conversation
            ai = Kani(engine, system_prompt="You are a helpful assistant.")
            start_time = time.time()
            response = await ai.chat_round_str("Tell me a short joke.")
            response_time = time.time() - start_time

            print(f"Response time: {response_time:.2f}s")
            print(f"Response: {response[:100]}...")

            return {
                "success": True,
                "load_time": load_time,
                "response_time": response_time,
                "memory_usage": get_memory_usage(),
                "model_id": "TheBloke/Llama-3-8B-Instruct-GGUF"
            }

        except Exception as e:
            print(f"LlamaCpp test failed: {e}")
            return {"success": False, "error": str(e)}

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_engine_evaluation(self):
        """Run all engine tests and compare results"""
        print("Evaluating Kani engines for Llama3 integration...")
        print(f"Starting memory: {get_memory_usage():.1f} MB")

        results = {}

        # Test API approach
        results["api"] = await self.test_api_approach()

        # Test HuggingFace Llama3
        results["huggingface"] = await self.test_huggingface_llama3()

        # Test LlamaCpp Llama3
        results["llamacpp"] = await self.test_llamacpp_llama3()

        # Print evaluation summary
        print(f"\n{'='*60}")
        print("EVALUATION SUMMARY")
        print(f"{'='*60}")

        for engine_type, result in results.items():
            if result["success"]:
                print(f"\n{engine_type.upper()}:")
                print(f"  Model: {result['model_id']}")
                print(f"  Load time: {result['load_time']:.2f}s")
                print(f"  Response time: {result['response_time']:.2f}s")
                print(f"  Memory usage: {result['memory_usage']:.1f} MB")
            else:
                print(f"\n{engine_type.upper()}: FAILED")
                print(f"  Error: {result['error']}")

        print(f"\nFinal memory: {get_memory_usage():.1f} MB")

        # Evaluation criteria
        print(f"\n{'='*60}")
        print("EVALUATION CRITERIA")
        print(f"{'='*60}")

        if results["api"]["success"]:
            api_memory = results["api"]["memory_usage"]
            api_response = results["api"]["response_time"]
            print(
                f"API baseline: {api_memory:.1f} MB memory, {api_response:.2f}s response")

            for engine_type, result in results.items():
                if engine_type != "api" and result["success"]:
                    memory_ratio = result["memory_usage"] / api_memory
                    response_ratio = result["response_time"] / api_response
                    print(
                        f"{engine_type.upper()}: {memory_ratio:.1f}x memory, {response_ratio:.1f}x response time")

        return results


def run_llama_evaluation():
    """Run the llama engine evaluation"""
    test_instance = TestLlamaEngines()
    test_instance.setUp()

    try:
        results = test_instance.test_engine_evaluation()
        return results
    finally:
        test_instance.tearDown()


if __name__ == "__main__":
    run_llama_evaluation()
