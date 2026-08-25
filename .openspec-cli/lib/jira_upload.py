"""
jira_upload.py — uploads markdown content to a Jira ticket description (ADF).

Usage:
  py jira_upload.py <ticket_id> <source_file> <base_url> <email> <token>

If the source file contains <!-- SUBTASK:<KEY> --> ... <!-- /SUBTASK:<KEY> -->
blocks, each block is uploaded to its own subtask and stripped from the parent.

Blocks wrapped in <!-- jira-skip --> ... <!-- /jira-skip --> are removed before upload.

<!-- STORY_POINTS:<N> --> markers set the Story Points field when JIRA_STORY_POINTS_FIELD
is configured (default: customfield_10016 — override via env).
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Allow running from install dir or repo lib dir
sys.path.insert(0, str(Path(__file__).resolve().parent))
from md_to_adf import markdown_to_adf  # noqa: E402

ticket_id, source_file, base_url, email, token = sys.argv[1:6]

with open(source_file, encoding="utf-8") as f:
    raw = f.read()

SUBTASK_RE = re.compile(
    r"<!--\s*SUBTASK:(\S+)\s*-->(.*?)<!--\s*/SUBTASK:\1\s*-->",
    re.DOTALL,
)
JIRA_SKIP_RE = re.compile(
    r"<!--\s*jira-skip\s*-->.*?<!--\s*/jira-skip\s*-->",
    re.DOTALL | re.IGNORECASE,
)
STORY_POINTS_RE = re.compile(
    r"<!--\s*STORY_POINTS:(\d+(?:\.\d+)?)\s*-->",
    re.IGNORECASE,
)
STORY_POINTS_CLOSE_RE = re.compile(r"<!--\s*/STORY_POINTS\s*-->", re.IGNORECASE)

STORY_POINTS_FIELD = os.environ.get("JIRA_STORY_POINTS_FIELD", "customfield_10016")

subtask_updates = [(key, body.strip()) for key, body in SUBTASK_RE.findall(raw)]
main_content = SUBTASK_RE.sub("", raw).strip()

creds = base64.b64encode(f"{email}:{token}".encode()).decode()


def strip_jira_skip(text: str) -> str:
    return JIRA_SKIP_RE.sub("", text).strip()


def extract_story_points(text: str) -> float | None:
    match = STORY_POINTS_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def clean_markers(text: str) -> str:
    text = STORY_POINTS_RE.sub("", text)
    text = STORY_POINTS_CLOSE_RE.sub("", text)
    return text.strip()


def prepare_content(content: str) -> tuple[str, float | None]:
    prepared = strip_jira_skip(content)
    points = extract_story_points(prepared)
    prepared = clean_markers(prepared)
    return prepared, points


def jira_request(method: str, path: str, payload: dict) -> tuple[bool, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")
        return False, f"HTTP {e.code} - {err}"


def update_issue(issue_key: str, content: str) -> bool:
    prepared, points = prepare_content(content)
    # Jira acepta (HTTP 204) un PUT combinado de description (ADF rico) +
    # custom field de story points, pero descarta el custom field en
    # silencio sin avisar. Separados en dos requests independientes, ambos
    # aplican correctamente -- confirmado empiricamente.
    ok, msg = jira_request(
        "PUT",
        f"/rest/api/3/issue/{issue_key}",
        {"fields": {"description": markdown_to_adf(prepared)}},
    )
    if not ok:
        print(f"Error: {msg} updating {issue_key}", file=sys.stderr)
        return False
    if points is None or not STORY_POINTS_FIELD:
        print(f"Updated ticket {issue_key} - {msg}")
        return True
    ok2, msg2 = jira_request(
        "PUT",
        f"/rest/api/3/issue/{issue_key}",
        {"fields": {STORY_POINTS_FIELD: points}},
    )
    if ok2:
        print(f"Updated ticket {issue_key} - {msg} (story points={points})")
        return True
    print(
        f"Warning: story points field '{STORY_POINTS_FIELD}' failed for {issue_key}; "
        f"description was updated OK. Detail: {msg2}",
        file=sys.stderr,
    )
    print(f"Updated ticket {issue_key} - {msg} (description only, story points failed)")
    return True

    print(f"Error: {msg} updating {issue_key}", file=sys.stderr)
    return False


ok = update_issue(ticket_id, main_content)
for subtask_key, subtask_content in subtask_updates:
    ok = update_issue(subtask_key, subtask_content) and ok

sys.exit(0 if ok else 1)
