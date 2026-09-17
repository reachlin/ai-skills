#!/usr/bin/env python3
"""Benchmark a local Ollama model against a fixed 10-level capability rubric.

Level 10 == Sonnet 5 baseline (full multi-step reasoning, code review, judgment
calls under ambiguity). Level 1 == trivial fixed-format lookup/copy. Each lower
level is a task type the local-llm skill would consider delegating.

This does NOT auto-grade every case (some are open-ended rewriting/reasoning
tasks). It runs each case, applies an automatic check where one exists, and
prints raw output for the rest so a human (or Claude) reads and scores it.

Usage:
    /opt/miniconda3/envs/claude-sandbox/bin/python capability_benchmark.py [--model NAME]
"""
import argparse
import re
import sys

from local_llm import ask, check_server, DEFAULT_MODEL

CASES = [
    # Level 1 - trivial fixed-format lookup/copy
    dict(level=1, id="1a", task="Sentiment (obvious)",
         prompt='Classify the sentiment of this sentence as exactly one word: POSITIVE, NEGATIVE, or NEUTRAL. Reply with only that word.\n\nSentence: "I love this product, it is amazing!"',
         check=lambda out: "POSITIVE" in out.upper() and "NEGATIVE" not in out.upper()),
    dict(level=1, id="1b", task="Case transform",
         prompt='Reply with only the uppercase version of this word, nothing else: "hello"',
         check=lambda out: out.strip().upper().strip('."\'') == "HELLO"),

    # Level 2 - simple classification with light ambiguity
    dict(level=2, id="2a", task="Log severity classification",
         prompt='Classify this log line as exactly one word: ERROR, WARN, or INFO. Reply with only that word.\n\nLog line: "ERROR: Connection refused to database"',
         check=lambda out: "ERROR" in out.upper() and "WARN" not in out.upper() and out.upper().count("INFO") == 0),
    dict(level=2, id="2b", task="Log severity classification (non-obvious keyword)",
         prompt='Classify this log line as exactly one word: ERROR, WARN, or INFO. Reply with only that word.\n\nLog line: "Payment succeeded for order #4521"',
         check=lambda out: "INFO" in out.upper() and "ERROR" not in out.upper() and "WARN" not in out.upper()),

    # Level 3 - single-record structured field extraction
    dict(level=3, id="3a", task="Extract name+email",
         prompt='Extract the name and email from this sentence. Reply with only valid JSON: {"name": "...", "email": "..."}\n\nSentence: "Please contact John Smith at john.smith@example.com for details."',
         check=lambda out: "john.smith@example.com" in out and "John Smith" in out),
    dict(level=3, id="3b", task="Extract order id+amount",
         prompt='Extract the order id and dollar amount from this sentence. Reply with only valid JSON: {"order_id": "...", "amount": "..."}\n\nSentence: "Order #78219 was charged $45.20"',
         check=lambda out: "78219" in out and "45.20" in out),

    # Level 4 - batch classification/extraction, order-preserving, strict format
    dict(level=4, id="4a", task="Batch log classification (8 lines, order-preserving)",
         prompt=(
             'Classify each log line below as ERROR, WARN, or INFO. '
             'Reply with exactly 8 lines, one label per line, same order as input, nothing else.\n\n'
             "1. ERROR: disk full on /var\n"
             "2. User login successful\n"
             "3. WARN: retrying connection (attempt 2/3)\n"
             "4. Order #991 shipped\n"
             "5. ERROR: null pointer exception in handler\n"
             "6. Cache miss for key user:412\n"
             "7. WARN: deprecated API called\n"
             "8. Health check passed\n"
         ),
         check=lambda out: [x.strip().upper() for x in re.findall(r"(ERROR|WARN|INFO)", out.upper())] ==
                            ["ERROR", "INFO", "WARN", "INFO", "ERROR", "INFO", "WARN", "INFO"]),
    dict(level=4, id="4b", task="Batch numeric extraction (6 lines, order-preserving)",
         prompt=(
             'Extract only the HTTP status code from each line below. '
             'Reply with exactly 6 lines, one number per line, same order, nothing else.\n\n'
             "1. GET /api/orders -> 200 OK\n"
             "2. POST /api/login -> 401 Unauthorized\n"
             "3. GET /api/missing -> 404 Not Found\n"
             "4. GET /api/health -> 200 OK\n"
             "5. POST /api/upload -> 500 Internal Server Error\n"
             "6. GET /api/cart -> 200 OK\n"
         ),
         check=lambda out: re.findall(r"\d{3}", out) == ["200", "401", "404", "200", "500", "200"]),

    # Level 5 - rewriting/summarization preserving key facts (manual grade)
    dict(level=5, id="5a", task="One-sentence summary preserving a number",
         prompt=(
             "Summarize this paragraph in exactly one sentence, preserving the specific dollar figure mentioned:\n\n"
             "The team spent the last quarter migrating the billing pipeline off the legacy database. "
             "The migration took longer than expected due to data validation issues. "
             "In total the project cost $128,000 in engineering time. "
             "The new pipeline is now live in production. "
             "No customer-facing downtime was reported during the cutover."
         ),
         check=None),
    dict(level=5, id="5b", task="Tone rewrite preserving facts",
         prompt=(
             "Rewrite this message in a professional tone, keeping the meeting time and location exactly as given:\n\n"
             "hey can we push our sync to 3pm thursday? also lets do it in the 4th floor conf room instead of zoom, "
             "i think its easier to just talk in person lol"
         ),
         check=None),

    # Level 6 - structured extraction with ambiguity / inference required
    dict(level=6, id="6a", task="Extract from messy signature block",
         prompt=(
             'Extract name, phone, and company from this email signature. Reply with only valid JSON: '
             '{"name": "...", "phone": "...", "company": "..."}. If company is not explicitly labeled, infer it from context.\n\n'
             "Signature:\n"
             "Best,\nMaria Chen\nSr. Product Manager | Chowbus\n(415) 555-0182\n"
             "www.chowbus.com"
         ),
         check=lambda out: "Maria Chen" in out and "555-0182" in out and "chowbus" in out.lower()),
    dict(level=6, id="6b", task="Inferred severity + impact from support ticket",
         prompt=(
             'Read this support ticket and reply with only valid JSON: '
             '{"severity": "critical|high|medium|low", "affected_service": "...", "customer_impact": "yes|no"}. '
             'Severity and customer_impact are not stated directly - infer them from the description.\n\n'
             "Ticket: \"Multiple restaurants report that credit card payments are failing at checkout since ~2pm. "
             "Cash payments still work fine. This started right after the payments-service deploy this morning.\""
         ),
         check=None),

    # Level 7 - light reasoning / arithmetic / rule application
    dict(level=7, id="7a", task="Arithmetic word problem",
         prompt='A cart has 3 items priced $12, $8, and $15. A 10% discount applies to the total. What is the final total after discount? Reply with only the dollar amount, e.g. "$31.50".',
         check=lambda out: "31.50" in out or "31.5" in out),
    dict(level=7, id="7b", task="Apply a rule table (not memorized labels)",
         prompt=(
             "Apply this rule table to classify each status code below:\n"
             "- 500-599 -> critical\n"
             "- 400-499 -> warning\n"
             "- everything else -> info\n\n"
             "Codes: 503, 201, 404, 302, 500\n"
             "Reply with exactly 5 lines, one label per line, same order, nothing else."
         ),
         check=lambda out: [l.strip().lower() for l in out.strip().splitlines() if l.strip()][:5] ==
                            ["critical", "info", "warning", "info", "critical"]),

    # Level 8 - multi-step reasoning / cross-referencing within one prompt
    dict(level=8, id="8a", task="Correlate two timelines to find root cause",
         prompt=(
             "Deploy A went out at 14:02 and touched the payments-service. "
             "Deploy B went out at 14:15 and touched the notifications-service. "
             "Error rate on payments-service started climbing at 14:05 and has stayed elevated since. "
             "Notifications-service has had no errors. "
             "Which deploy most likely caused the regression, and why? Answer in one sentence."
         ),
         check=None),
    dict(level=8, id="8b", task="Dependency ordering",
         prompt=(
             "Service A depends on Service B. Service B depends on Service C. Service D depends on Service A. "
             "Give the correct deployment order (dependencies first). Reply with only a comma-separated list of letters."
         ),
         check=lambda out: re.sub(r"[^A-D,]", "", out.upper()).replace(",,", ",").strip(",") == "C,B,A,D"),

    # Level 9 - technical/code reasoning
    dict(level=9, id="9a", task="Find the bug in a short function",
         prompt=(
             "Find the bug in this Python function and explain the fix in one sentence:\n\n"
             "def get_last_n(items, n):\n"
             "    result = []\n"
             "    for i in range(n):\n"
             "        result.append(items[i])\n"
             "    return result\n\n"
             "(It's supposed to return the LAST n items of the list, not the first n.)"
         ),
         check=None),
    dict(level=9, id="9b", task="Regex comprehension",
         prompt=(
             'Does the regex ^[a-z0-9]+(\\.[a-z0-9]+)*@[a-z0-9]+\\.[a-z]{2,}$ match the string '
             '"john..smith@example.com"? Answer yes or no and explain why in one sentence.'
         ),
         check=lambda out: out.strip().lower().startswith("no")),

    # Level 10 - Sonnet-5-baseline complex reasoning / judgment under ambiguity
    dict(level=10, id="10a", task="Constraint scheduling",
         prompt=(
             "Assign 4 tasks (W, X, Y, Z) to 2 people (Alice, Bob) such that each person gets 2 tasks, "
             "total effort per person is balanced, and Alice cannot do task Z (she lacks access). "
             "Effort: W=5, X=3, Y=4, Z=2. Give the assignment and reasoning."
         ),
         check=None),
    dict(level=10, id="10b", task="Cross-referenced security review",
         prompt=(
             "An ECS task role's assume-role policy trusts both 's3.amazonaws.com' and 'ecs-tasks.amazonaws.com' as "
             "principals, but nothing in the codebase ever has S3 assume this role directly. Separately, the role has "
             "an attached policy granting s3:* on one bucket ARN. Is the extra 's3.amazonaws.com' trust principal a "
             "security concern, and why or why not? Answer in 2-3 sentences."
         ),
         check=None),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if not check_server():
        print("ERROR: Ollama server not reachable at localhost:11434.", file=sys.stderr)
        return 1

    for case in CASES:
        try:
            data = ask(case["prompt"], model=args.model, timeout=120)
            output = data["message"]["content"]
        except Exception as e:
            output = f"<ERROR: {e}>"

        auto = None
        if case["check"] is not None:
            try:
                auto = bool(case["check"](output))
            except Exception:
                auto = False

        print(f"=== L{case['level']} [{case['id']}] {case['task']} ===")
        print(f"--- output ---\n{output.strip()}\n")
        print(f"auto_check: {auto if auto is not None else 'MANUAL REVIEW NEEDED'}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
