#!/usr/bin/env python3
"""Restore Claude Code skills/settings from a claude-backup zip, safely.

Compares every file in the backup against its live counterpart under ~/.claude/:
content hash first, mtime only as a tiebreaker. Dry-run by default.

Usage:
  restore.py                      # dry-run report against newest backup
  restore.py --list               # list available backups
  restore.py --from <zip>         # use a specific backup
  restore.py --apply              # actually restore (safe cases only)
  restore.py --apply --force      # also overwrite files that are newer locally
  restore.py --apply skills/bark  # limit to a path prefix (repeatable)
"""
import argparse
import hashlib
import os
import shutil
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

DRIVE = Path(os.environ.get("CLAUDE_BACKUP_DIR") or
             Path.home() / "Library/CloudStorage/GoogleDrive-you@example.com/My Drive/claude-backups")
TARGET_ROOT = Path.home() / ".claude"
MTIME_TOLERANCE = 2.0  # zip stores 2-second-resolution local timestamps

# Never restored, no matter what is in the archive.
BLOCKED = {".env"}

# Local areas the backup is expected to cover. Anything here that the archive
# lacks is genuinely local-only; everything else under ~/.claude (transcripts,
# history, caches, plugins) is out of scope and never reported.
SCAN_DIRS = ["skills", "memory", "commands"]
SCAN_FILES = ["CLAUDE.md", "settings.json", "keybindings.json"]
IGNORE_NAMES = {".DS_Store", ".env"}
IGNORE_SUFFIXES = (".bak",)  # our own pre-overwrite copies

RESTORE, SKIP_SAME, WARN_NEWER, WARN_TIE = "restore", "same", "local-newer", "ambiguous"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_backups():
    if not DRIVE.parent.exists():
        sys.exit(f"ERROR: Google Drive not mounted at {DRIVE.parent}")
    return sorted(DRIVE.glob("claude-backup-*.zip"), key=lambda p: p.name, reverse=True)


def zip_mtime(info: zipfile.ZipInfo) -> float:
    """Zip entry timestamp as a local-time epoch (matches os.stat mtime)."""
    return time.mktime(info.date_time + (0, 0, -1))


def classify(info: zipfile.ZipInfo, zf: zipfile.ZipFile, local: Path):
    """Decide what to do with one backup member. Returns (action, detail)."""
    if not local.exists():
        return RESTORE, "missing locally"

    backup_bytes = zf.read(info)
    local_bytes = local.read_bytes()
    if sha256(backup_bytes) == sha256(local_bytes):
        return SKIP_SAME, "identical content"

    # Content differs -> mtime decides direction.
    b_time, l_time = zip_mtime(info), local.stat().st_mtime
    delta = b_time - l_time
    if delta > MTIME_TOLERANCE:
        return RESTORE, f"backup newer by {fmt_delta(delta)}"
    if delta < -MTIME_TOLERANCE:
        return WARN_NEWER, f"local newer by {fmt_delta(-delta)}"
    return WARN_TIE, "same mtime but different content"


def scan_local(members: set, paths) -> list:
    """Files present in the backed-up areas of TARGET_ROOT but absent from the archive."""
    candidates = []
    for d in SCAN_DIRS:
        candidates += [p for p in (TARGET_ROOT / d).rglob("*") if p.is_file()]
    for f in SCAN_FILES:
        if (TARGET_ROOT / f).is_file():
            candidates.append(TARGET_ROOT / f)
    for proj_mem in (TARGET_ROOT / "projects").glob("*/memory"):
        candidates += [p for p in proj_mem.rglob("*") if p.is_file()]

    out = []
    for p in candidates:
        rel = str(p.relative_to(TARGET_ROOT))
        if rel in members or p.name in IGNORE_NAMES or rel.endswith(IGNORE_SUFFIXES):
            continue
        if paths and not any(rel.startswith(x.rstrip("/")) for x in paths):
            continue
        out.append(rel)
    return sorted(out)


