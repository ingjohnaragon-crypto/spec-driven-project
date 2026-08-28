"""vault_lint.py — Static analysis for Vault Python sandbox restrictions."""
from __future__ import annotations

import argparse
import ast
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

FORBIDDEN_IMPORTS: set[str] = {
    "os", "sys", "json", "re", "math", "datetime", "collections",
    "functools", "itertools", "random", "hashlib", "uuid", "logging",
    "traceback", "threading", "subprocess", "requests", "http", "urllib",
}

ALLOWED_TOP_LEVEL_IMPORTS: set[str] = {"contracts_api", "decimal", "zoneinfo"}

FORBIDDEN_CALLS: set[str] = {
    "eval", "exec", "compile", "__import__",
    "globals", "locals", "vars", "dir",
    "getattr", "setattr", "hasattr", "delattr",
    "type", "open", "print", "input",
}

# Canonical source: ai-specs/.agents/stacks/vault-smart-contracts.md § ALLOWED
CONTRACT_ALLOWED_GLOBALS: set[str] = {
    "api", "version", "display_name", "summary", "description",
    "tside", "supported_denominations", "parameters",
    "event_types", "event_types_groups",
    "data_fetchers",  # API 4.0 metadata name for observation/interval fetchers
    "DEFAULT_ADDRESS", "DEFAULT_ASSET",
}

BALANCE_VALUE_NAMES: set[str] = {"balance", "bal", "value"}

# Display checklist — label + violation rule codes that fail it
DISPLAY_RULES: tuple[tuple[str, frozenset[str]], ...] = (
    ("No stdlib imports detected", frozenset({"FORBIDDEN_IMPORT", "UNKNOWN_IMPORT"})),
    ("No eval/exec/globals/locals", frozenset({"FORBIDDEN_CALL", "EXCEPTION_CHAINING"})),
    ("No mutable global state", frozenset({"MUTABLE_GLOBAL"})),
    ("Decimal used (not float)", frozenset({"FLOAT_USED"})),
    ("ZoneInfo used (not timezone.utc)", frozenset({"TIMEZONE_UTC"})),
    ("No client_transaction_id", frozenset({"CLIENT_TRANSACTION_ID"})),
    ("Phase read from BalanceCoordinate", frozenset({"PHASE_ON_BALANCE"})),
    (
        "INSTANCE params declare update_permission",
        frozenset({"INSTANCE_UPDATE_PERMISSION", "DERIVED_UPDATE_PERMISSION"}),
    ),
)

_GREEN = "\033[0;32m"
_RED = "\033[0;31m"
_CYAN = "\033[0;36m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _enable_windows_vt() -> bool:
    """Enable ANSI VT mode on Windows conhost/Windows Terminal. Returns True if enabled."""
    if sys.platform != "win32":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except (AttributeError, OSError, ValueError):
        return False


def _use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not sys.stdout.isatty():
        return False
    # On Windows, Python often emits ANSI that Git Bash/cmd show as "←[0;32m".
    # Only color when the console actually accepts VT sequences.
    if sys.platform == "win32":
        return _enable_windows_vt()
    return True


def _c(code: str, text: str) -> str:
    if not _use_color():
        return text
    return f"{code}{text}{_RESET}"


@dataclass
class Violation:
    file: str
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line} [{self.rule}] {self.message}"


