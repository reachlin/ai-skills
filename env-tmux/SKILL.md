---
name: env-tmux
description: Start a new tmux session with environment variables injected from a .env file. Use this skill whenever the user wants to start a tmux session loaded with env vars or secrets, says "start a secure session", "new session with env", "tmux with env vars", "load env into tmux", or wants a clean session with credentials or config from a file. Trigger even if they just say "secure session" or "env session".
---

Start a detached tmux session named `secure-<random>` with environment variables from a file injected into the shell.

## Steps

1. Determine the env file — ask the user if not mentioned (default: `.env` in the current directory)
2. Run the bundled script:
   ```
   bash ~/.claude/skills/env-tmux/scripts/start-env-session.sh [path/to/env-file]
   ```
3. Report the session name and attach command to the user

## Env file format

The script handles both formats and ignores blank lines and `#` comments:
```
KEY=VALUE
export KEY=VALUE
```

## After creation

The session is detached — the user attaches to it themselves:
```
tmux attach -t secure-a3f2c1
```

Let the user know the session name so they can run commands in it.
