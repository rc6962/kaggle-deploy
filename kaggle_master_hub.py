#!/usr/bin/env python3
"""
Master Kaggle LLM Multi-Model Hub & Switcher
Runs a persistent local control engine inside the dual-T4 Kaggle notebook.
"""

import os, sys, time, subprocess, urllib.request, json, re, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

WORK_DIR = "/kaggle/working"
MODELS_DIR = "/kaggle/working/models"
os.makedirs(MODELS_DIR, exist_ok=True)

# Pre-registered model library
CATALOG = {
    "rvn": {
        "repo": "0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF",
        "file": "RVN-Q4_K_M.gguf",
        "template": "chat_template.jinja",
        "ngl": 99,
        "ctx": 16384
    },
    "deckard": {
        "repo": "CountCandy/gemma-4-31B-it-The-DECKARD-HERETIC-UNCENSORED-Thinking-GGUFs",
        "file": "gemma-4-31b-it-The-DECKARD-HERETIC-UNCENSORED-Thinking-Q4_K_M.gguf",
        "template": None,
        "ngl": 80,
        "ctx": 16384
    },
    "hauhau": {
        "repo": "HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF",
        "file": "Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-FastMTP-32K.gguf",
        "template": None,
        "ngl": 99,
        "ctx": 16384
    },
    "nemo": {
        "repo": "mradermacher/Mistral-Nemo-2407-12B-Thinking-Claude-Gemini-GPT5.2-Uncensored-HERETIC-GGUF",
        "file": "Mistral-Nemo-2407-12B-Thinking-Claude-Gemini-GPT5.2-Uncensored-HERETIC.Q3_K_M.gguf",
        "template": None,
        "ngl": 99,
        "ctx": 32768
    }
}

CURRENT_MODEL = "rvn"
API_KEY = os.environ.get("ENDPOINT_API_KEY", "sk-balls-uncensored")

# 1. Use pre-compiled binary from Kaggle dataset if available, otherwise build
DATASET_BIN = "/kaggle/input/llama-cpp-sm75-bin"
import glob
print(f"Contents of /kaggle/input/: {os.listdir('/kaggle/input/') if os.path.exists('/kaggle/input/') else 'NOT FOUND'}")
if os.path.exists(DATASET_BIN):
    print(f"Contents of {DATASET_BIN}: {os.listdir(DATASET_BIN)}")
    found_bins = glob.glob(f"{DATASET_BIN}/**/llama-server", recursive=True)
    print(f"Found llama-server binaries: {found_bins}")
    if found_bins:
        bin_dir = os.path.dirname(found_bins[0])
        print(f"Using binary from: {bin_dir}")
        os.makedirs(f"{WORK_DIR}/llama.cpp/build/bin", exist_ok=True)
        subprocess.run(f"cp -r {bin_dir}/* {WORK_DIR}/llama.cpp/build/bin/", shell=True, check=True)
        print("Copied pre-compiled binaries")
cf_paths = glob.glob(f"{DATASET_BIN}/**/cloudflared", recursive=True)
if cf_paths and not os.path.exists(f"{WORK_DIR}/cloudflared"):
    subprocess.run(f"cp {cf_paths[0]} {WORK_DIR}/cloudflared && chmod +x {WORK_DIR}/cloudflared", shell=True, check=True)
    print("Copied pre-compiled cloudflared")

if os.path.exists(f"{WORK_DIR}/llama.cpp/build/bin/llama-server"):
    print("llama.cpp ready (pre-compiled, skipping build)")
else:
    print("Applying CUDA symlink fix & building llama.cpp...")
    subprocess.run("ln -sf /usr/local/nvidia/lib64/libcuda.so /usr/local/cuda/lib64/libcuda.so 2>/dev/null || true", shell=True)
    subprocess.run("ln -sf /usr/lib/x86_64-linux-gnu/libcuda.so.1 /usr/local/cuda/lib64/libcuda.so 2>/dev/null || true", shell=True)
    subprocess.run("ln -sf /usr/lib/x86_64-linux-gnu/libcuda.so.1 /usr/lib/x86_64-linux-gnu/libcuda.so 2>/dev/null || true", shell=True)
    subprocess.run(f"cd {WORK_DIR} && git clone --depth 1 https://github.com/ggml-org/llama.cpp", shell=True, check=True)
    subprocess.run(
        f"cd {WORK_DIR}/llama.cpp && "
        "cmake -B build -DGGML_CUDA=ON -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release "
        "-DCMAKE_CUDA_ARCHITECTURES=75 -DCMAKE_PREFIX_PATH=/usr/local/nvidia -DCUDAToolkit_ROOT=/usr/local/cuda && "
        "cmake --build build --config Release -j4 --target llama-server llama-cli",
        shell=True, check=True
    )
