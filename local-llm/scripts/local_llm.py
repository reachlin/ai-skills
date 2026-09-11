#!/usr/bin/env python3
"""Send one task to the local Ollama model and print its response.

Usage:
    /opt/miniconda3/envs/claude-sandbox/bin/python local_llm.py "<prompt>" [--input-file PATH] [--model NAME]

The prompt should be fully self-contained (task instructions + any inline
data). For larger data, put it in a file and pass --input-file; its contents
are appended after the prompt.
"""
import argparse
import sys

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:7b-instruct"


def check_server() -> bool:
    try:
        requests.get("http://localhost:11434/api/version", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False


def ask(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 120) -> str:
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", help="Full task prompt for the local model")
    parser.add_argument("--input-file", help="Optional file whose contents get appended to the prompt")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model name (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    if not check_server():
        print(
            "ERROR: Ollama server not reachable at localhost:11434.\n"
            "Start it in tmux with: tmux new-session -d -s ollama-serve \"ollama serve\"",
            file=sys.stderr,
        )
        return 1

    prompt = args.prompt
    if args.input_file:
        with open(args.input_file, "r") as f:
            prompt = f"{prompt}\n\n{f.read()}"

    try:
        print(ask(prompt, model=args.model))
    except requests.exceptions.RequestException as e:
        print(f"ERROR: request to Ollama failed: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
