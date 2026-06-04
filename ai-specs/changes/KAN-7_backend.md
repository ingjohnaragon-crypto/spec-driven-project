# Backend Implementation Plan: KAN-7 Add os-vault-lint for Vault Python Sandbox Validation

> **Status**: DONE — Merged to `develop` via PR #8 (commits `d04e2d7` + `101fd5c`)

## 1. Overview

This ticket delivers `os-vault-lint` — a static-analysis CLI command that scans
`contracts/*.py` files using Python's built-in `ast` module and reports any Vault
sandbox violations **before** tests run.

Vault Smart Contracts execute in a sandboxed Python environment that rejects many
standard-library patterns at **runtime**, with no file/line diagnostics. `os-vault-lint`
shifts detection to a fast, zero-dependency static step that gives precise `FILE:LINE`
output and blocks CI early.

Active stack: `python-fastapi` (`Python 3.12 + FastAPI`)

Forbidden patterns are defined in `ai-specs/.agents/stacks/vault-smart-contracts.md`.

---

## 2. Architecture Context

- **Active stack**: `python-fastapi` (`Python 3.12 + FastAPI`)
- **Layers involved**: CLI tooling, CI pipeline, Tests

This ticket does not touch the FastAPI application layers (Domain / Application /
Presentation / Infrastructure). All changes are confined to the developer-tooling
and CI layers.

### Files delivered

| Layer | File | Action |
|---|---|---|
| CLI tooling — Python | `.openspec-cli/lib/vault_lint.py` | Created |
| CLI tooling — Shell | `.openspec-cli/commands/os-vault-lint` | Created (mode `100755`) |
| CLI tooling — Shell | `.openspec-cli/commands/os-vault-test` | Modified |
| CI pipeline | `.github/workflows/ci.yml` | Modified |
| Tests | `tests/test_vault_lint.py` | Created |
| Config | `pytest.ini` | Modified (`pythonpath` added) |
| Config | `.gitignore` | Modified (Python + CLI patterns added) |
| Docs | `ai-specs/specs/development_guide.md` | Modified |

---

## 3. Implementation Steps

### Step 0: Create Feature Branch ✅

- **Branch**: `feature/KAN-7-backend`

---

### Step 1: Create Python AST Linter — `.openspec-cli/lib/vault_lint.py` ✅

Core linting logic using only Python standard library — no `pip install` required.

**Design delivered**:
- `Violation` dataclass: `file`, `line`, `rule`, `message`; `__str__` → `FILE:LINE [RULE] message`
- `VaultLintVisitor(ast.NodeVisitor)`: walks AST, appends violations
- `lint_file(path: Path) -> list[Violation]`
- `lint_directory(directory: Path) -> list[Violation]`
- `main(argv: list[str] | None = None) -> int`: argparse CLI entry point

**Implementation notes vs plan**:
- `visit_Call` restricted to `isinstance(node.func, ast.Name)` only — original plan
  also checked `ast.Attribute`, which would have caused false positives on method calls
  like `obj.type(...)` or `obj.open(...)`. Fixed during code review.
- `visit_FunctionDef` saves/restores `_in_function` via `prev` variable — correctly
  handles nested functions without resetting state prematurely.
- `visit_AsyncFunctionDef` implemented as a proper delegating method instead of a
  class-level assignment (avoids `type: ignore[assignment]`).
- `CONTRACT_ALLOWED_GLOBALS` carries a comment linking to the source spec section.

**Rule constants**:

| Constant | Contents |
|---|---|
| `FORBIDDEN_IMPORTS` | `os sys json re math datetime collections functools itertools random hashlib uuid logging traceback threading subprocess requests http urllib` |
| `ALLOWED_TOP_LEVEL_IMPORTS` | `contracts_api decimal` |
| `FORBIDDEN_CALLS` | `eval exec compile __import__ globals locals vars dir getattr setattr hasattr delattr type open print input` |
| `CONTRACT_ALLOWED_GLOBALS` | `api version display_name summary description tside supported_denominations parameters event_types event_types_groups DEFAULT_ADDRESS DEFAULT_ASSET` |

**AST visitors**:

| Visitor | Rule |
|---------|------|
| `visit_Import` | `FORBIDDEN_IMPORT` / `UNKNOWN_IMPORT` |
| `visit_ImportFrom` | `FORBIDDEN_IMPORT` / `UNKNOWN_IMPORT` |
| `visit_Call` | `FORBIDDEN_CALL` (bare name calls only — `ast.Name`) |
| `visit_Raise` | `EXCEPTION_CHAINING` |
| `visit_FunctionDef` / `visit_AsyncFunctionDef` | Track `_in_function` scope |
| `visit_Assign` | `MUTABLE_GLOBAL` |

