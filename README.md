# ai-skills

A collection of [Claude Code](https://claude.com/claude-code) Skills — small,
self-contained bundles of instructions (and sometimes scripts) that teach
Claude Code how to do a specific task well, so it doesn't have to reinvent the
approach every time.

Each skill is a folder with a `SKILL.md` (frontmatter + instructions) and an
optional `scripts/` directory. To use one, copy its folder into
`~/.claude/skills/`:

```bash
cp -r local-llm ~/.claude/skills/
```

Claude Code picks up skills automatically based on the `description` in each
`SKILL.md`'s frontmatter — no restart or registration step needed.

## What's in here

| Skill | What it does |
|---|---|
| [`local-llm`](local-llm) | Delegates simple, high-volume subtasks (classification, extraction, batch rewriting) to a local Ollama model instead of burning cloud tokens on mechanical work. Includes guidance on when delegating makes sense vs. when it doesn't. |
| [`slack-message`](slack-message) | Sends a message to Slack via an incoming webhook, with optional `--user` @-mention. Secrets load from a local `.env`, never hardcoded. |
| [`claude-backup`](claude-backup) / [`claude-restore`](claude-restore) | Backs up Claude Code skills/settings to a zip on Google Drive (or any synced folder) and restores them safely — comparing content hash first and warning instead of clobbering when the local copy is newer. Useful for keeping two machines in sync without blind overwrites. |
| [`env-tmux`](env-tmux) | Starts a long-running command in a named tmux session with your `.env` injected, so background processes survive and stay easy to find/attach to later. |
| [`imessage-send`](imessage-send) | Sends a single iMessage on macOS via AppleScript/`osascript`, including the fix for the common `service "iMessage"` resolution error. |
| [`trail-map`](trail-map) | Turns a GPX track into a styled trail map — fetches OpenStreetMap data, renders it, and optionally re-styles it as a hand-drawn illustration via GPT Image. |
| [`fallout-blueprint`](fallout-blueprint) | Generates Fallout-style vault blueprint images from a prompt using GPT Image. |
| [`bark`](bark) | Sends an encrypted push notification to iOS via the [Bark](https://github.com/Finb/Bark) app. |
| [`linkedin-post`](linkedin-post) | Drafts and posts LinkedIn content, with a "confirm the draft before publishing" gate — a pattern worth borrowing for any skill that posts something publicly on your behalf. |

## Notes on adapting these

A few skills reference machine-specific paths or a runtime convention
(`/opt/miniconda3/envs/claude-sandbox/bin/python`) that made sense on the
machine these were written on — swap in your own Python interpreter and paths.
Places to check:

- `claude-backup` / `claude-restore` read a `CLAUDE_BACKUP_DIR` environment
  variable for where backups live (defaults to a Google Drive path — set it to
  wherever you actually want backups to go).
- `trail-map` clones a companion rendering repo
  ([`map-creator`](https://github.com/Hatari130/map-creator)) into
  `MAP_CREATOR_DIR` (defaults to `~/dev/3rd-party/map-creator`, override via
  the env var) — it's a separate public repo this skill depends on.
- `slack-message` has an empty `KNOWN_USERS` alias dict in
  `scripts/slack_message.py` — add your own short aliases for people you
  @-mention often, or just pass raw Slack user IDs.

None of these skills hardcode API keys, tokens, or webhook URLs — they all load
secrets at runtime from a local `.env` file that is never committed. If you
adapt one of these for your own use, keep that pattern.

## License

MIT — do whatever you want with these.
