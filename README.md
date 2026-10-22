# Kaggle LLM Deploy Scripts

Free, copy-paste deploy scripts for running **uncensored LLMs** on Kaggle's free GPU tier (T4×2, 30 hrs/week).

## 🚀 Quick Start

### Prerequisites (one time)
1. **Kaggle account** → kaggle.com → Sign up
2. **Kaggle API token** → kaggle.com/settings → "Create New Token" → downloads `kaggle.json`
3. **Phone/PC browser** (Kaggle UI doesn't work well in Termux)

### Option 1: One-Command CLI (Easiest)
```bash
# Install endpoint CLI
pip install git+https://github.com/myth-tools/endpoint.git

# Add your Kaggle token
mkdir -p ~/.kaggle
cat > ~/.kaggle/kaggle.json << 'EOF'
{"username":"YOUR_USERNAME","key":"YOUR_API_KEY"}
EOF
chmod 600 ~/.kaggle/kaggle.json

# Deploy with one command
endpoint -g boot
# → Interactive model picker
# → Deploys to Kaggle T4×2
# → Gives you Cloudflare tunnel URL (e.g., https://abc-123.trycloudflare.com/v1)
```

### Option 2: Kaggle Notebook (Copy-Paste)
1. Go to **kaggle.com/code** → **New Notebook**
2. **Settings** → **GPU: T4 x2** → **Internet: ON** → **Save**
3. **Add Data** → **Your Datasets** → Select a dataset with models (or let script download)
4. Copy **ONE** of these scripts into a cell and run:

```bash
# Best overall (recommended)
python3 deploy.py rvn

# Best Gemma (highest W10 score)
python3 deploy.py gemma31

# Original pipelines
python3 deploy.py tahsine
python3 deploy.py bugtrace
python3 deploy.py horde
```

### Option 3: Raw Script URLs (Direct Copy-Paste)
```
https://raw.githubusercontent.com/rc6962/kaggle-deploy/master/kaggle_rvn_qwen38.py
https://raw.githubusercontent.com/rc6962/kaggle-deploy/master/kaggle_gemma31_deckard.py
https://raw.githubusercontent.com/rc6962/kaggle-deploy/master/kaggle_tahsine_setup.py
https://raw.githubusercontent.com/rc6962/kaggle-deploy/master/kaggle_bugtrace_setup.py
https://raw.githubusercontent.com/rc6962/kaggle-deploy/master/kaggle_horde_worker.py
```

---

## 📦 Available Models

| Command | Model | Size | UGI Scores | Notes |
|---------|-------|------|------------|-------|
| `rvn` | **Qwen3.8-27B RVN Heretic** | 16.5 GB | W10 ~7-8, Hazardous ~3-4 | **Best balance** — fits T4×2 perfectly, 0-1% refusals |
| `gemma31` | **Gemma-4-31B DECKARD HERETIC** | 18 GB | **W10 9.2, W10-Direct 10, Hazardous 4.7** | Best Gemma, needs CPU offload |
| `tahsine` | Qwen 32B / various | 22 GB | Varies | Full 3-notebook pipeline |
| `bugtrace` | BugTraceAI Apex G4 26B | 14 GB | — | Fastest single cell |
| `horde` | AI Horde Worker | — | — | Earns kudos for your API key |

---

## 📊 UGI Scores Explained (Layman's Terms)

| Score | What It Means | 0 = | 10 = |
|-------|---------------|-----|------|
| **Hazardous** | "Will it tell me dangerous stuff?" | Refuses all danger | Answers all danger |
| **W/10 (Willingness)** | "How far can I push it?" | Refuses immediately | Never refuses |
| **W10-Direct** | Outright refusal ("I can't help") | Always says no | Never says no |
| **W10-Adherence** | Follows your instruction vs. lecturing | Ignores you, lectures | Does exactly what asked |
| **Entertainment** | Adult content, dark humor | PG, sanitized | Unfiltered |
| **SocPol** | Hot political takes | Evasive, neutral | Opinionated, detailed |

**High scores = model does what you ask without moralizing.**

---

## 🤖 Telegram Bot (Remote Deploy from Anywhere)

### Setup (run on a VPS/always-on machine)
```bash
git clone https://github.com/rc6962/kaggle-deploy.git
cd kaggle-deploy
pip install python-telegram-bot

# Configure
export BOT_TOKEN="your_bot_token_from_@BotFather"
export ADMIN_CHAT_ID="your_telegram_chat_id"

# Run
python3 tg_deploy_bot.py
```

### Usage (from Telegram)
```
/deploy rvn          # Deploy Qwen3.8-27B RVN
/deploy gemma31      # Deploy Gemma-4-31B DECKARD
/deploy tahsine      # Deploy tahsine pipeline
/deploy bugtrace     # Deploy BugTraceAI
/deploy horde        # Start AI Horde worker
/status              # Show running deploys
/stop                # Stop all
/help                # Show help
```

---

## 🌐 Web UI (Run on Phone)

```bash
cd ~/kaggle-deploy
python3 web_ui.py
# Open http://localhost:5000 in phone browser
```

Buttons for: Deploy RVN / Gemma31 / Tahsine / BugTrace / Horde / Status / Stop

---

## 🔧 After Deployment

### Get Your Endpoint URL
After script runs, you'll see:
```
🎉 DEPLOYED! Your OpenAI-compatible endpoint:
  https://abc-123-def.trycloudflare.com/v1
```

### Test It
```bash
curl https://abc-123-def.trycloudflare.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"local","messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'
```

### Use in Hermes (Already Configured)
```bash
hermes chat -q "Your prompt" --provider custom:AI\ Horde -m "Qwen3.8-27b-Uncensored"
```

### Use in LiteLLM / Open WebUI / Cursor
```bash
# Generate LiteLLM config
python3 gen_litellm.py https://abc-123-def.trycloudflare.com/v1 Qwen3.8-27b-Uncensored

# Run LiteLLM proxy
docker run -p 4000:4000 -v $(pwd)/litellm_config.yaml:/app/config.yaml ghcr.io/berriai/litellm:main-latest --config /app/config.yaml
# Now use http://localhost:4000/v1 with Bearer ***
```

---

## ⚠️ Important: Quota Management

**ALWAYS stop when done:**
```bash
# Via CLI
endpoint stop

# Via script (run in Kaggle notebook)
import subprocess
subprocess.run("pkill -f 'llama-server|cloudflared'", shell=True)
```

Kaggle free tier: **30 GPU-hours/week**, **9-hour session max**. Quota resets Monday UTC.

---

## 📁 Repository Structure

```
kaggle-deploy/
├── deploy.py                    # Unified launcher
├── kaggle_rvn_qwen38.py         # Qwen3.8-27B RVN (recommended)
├── kaggle_gemma31_deckard.py    # Gemma-4-31B DECKARD (best Gemma)
├── kaggle_tahsine_setup.py      # Original tahsine pipeline
├── kaggle_bugtrace_setup.py     # BugTraceAI single cell
├── kaggle_horde_worker.py       # AI Horde worker
├── ep.py                        # endpoint CLI wrapper
├── gen_litellm.py               # LiteLLM config generator
├── tg_deploy_bot.py             # Telegram bot
├── web_ui.py                    # Phone web UI
└── README.md                    # This file
```

---

## 🛠 Troubleshooting

| Problem | Fix |
|---------|-----|
| `CUDA error` | Ensure GPU T4×2 selected, Internet ON |
| `OOM` | Use `rvn` (16.5GB), reduce `-ngl` to 80, or use smaller model |
| No tunnel URL | Wait 2 min, check `/kaggle/working/tunnel.log` |
| 9h session limit | Hard cap — restart notebook |
| Quota exhausted | 30 hrs/week resets Monday UTC |
| Model not found | Check HF repo/file name matches exactly |

---

## 📝 License

MIT — Use responsibly. These models have reduced safety guardrails.