#!/usr/bin/env python3
"""Send an encrypted Bark push (AES-256-GCM). Run with the claude-sandbox python.

Usage:
  send_encrypted.py --body "text" [--title "text"] [--sound name]
  send_encrypted.py --markdown "**bold** text\n- item" [--title "text"]
"""
import argparse
import base64
import json
import os
import secrets
import string
import subprocess

from Crypto.Cipher import AES
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.claude/.env"))

DEVICE_KEY = os.environ["BARK_DEVICE_KEY"]
AES_KEY = os.environ["BARK_AES_KEY"]  # 32 ASCII chars -> AES-256, GCM mode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body")
    parser.add_argument("--title")
    parser.add_argument("--sound")
    parser.add_argument("--markdown", help="Markdown text; rendered to plain text as the body on-device")
    args = parser.parse_args()
    if not args.body and not args.markdown:
        parser.error("one of --body or --markdown is required")

    alphabet = string.ascii_letters + string.digits
    iv = "".join(secrets.choice(alphabet) for _ in range(12))

    payload = {}
    if args.body:
        payload["body"] = args.body
    if args.markdown:
        payload["markdown"] = args.markdown
        payload.setdefault("body", "New message")  # fallback text before on-device markdown parsing
    if args.title:
        payload["title"] = args.title
    if args.sound:
        payload["sound"] = args.sound
    plaintext = json.dumps(payload).encode("utf-8")

    cipher = AES.new(AES_KEY.encode("utf-8"), AES.MODE_GCM, nonce=iv.encode("utf-8"))
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    ciphertext_b64 = base64.b64encode(ciphertext + tag).decode("utf-8")

    result = subprocess.run(
        [
            "curl", "-s",
            "--get", f"https://api.day.app/{DEVICE_KEY}",
            "--data-urlencode", f"ciphertext={ciphertext_b64}",
            "--data-urlencode", f"iv={iv}",
        ],
        capture_output=True, text=True,
    )
    print("payload:", plaintext.decode("utf-8"))
    print("iv:", iv)
    print("response:", result.stdout)


if __name__ == "__main__":
    main()
