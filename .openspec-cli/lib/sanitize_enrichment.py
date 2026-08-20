#!/usr/bin/env python3
"""
sanitize_enrichment.py — keep only the enriched ticket markdown.

Usage:
  py sanitize_enrichment.py <input.md> <output.md>

Extracts from the first '# Ticket enriquecido:' / '# Enriched Ticket:' heading
to EOF. Drops prompt contamination, control chars, and Copilot chat chrome.
Exits 1 if no valid enrichment heading is found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


HEADING_RE = re.compile(
    r"^#\s+(Ticket enriquecido:|Enriched Ticket:)\s*.+$",
    re.MULTILINE | re.IGNORECASE,
)

# Typical Copilot/chat leftovers that must not land in Jira
NOISE_PREFIXES = (
    "you are acting as",
    "follow these steps",
    "## active language",
    "## active stack",
    "## stack agent",
    "## stack standards",
    "## your task",
    "please analyze and fix the jira ticket",
)


def sanitize(raw: str) -> str | None:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Strip BOM / NULs / other control chars (keep \n \t)
    text = text.lstrip("\ufeff")
    text = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)

    match = HEADING_RE.search(text)
    if not match:
        return None

    body = text[match.start():].strip() + "\n"

    # Drop trailing chat boilerplate after the document
    for marker in (
        "\n> Enriched content saved",
        "\nRun `os-enrich-apply",
        "\nCopilot:",
        "\nGitHub Copilot:",
    ):
        idx = body.find(marker)
        if idx > 0:
            body = body[:idx].rstrip() + "\n"

    # Reject if still looks like the original prompt leaked in
    lowered = body.lower()
    noise_hits = sum(1 for p in NOISE_PREFIXES if p in lowered)
    if noise_hits >= 3 and len(body) > 8000:
        # Likely prompt echoed back — try cutting after first major section dump
        return None

    return body


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: sanitize_enrichment.py <input.md> <output.md>", file=sys.stderr)
        return 2

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    raw = src.read_text(encoding="utf-8", errors="replace")
    cleaned = sanitize(raw)
    if cleaned is None:
        print(
            "ERROR: No valid enrichment heading found "
            "('# Ticket enriquecido:' / '# Enriched Ticket:'). "
            "Paste ONLY Copilot's markdown reply.",
            file=sys.stderr,
        )
        return 1

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(cleaned, encoding="utf-8")
    print(f"Sanitized enrichment -> {dst} ({len(cleaned)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
