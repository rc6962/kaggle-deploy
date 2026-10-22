#!/usr/bin/env python3
"""
AI Horde Worker — Earn kudos for your API key
Run on Kaggle (GPU T4×2, Internet ON) to contribute compute.
"""

import os, subprocess, sys, time, json, secrets

# ========== CONFIG ==========
API_KEY = "B2SwtB8hDMvceHE1U8iLKQ"  # YOUR KEY
WORKER_NAME = f"kaggle-{secrets.token_hex(4)}"
MODELS = ["koboldcpp/Qwen2.5-3B-Termux", "koboldcpp/Llama-3.2-1B-Instruct"]  # Light models for T4
# ============================

def run(cmd, cwd=None, check=True, timeout=1800):
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if result.stdout:
        print(result.stdout[-2000:])
    if result.stderr:
        print(result.stderr[-2000:], file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Failed: {cmd}")
    return result

def main():
    print("=" * 60)
    print("AI HORDE WORKER — Kaggle T4×2")
    print("=" * 60)

    # 1. Fix libcuda
    print("\n[1/6] Fixing libcuda...")
    run("ln -sf /usr/lib/x86_64-linux-gnu/libcuda.so.1 /usr/lib/x86_64-linux-gnu/libcuda.so", check=False)

    # 2. Install requirements
    print("\n[2/6] Installing requirements...")
    run("pip install -q --upgrade pip")
    run("CMAKE_ARGS='-DGGML_CUDA=on' pip install -q llama-cpp-python --no-cache-dir")
    run("pip install -q requests psutil")

    # 3. Download worker bridge
    print("\n[3/6] Downloading worker bridge...")
    bridge_url = "https://raw.githubusercontent.com/Haidra-Org/Simple-AI-Horde-Colab/main/bridge_alchemy.py"
    run(f"wget -q -O /kaggle/working/bridge.py {bridge_url}")

    # 4. Patch bridge with your config
    print("\n[4/6] Configuring worker...")
    bridge = open("/kaggle/working/bridge.py").read()
    bridge = bridge.replace('API_KEY = ""', f'API_KEY = "{API_KEY}"')
    bridge = bridge.replace('WORKER_NAME = ""', f'WORKER_NAME = "{WORKER_NAME}"')
    # Update models list
    import re
    bridge = re.sub(r'MODELS = \[.*?\]', f'MODELS = {MODELS}', bridge, flags=re.DOTALL)
    open("/kaggle/working/bridge.py", "w").write(bridge)

    # 5. Download small models
    print("\n[5/6] Downloading models...")
    for model in MODELS:
        repo, file = model.split("/")[0], model.split("/")[1] + "-Q4_K_M.gguf"
        run(f"huggingface-cli download {repo} --include '*Q4_K_M.gguf' --local-dir /kaggle/working/models", check=False)

    # 6. Start worker
    print("\n[6/6] Starting worker...")
    print(f"Worker: {WORKER_NAME}")
    print(f"Models: {MODELS}")
    print("Running... (Ctrl+C to stop, saves GPU quota)")

    os.chdir("/kaggle/working")
    subprocess.run([sys.executable, "bridge.py"])

if __name__ == "__main__":
    main()