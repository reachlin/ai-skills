#!/usr/bin/env python3
"""Send a message to Slack via the configured incoming webhook.

Usage:
    python slack_message.py "message text" [--user USER_ID_OR_ALIAS]

Add your own aliases to KNOWN_USERS below (resolved to Slack user IDs for
@-mention), e.g. "me": "U0123ABCD". Otherwise pass a raw Slack user ID directly.
"""
import argparse
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.claude/.env"))

KNOWN_USERS = {
    # "me": "U0123ABCD",
}


def resolve_user(user: str) -> str:
    return KNOWN_USERS.get(user.lower(), user)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", help="Message text to send")
    parser.add_argument("--user", help="Slack user ID or known alias to @-mention")
    args = parser.parse_args()

    webhook = os.environ.get("SLACK_WEB_HOOK")
    if not webhook:
        print("ERROR: SLACK_WEB_HOOK not set in ~/.claude/.env", file=sys.stderr)
        return 1

    text = args.message
    if args.user:
        text = f"<@{resolve_user(args.user)}> {text}"

    resp = requests.post(webhook, json={"text": text}, timeout=10)
    if resp.text.strip() != "ok":
        print(f"ERROR: Slack returned unexpected response: {resp.status_code} {resp.text}", file=sys.stderr)
        return 1

    print("Message sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
