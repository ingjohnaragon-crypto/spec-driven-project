#!/usr/bin/env python3
"""vault_prune_mine_log.py — removes non-"mine" entries from the local --mine log.

An earlier version of vault_backfill_mine_log.py added every non-internal
product in the (shared) Vault instance to the local log, contaminating it
with other teams' products. This rewrites the log to keep only entries whose
product_id is in the allowlist or matches the naming-convention prefix,
backing up the original first (log_file + ".bak", overwritten each run).

Purely local -- makes no Vault API calls.

Usage:
  py vault_prune_mine_log.py <log_file> <allowlist_file> [prefix]
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vault_mine_filter import DEFAULT_PREFIX, is_mine, load_allowlist  # noqa: E402

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RESET = "\033[0m"


def err(msg: str) -> None:
    print(f"{RED}✖  {msg}{RESET}", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"{GREEN}✔  {msg}{RESET}")


def warn(msg: str) -> None:
    print(f"{YELLOW}⚠  {msg}{RESET}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: py vault_prune_mine_log.py <log_file> <allowlist_file> [prefix]", file=sys.stderr)
        return 1

    log_file, allowlist_file = sys.argv[1:3]
    prefix = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else DEFAULT_PREFIX
    allowlist = load_allowlist(allowlist_file)

    if not os.path.isfile(log_file):
        print(f"\n  (nothing to prune -- {log_file} doesn't exist)")
        return 0

    kept_lines = []
    removed = []
    malformed = 0

    with open(log_file, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
            except json.JSONDecodeError:
                malformed += 1
                continue
            product_id = entry.get("product_id", "")
            if is_mine(product_id, allowlist, prefix):
                kept_lines.append(stripped)
            else:
                removed.append(product_id or "(no product_id)")

    if not removed and not malformed:
        ok("Nothing to prune -- every entry is already covered by the allowlist/prefix.")
        return 0

    backup_file = log_file + ".bak"
    shutil.copyfile(log_file, backup_file)

    with open(log_file, "w", encoding="utf-8") as f:
        for line in kept_lines:
            f.write(line + "\n")

    ok(f"Pruned {len(removed)} non-mine entr{'y' if len(removed) == 1 else 'ies'} from the local --mine log.")
    print(f"  Backup saved to: {backup_file}")
    print(f"  Kept: {len(kept_lines)}")
    for product_id in removed:
        print(f"  - removed: {product_id}")
    if malformed:
        warn(f"Also dropped {malformed} malformed log line(s) that could not be parsed as JSON")

    return 0


sys.exit(main())
