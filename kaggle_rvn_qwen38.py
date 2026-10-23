#!/usr/bin/env python3
"""
Deploy Qwen3.8-27B RVN Heretic Abliterated (0bserverx) — Best balance for Kaggle
UGI: ~W10 7-8, Hazardous ~3-4, 0-1% refusals, KL 0.0085
Size: Q4_K_M = 16.5 GB — fits T4×2 perfectly
"""

import os, subprocess, time, urllib.request, json, signal, re

# ========== CONFIG ==========
MODEL_REPO = "0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF"
MODEL_FILE = "RVN-Q4_K_M.gguf"          # 16.5 GB, best quality/size
CHAT_TEMPLATE = "chat_template.jinja"   # REQUIRED for Qwen3.8 tool/function calling
# =============================

print("="*60)
print(f"Deploying {MODEL_FILE} from {MODEL_REPO}")
print("UGI: W10 ~7-8, Hazardous ~3-4, Refusals 0-1%")
print("="*60)

# 1. Build llama.cpp with CUDA for T4 (compute capability 75)
if not os.path.exists("/kaggle/working/llama.cpp/build/bin/llama-server"):
    print("Applying Kaggle CUDA driver symlink fix...")
    subprocess.run("ln -sf /usr/local/nvidia/lib64/libcuda.so /usr/local/cuda/lib64/libcuda.so 2>/dev/null || true", shell=True)
    subprocess.run("ln -sf /usr/lib/x86_64-linux-gnu/libcuda.so.1 /usr/local/cuda/lib64/libcuda.so 2>/dev/null || true", shell=True)
    subprocess.run("ln -sf /usr/lib/x86_64-linux-gnu/libcuda.so.1 /usr/lib/x86_64-linux-gnu/libcuda.so 2>/dev/null || true", shell=True)

    print("Building llama.cpp...")
    subprocess.run("rm -rf /kaggle/working/llama.cpp && cd /kaggle/working && git clone --depth 1 https://github.com/ggml-org/llama.cpp", shell=True, check=True)
    subprocess.run(
        "cd /kaggle/working/llama.cpp && "
        "cmake -B build "
        "-DGGML_CUDA=ON "
        "-DGGML_NATIVE=OFF "
        "-DCMAKE_BUILD_TYPE=Release "
        "-DCMAKE_CUDA_ARCHITECTURES=75 "
        "-DCMAKE_PREFIX_PATH=/usr/local/nvidia "
        "-DCUDAToolkit_ROOT=/usr/local/cuda && "
        "cmake --build build --config Release -j4 --target llama-server llama-cli",
        shell=True, check=True
    )
print("✓ llama.cpp built")

# 2. Download model + chat template
print("Downloading model...")
os.makedirs("/kaggle/working/models", exist_ok=True)
try:
    from huggingface_hub import hf_hub_download
except ImportError:
    subprocess.run("pip install -q -U huggingface_hub", shell=True, check=True)
    from huggingface_hub import hf_hub_download

print(f"Downloading {MODEL_FILE}...")
model_path = hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE, local_dir="/kaggle/working/models")
print(f"✓ Model: {model_path}")

print(f"Downloading {CHAT_TEMPLATE}...")
template_path = hf_hub_download(repo_id=MODEL_REPO, filename=CHAT_TEMPLATE, local_dir="/kaggle/working/models")
print(f"✓ Template: {template_path}")

# 3. Start server
print("Starting server...")
subprocess.run("pkill -f llama-server; sleep 2", shell=True)
log = open("/kaggle/working/server.log", "w")
server = subprocess.Popen([
    "/kaggle/working/llama.cpp/build/bin/llama-server",
    "-m", model_path,
    "--chat-template-file", template_path,
    "--host", "0.0.0.0", "--port", "8080",
    "-c", "16384", "-ngl", "99", "--parallel", "2", "--jinja"
], stdout=log, stderr=log)
print(f"Server PID: {server.pid}")

# 4. Wait for ready
print("Waiting for server ready...")
for i in range(240):
    time.sleep(5)
    try:
        r = urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=3)
        if r.status == 200:
            print("✓ SERVER READY")
            break
    except:
        pass
    if server.poll() is not None:
        print("✗ Server died — check /kaggle/working/server.log")
        break
else:
    print("Still loading — check /kaggle/working/server.log")

# 5. Cloudflare tunnel
print("Starting Cloudflare tunnel...")
if not os.path.exists("/kaggle/working/cloudflared"):
    subprocess.run(
        "wget -q -O /kaggle/working/cloudflared "
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 "
        "&& chmod +x /kaggle/working/cloudflared", shell=True, check=True
    )
subprocess.run("pkill -f cloudflared; sleep 1", shell=True)
tlog = open("/kaggle/working/tunnel.log", "w")
subprocess.Popen([
    "/kaggle/working/cloudflared", "tunnel", "--url", "http://localhost:8080", "--no-autoupdate"
], stdout=tlog, stderr=tlog)

# 6. Extract URL
url = None
for _ in range(30):
    time.sleep(2)
    txt = open("/kaggle/working/tunnel.log").read()
    m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", txt)
    if m:
        url = m.group(0)
        break

if url:
    print("\n" + "="*60)
    print("🎉 DEPLOYED! Your OpenAI-compatible endpoint:")
    print(f"  {url}/v1")
    print("="*60)
    print("TEST:")
    print(f'curl {url}/v1/chat/completions -H "Content-Type: application/json" -d \'{{"model":"local","messages":[{{"role":"user","content":"Hello"}}]}}\'')
    print("="*60)
    print("In Hermes: --provider custom:AI\\ Horde -m \"Qwen3.8-27b-Uncensored\"")
    print("="*60)
else:
    print("URL not found — check /kaggle/working/tunnel.log")