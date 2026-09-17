#!/usr/bin/env python3
"""Summarize local-llm delegation usage: call count and tokens offloaded from Claude.

Usage:
    /opt/miniconda3/envs/claude-sandbox/bin/python usage_summary.py
"""
import json
from collections import defaultdict
from pathlib import Path

USAGE_LOG = Path(__file__).resolve().parent.parent / "usage_log.jsonl"


def main() -> int:
    if not USAGE_LOG.exists():
        print("No usage recorded yet.")
        return 0

    total_calls = 0
    total_prompt_tokens = 0
    total_response_tokens = 0
    by_model = defaultdict(lambda: {"calls": 0, "prompt_tokens": 0, "response_tokens": 0})

    with open(USAGE_LOG) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            total_calls += 1
            total_prompt_tokens += entry.get("prompt_tokens", 0)
            total_response_tokens += entry.get("response_tokens", 0)
            m = by_model[entry.get("model", "unknown")]
            m["calls"] += 1
            m["prompt_tokens"] += entry.get("prompt_tokens", 0)
            m["response_tokens"] += entry.get("response_tokens", 0)

    total_tokens = total_prompt_tokens + total_response_tokens
    print(f"Total calls: {total_calls}")
    print(f"Total tokens offloaded (prompt + response, local model's count): {total_tokens}")
    print(f"  prompt tokens:   {total_prompt_tokens}")
    print(f"  response tokens: {total_response_tokens}")
    print()
    print("By model:")
    for model, stats in by_model.items():
        print(f"  {model}: {stats['calls']} calls, {stats['prompt_tokens'] + stats['response_tokens']} tokens")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
