"""Tests for vault_lint.py — Vault Python sandbox restriction linter."""
from __future__ import annotations

from pathlib import Path

from vault_lint import Violation, lint_directory, lint_file, main


def _write(tmp_path: Path, code: str, name: str = "contract.py") -> Path:
    p = tmp_path / name
    p.write_text(code, encoding="utf-8")
    return p


def lint_source(tmp_path: Path, code: str) -> list[Violation]:
    return lint_file(_write(tmp_path, code))


# ── Happy path ────────────────────────────────────────────────


def test_should_pass_when_contract_has_no_violations(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "x = 1\n")
    assert violations == []


def test_should_pass_when_contract_imports_contracts_api_and_decimal_only(
    tmp_path: Path,
) -> None:
    code = (
        "from contracts_api import Tside\n"
        "from decimal import Decimal, ROUND_HALF_UP\n"
    )
    violations = lint_source(tmp_path, code)
    assert violations == []


def test_should_pass_for_existing_savings_product_contract() -> None:
    path = Path(__file__).parent.parent / "contracts" / "savings_product.py"
    violations = lint_file(path)
    assert violations == [], f"Unexpected violations in savings_product.py: {violations}"


# ── Forbidden imports ─────────────────────────────────────────


def test_should_fail_when_contract_imports_os(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "import os\n")
    assert len(violations) == 1
    assert violations[0].rule == "FORBIDDEN_IMPORT"
    assert "os" in violations[0].message


def test_should_fail_when_contract_imports_json(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "import json\n")
    assert len(violations) == 1
    assert violations[0].rule == "FORBIDDEN_IMPORT"
    assert "json" in violations[0].message


def test_should_fail_when_contract_uses_from_datetime_import(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "from datetime import datetime\n")
    assert len(violations) == 1
    assert violations[0].rule == "FORBIDDEN_IMPORT"


def test_should_flag_unknown_import_statement(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "import unknown_lib\n")
    assert len(violations) == 1
    assert violations[0].rule == "UNKNOWN_IMPORT"
    assert "unknown_lib" in violations[0].message


def test_should_flag_unknown_from_import_statement(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "from unknown_lib import something\n")
    assert len(violations) == 1
    assert violations[0].rule == "UNKNOWN_IMPORT"


# ── Forbidden calls ───────────────────────────────────────────


def test_should_fail_when_contract_calls_eval(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "result = eval('1+1')\n")
    assert len(violations) == 1
    assert violations[0].rule == "FORBIDDEN_CALL"
    assert "eval" in violations[0].message


def test_should_fail_when_contract_calls_exec(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "exec('x = 1')\n")
    assert len(violations) == 1
    assert violations[0].rule == "FORBIDDEN_CALL"
    assert "exec" in violations[0].message


def test_should_fail_when_contract_calls_print(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "print('debug')\n")
    assert len(violations) == 1
    assert violations[0].rule == "FORBIDDEN_CALL"
    assert "print" in violations[0].message


def test_should_fail_when_contract_calls_getattr(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "v = getattr(obj, 'name')\n")
    assert len(violations) == 1
    assert violations[0].rule == "FORBIDDEN_CALL"
    assert "getattr" in violations[0].message


def test_should_fail_when_contract_calls_open(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "f = open('file.txt')\n")
    assert len(violations) == 1
    assert violations[0].rule == "FORBIDDEN_CALL"
    assert "open" in violations[0].message


# ── Exception chaining ────────────────────────────────────────


def test_should_fail_when_contract_uses_raise_from(tmp_path: Path) -> None:
    code = (
        "try:\n"
        "    pass\n"
        "except Exception as e:\n"
        "    raise ValueError('msg') from e\n"
    )
    violations = lint_source(tmp_path, code)
    assert len(violations) == 1
    assert violations[0].rule == "EXCEPTION_CHAINING"


# ── Mutable global state ──────────────────────────────────────


def test_should_fail_when_contract_has_mutable_global_dict(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "CACHE = {}\n")
    assert len(violations) == 1
    assert violations[0].rule == "MUTABLE_GLOBAL"
    assert "CACHE" in violations[0].message


def test_should_fail_when_contract_has_mutable_global_list(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "STATE = []\n")
    assert len(violations) == 1
    assert violations[0].rule == "MUTABLE_GLOBAL"
    assert "STATE" in violations[0].message


def test_should_not_flag_mutable_local_inside_function(tmp_path: Path) -> None:
    code = "def hook(vault, args):\n    local_cache = {}\n    return local_cache\n"
    violations = lint_source(tmp_path, code)
    assert violations == []


def test_should_not_flag_mutable_local_inside_async_function(tmp_path: Path) -> None:
    code = "async def hook(vault, args):\n    local_cache = {}\n    return local_cache\n"
    violations = lint_source(tmp_path, code)
    assert violations == []


def test_should_not_flag_allowed_contract_globals(tmp_path: Path) -> None:
    code = (
        "from contracts_api import Parameter\n"
        "parameters = [Parameter()]\n"
        "event_types = []\n"
        "event_types_groups = []\n"
    )
    violations = lint_source(tmp_path, code)
    assert violations == []


# ── Line numbers ──────────────────────────────────────────────


def test_should_report_correct_line_number_for_violation(tmp_path: Path) -> None:
    code = "x = 1\nimport os\n"
    violations = lint_source(tmp_path, code)
    assert len(violations) == 1
    assert violations[0].line == 2


# ── Multiple violations ───────────────────────────────────────


def test_should_report_multiple_violations_in_single_file(tmp_path: Path) -> None:
    code = "import os\nimport sys\neval('x')\n"
    violations = lint_source(tmp_path, code)
    assert len(violations) == 3


# ── Directory scanning ────────────────────────────────────────


def test_should_lint_directory_and_aggregate_violations_across_files(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "import os\n", "a.py")
    _write(tmp_path, "import json\n", "b.py")
    _write(tmp_path, "x = 1\n", "c.py")
    violations = lint_directory(tmp_path)
    assert len(violations) == 2


# ── Violation __str__ ─────────────────────────────────────────


def test_violation_str_format(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "import os\n")
    assert len(violations) == 1
    text = str(violations[0])
    assert "[FORBIDDEN_IMPORT]" in text
    assert ":1" in text


# ── main() exit codes ─────────────────────────────────────────


def test_main_should_return_0_when_no_violations(tmp_path: Path) -> None:
    p = _write(tmp_path, "x = 1\n")
    result = main([str(p)])
    assert result == 0


def test_main_should_return_1_when_violations_found(tmp_path: Path) -> None:
    p = _write(tmp_path, "import os\n")
    result = main([str(p)])
    assert result == 1


def test_main_should_return_1_when_target_not_found(tmp_path: Path) -> None:
    result = main([str(tmp_path / "nonexistent.py")])
    assert result == 1


def test_main_should_lint_directory_when_target_is_dir(tmp_path: Path) -> None:
    _write(tmp_path, "import os\n", "bad.py")
    result = main([str(tmp_path)])
    assert result == 1
