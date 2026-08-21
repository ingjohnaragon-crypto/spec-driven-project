"""
md_to_adf.py — Markdown → Atlassian Document Format (ADF) for Jira Cloud.

Supports:
  # / ## / ### headings
  - / * bullet lists (grouped)
  1. ordered lists (grouped)
  - [ ] / - [x] task lists (grouped)
  ``` code fences
  --- horizontal rules
  blank-line paragraphs
  inline **bold**, *italic*, `code`

Usage as library:
  from md_to_adf import markdown_to_adf
  adf = markdown_to_adf(text)

CLI smoke test:
  py md_to_adf.py < markdown.md
"""
from __future__ import annotations

import json
import re
import sys
import uuid


def _uid() -> str:
    return str(uuid.uuid4())


def _inline(text: str) -> list[dict]:
    """Parse a limited set of inline markdown marks into ADF text nodes."""
    if not text:
        return []

    pattern = re.compile(
        r"(\*\*(.+?)\*\*|`([^`]+)`|(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*))"
    )
    nodes: list[dict] = []
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            nodes.append({"type": "text", "text": text[pos:match.start()]})
        if match.group(2) is not None:
            nodes.append({
                "type": "text",
                "text": match.group(2),
                "marks": [{"type": "strong"}],
            })
        elif match.group(3) is not None:
            nodes.append({
                "type": "text",
                "text": match.group(3),
                "marks": [{"type": "code"}],
            })
        else:
            nodes.append({
                "type": "text",
                "text": match.group(4),
                "marks": [{"type": "em"}],
            })
        pos = match.end()
    if pos < len(text):
        nodes.append({"type": "text", "text": text[pos:]})
    return nodes or [{"type": "text", "text": text}]


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "content": _inline(text)}


def _heading(level: int, text: str) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": max(1, min(level, 6))},
        "content": _inline(text),
    }


def _flush_list(buffer: list[tuple[str, str]], list_kind: str) -> dict | None:
    if not buffer:
        return None

    if list_kind == "task":
        items = []
        for state, text in buffer:
            items.append({
                "type": "taskItem",
                "attrs": {"localId": _uid(), "state": state},
                "content": _inline(text),
            })
        return {
            "type": "taskList",
            "attrs": {"localId": _uid()},
            "content": items,
        }

    items = []
    for _, text in buffer:
        items.append({
            "type": "listItem",
            "content": [_paragraph(text)],
        })
    return {
        "type": "bulletList" if list_kind == "bullet" else "orderedList",
        "content": items,
    }


def markdown_to_adf(text: str) -> dict:
    """Convert markdown-ish text to an ADF document node."""
    content: list[dict] = []
    list_buf: list[tuple[str, str]] = []
    list_kind: str | None = None
    in_code = False
    code_lines: list[str] = []

    def flush_list() -> None:
        nonlocal list_buf, list_kind
        node = _flush_list(list_buf, list_kind or "bullet")
        if node:
            content.append(node)
        list_buf = []
        list_kind = None

    def flush_code() -> None:
        nonlocal code_lines
        code_text = "\n".join(code_lines)
        content.append({
            "type": "codeBlock",
            "attrs": {"language": "text"},
            "content": [{"type": "text", "text": code_text}] if code_text else [],
        })
        code_lines = []

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_list()
                in_code = True
                code_lines = []
            continue

        if in_code:
            code_lines.append(raw_line.rstrip("\n"))
            continue

        if not line.strip():
            flush_list()
            continue

        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", line.strip()):
            flush_list()
            content.append({"type": "rule"})
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            flush_list()
            content.append(_heading(len(heading.group(1)), heading.group(2).strip()))
            continue

        task = re.match(r"^[-*]\s+\[([ xX])\]\s+(.*)$", line)
        if task:
            state = "DONE" if task.group(1).lower() == "x" else "TODO"
            if list_kind not in (None, "task"):
                flush_list()
            list_kind = "task"
            list_buf.append((state, task.group(2).strip()))
            continue

        bullet = re.match(r"^[-*]\s+(.*)$", line)
        if bullet:
            if list_kind not in (None, "bullet"):
                flush_list()
            list_kind = "bullet"
            list_buf.append(("", bullet.group(1).strip()))
            continue

        ordered = re.match(r"^\d+[.)]\s+(.*)$", line)
        if ordered:
            if list_kind not in (None, "ordered"):
                flush_list()
            list_kind = "ordered"
            list_buf.append(("", ordered.group(1).strip()))
            continue

        flush_list()
        content.append(_paragraph(line.strip()))

    if in_code:
        flush_code()
    flush_list()

    if not content:
        content = [_paragraph(text.strip() or " ")]

    return {"type": "doc", "version": 1, "content": content}


if __name__ == "__main__":
    src = sys.stdin.read() if not sys.argv[1:] else open(sys.argv[1], encoding="utf-8").read()
    print(json.dumps(markdown_to_adf(src), ensure_ascii=False, indent=2))
