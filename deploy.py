#!/usr/bin/env python3
"""
Unified Kaggle Deploy Launcher
Usage: python3 deploy.py [model] [--list]

Models:
  rvn       - Qwen3.8-27B RVN Heretic (best balance, 16.5GB) ← RECOMMENDED
  gemma31   - Gemma-4-31B DECKARD HERETIC (best Gemma, 18GB, needs offload)
  tahsine   - Full pipeline (original tahsine script)
  bugtrace  - Single-cell BugTraceAI
  horde     - AI Horde worker
"""

import sys, os, subprocess

SCRIPTS = {
    "rvn": "kaggle_rvn_qwen38.py",
    "gemma31": "kaggle_gemma31_deckard.py",
    "tahsine": "kaggle_tahsine_setup.py",
    "bugtrace": "kaggle_bugtrace_setup.py",
    "horde": "kaggle_horde_worker.py",
}

MODEL_INFO = {
    "rvn": "Qwen3.8-27B RVN Heretic Abliterated — 16.5GB, W10~7-8, Hazardous~3-4, 0-1% refusals, fits T4×2 perfectly",
    "gemma31": "Gemma-4-31B DECKARD HERETIC — 18GB, W10 9.2, W10-Direct 10, Hazardous 4.7, needs CPU offload",
    "tahsine": "Full pipeline (Qwen 32B etc) — original 3-notebook pipeline",
    "bugtrace": "Single-cell BugTraceAI Apex G4 26B — fastest single cell",
    "horde": "AI Horde worker — earns kudos for your API key",
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        print("\nAvailable models:")
        for k, v in MODEL_INFO.items():
            print(f"  {k:10s} — {v}")
        return

    if sys.argv[1] == "--list":
        for k, v in MODEL_INFO.items():
            print(f"{k}: {v}")
        return

    model = sys.argv[1]
    if model not in SCRIPTS:
        print(f"Unknown model: {model}")
        print("Run: python3 deploy.py --list")
        return

    script = SCRIPTS[model]
    script_path = os.path.join(os.path.dirname(__file__), script)
    
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        return

    print(f"Running {model} deploy script...")
    print(f"Script: {script}")
    print("="*60)
    
    # Run the script
    result = subprocess.run([sys.executable, script_path], timeout=1800)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()