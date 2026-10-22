#!/usr/bin/env python3
"""
Unified Kaggle Deploy Launcher
Run: python3 deploy.py <command>

Commands:
  tahsine    - Full llama.cpp server (Qwen 32B etc)
  bugtrace   - Single-cell BugTraceAI Apex G4 26B
  horde      - AI Horde worker (earn kudos)
  endpoint   - myth-tools endpoint CLI wrapper
  list       - Show all available scripts
"""

import os, sys, subprocess

SCRIPTS = {
    "tahsine": "kaggle_tahsine_setup.py",
    "bugtrace": "kaggle_bugtrace_setup.py",
    "horde": "kaggle_horde_worker.py",
    "endpoint": "ep.py",
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "list"):
        print(__doc__)
        print("\nAvailable:")
        for k, v in SCRIPTS.items():
            path = os.path.join(os.path.dirname(__file__), v)
            status = "✓" if os.path.exists(path) else "✗"
            print(f"  {status} {k:10s} -> {v}")
        return 0

    cmd = sys.argv[1]
    if cmd not in SCRIPTS:
        print(f"Unknown: {cmd}")
        return 1

    script = os.path.join(os.path.dirname(__file__), SCRIPTS[cmd])
    if not os.path.exists(script):
        print(f"Missing: {script}")
        return 1

    # Pass remaining args to the script
    os.execv(sys.executable, [sys.executable, script] + sys.argv[2:])

if __name__ == "__main__":
    sys.exit(main())