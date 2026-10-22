#!/usr/bin/env python3
"""
Generate LiteLLM config for Kaggle endpoints
Run: python3 gen_litellm.py <tunnel_url> [model_name]
Outputs: litellm_config.yaml
"""

import sys, os, yaml

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gen_litellm.py <tunnel_url> [model_name]")
        print("Example: python3 gen_litellm.py https://abc-123.trycloudflare.com Qwen3.8-27b-Uncensored")
        return 1

    tunnel_url = sys.argv[1].rstrip('/')
    model_name = sys.argv[2] if len(sys.argv) > 2 else "kaggle-model"

    config = {
        "model_list": [
            {
                "model_name": model_name,
                "litellm_params": {
                    "model": f"openai/{model_name}",
                    "api_base": f"{tunnel_url}/v1",
                    "api_key": "sk-kaggle-local",
                    "custom_llm_provider": "openai",
                },
                "model_info": {
                    "max_tokens": 8192,
                    "context_window": 131072,
                }
            }
        ],
        "general_settings": {
            "master_key": "sk-litellm-master",
            "ui": True,
            "telemetry": False,
        },
        "router_settings": {
            "routing_strategy": "simple-shuffle",
            "fallback_models": [],
        }
    }

    output = "litellm_config.yaml"
    with open(output, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Generated {output}")
    print(f"\nRun LiteLLM:")
    print(f"  docker run -p 4000:4000 -v $(pwd)/{output}:/app/config.yaml ghcr.io/berriai/litellm:main-latest --config /app/config.yaml")
    print(f"\nThen use: http://localhost:4000/v1/chat/completions with Authorization: Bearer sk-litellm-master")
    return 0

if __name__ == "__main__":
    sys.exit(main())