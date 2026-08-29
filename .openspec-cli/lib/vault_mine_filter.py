"""vault_mine_filter.py — shared allowlist/prefix "is this mine" filtering.

The Vault Core API has no per-team/tenant ownership field (confirmed against
the Core API docs: GET /v1/products exposes id, current_version_id,
display_name, is_internal -- nothing that identifies a creator). In a shared
sandbox, that means os-vault-products --mine can't trust a raw dump of every
product in the instance; it needs an explicit local allowlist plus an
optional naming-convention prefix, both applied on top of the deploy log.

Used by vault_backfill_mine_log.py and vault_prune_mine_log.py.
"""
from __future__ import annotations

import os

DEFAULT_PREFIX = "openspec_"


def load_allowlist(path: str) -> set:
    """One product_id per line; blank lines and '#' comments are ignored."""
    ids: set = set()
    if not path or not os.path.isfile(path):
        return ids
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            ids.add(line)
    return ids


def is_mine(product_id: str, allowlist: set, prefix: str) -> bool:
    if not product_id:
        return False
    if product_id in allowlist:
        return True
    if prefix and product_id.startswith(prefix):
        return True
    return False
