#!/usr/bin/env python3
"""
Run the tier's text reasoning LLM via Ollama.
Takes a prompt (from child reports + own gestalt), prints integrated paragraph.
Handles sequential load/unload via Ollama's lazy-load mechanism.
"""
import argparse
import json
import requests
import sys


def run_ollama(model: str, prompt: str, ollama_url: str = "http://localhost:11434") -> str:
    """Send prompt to Ollama and return the response text."""
    url = f"{ollama_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return f"ERROR: cannot connect to Ollama at {ollama_url}"
    except requests.exceptions.Timeout:
        return "ERROR: Ollama request timed out (300s)"
    except Exception as e:
        return f"ERROR: {e}"


def main():
    parser = argparse.ArgumentParser(description="Run text reasoner via Ollama")
    parser.add_argument("--model", required=True, help="Ollama model tag (e.g. qwen3:8b)")
    parser.add_argument("--prompt", help="Prompt text (or read from stdin if omitted)")
    parser.add_argument("--prompt-file", help="Read prompt from file")
    parser.add_argument("--ollama-url", default="http://localhost:11434",
                        help="Ollama API URL (default: http://localhost:11434)")
    args = parser.parse_args()

    if args.prompt_file:
        with open(args.prompt_file) as f:
            prompt = f.read()
    elif args.prompt:
        prompt = args.prompt
    else:
        prompt = sys.stdin.read()

    if not prompt.strip():
        print("ERROR: empty prompt", file=sys.stderr)
        sys.exit(1)

    result = run_ollama(args.model, prompt, args.ollama_url)
    print(result)


if __name__ == "__main__":
    main()