def fmt_delta(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="restrict to these path prefixes inside the backup")
    ap.add_argument("--from", dest="src", help="backup zip to restore from (default: newest)")
    ap.add_argument("--list", action="store_true", help="list available backups and exit")
    ap.add_argument("--apply", action="store_true", help="write changes (default is dry-run)")
    ap.add_argument("--force", action="store_true", help="also overwrite locally-newer files")
    args = ap.parse_args()

    backups = find_backups()
    if args.list:
        if not backups:
            sys.exit("No backups found.")
        print(f"Backups in {DRIVE} (newest first):")
        for b in backups:
            size = b.stat().st_size / 1e6
            print(f"  {b.name}  ({size:.1f} MB)")
        return

    src = Path(args.src) if args.src else (backups[0] if backups else None)
    if not src or not src.exists():
        sys.exit("ERROR: no backup zip found. Run with --list to see what is available.")

    print(f"Backup : {src.name}")
    print(f"Target : {TARGET_ROOT}")
    print(f"Mode   : {'APPLY' if args.apply else 'DRY-RUN (no files written)'}"
          f"{' +FORCE' if args.force else ''}\n")

    buckets = {RESTORE: [], SKIP_SAME: [], WARN_NEWER: [], WARN_TIE: []}
    blocked, restored, failed = [], [], []
    members = set()

    with zipfile.ZipFile(src) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            # Strip a leading "./" as a prefix -- lstrip() would eat the dot of ".env".
            member = info.filename
            while member.startswith("./"):
                member = member[2:]
            if not member or Path(member).name in BLOCKED or os.path.isabs(member) \
                    or ".." in Path(member).parts:
                blocked.append(member or info.filename)
                continue
            members.add(member)
            if args.paths and not any(member.startswith(p.rstrip("/")) for p in args.paths):
                continue

            local = TARGET_ROOT / member
            action, detail = classify(info, zf, local)
            buckets[action].append((member, detail))

            should_write = action == RESTORE or (args.force and action in (WARN_NEWER, WARN_TIE))
            if args.apply and should_write:
                try:
                    local.parent.mkdir(parents=True, exist_ok=True)
                    if local.exists():
                        shutil.copy2(local, local.with_suffix(local.suffix + ".bak"))
                    local.write_bytes(zf.read(info))
                    os.utime(local, (zip_mtime(info), zip_mtime(info)))
                    if info.external_attr >> 16 & 0o111:  # preserve exec bit
                        local.chmod(local.stat().st_mode | 0o111)
                    restored.append(member)
                except OSError as e:
                    failed.append(f"{member}: {e}")

    report(buckets, blocked, restored, failed, args, scan_local(members, args.paths))


def report(buckets, blocked, restored, failed, args, local_only):
    def show(title, items, limit=None):
        if not items:
            return
        print(f"{title} ({len(items)})")
        shown = items if limit is None else items[:limit]
        for member, detail in shown:
            print(f"  {member}  -- {detail}")
        if limit and len(items) > limit:
            print(f"  ... and {len(items) - limit} more")
        print()

    show("RESTORE  backup wins", buckets[RESTORE])
    show("WARNING  local is NEWER than backup -- not restored", buckets[WARN_NEWER])
    show("WARNING  differing content, identical mtime -- cannot tell which is newer", buckets[WARN_TIE])
    print(f"UNCHANGED  identical in both ({len(buckets[SKIP_SAME])} files)\n")

    if local_only:
        skills = sorted({p.split("/")[1] for p in local_only
                         if p.startswith("skills/") and "/" in p[7:]})
        print(f"LOCAL-ONLY  here but NOT in this backup ({len(local_only)} files) -- "
              f"never restored, never deleted")
        if skills:
            print(f"  skills not in the backup: {', '.join(skills)}")
        for p in local_only[:10]:
            print(f"  {p}")
        if len(local_only) > 10:
            print(f"  ... and {len(local_only) - 10} more")
        print("  -> back up THIS machine to carry these to the other one.\n")

    if blocked:
        print(f"BLOCKED  never restored: {', '.join(sorted(set(blocked)))}\n")

    warn_count = len(buckets[WARN_NEWER]) + len(buckets[WARN_TIE])
    if args.apply:
        print(f"Applied: {len(restored)} file(s) written (originals kept as *.bak).")
        if failed:
            print(f"FAILED: {len(failed)}")
            for f in failed:
                print(f"  {f}")
        if warn_count and not args.force:
            print(f"Left alone: {warn_count} file(s) with warnings. Review them, "
                  f"then re-run with --force to overwrite.")
    else:
        n = len(buckets[RESTORE])
        if args.force:
            n += warn_count
        print(f"Would restore {n} file(s). Re-run with --apply to write.")
        if warn_count and not args.force:
            print(f"{warn_count} file(s) need review before they would be touched.")

    print("\nNote: local files never present in the backup are left untouched; "
          "nothing is deleted.")


if __name__ == "__main__":
    main()
