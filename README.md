# Kaggle LLM Deploy Scripts

Free, copy-paste deploy scripts for running LLMs on Kaggle's free GPU tier (T4×2, 30 hrs/week).

## Quick Start

### 1. Prerequisites
- Kaggle account (free)
- Phone/PC browser for Kaggle UI

### 2. Create Kaggle Dataset for Model Storage (one-time)
```
kaggle.com/datasets → New Dataset → Name: "models" → Private → Save
```
Note your dataset slug: `yourusername/models`

### 3. Upload Models to Dataset (one-time, from any machine with Python)
```bash
pip install -U 'huggingface_hub[cli]'

# Qwen3.8-27B-abliterated (BEST for Kaggle)
huggingface-cli download huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF \
  --include '*UD-DW-Q4_K_M.gguf' --local-dir ./models

# Dolphin-24B (optional)
huggingface-cli download bartowski/cognitivecomputations_Dolphin3.0-Mistral-24B-GGUF \
  --include '*Q4_K_M.gguf' --local-dir ./models

# Gemma-31B QAT abliterated (optional)
huggingface-cli download huihui-ai/Huihui-gemma-4-31B-it-qat-q4_0-unquantized-abliterated-GGUF \
  --include '*Q4_K.gguf' --local-dir ./models

# Upload to Kaggle dataset
kaggle datasets version -p ./models -m "add models"
```

## Scripts

### `kaggle_tahsine_setup.py` — Full Pipeline (Qwen 32B, etc.)
**Best for:** Serving your own models with full control

```python
# 1. Kaggle → New Notebook → GPU T4×2, Internet ON
# 2. Add Data → yourusername/models → mount at /kaggle/input/models
# 3. Paste this entire script into a cell, edit MODEL_PATH, run
```

**Features:**
- Builds llama.cpp with CUDA for T4 (compute 75)
- Loads model from your dataset (persists across sessions)
- OpenAI-compatible server on port 8080
- Cloudflare Quick Tunnel (public `trycloudflare.com` URL)
- STOP cell preserves GPU quota

### `kaggle_bugtrace_setup.py` — Single Cell All-in-One
**Best for:** Fastest deploy, zero config

```python
# 1. Kaggle → New Notebook → GPU T4×2, Internet ON
# 2. Add Data → your dataset with BugTraceAI model
# 3. Paste entire script, edit MODEL_REPO/MODEL_FILE/DATASET_SLUG, run
```

**Features:**
- Auto libcuda fix
- CUDA llama-cpp-python install
- Model load + warm-up
- Server + tunnel in one cell

### `kaggle_horde_worker.py` — AI Horde Worker
**Best for:** Earning kudos for your API key (faster Horde requests)

```python
# 1. Kaggle → New Notebook → GPU T4×2, Internet ON
# 2. Paste script, verify API_KEY, run
# 3. Worker runs until Ctrl+C or 9h session limit
```

**Features:**
- Downloads lightweight models (Qwen 3B, Llama 1B)
- Runs Haidra bridge_alchemy.py
- Earns kudos → priority queue for your requests

### `ep.py` — Endpoint CLI Wrapper (myth-tools/endpoint)
**Best for:** Managing endpoints from your phone terminal

```bash
# Install once
python3 ep.py install

# Then use from anywhere
ep boot          # Interactive GPU/model picker
ep register      # Optional: Cloudflare Worker proxy
ep logs          # View logs
ep stop          # Stop endpoint
ep status        # Check status
```

### `deploy.py` — Unified Launcher
```bash
python3 deploy.py list       # Show all
python3 deploy.py tahsine    # Run tahsine script
python3 deploy.py bugtrace   # Run bugtrace script
python3 deploy.py horde      # Run horde script
python3 deploy.py endpoint   # Run endpoint CLI
```

## Model Recommendations for Kaggle T4×2 (32GB VRAM)

| Model | VRAM | Quality | Uncensored | Dataset Path |
|-------|------|---------|------------|--------------|
| **Qwen3.8-27B-abliterated** | 16.6 GB | ⭐⭐⭐⭐⭐ | ~19% refusals | `huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF/UD-DW-Q4_K_M.gguf` |
| **Dolphin-3.0-Mistral-24B** | 14.3 GB | ⭐⭐⭐⭐ | ~5% refusals | `bartowski/cognitivecomputations_Dolphin3.0-Mistral-24B-GGUF/Q4_K_M.gguf` |
| **Gemma-4-31B-abliterated QAT** | 18.7 GB | ⭐⭐⭐⭐ | 0% hard refusals | `huihui-ai/Huihui-gemma-4-31B-it-qat-q4_0-unquantized-abliterated-GGUF/Q4_K.gguf` |
| BugTraceAI-Apex-G4-26B | ~15 GB | ⭐⭐⭐⭐ | Uncensored | `TheBloke/BugTraceAI-Apex-G4-26B-GGUF/Q4_K_M.gguf` |

## Kubernetes-Style Persistent Deploy (Advanced)

For 24/7 serving without Kaggle's 9h/30h limits:

```bash
# RunPod (cheapest 24/7)
# 1. runpod.io → Pod → A100 40GB ($0.39/hr) or 2×A6000 48GB ($0.29/hr)
# 2. Same script works, just change GPU count

# Vast.ai (cheapest spot)
# vast.ai → search "RTX 3090/4090" → $0.15-0.30/hr
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `CUDA error` | Ensure GPU T4×2 selected in notebook settings |
| `OOM` | Reduce `-ngl` (GPU layers) or use smaller model |
| Tunnel URL not found | Wait longer, check `/kaggle/working/tunnel.log` |
| Session dies at 9h | Hard limit — restart notebook |
| Quota exhausted | 30 hrs/week resets Monday — run STOP cell always |

## Automation Ideas (PRs Welcome)

- [ ] GitHub Action: Auto-test scripts on schedule
- [ ] Telegram bot: `/deploy tahsine` → creates Kaggle notebook via API
- [ ] Cron: Auto-push model updates to dataset weekly
- [ ] LiteLLM config generator: `deploy.py litellm` → outputs `config.yaml`
- [ ] Health check endpoint: `/health` + `/metrics` for monitoring

## License

MIT — Use freely, contribute back.

## Links

- **Repo:** https://github.com/rc6962/kaggle-deploy
- **Raw scripts:** https://raw.githubusercontent.com/rc6962/kaggle-deploy/master/
- **AI Horde:** https://aihorde.net (get API key, earn kudos)
- **Kaggle GPU:** https://kaggle.com/code (30 hrs/week free T4×2)