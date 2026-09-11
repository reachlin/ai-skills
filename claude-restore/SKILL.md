---
name: claude-restore
description: Restore Claude Code skills and settings from a Google Drive backup zip, comparing each file against the live copy instead of blind-overwriting. Use when the user says "restore my skills", "restore claude", "restore from backup", "recover my skills", or asks to compare local skills against a backup.
---

# Claude Restore Skill

Restores from the zips created by the `claude-backup` skill at
`~/Library/CloudStorage/GoogleDrive-you@example.com/My Drive/claude-backups/`
(or wherever `CLAUDE_BACKUP_DIR` points, if set — see the `claude-backup` skill).

**This never blind-copies.** Every file in the backup is compared against its live
counterpart under `~/.claude/` before anything is written.

## Comparison rules

Content hash decides first; mtime is only a tiebreaker.

| Situation | Action |
|-----------|--------|
| File missing locally | **Restore** |
| Content identical (sha256) | Skip — no action, timestamps ignored |
| Content differs, backup mtime newer | **Restore** |
| Content differs, local mtime newer | **Warn, do not touch** (needs `--force`) |
| Content differs, mtimes equal | **Warn, do not touch** — can't tell which wins |

`~/.claude/.env` is never restored, and local files absent from the backup are
never deleted. Overwritten files are kept alongside as `<name>.bak`.

## LOCAL-ONLY section

The report also lists files that exist **here but not in the backup**, with the
skill names called out. These are never restored and never deleted — the section
is purely a signal that this machine has content the backup lacks.

Only the areas `claude-backup` covers are scanned (`skills/`, `memory/`,
`commands/`, `projects/*/memory/`, and the top-level config files). Transcripts,
history, caches, plugins, `.env` and `.bak` files are out of scope.

On a two-laptop setup this is how you know to run `claude-backup` **here** before
syncing the other way — see Two-machine workflow below.

## Steps

1. **Always dry-run first.** This writes nothing:

```bash
/opt/miniconda3/envs/claude-sandbox/bin/python ~/.claude/skills/claude-restore/scripts/restore.py
```

2. Show the user the report — especially the WARNING sections. Do not skip past them.

3. If they approve, apply:

```bash
/opt/miniconda3/envs/claude-sandbox/bin/python ~/.claude/skills/claude-restore/scripts/restore.py --apply
```

4. For a warned file, diff it against the backup and let the user decide before using
   `--force`. Never pass `--force` on your own initiative.

## Options

```bash
--list                # show available backups, newest first
--from <zip>          # restore from a specific backup (default: newest)
--apply               # write changes (default is dry-run)
--force               # also overwrite locally-newer / ambiguous files
skills/bark memory    # positional path prefixes: restrict to part of the backup
```

Restoring a single skill:

```bash
... /scripts/restore.py --apply skills/bark
```

## Two-machine workflow

To converge both laptops on the same set of skills, the round trip must run in
**both** directions — one pass only propagates one way:

1. Laptop A: `claude-backup`
2. Laptop B: `claude-restore --apply` — B gains A's extras, keeps its own
3. Laptop B: `claude-backup` — this zip now holds both machines' skills
4. Laptop A: `claude-restore --apply --from <B's zip>` — A gains B's extras

The LOCAL-ONLY section tells you whether step 3 is actually needed.

Two things to know:

- **Deletes never propagate.** Remove a skill on A and the next cross-restore
  brings it back. Retiring a skill means deleting it on both machines before the
  next sync.
- **Conflicting edits resolve by clock**, last writer wins, `.bak` is the only
  trace. Safe if a given skill is edited on one laptop at a time; unreliable if
  the same skill is edited in both places between syncs.
- Both laptops write to the same Drive folder and zip names carry only a
  timestamp, no hostname — so the newest backup may be the *other* machine's.
  Pass `--from` explicitly in a two-machine setup.

## Limits of mtime

Timestamps are a weak version signal, which is why content hashing comes first:

- Restoring a file sets its mtime to the backup's value, not "now" — repeat runs stay stable
- A newer mtime means *written later*, not *better*
- Two machines editing the same skill can't be reconciled by time alone

For real history (diff, blame, rollback to N-2), keep `~/.claude/skills/` in a private
git repo; the Drive zips remain the offsite disaster copy.
