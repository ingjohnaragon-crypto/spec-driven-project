"""Tests for vault_lint.py — Vault Python sandbox restriction linter."""
from __future__ import annotations

import sys
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


# ── API 4.0 style rules ───────────────────────────────────────


def test_should_fail_when_contract_uses_float_literal(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "amount = 100.00\n")
    assert any(v.rule == "FLOAT_USED" for v in violations)


def test_should_fail_when_contract_calls_float(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "amount = float('1.5')\n")
    assert any(v.rule == "FLOAT_USED" for v in violations)


def test_should_fail_when_contract_uses_timezone_utc(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "dt = timezone.utc\n")
    assert len(violations) == 1
    assert violations[0].rule == "TIMEZONE_UTC"


def test_should_fail_when_contract_uses_client_transaction_id(tmp_path: Path) -> None:
    code = "CustomInstruction(postings=[], client_transaction_id='x')\n"
    violations = lint_source(tmp_path, code)
    assert any(v.rule == "CLIENT_TRANSACTION_ID" for v in violations)


def test_should_fail_when_phase_read_from_balance_value(tmp_path: Path) -> None:
    code = "if balance.phase == Phase.COMMITTED:\n    pass\n"
    violations = lint_source(tmp_path, code)
    assert any(v.rule == "PHASE_ON_BALANCE" for v in violations)


def test_should_allow_zoneinfo_import(tmp_path: Path) -> None:
    violations = lint_source(tmp_path, "from zoneinfo import ZoneInfo\n")
    assert violations == []


# ── Parameter update_permission (Vault deploy schema) ─────────


def test_should_fail_when_instance_parameter_omits_update_permission(
    tmp_path: Path,
) -> None:
    code = (
        "p = Parameter(\n"
        "    name='denomination',\n"
        "    shape=DenominationShape(),\n"
        "    level=ParameterLevel.INSTANCE,\n"
        "    default_value='GBP',\n"
        ")\n"
    )
    violations = lint_source(tmp_path, code)
    assert any(v.rule == "INSTANCE_UPDATE_PERMISSION" for v in violations)
    assert any("denomination" in v.message for v in violations)


def test_should_pass_when_instance_parameter_sets_update_permission(
    tmp_path: Path,
) -> None:
    code = (
        "p = Parameter(\n"
        "    name='denomination',\n"
        "    level=ParameterLevel.INSTANCE,\n"
        "    update_permission=ParameterUpdatePermission.USER_EDITABLE,\n"
        ")\n"
    )
    violations = lint_source(tmp_path, code)
    assert violations == []


def test_should_pass_when_template_parameter_omits_update_permission(
    tmp_path: Path,
) -> None:
    code = (
        "p = Parameter(\n"
        "    name='interest_rate',\n"
        "    level=ParameterLevel.TEMPLATE,\n"
        "    default_value=Decimal('0.05'),\n"
        ")\n"
    )
    violations = lint_source(tmp_path, code)
    assert violations == []


def test_should_pass_when_derived_instance_parameter_omits_update_permission(
    tmp_path: Path,
) -> None:
    code = (
        "p = Parameter(\n"
        "    name='accrued_interest',\n"
        "    level=ParameterLevel.INSTANCE,\n"
        "    derived=True,\n"
        ")\n"
    )
    violations = lint_source(tmp_path, code)
    assert violations == []


def test_should_fail_when_derived_parameter_sets_update_permission(
    tmp_path: Path,
) -> None:
    code = (
        "p = Parameter(\n"
        "    name='accrued_interest',\n"
        "    level=ParameterLevel.INSTANCE,\n"
        "    derived=True,\n"
        "    update_permission=ParameterUpdatePermission.USER_EDITABLE,\n"
        ")\n"
    )
    violations = lint_source(tmp_path, code)
    assert any(v.rule == "DERIVED_UPDATE_PERMISSION" for v in violations)


# ── Hook data requirements (API 4.0) ─────────────────────────


def test_should_fail_when_hook_reads_parameters_without_requires(tmp_path: Path) -> None:
    code = (
        "def pre_posting_hook(vault, hook_arguments):\n"
        "    return vault.get_parameter_timeseries(name='denomination').latest()\n"
    )
    violations = lint_source(tmp_path, code)
    assert any(v.rule == "MISSING_PARAMETERS_REQUIREMENT" for v in violations)


def test_should_fail_when_hook_reads_balances_without_fetcher(tmp_path: Path) -> None:
    code = (
        "def pre_posting_hook(vault, hook_arguments):\n"
        "    return vault.get_balances_observation(fetcher_id='live_balances').balances\n"
    )
    violations = lint_source(tmp_path, code)
    assert any(v.rule == "MISSING_BALANCES_FETCHER" for v in violations)


def test_should_pass_when_hook_declares_both_requirements(tmp_path: Path) -> None:
    code = (
        "@requires(parameters=True)\n"
        "@fetch_account_data(balances=['live_balances'])\n"
        "def pre_posting_hook(vault, hook_arguments):\n"
        "    d = vault.get_parameter_timeseries(name='denomination').latest()\n"
        "    return vault.get_balances_observation(fetcher_id='live_balances').balances\n"
    )
    violations = lint_source(tmp_path, code)
    assert violations == []


