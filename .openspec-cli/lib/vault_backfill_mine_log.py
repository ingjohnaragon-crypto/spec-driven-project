#!/usr/bin/env python3
"""vault_backfill_mine_log.py — seeds the local --mine log with existing Vault products.

os-vault-products --mine only knows about products deployed *after* the log
existed (os-vault-deploy writes to it going forward). This backfills the log
with products that were deployed before that tracking was added.

The Vault sandbox is shared across teams, so a raw "everything in
GET /v1/products" dump is NOT safe to trust as "mine" -- it would pull in
other teams' products too. A product is only backfilled if its id is in the
allowlist file, or starts with the naming-convention prefix (default
"openspec_"). Everything else is left out and counted separately as
"skipped (not mine)". Existing log entries are left untouched;
already-recorded product ids are skipped.

Usage:
  py vault_backfill_mine_log.py <base_url> <token> <log_file> <include_internal:true|false> \
      <allowlist_file> [prefix]
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vault_mine_filter import DEFAULT_PREFIX, is_mine, load_allowlist  # noqa: E402

RED = "\033[0;31m"
GREEN = "\033[0;32m"
RESET = "\033[0m"

PAGE_SIZE = 30


def err(msg: str) -> None:
    print(f"{RED}✖  {msg}{RESET}", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"{GREEN}✔  {msg}{RESET}")


def vault_get(base_url: str, token: str, path: str) -> dict:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"X-Auth-Token": token, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def paginated_products(base_url: str, token: str) -> list:
    items: list = []
    page_token = ""
    while True:
        params = {"page_size": PAGE_SIZE}
        if page_token:
            params["page_token"] = page_token
        url = f"/v1/products?{urllib.parse.urlencode(params)}"
        data = vault_get(base_url, token, url)
        items.extend(data.get("products", []))
        page_token = data.get("next_page_token", "")
        if not page_token:
            break
    return items


def load_existing_ids(log_file: str) -> set:
    ids: set = set()
    if not os.path.isfile(log_file):
        return ids
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("product_id"):
                ids.add(entry["product_id"])
    return ids


def main() -> int:
    if len(sys.argv) < 6:
        print(
            "Usage: py vault_backfill_mine_log.py <base_url> <token> <log_file> "
            "<include_internal> <allowlist_file> [prefix]",
            file=sys.stderr,
        )
        return 1

    base_url, token, log_file, include_internal_arg, allowlist_file = sys.argv[1:6]
    prefix = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] else DEFAULT_PREFIX
    include_internal = include_internal_arg.lower() == "true"
    allowlist = load_allowlist(allowlist_file)

    try:
        all_products = paginated_products(base_url, token)
    except urllib.error.HTTPError as e:
        err(f"Fetching products failed (HTTP {e.code}):")
        print(e.read().decode(errors="replace"), file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        err(f"Could not reach Vault: {e.reason}")
        return 1

    internal_skipped = 0
    not_mine_skipped = 0
    products = []
    for p in all_products:
        if p.get("is_internal") and not include_internal:
            internal_skipped += 1
            continue
        product_id = p.get("id", "")
        if not is_mine(product_id, allowlist, prefix):
            not_mine_skipped += 1
            continue
        products.append(p)

    existing_ids = load_existing_ids(log_file)
    already_recorded = 0
    new_entries = []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for p in products:
        product_id = p.get("id", "")
        if not product_id:
            continue
        if product_id in existing_ids:
            already_recorded += 1
            continue
        new_entries.append({
            "timestamp": now,
            "product_id": product_id,
            "display_name": p.get("display_name", ""),
            "product_version_id": p.get("current_version_id", ""),
            "contract_file": "",
            "source": "backfill",
        })

    if new_entries:
        with open(log_file, "a", encoding="utf-8") as f:
            for entry in new_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    ok(f"Backfilled {len(new_entries)} product(s) into the local --mine log.")
    for entry in new_entries:
        print(f"  + {entry['display_name'] or entry['product_id']}  ({entry['product_id']})")
    if already_recorded:
        print(f"  ({already_recorded} already recorded, skipped)")
    if internal_skipped:
        print(f"  ({internal_skipped} internal product(s) skipped -- pass --include-internal to include them)")
    if not_mine_skipped:
        print(f"  ({not_mine_skipped} product(s) skipped (not mine) -- not in the allowlist and no '{prefix}' prefix)")

    return 0


sys.exit(main())
