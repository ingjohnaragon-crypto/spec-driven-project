"""vault_lint.py — Static analysis for Vault Python sandbox restrictions."""
from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

FORBIDDEN_IMPORTS: set[str] = {
    "os", "sys", "json", "re", "math", "datetime", "collections",
    "functools", "itertools", "random", "hashlib", "uuid", "logging",
    "traceback", "threading", "subprocess", "requests", "http", "urllib",
}

ALLOWED_TOP_LEVEL_IMPORTS: set[str] = {"contracts_api", "decimal"}

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
    "balance_observation_fetchers",
    "DEFAULT_ADDRESS", "DEFAULT_ASSET",
}


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
                    f"(allowed: contracts_api, decimal)",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vault Python sandbox restriction linter")
    parser.add_argument(
        "targets",
        nargs="*",
        default=["contracts/"],
        help="Files or directories to lint (default: contracts/)",
    )
    args = parser.parse_args(argv)

    all_violations: list[Violation] = []
    for target_str in args.targets:
        target = Path(target_str)
        if target.is_dir():
            all_violations.extend(lint_directory(target))
        elif target.is_file():
            all_violations.extend(lint_file(target))
        else:
            print(f"ERROR: target not found: {target}", file=sys.stderr)
            return 1

    for v in all_violations:
        print(v)

    if all_violations:
        print(f"\n{len(all_violations)} violation(s) found.", file=sys.stderr)
        return 1

    print("No violations found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