def test_should_detect_requirement_through_helper_call(tmp_path: Path) -> None:
    code = (
        "def _param(vault, name):\n"
        "    return vault.get_parameter_timeseries(name=name).latest()\n"
        "\n"
        "def scheduled_event_hook(vault, hook_arguments):\n"
        "    return _param(vault, 'denomination')\n"
    )
    violations = lint_source(tmp_path, code)
    assert any(v.rule == "MISSING_PARAMETERS_REQUIREMENT" for v in violations)


def test_should_not_flag_non_hook_helper_that_reads_parameters(tmp_path: Path) -> None:
    code = (
        "def _param(vault, name):\n"
        "    return vault.get_parameter_timeseries(name=name).latest()\n"
    )
    violations = lint_source(tmp_path, code)
    assert violations == []


def test_should_accept_requires_balances_range_for_balances(tmp_path: Path) -> None:
    code = (
        "@requires(parameters=True, balances='latest live')\n"
        "def scheduled_event_hook(vault, hook_arguments):\n"
        "    vault.get_parameter_timeseries(name='x').latest()\n"
        "    return vault.get_balances_observation(fetcher_id='b').balances\n"
    )
    violations = lint_source(tmp_path, code)
    assert violations == []


# ── main() exit codes ─────────────────────────────────────────


def test_main_should_return_0_when_no_violations(tmp_path: Path, capsys) -> None:
    p = _write(tmp_path, "x = 1\n")
    result = main([str(p)])
    assert result == 0
    out = capsys.readouterr().out
    assert "Checking Vault sandbox restrictions..." in out
    assert "✔ No stdlib imports detected" in out
    assert "✔ 9/9 Vault rules — CLEAN" in out


def test_main_should_return_1_when_violations_found(tmp_path: Path, capsys) -> None:
    p = _write(tmp_path, "import os\n")
    result = main([str(p)])
    assert result == 1
    out = capsys.readouterr().out
    assert "✖ No stdlib imports detected" in out
    assert "Vault rules — FAILED" in out


def test_main_should_return_1_when_target_not_found(tmp_path: Path) -> None:
    result = main([str(tmp_path / "nonexistent.py")])
    assert result == 1


def test_main_should_lint_directory_when_target_is_dir(tmp_path: Path) -> None:
    _write(tmp_path, "import os\n", "bad.py")
    result = main([str(tmp_path)])
    assert result == 1


def test_main_should_return_1_when_directory_has_no_py_files(tmp_path: Path) -> None:
    result = main([str(tmp_path)])
    assert result == 1


# ── Color / Windows helpers ───────────────────────────────────


def test_use_color_respects_no_color(monkeypatch) -> None:
    from vault_lint import _use_color

    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    assert _use_color() is False


def test_use_color_respects_force_color(monkeypatch) -> None:
    from vault_lint import _c, _GREEN, _use_color

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert _use_color() is True
    assert _GREEN in _c(_GREEN, "ok")


def test_use_color_on_non_tty(monkeypatch) -> None:
    from vault_lint import _use_color

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    assert _use_color() is False


def test_enable_windows_vt_noop_on_non_windows(monkeypatch) -> None:
    from vault_lint import _enable_windows_vt

    monkeypatch.setattr(sys, "platform", "linux")
    assert _enable_windows_vt() is True


def test_enable_windows_vt_handles_console_mode_failure(monkeypatch) -> None:
    from vault_lint import _enable_windows_vt
    import types

    class _Kernel:
        def GetStdHandle(self, _n):  # noqa: N802
            return 1

        def GetConsoleMode(self, _h, _mode):  # noqa: N802
            return 0

    fake = types.ModuleType("ctypes")
    fake.windll = types.SimpleNamespace(kernel32=_Kernel())
    fake.c_uint32 = lambda: types.SimpleNamespace(value=0)
    fake.byref = lambda x: x
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "ctypes", fake)
    assert _enable_windows_vt() is False


def test_enable_windows_vt_success(monkeypatch) -> None:
    from vault_lint import _enable_windows_vt
    import types

    class _Kernel:
        def GetStdHandle(self, _n):  # noqa: N802
            return 1

        def GetConsoleMode(self, _h, mode):  # noqa: N802
            mode.value = 0
            return 1

        def SetConsoleMode(self, _h, _mode):  # noqa: N802
            return 1

    fake = types.ModuleType("ctypes")
    fake.windll = types.SimpleNamespace(kernel32=_Kernel())
    fake.c_uint32 = lambda: types.SimpleNamespace(value=0)
    fake.byref = lambda x: x
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "ctypes", fake)
    assert _enable_windows_vt() is True


def test_enable_windows_vt_handles_exceptions(monkeypatch) -> None:
    from vault_lint import _enable_windows_vt
    import types

    fake = types.ModuleType("ctypes")
    fake.windll = types.SimpleNamespace(kernel32=None)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "ctypes", fake)
    assert _enable_windows_vt() is False


def test_configure_stdout_swallows_errors(monkeypatch) -> None:
    from vault_lint import _configure_stdout

    def _boom(*_a, **_k):
        raise OSError("nope")

    monkeypatch.setattr(sys.stdout, "reconfigure", _boom, raising=False)
    monkeypatch.setattr(sys.stderr, "reconfigure", _boom, raising=False)
    _configure_stdout()  # must not raise


def test_use_color_on_linux_tty(monkeypatch) -> None:
    from vault_lint import _use_color

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert _use_color() is True