print("✓ llama.cpp ready")

# Use pre-compiled cloudflared if available
if os.path.exists(f"{DATASET_BIN}/cloudflared") and not os.path.exists(f"{WORK_DIR}/cloudflared"):
    subprocess.run(f"cp {DATASET_BIN}/cloudflared {WORK_DIR}/cloudflared && chmod +x {WORK_DIR}/cloudflared", shell=True, check=True)
    print("✓ Copied pre-compiled cloudflared")

# Ensure huggingface_hub is installed
try:
    from huggingface_hub import hf_hub_download
except ImportError:
    subprocess.run("pip install -q -U huggingface_hub", shell=True, check=True)
    from huggingface_hub import hf_hub_download

SERVER_PROC = None

def start_model(mkey):
    global SERVER_PROC, CURRENT_MODEL
    if mkey not in CATALOG:
        return False, "Unknown model"
    cfg = CATALOG[mkey]
    print(f"\n[Switching to {mkey}] Downloading {cfg['file']} if needed...")
    mpath = hf_hub_download(repo_id=cfg["repo"], filename=cfg["file"], local_dir=MODELS_DIR)
    tpath = None
    if cfg["template"]:
        tpath = hf_hub_download(repo_id=cfg["repo"], filename=cfg["template"], local_dir=MODELS_DIR)
    
    if SERVER_PROC:
        print("Stopping current llama-server...")
        subprocess.run("pkill -f llama-server; sleep 2", shell=True)
    
    cmd = [
        f"{WORK_DIR}/llama.cpp/build/bin/llama-server",
        "-m", mpath,
        "--host", "0.0.0.0", "--port", "8080",
        "-c", str(cfg["ctx"]), "-ngl", str(cfg["ngl"]),
        "--parallel", "2", "--jinja"
    ]
    if tpath:
        cmd.extend(["--chat-template-file", tpath])
    if API_KEY:
        cmd.extend(["--api-key", API_KEY])
    
    slog = open(f"{WORK_DIR}/server.log", "w")
    SERVER_PROC = subprocess.Popen(cmd, stdout=slog, stderr=slog)
    CURRENT_MODEL = mkey
    print(f"✓ Started {mkey} on PID {SERVER_PROC.pid}")
    return True, f"Running {mkey}"

# Start initial model
start_model("rvn")

# Start tunnel
if not os.path.exists(f"{WORK_DIR}/cloudflared"):
    subprocess.run(
        f"wget -q -O {WORK_DIR}/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x {WORK_DIR}/cloudflared",
        shell=True, check=True
    )

subprocess.run("pkill -f cloudflared; sleep 1", shell=True)
tlog = open(f"{WORK_DIR}/tunnel.log", "w")
TUNNEL_PROC = subprocess.Popen([
    f"{WORK_DIR}/cloudflared", "tunnel", "--url", "http://localhost:8080", "--no-autoupdate"
], stdout=tlog, stderr=tlog)

# Extract and report URL
url = None
for _ in range(30):
    time.sleep(2)
    txt = open(f"{WORK_DIR}/tunnel.log").read()
    m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", txt)
    if m:
        url = m.group(0)
        break

if url:
    print("\n" + "="*60)
    print("🎉 DEPLOYED MASTER HUB!")
    print(f"Live URL: {url}/v1")
    print("="*60)

# Keep supervision loop
try:
    while True:
        time.sleep(2)
        if SERVER_PROC and SERVER_PROC.poll() is not None:
            print("Restarting server...")
            start_model(CURRENT_MODEL)
        if TUNNEL_PROC and TUNNEL_PROC.poll() is not None:
            print("Restarting tunnel...")
            TUNNEL_PROC = subprocess.Popen([
                f"{WORK_DIR}/cloudflared", "tunnel", "--url", "http://localhost:8080", "--no-autoupdate"
            ], stdout=tlog, stderr=tlog)
except KeyboardInterrupt:
    print("Halting...")
    subprocess.run("pkill -f 'llama-server|cloudflared'", shell=True)
