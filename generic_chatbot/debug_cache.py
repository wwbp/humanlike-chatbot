#!/usr/bin/env python3
"""Debug script to check cache structure"""

import os

def debug_cache():
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    print(f"Cache dir: {cache_dir}")
    print(f"Exists: {os.path.exists(cache_dir)}")
    
    if os.path.exists(cache_dir):
        print("\nContents of cache:")
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            print(f"  {item} ({'dir' if os.path.isdir(item_path) else 'file'})")
        
        # Check GGUF model directory
        model_dir = "models--QuantFactory--Meta-Llama-3-8B-Instruct-GGUF"
        model_path = os.path.join(cache_dir, model_dir)
        print(f"\nModel dir: {model_path}")
        print(f"Exists: {os.path.exists(model_path)}")
        
        if os.path.exists(model_path):
            print("\nContents of model dir:")
            for item in os.listdir(model_path):
                item_path = os.path.join(model_path, item)
                print(f"  {item} ({'dir' if os.path.isdir(item_path) else 'file'})")
            
            # Look for GGUF files recursively
            print("\nLooking for GGUF files:")
            for root, dirs, files in os.walk(model_path):
                for file in files:
                    if file.endswith('.gguf'):
                        full_path = os.path.join(root, file)
                        print(f"  Found: {full_path}")
                        print(f"  Relative to cache: {os.path.relpath(full_path, cache_dir)}")

if __name__ == "__main__":
    debug_cache()