---

### Step 2: Create Bash Wrapper — `.openspec-cli/commands/os-vault-lint` ✅

- Mode `100755` (executable bit set via `git update-index --chmod=+x`)
- Uses `os_load_config` + correct `colors.sh` functions: `os_divider`, `os_label`,
  `os_info`, `os_step`, `os_success`, `os_error`
- Default target: `contracts/`; accepts one optional positional argument

---

### Step 3: Modify `os-vault-test` — Add Lint Pre-Check ✅

Inserted before `os_step "Running tests..."`:

```bash
os_step "Running Vault lint pre-check..."
"${SCRIPT_DIR}/os-vault-lint" "contracts/" || {
    os_error "Lint failed — fix sandbox violations before running tests."
    exit 1
}
```

Lint target is hardcoded to `contracts/`, not `$TEST_TARGET`.

---

### Step 4: Modify CI — `.github/workflows/ci.yml` ✅

Two new steps added (in order):

```yaml
- name: Run Vault lint (sandbox restriction check)
  run: python .openspec-cli/lib/vault_lint.py contracts/

- name: Run vault_lint unit tests
  run: pytest tests/test_vault_lint.py -v --cov=vault_lint --cov-fail-under=90
```

Both run before `Run Vault Smart Contract tests`. The second step was added during
code review to ensure regressions in `vault_lint.py` are caught in CI.

---

### Step 5: Create Unit Tests — `tests/test_vault_lint.py` ✅

27 tests, all passing. Module imported via `pytest.ini` `pythonpath` (no `sys.path.insert`).

**Tests delivered**:

| Test | Result |
|------|--------|
| `test_should_pass_when_contract_has_no_violations` | ✅ |
| `test_should_pass_when_contract_imports_contracts_api_and_decimal_only` | ✅ |
| `test_should_pass_for_existing_savings_product_contract` | ✅ |
| `test_should_fail_when_contract_imports_os` | ✅ |
| `test_should_fail_when_contract_imports_json` | ✅ |
| `test_should_fail_when_contract_uses_from_datetime_import` | ✅ |
| `test_should_flag_unknown_import_statement` | ✅ |
| `test_should_flag_unknown_from_import_statement` | ✅ |
| `test_should_fail_when_contract_calls_eval` | ✅ |
| `test_should_fail_when_contract_calls_exec` | ✅ |
| `test_should_fail_when_contract_calls_print` | ✅ |
| `test_should_fail_when_contract_calls_getattr` | ✅ |
| `test_should_fail_when_contract_calls_open` | ✅ |
| `test_should_fail_when_contract_uses_raise_from` | ✅ |
| `test_should_fail_when_contract_has_mutable_global_dict` | ✅ |
| `test_should_fail_when_contract_has_mutable_global_list` | ✅ |
| `test_should_not_flag_mutable_local_inside_function` | ✅ |
| `test_should_not_flag_mutable_local_inside_async_function` | ✅ |
| `test_should_not_flag_allowed_contract_globals` | ✅ |
| `test_should_report_correct_line_number_for_violation` | ✅ |
| `test_should_report_multiple_violations_in_single_file` | ✅ |
| `test_should_lint_directory_and_aggregate_violations_across_files` | ✅ |
| `test_violation_str_format` | ✅ |
| `test_main_should_return_0_when_no_violations` | ✅ |
| `test_main_should_return_1_when_violations_found` | ✅ |
| `test_main_should_return_1_when_target_not_found` | ✅ |
| `test_main_should_lint_directory_when_target_is_dir` | ✅ |

---

### Step 6: Update Technical Documentation ✅

- `ai-specs/specs/development_guide.md` — `os-vault-lint` command, output format, rules
  table, and coverage command documented.
- `.gitignore` — Python (`__pycache__/`, `*.pyc`, `.coverage`, `htmlcov/`) and CLI
  internal file patterns (`.openspec-cli/.*.applied`, `.last-prompt.md`,
  `.pr-diff.patch`) added.
- `pytest.ini` — `pythonpath = .openspec-cli/lib` added for clean test imports.

---

## 4. Implementation Order

