#!/usr/bin/env python3
"""Fail CI when a contracts/*.py product has no matching tests/test_<name>.py.

Why: pytest --cov=contracts measures every module under contracts/. If a new
contract is added but its tests are omitted from CI, that file stays at 0% and
the package total collapses below --cov-fail-under.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"
TESTS = ROOT / "tests"


def main() -> int:
    missing: list[str] = []
    contracts = sorted(
        p for p in CONTRACTS.glob("*.py") if p.name != "__init__.py"
    )
    if not contracts:
        print("ERROR: no contracts found under contracts/", file=sys.stderr)
        return 1

    print("Contract ↔ test pairing:")
    for contract in contracts:
        name = contract.stem
        test = TESTS / f"test_{name}.py"
        if test.is_file():
            print(f"  ✔ {contract.relative_to(ROOT)} → {test.relative_to(ROOT)}")
        else:
            print(f"  ✖ {contract.relative_to(ROOT)} → MISSING {test.relative_to(ROOT)}")
            missing.append(name)

    if missing:
        print(
            "\nERROR: every contracts/<name>.py must have tests/test_<name>.py.\n"
            "Add the missing test module(s) before merging, or CI coverage of "
            "`contracts/` will drop below the fail-under threshold.",
            file=sys.stderr,
        )
        return 1

    print(f"\nAll {len(contracts)} contract(s) have a matching test module.")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass
    raise SystemExit(main())
