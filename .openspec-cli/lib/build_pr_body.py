#!/usr/bin/env python3
"""Build a rich PR body for os-commit from plan + enrichment + staged files."""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


def _section(text: str, start: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    grab = False
    for line in lines:
        if line.startswith(start):
            grab = True
            continue
        if grab and line.startswith("## "):
            break
        if grab:
            out.append(line)
    return "\n".join(out).strip()


def _story_points(text: str) -> str:
    m = re.search(r"STORY_POINTS:(\d+)", text)
    return m.group(1) if m else ""


def _bullets(paths: list[str]) -> str:
    return "\n".join(f"- {p}" for p in paths) if paths else "- _(ninguno)_"


def build_body(
    *,
    ticket: str,
    staged: list[str],
    lang: str,
    repo_root: Path,
    stack: str,
    stack_label: str,
    test_cmd: str,
    coverage_cmd: str,
    jira_base: str,
) -> str:
    plan = repo_root / "ai-specs" / "changes" / "planes" / ticket / f"{ticket}_backend.md"
    enrich_md = (
        repo_root
        / "ai-specs"
        / "changes"
        / "enriquecimientos"
        / ticket
        / f"{ticket}_enriched.md"
    )
    enrich_applied = Path(str(enrich_md) + ".applied")
    enrich = enrich_md if enrich_md.is_file() else enrich_applied

    plan_text = plan.read_text(encoding="utf-8") if plan.is_file() else ""
    enrich_text = enrich.read_text(encoding="utf-8") if enrich.is_file() else ""

    points = _story_points(plan_text) or _story_points(enrich_text)
    title = ""
    if plan_text:
        title = plan_text.splitlines()[0].lstrip("# ").strip()

    resumen = _section(plan_text, "## 1. Resumen") or _section(
        enrich_text, "## Descripción mejorada"
    )
    decisiones = _section(plan_text, "### 2.1 Decisiones")
    aceptacion = _section(enrich_text, "## Criterios de aceptación")

    contracts = [p for p in staged if p.startswith("contracts/") and p.endswith(".py")]
    tests = [p for p in staged if p.startswith("tests/")]
    docs = [
        p
        for p in staged
        if p.startswith("ai-specs/changes/planes/")
        or p.startswith("ai-specs/changes/enriquecimientos/")
    ]
    tooling = [
        p
        for p in staged
        if p.startswith(".openspec-cli/") or p.startswith("ai-specs/.commands/")
    ]

    jira_url = f"{jira_base.rstrip('/')}/browse/{ticket}" if jira_base else f"/browse/{ticket}"

    if lang == "es":
        lines = [
            "## Resumen",
            title or f"Implementa {ticket}",
            "",
            f"Stack: `{stack}` ({stack_label})",
        ]
        if points:
            lines.append(f"Story points: **{points}**")
        lines += [
            "",
            resumen or f"Implementa {ticket} en el stack activo.",
            "",
            "## Decisiones clave",
            decisiones or "_(ver plan de implementación)_",
            "",
            "## Criterios de aceptación",
            aceptacion or "_(ver enriquecimiento)_",
            "",
            "## Contratos",
            _bullets(contracts),
            "",
            "## Tests",
            _bullets(tests),
            "",
            "## Documentación (plan / enriquecimiento)",
            _bullets(docs),
            "",
            "## Tooling / templates",
            _bullets(tooling),
            "",
            "## Checklist",
            f"- [ ] Tests pasan (`os-vault-test` / `{test_cmd}`)",
            f"- [ ] Cobertura >= 90% (`{coverage_cmd}`)",
            "- [ ] Plan y enriquecimiento versionados en `ai-specs/changes/`",
            "- [ ] El contrato respeta las restricciones del sandbox Vault",
            "",
            "## Referencias",
        ]
        if plan.is_file():
            lines.append(
                f"- Plan: `ai-specs/changes/planes/{ticket}/{ticket}_backend.md`"
            )
        if enrich.is_file():
            lines.append(
                f"- Enriquecimiento: `ai-specs/changes/enriquecimientos/{ticket}/`"
            )
        lines.append(f"- Jira: [{ticket}]({jira_url})")
        return "\n".join(lines) + "\n"

    lines = [
        "## Summary",
        title or f"Implements {ticket}",
        "",
        f"Stack: `{stack}` ({stack_label})",
    ]
    if points:
        lines.append(f"Story points: **{points}**")
    lines += [
        "",
        resumen or f"Implements {ticket} on the active stack.",
        "",
        "## Key decisions",
        decisiones or "_(see implementation plan)_",
        "",
        "## Acceptance criteria",
        aceptacion or "_(see enrichment)_",
        "",
        "## Contracts",
        _bullets(contracts),
        "",
        "## Tests",
        _bullets(tests),
        "",
        "## Documentation (plan / enrichment)",
        _bullets(docs),
        "",
        "## Tooling / templates",
        _bullets(tooling),
        "",
        "## Checklist",
        f"- [ ] Tests pass (`os-vault-test` / `{test_cmd}`)",
        f"- [ ] Coverage >= 90% (`{coverage_cmd}`)",
        "- [ ] Plan and enrichment versioned under `ai-specs/changes/`",
        "- [ ] Contract respects Vault Python sandbox restrictions",
        "",
        "## References",
    ]
    if plan.is_file():
        lines.append(f"- Plan: `ai-specs/changes/planes/{ticket}/{ticket}_backend.md`")
    if enrich.is_file():
        lines.append(f"- Enrichment: `ai-specs/changes/enriquecimientos/{ticket}/`")
    lines.append(f"- Jira: [{ticket}]({jira_url})")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticket")
    parser.add_argument("--lang", default="es")
    parser.add_argument("--staged-file", help="File with staged paths, one per line")
    parser.add_argument("--repo-root", default=os.environ.get("OS_REPO_ROOT", "."))
    args = parser.parse_args(argv)

    if args.staged_file:
        staged = [
            ln.strip().replace("\\", "/").lstrip("./")
            for ln in Path(args.staged_file).read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    else:
        staged = [
            ln.strip().replace("\\", "/").lstrip("./")
            for ln in sys.stdin.read().splitlines()
            if ln.strip()
        ]

    body = build_body(
        ticket=args.ticket,
        staged=staged,
        lang=args.lang,
        repo_root=Path(args.repo_root),
        stack=os.environ.get("OS_ACTIVE_STACK", "vault-smart-contracts"),
        stack_label=os.environ.get("OS_STACK_LABEL", ""),
        test_cmd=os.environ.get("OS_TEST_CMD", "pytest"),
        coverage_cmd=os.environ.get("OS_COVERAGE_CMD", "pytest --cov"),
        jira_base=os.environ.get("JIRA_BASE_URL", ""),
    )
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
