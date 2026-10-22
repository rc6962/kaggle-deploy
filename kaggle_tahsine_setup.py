#!/usr/bin/env python3
"""
Kaggle LLM Server — tahsine/kaggle-llm-server pipeline
Single script that does all 3 notebooks in sequence.
Run in a Kaggle notebook cell (GPU T4×2, Internet ON).
"""

import os, subprocess, sys, time, urllib.request, json, re, signal

# ========== CONFIG ==========
MODEL_REPO = "Qwen/Qwen2.5-32B-Instruct-GGUF"
MODEL_FILE = "qwen2.5-32b-instruct-q4_k_m.gguf"
DATASET_SLUG = "yourusername/llm-models"  # CHANGE THIS
CACHE_DIR = "/kaggle/input/llm-models"
WORK_DIR = "/kaggle/working"
# ============================

def run(cmd, cwd=None, check=True, timeout=1800):
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or WORK_DIR,
                           capture_output=True, text=True, timeout=timeout)
    if result.stdout:
        print(result.stdout[-2000:])
    if result.stderr:
        print(result.stderr[-2000:], file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return result

def wait_for_url(url, timeout=300):
    for i in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=5)
            return True
        except:
            time.sleep(1)
    return False

def main():
    print("=" * 60)
    print("KAGGLE LLM SERVER — tahsine pipeline")
    print("=" * 60)

    # 1. Ensure dataset mounted
    if not os.path.exists(CACHE_DIR):
        print(f"⚠ Dataset not mounted at {CACHE_DIR}")
        print("   Add Data → your dataset → mount at /kaggle/input/llm-models")
        return 1

    # 2. Build llama.cpp with CUDA for T4
    llama_bin = os.path.join(WORK_DIR, "llama.cpp", "build", "bin", "llama-server")
    if not os.path.exists(llama_bin):
        print("\n[1/5] Building llama.cpp with CUDA...")
        run("git clone --depth 1 https://github.com/ggml-org/llama.cpp")
        run("cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=75", cwd="llama.cpp")
        run("cmake --build build --config Release -j4 --target llama-server", cwd="llama.cpp")
    else:
        print("\n[1/5] llama.cpp already built")

    # 3. Find model file
    model_path = os.path.join(CACHE_DIR, MODEL_FILE)
    if not os.path.exists(model_path):
        # Search recursively
        for root, dirs, files in os.walk(CACHE_DIR):
            if MODEL_FILE in files:
                model_path = os.path.join(root, MODEL_FILE)
                break
    if not os.path.exists(model_path):
        print(f"✗ Model not found: {MODEL_FILE}")
        print(f"   Expected at {CACHE_DIR}/{MODEL_FILE}")
        return 1
    print(f"\n[2/5] Model found: {model_path}")

    # 4. Start server
    print("\n[3/5] Starting llama-server...")
    run("pkill -f llama-server; sleep 2", check=False)
    log = open(os.path.join(WORK_DIR, "server.log"), "w")
    server = subprocess.Popen([
        llama_bin, "-m", model_path,
        "--host", "0.0.0.0", "--port", "8080",
        "-c", "8192", "-ngl", "99", "--parallel", "2"
    ], stdout=log, stderr=log, cwd=WORK_DIR)
    print(f"Server PID: {server.pid}")

    # 5. Wait for ready
    print("[4/5] Waiting for server...")
    if not wait_for_url("http://127.0.0.1:8080/health", 300):
        print("✗ Server didn't start — check server.log")
        return 1
    print("✓ Server ready")

    # 6. Cloudflare tunnel
    print("\n[5/5] Starting Cloudflare tunnel...")
    cf = os.path.join(WORK_DIR, "cloudflared")
    if not os.path.exists(cf):
        run(f"wget -q -O {cf} https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x {cf}")
    run("pkill -f cloudflared; sleep 1", check=False)
    tlog = open(os.path.join(WORK_DIR, "tunnel.log"), "w")
    subprocess.Popen([cf, "tunnel", "--url", "http://localhost:8080", "--no-autoupdate"],
                     stdout=tlog, stderr=tlog, cwd=WORK_DIR)

    # Extract URL
    url = None
    for _ in range(30):
        time.sleep(2)
        txt = open(os.path.join(WORK_DIR, "tunnel.log")).read()
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", txt)
        if m:
            url = m.group(0)
            break

    if url:
        print("\n" + "=" * 60)
        print("SUCCESS — Public endpoint:")
        print(f"  {url}/v1")
        print("=" * 60)
        print(f"\nTest: curl {url}/v1/chat/completions -H 'Content-Type: application/json' -d '{{\"model\":\"local\",\"messages\":[{{\"role\":\"user\",\"content\":\"hello\"}}]}}'")
    else:
        print("✗ Tunnel URL not found — check tunnel.log")

    return 0

if __name__ == "__main__":
    sys.exit(main())