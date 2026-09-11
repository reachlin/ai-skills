#!/bin/bash
# Back up Claude Code essentials to a timestamped zip in Google Drive.
# Never includes secrets (~/.claude/.env is excluded by design).
set -euo pipefail

DEST="${CLAUDE_BACKUP_DIR:-$HOME/Library/CloudStorage/GoogleDrive-you@example.com/My Drive/claude-backups}"
KEEP=12
TS=$(date -u +%Y%m%d-%H%M%SZ)
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

if [ ! -d "$(dirname "$DEST")" ]; then
  echo "ERROR: Google Drive not mounted at $(dirname "$DEST")" >&2
  exit 1
fi
mkdir -p "$DEST"

# --- Essentials ---
rsync -a "$HOME/.claude/skills/" "$STAGE/skills/"
[ -d "$HOME/.claude/memory" ]   && rsync -a "$HOME/.claude/memory/"   "$STAGE/memory/"
[ -d "$HOME/.claude/commands" ] && rsync -a "$HOME/.claude/commands/" "$STAGE/commands/"
for f in CLAUDE.md settings.json keybindings.json; do
  [ -f "$HOME/.claude/$f" ] && cp "$HOME/.claude/$f" "$STAGE/"
done

# Project memories only — never session transcripts
for d in "$HOME/.claude/projects"/*/memory; do
  [ -d "$d" ] || continue
  proj=$(basename "$(dirname "$d")")
  rsync -a "$d/" "$STAGE/projects/$proj/memory/"
done

# Belt and braces: no secrets in the archive
find "$STAGE" -name ".env" -delete

ZIP="$DEST/claude-backup-$TS.zip"
(cd "$STAGE" && zip -qr "$ZIP" .)
echo "Created: $ZIP ($(du -h "$ZIP" | cut -f1))"

# Retention: keep the newest $KEEP zips matching our own naming pattern
ls -1t "$DEST"/claude-backup-*.zip 2>/dev/null | tail -n +$((KEEP + 1)) | while IFS= read -r old; do
  echo "Pruned old backup: $(basename "$old")"
  rm -f "$old"
done

echo "--- Backups on Drive (newest first) ---"
ls -1t "$DEST"/claude-backup-*.zip | head -5