1. ✅ Step 0 — Feature branch
2. ✅ Step 1 — `vault_lint.py`
3. ✅ Step 2 — `os-vault-lint` wrapper
4. ✅ Step 3 — `os-vault-test` pre-check
5. ✅ Step 4 — `ci.yml`
6. ✅ Step 5 — `tests/test_vault_lint.py`
7. ✅ Step 6 — Documentation

---

## 5. Testing Checklist

- [x] `pytest tests/test_vault_lint.py -v` passes — 27/27
- [x] `pytest --cov=vault_lint --cov-fail-under=90` passes — **99% coverage**
  (only `__main__` guard uncovered)
- [x] `python .openspec-cli/lib/vault_lint.py contracts/` exits `0` — no false positives
      on `savings_product.py`
- [x] `os-vault-test` calls `os-vault-lint contracts/` and aborts if it fails
- [x] CI step `Run Vault lint` precedes `Run Vault Smart Contract tests`
- [x] CI step `Run vault_lint unit tests` also added
- [x] Existing `pytest tests/test_savings_product.py` still passes — 46/46 total

---

## 6. Tooling Reference

| Purpose | Command |
|---|---|
| Build | `pip install -r requirements.txt` |
| Test | `pytest` |
| Run | `uvicorn main:app --reload` |
| Lint | `ruff check .` |
| Coverage | `pytest --cov --cov-report=html` |
| Run linter on contracts | `python .openspec-cli/lib/vault_lint.py contracts/` |
| Run linter via CLI | `os-vault-lint` |
| Lint coverage (linter only) | `pytest tests/test_vault_lint.py --cov=vault_lint --cov-fail-under=90` |

---

## 7. Error Response Format

`os-vault-lint` is a CLI tool — it does not expose HTTP endpoints.

**Standard output** (one line per violation):
```
<file>:<line> [<RULE_ID>] <human-readable message>
```

**Standard error** (only when violations exist):
```
N violation(s) found.
```

**Exit codes**: `0` = no violations · `1` = violations found or target not found

---

## 8. Dependencies

No new `pip` dependencies. `vault_lint.py` uses only Python 3.12 standard library:
`ast`, `sys`, `pathlib`, `argparse`, `dataclasses`.

---

## 9. Notes

**Divergences from original plan corrected during code review (PR #8)**:

| Finding | Resolution |
|---------|-----------|
| `visit_Call` also checked `ast.Attribute` → false positives on `obj.type(...)` | Restricted to `ast.Name` only |
| `visit_AsyncFunctionDef` assigned via class-level alias (type-unsafe) | Replaced with proper delegating method |
| `sys.path.insert` in test file polluted global import path | Replaced with `pythonpath` in `pytest.ini` |
| Build artifacts committed (`.coverage`, `__pycache__`, `.pyc`) | Removed via `git rm --cached`; added to `.gitignore` |
| Internal CLI files committed (`.applied`, `.last-prompt.md`) | Removed and gitignored |
| `os-vault-lint` executable bit not set | Fixed via `git update-index --chmod=+x` |
| `test_vault_lint.py` not executed in CI | Added `Run vault_lint unit tests` step |

**Pre-existing issue tracked as follow-up**:
- `os-vault-test` uses `os_print_separator`, `os_print_header`, `os_print_info`,
  `os_print_success`, `os_print_error` — none of which exist in `colors.sh`. These
  silently no-op. The new code added by this ticket correctly uses `os_error` / `os_step`.
  A follow-up ticket should migrate the pre-existing calls to `os_divider`, `os_label`,
  `os_info`, `os_success`, `os_error`.

---

## 10. Implementation Verification Checklist

- [x] **Code quality**: stdlib-only imports; clean `from __future__ import annotations`
- [x] **No runtime deps**: `vault_lint.py` imports only standard library modules
- [x] **CLI contract**: exits `0` on clean contracts, `1` on violations
- [x] **Pre-test gate**: `os-vault-test` runs lint first and aborts if lint fails
- [x] **CI gate**: `Run Vault lint` precedes `Run Vault Smart Contract tests` in `ci.yml`
- [x] **CI coverage**: `Run vault_lint unit tests` step added to CI
- [x] **Tests**: 27 green, coverage 99% on `vault_lint.py`
- [x] **No regressions**: `test_savings_product.py` suite still passes (46/46 total)
- [x] **Documentation**: `development_guide.md` and `.gitignore` updated
- [x] **Executable bit**: `os-vault-lint` mode `100755`
- [x] **Git hygiene**: no build artifacts or internal CLI files tracked
