#!/usr/bin/env python3
"""
Endpoint CLI wrapper — myth-tools/endpoint
Install once, then use `ep` command to manage Kaggle LLM endpoints from your phone.
"""

import os, subprocess, sys, shutil

def install_endpoint():
    """Install endpoint CLI from local clone."""
    repo = "/data/data/com.termux/files/home/kaggle_notebooks/endpoint"
    if not os.path.exists(repo):
        print("Cloning myth-tools/endpoint...")
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/myth-tools/endpoint.git", repo], check=True)
    
    print("Installing endpoint...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", repo], check=True)
    print("✓ endpoint installed")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  ep install          # Install endpoint CLI")
        print("  ep boot             # Start Kaggle GPU + pick model (interactive)")
        print("  ep register         # Register Cloudflare Worker proxy (optional)")
        print("  ep logs             # Show endpoint logs")
        print("  ep stop             # Stop endpoint")
        print("  ep status           # Check endpoint status")
        return 0

    cmd = sys.argv[1]

    if cmd == "install":
        install_endpoint()
    
    elif cmd in ("boot", "register", "logs", "stop", "status"):
        # Run endpoint command
        try:
            subprocess.run(["endpoint", cmd] + sys.argv[2:], check=True)
        except FileNotFoundError:
            print("endpoint not installed. Run: ep install")
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")
    
    else:
        print(f"Unknown command: {cmd}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())