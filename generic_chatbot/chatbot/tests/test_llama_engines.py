"""Llama engines test - online vs offline"""

import os
import time
import pytest
from kani import Kani


async def run_test(name, engine):
    """Test engine and print results"""
    print(f"\n{'='*40}\nTESTING {name.upper()}\n{'='*40}")
    print(
        f"Memory: {__import__('psutil').Process().memory_info().rss / 1024 / 1024:.1f} MB")

    start = time.time()
    response = await Kani(engine, system_prompt="You are a helpful assistant.").chat_round_str("Say 'Hello World' in a unqiue way.")
    print(f"Response time: {time.time() - start:.2f}s\nResponse: {response}")


@pytest.mark.asyncio
async def test_huggingface_online():
    """HuggingFace online (downloads model)"""
    from kani.engines.huggingface import HuggingEngine
    import torch

    engine = HuggingEngine(
        model_id="meta-llama/Meta-Llama-3-8B-Instruct",
        model_load_kwargs={"device_map": "auto",
                           "torch_dtype": torch.bfloat16, "low_cpu_mem_usage": True}
    )
    await run_test("HuggingFace Online", engine)


@pytest.mark.asyncio
async def test_huggingface_offline():
    """HuggingFace offline (cached model)"""
    from kani.engines.huggingface import HuggingEngine
    import torch

    engine = HuggingEngine(
        model_id="meta-llama/Meta-Llama-3-8B-Instruct",
        model_load_kwargs={"device_map": "auto", "torch_dtype": torch.bfloat16,
                           "low_cpu_mem_usage": True, "local_files_only": True}
    )
    await run_test("HuggingFace Offline", engine)


@pytest.mark.asyncio
async def test_llamacpp_online():
    """LlamaCpp online (downloads model)"""
    from kani.engines.llamacpp import LlamaCppEngine
    from kani.engines.huggingface import ChatTemplatePromptPipeline

    pipeline = ChatTemplatePromptPipeline.from_pretrained(
        "meta-llama/Meta-Llama-3-8B-Instruct")
    engine = LlamaCppEngine(repo_id="QuantFactory/Meta-Llama-3-8B-Instruct-GGUF",
                            filename="*Q4_K_M.gguf", prompt_pipeline=pipeline)
    await run_test("LlamaCpp Online", engine)


@pytest.mark.asyncio
async def test_llamacpp_offline():
    """LlamaCpp offline (cached model)"""
    from kani.engines.llamacpp import LlamaCppEngine
    from kani.engines.huggingface import ChatTemplatePromptPipeline

    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    model_dir = "models--QuantFactory--Meta-Llama-3-8B-Instruct-GGUF"
    tokenizer_dir = "models--meta-llama--Meta-Llama-3-8B-Instruct/snapshots"

    # Skip if model not downloaded
    if not os.path.exists(os.path.join(cache_dir, model_dir)):
        print("❌ Model not found")
        return

    # Get GGUF file path (it's in the snapshots subdirectory)
    snapshots_dir = os.path.join(cache_dir, model_dir, "snapshots")
    if not os.path.exists(snapshots_dir):
        print("❌ Snapshots directory not found")
        return

    # Find the snapshot hash directory
    snapshot_hash = next(d for d in os.listdir(
        snapshots_dir) if os.path.isdir(os.path.join(snapshots_dir, d)))
    snapshot_dir = os.path.join(snapshots_dir, snapshot_hash)

    # Find the GGUF file in the snapshot directory
    gguf_file = next(f for f in os.listdir(
        snapshot_dir) if f.endswith('.gguf'))
    gguf_path = os.path.join(snapshot_dir, gguf_file)

    # Get tokenizer path (also in snapshots subdirectory)
    tokenizer_snapshots_dir = os.path.join(
        cache_dir, "models--meta-llama--Meta-Llama-3-8B-Instruct", "snapshots")
    if not os.path.exists(tokenizer_snapshots_dir):
        print("❌ Tokenizer snapshots directory not found")
        return

    # Find the tokenizer snapshot hash directory
    tokenizer_snapshot_hash = next(d for d in os.listdir(
        tokenizer_snapshots_dir) if os.path.isdir(os.path.join(tokenizer_snapshots_dir, d)))
    tokenizer_snapshot_dir = os.path.join(
        tokenizer_snapshots_dir, tokenizer_snapshot_hash)

    # Load pipeline and engine
    pipeline = ChatTemplatePromptPipeline.from_pretrained(
        tokenizer_snapshot_dir, local_files_only=True)
    engine = LlamaCppEngine(model_path=gguf_path, prompt_pipeline=pipeline)
    # Set repo_id for model-specific parsing
    engine.repo_id = "meta-llama/Meta-Llama-3-8B-Instruct"
    await run_test("LlamaCpp Offline", engine)


if __name__ == "__main__":
    import asyncio
    for test in [test_huggingface_online, test_huggingface_offline, test_llamacpp_online, test_llamacpp_offline]:
        asyncio.run(test())
