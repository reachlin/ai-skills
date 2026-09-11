---
name: claude-backup
description: Back up Claude Code skills and essential settings to a timestamped zip in Google Drive. Use when the user says "backup my skills", "backup claude", "backup claude settings", "save skills to google drive", or asks for a Claude Code config backup.
---

# Claude Backup Skill

Creates `claude-backup-<YYYYMMDD-HHMMSSZ>.zip` (UTC timestamp) in Google Drive at
`~/Library/CloudStorage/GoogleDrive-you@example.com/My Drive/claude-backups/`
and prunes to the newest 12 backups.

Set `CLAUDE_BACKUP_DIR` to override the destination — e.g. point it at your own
Google Drive mount path (find it under `~/Library/CloudStorage/`) or any other
synced folder.

## What's included

| Path in zip | Source |
|-------------|--------|
| `skills/` | `~/.claude/skills/` (all user skills, including this one) |
| `memory/` | `~/.claude/memory/` (user-level memory) |
| `projects/<slug>/memory/` | per-project auto-memory (memories only — never session transcripts) |
| `commands/` | `~/.claude/commands/` (legacy slash commands) |
| `CLAUDE.md`, `settings.json`, `keybindings.json` | top-level config files (only those that exist) |

**Never included:** `~/.claude/.env` (secrets must not land in Google Drive), session transcripts, history, caches, plugins (reinstallable).

## Steps

1. Run the backup script:

```bash
bash ~/.claude/skills/claude-backup/scripts/backup.sh
```

2. Relay the script output to the user: the created zip path + size, anything pruned, and the current backup list.

3. If the script fails with "Google Drive not mounted", tell the user to start Google Drive for desktop and retry.

## Restore (manual)

Unzip into a scratch directory and copy the needed pieces back under `~/.claude/`. Never blind-overwrite `~/.claude/` wholesale — settings.json may have moved on since the backup.

## Notes

- Retention is 12 zips; only files matching `claude-backup-*.zip` are ever pruned — nothing else in the Drive folder is touched.
- This skill replaced the old folder-mirror backup at `My Drive/skills/` (removed 2026-07-03).
