#!/usr/bin/env bash
# Start a detached tmux session with env vars injected from a file.

ENV_FILE="${1:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: env file '$ENV_FILE' not found" >&2
  exit 1
fi

# Generate a random session name like "secure-a3f2c1"
SESSION_NAME="secure-$(openssl rand -hex 3 2>/dev/null || cat /dev/urandom | LC_ALL=C tr -dc 'a-f0-9' | head -c 6)"

# Parse env file into -e KEY=VALUE args for tmux
TMUX_ENV_ARGS=()
while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip blank lines and comments
  [[ -z "${line//[[:space:]]/}" ]] && continue
  [[ "$line" =~ ^[[:space:]]*# ]] && continue

  # Strip leading "export " if present
  line="${line#export }"
  line="${line#"${line%%[! ]*}"}"  # ltrim

  # Must be KEY=VALUE form
  [[ "$line" != *=* ]] && continue

  TMUX_ENV_ARGS+=(-e "$line")
done < "$ENV_FILE"

tmux new-session -d -s "$SESSION_NAME" "${TMUX_ENV_ARGS[@]}"

echo "Session : $SESSION_NAME"
echo "Attach  : tmux attach -t $SESSION_NAME"
echo "Env file: $ENV_FILE (${#TMUX_ENV_ARGS[@]} vars loaded)"