class VaultLintVisitor(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.violations: list[Violation] = []
        self._in_function: bool = False

    def _add(self, node: ast.AST, rule: str, msg: str) -> None:
        self.violations.append(
            Violation(self.filename, node.lineno, rule, msg)  # type: ignore[attr-defined]
        )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in FORBIDDEN_IMPORTS:
                self._add(node, "FORBIDDEN_IMPORT", f"import {alias.name!r} is not allowed")
            elif root not in ALLOWED_TOP_LEVEL_IMPORTS:
                self._add(
                    node,
                    "UNKNOWN_IMPORT",
                    f"import {alias.name!r} is not in the allowed list "
                    f"(allowed: contracts_api, decimal, zoneinfo)",
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        root = module.split(".")[0]
        if root in FORBIDDEN_IMPORTS:
            self._add(node, "FORBIDDEN_IMPORT", f"from {module!r} import ... is not allowed")
        elif root not in ALLOWED_TOP_LEVEL_IMPORTS:
            self._add(
                node,
                "UNKNOWN_IMPORT",
                f"from {module!r} import ... is not in the allowed list",
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            self._add(
                node,
                "FORBIDDEN_CALL",
                f"call to {node.func.id!r} is not allowed in contracts",
            )
        if isinstance(node.func, ast.Name) and node.func.id == "float":
            self._add(node, "FLOAT_USED", "use Decimal instead of float()")
        for kw in node.keywords:
            if kw.arg == "client_transaction_id":
                self._add(
                    node,
                    "CLIENT_TRANSACTION_ID",
                    "client_transaction_id is not allowed — use instruction_details",
                )
        if isinstance(node.func, ast.Name) and node.func.id == "Parameter":
            self._check_parameter_update_permission(node)
        self.generic_visit(node)

    def _check_parameter_update_permission(self, node: ast.Call) -> None:
        """INSTANCE parameters require update_permission; DERIVED must not set it.

        Vault's POST /v1/product-versions rejects an instance-level parameter
        with no update_permission (misleading error points at the deploy, but
        the fix is in the contract). update_permission is not supported for
        DERIVED/TEMPLATE parameters.
        """
        name = "<unknown>"
        level_is_instance = False
        is_derived = False
        has_update_permission = False
        for kw in node.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                name = str(kw.value.value)
            elif kw.arg == "level" and isinstance(kw.value, ast.Attribute):
                level_is_instance = kw.value.attr == "INSTANCE"
            elif kw.arg == "derived":
                is_derived = isinstance(kw.value, ast.Constant) and kw.value.value is True
            elif kw.arg == "update_permission":
                has_update_permission = True

        if is_derived and has_update_permission:
            self._add(
                node,
                "DERIVED_UPDATE_PERMISSION",
                f"derived parameter {name!r} must not set update_permission "
                "(not supported for DERIVED/TEMPLATE)",
            )
        elif level_is_instance and not is_derived and not has_update_permission:
            self._add(
                node,
                "INSTANCE_UPDATE_PERMISSION",
                f"INSTANCE parameter {name!r} must set update_permission="
                "ParameterUpdatePermission.USER_EDITABLE (required by Vault deploy)",
            )

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, float):
            self._add(
                node,
                "FLOAT_USED",
                f"float literal {node.value!r} is forbidden — use Decimal",
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "timezone"
            and node.attr == "utc"
        ):
            self._add(
                node,
                "TIMEZONE_UTC",
                "timezone.utc is forbidden — use ZoneInfo('UTC')",
            )
        if (
            isinstance(node.value, ast.Name)
            and node.value.id in BALANCE_VALUE_NAMES
            and node.attr == "phase"
        ):
            self._add(
                node,
                "PHASE_ON_BALANCE",
                f"read phase from BalanceCoordinate (key), not from {node.value.id!r}",
            )
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        if node.cause is not None:
            self._add(
                node,
                "EXCEPTION_CHAINING",
                "'raise ... from ...' is not allowed in contracts",
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        prev = self._in_function
        self._in_function = True
        self.generic_visit(node)
        self._in_function = prev

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_Assign(self, node: ast.Assign) -> None:
        if not self._in_function:
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and isinstance(node.value, (ast.List, ast.Dict, ast.Set))
                    and target.id not in CONTRACT_ALLOWED_GLOBALS
                ):
                    self._add(
                        node,
                        "MUTABLE_GLOBAL",
                        f"module-level mutable variable {target.id!r} is forbidden "
                        "(state is reset between hook calls)",
                    )
        self.generic_visit(node)


def lint_file(path: Path) -> list[Violation]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    visitor = VaultLintVisitor(str(path))
    visitor.visit(tree)
    return visitor.violations


def lint_directory(directory: Path) -> list[Violation]:
    violations: list[Violation] = []
    for py_file in sorted(directory.glob("*.py")):
        violations.extend(lint_file(py_file))
    return violations


def collect_targets(target_strs: list[str]) -> list[Path] | None:
    """Resolve CLI targets to concrete .py files. Returns None if a target is missing."""
    files: list[Path] = []
    for target_str in target_strs:
        target = Path(target_str)
        if target.is_dir():
            files.extend(sorted(target.glob("*.py")))
        elif target.is_file():
            files.append(target)
        else:
            print(f"ERROR: target not found: {target}", file=sys.stderr)
            return None
    return files


def _print_checklist(violations: list[Violation], elapsed_s: float) -> int:
    """Print the Vault rules checklist. Returns number of failed display rules."""
    print("Checking Vault sandbox restrictions...")
    failed_rules = 0
    total = len(DISPLAY_RULES)
    violated_codes = {v.rule for v in violations}

    for label, codes in DISPLAY_RULES:
        ok = violated_codes.isdisjoint(codes)
        if ok:
            print(_c(_GREEN, f"  ✔ {label}"))
        else:
            failed_rules += 1
            print(_c(_RED, f"  ✖ {label}"))

    print(_c(_CYAN, "────────────────────────────────────────────"))

    passed = total - failed_rules
    if failed_rules == 0:
        summary = f"✔ {passed}/{total} Vault rules — CLEAN"
        print(f"{_c(_GREEN + _BOLD, summary)}                    ⏱ {elapsed_s:.2f}s")
    else:
        summary = f"✖ {passed}/{total} Vault rules — FAILED"
        print(f"{_c(_RED + _BOLD, summary)}                   ⏱ {elapsed_s:.2f}s")

    if violations:
        print()
        for v in violations:
            print(v)

    return failed_rules


def _configure_stdout() -> None:
    """Avoid UnicodeEncodeError on Windows consoles (cp1252) for ✔/✖/⏱."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass


def main(argv: list[str] | None = None) -> int:
    _configure_stdout()
    parser = argparse.ArgumentParser(description="Vault Python sandbox restriction linter")
    parser.add_argument(
        "targets",
        nargs="*",
        default=["contracts/"],
        help="Files or directories to lint (default: contracts/)",
    )
    args = parser.parse_args(argv)

    files = collect_targets(args.targets)
    if files is None:
        return 1

    if not files:
        print("ERROR: no .py files found in target(s).", file=sys.stderr)
        return 1

    started = time.perf_counter()
    all_violations: list[Violation] = []
    for path in files:
        all_violations.extend(lint_file(path))
    elapsed = time.perf_counter() - started

    failed_rules = _print_checklist(all_violations, elapsed)
    return 1 if failed_rules or all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
