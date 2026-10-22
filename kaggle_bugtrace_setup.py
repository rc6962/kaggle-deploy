#!/usr/bin/env python3
"""
BugTraceAI Apex G4 26B Q4 — Single cell Kaggle deploy
Paste this entire file into ONE Kaggle notebook cell (GPU T4×2, Internet ON).
"""

import os, subprocess, sys, time, urllib.request, re, json, signal, warnings
warnings.filterwarnings("ignore")

# ========== CONFIG (edit these) ==========
MODEL_REPO = "TheBloke/BugTraceAI-Apex-G4-26B-GGUF"
MODEL_FILE = "bugtraceai-apex-g4-26b.Q4_K_M.gguf"
DATASET_SLUG = "yourusername/bugtraceai-model"  # CHANGE THIS
# =========================================

CACHE_DIR = "/kaggle/input/bugtraceai-model"
WORK_DIR = "/kaggle/working"

def run(cmd, cwd=None, check=True, timeout=1800):
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or WORK_DIR,
                           capture_output=True, text=True, timeout=timeout)
    if result.stdout:
        print(result.stdout[-3000:])
    if result.stderr:
        print(result.stderr[-3000:], file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed (exit {result.returncode}): {cmd}")
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
    print("BUGTRACEAI APEX G4 26B — Single Cell Deploy")
    print("=" * 60)

    # 0. Fix libcuda symlink (common Kaggle issue)
    print("\n[0/6] Fixing libcuda...")
    run("ln -sf /usr/lib/x86_64-linux-gnu/libcuda.so.1 /usr/lib/x86_64-linux-gnu/libcuda.so", check=False)

    # 1. Install llama-cpp-python with CUDA
    print("\n[1/6] Installing llama-cpp-python (CUDA)...")
    run("pip install -q --upgrade pip")
    run("CMAKE_ARGS='-DGGML_CUDA=on' pip install -q llama-cpp-python --no-cache-dir")

    # 2. Mount dataset
    if not os.path.exists(CACHE_DIR):
        print(f"\n⚠ Dataset not mounted at {CACHE_DIR}")
        print("   Add Data → your dataset → mount at /kaggle/input/bugtraceai-model")
        return 1
    print(f"\n[2/6] Dataset mounted: {CACHE_DIR}")

    # 3. Find model
    model_path = None
    for root, dirs, files in os.walk(CACHE_DIR):
        if MODEL_FILE in files:
            model_path = os.path.join(root, MODEL_FILE)
            break
    if not model_path:
        print(f"✗ Model not found: {MODEL_FILE}")
        return 1
    print(f"[3/6] Model: {model_path}")

    # 4. Load + warm up
    print("\n[4/6] Loading model...")
    from llama_cpp import Llama
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=99,
        n_ctx=8192,
        n_threads=8,
        verbose=False,
        seed=42
    )
    print("✓ Model loaded")

    # Warm-up
    print("[5/6] Warm-up inference...")
    _ = llm("Warm up.", max_tokens=5, echo=False)
    print("✓ Warmed up")

    # 5. Start OpenAI-compatible server
    print("\n[6/6] Starting server + tunnel...")
    run("pkill -f llama-server; sleep 2", check=False)

    # Use llama-cpp-python's built-in server
    from llama_cpp.server import app
    import uvicorn
    from threading import Thread

    server_thread = Thread(target=uvicorn.run, kwargs={
        "app": app, "host": "0.0.0.0", "port": 8080, "log_level": "warning"
    }, daemon=True)
    server_thread.start()

    if not wait_for_url("http://127.0.0.1:8080/health", 60):
        print("✗ Server failed to start")
        return 1
    print("✓ Server ready")

    # Cloudflare tunnel
    cf = os.path.join(WORK_DIR, "cloudflared")
    if not os.path.exists(cf):
        run("wget -q -O /kaggle/working/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x /kaggle/working/cloudflared")
    run("pkill -f cloudflared; sleep 1", check=False)
    tlog = open("/kaggle/working/tunnel.log", "w")
    subprocess.Popen(["/kaggle/working/cloudflared", "tunnel", "--url", "http://localhost:8080", "--no-autoupdate"],
                     stdout=tlog, stderr=tlog)

    url = None
    for _ in range(30):
        time.sleep(2)
        txt = open("/kaggle/working/tunnel.log").read()
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

    # Keep alive
    print("\n[RUNNING] Press Ctrl+C to stop (saves GPU quota)")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        run("pkill -f 'uvicorn|cloudflared'; echo 'Stopped'")
    return 0

if __name__ == "__main__":
    sys.exit(main())