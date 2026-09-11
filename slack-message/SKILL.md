---
name: slack-message
description: Send a Slack message via the configured incoming webhook. Use this skill whenever the user asks to "send a slack message", "notify slack", "post to slack", "send notification to slack", "notify", "alert the team", "let the team know", or wants to message/mention someone on Slack — even if they just say "notify" or "send a message" without naming Slack explicitly.
version: 2.0.0
---

# Slack Message Skill

Send messages to Slack via the configured incoming webhook, using the bundled script.

## How to Send a Slack Message

```bash
/opt/miniconda3/envs/claude-sandbox/bin/python ~/.claude/skills/slack-message/scripts/slack_message.py "your message here"
```

To @-mention someone, add `--user` with their raw Slack user ID (e.g. `U012AB3CD`):

```bash
/opt/miniconda3/envs/claude-sandbox/bin/python ~/.claude/skills/slack-message/scripts/slack_message.py "please review the latest PR" --user U012AB3CD
```

The webhook URL is loaded from `SLACK_WEB_HOOK` in `~/.claude/.env` — never hardcode it in this file or in any command.

## Adding your own aliases (optional)

If you frequently mention the same few people, add short aliases to the
`KNOWN_USERS` dict at the top of `scripts/slack_message.py` (e.g. `"me": "U0123..."`)
so you can pass `--user me` instead of the raw ID. Keep teammates' Slack IDs out
of anything you share publicly.

## Notes

- The script prints `Message sent.` on success; report failures to the user with the error it prints.
- This replaces the older `notify` and `notify-slack` skills (removed 2026-09-11) — both did the same thing, one with a webhook hardcoded in plaintext, the other pointing at a script that no longer exists.
