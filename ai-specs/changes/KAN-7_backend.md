# Backend Implementation Plan: KAN-7 Add os-vault-lint for Vault Python Sandbox Validation

## 1. Overview

This ticket delivers `os-vault-lint` — a static-analysis CLI command that scans
`contracts/*.py` files using Python's built-in `ast` module and reports any Vault
sandbox violations **before** tests run.

Vault Smart Contracts execute in a sandboxed Python environment that rejects many
standard-library patterns at **runtime**, with no file/line diagnostics. Currently a
developer only discovers violations when `os-vault-test` fails. `os-vault-lint` shifts
that detection to a fast, zero-dependency static step that gives precise `FILE:LINE`
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

### Files affected per layer

| Layer | File | Action |
|---|---|---|
| CLI tooling — Python | `.openspec-cli/lib/vault_lint.py` | **Create** |
| CLI tooling — Shell | `.openspec-cli/commands/os-vault-lint` | **Create** |
| CLI tooling — Shell | `.openspec-cli/commands/os-vault-test` | **Modify** |
| CI pipeline | `.github/workflows/ci.yml` | **Modify** |
| Tests | `tests/test_vault_lint.py` | **Create** |

---

## 3. Implementation Steps

### Step 0: Create Feature Branch

- **Action**: Create and switch to a new feature branch
- **Branch**: `feature/KAN-7-backend`
- **Commands**:
  ```bash
  git checkout main && git pull origin main
  git checkout -b feature/KAN-7-backend
  ```

---

### Step 1: Create Python AST Linter — `.openspec-cli/lib/vault_lint.py`

- **File**: `.openspec-cli/lib/vault_lint.py`
- **Purpose**: Core linting logic. Uses only Python standard library (`ast`, `sys`,
  `pathlib`, `argparse`, `dataclasses`) — no `pip install` required.
- **Design**:
  - `Violation` dataclass: `file`, `line`, `rule`, `message`; `__str__` renders
    `FILE:LINE [RULE] message`
  - `VaultLintVisitor(ast.NodeVisitor)`: walks the AST and appends violations
  - `lint_file(path: Path) -> list[Violation]`: parses one file, returns violations
  - `lint_directory(directory: Path) -> list[Violation]`: globs `*.py`, aggregates
  - `main(argv) -> int`: `argparse` entry point; exits `0` (clean) or `1` (violations)

- **Rule constants to define**:

  | Constant | Contents |
  |---|---|
  | `FORBIDDEN_IMPORTS` | `os sys json re math datetime collections functools itertools random hashlib uuid logging traceback threading subprocess requests http urllib` |
  | `ALLOWED_TOP_LEVEL_IMPORTS` | `contracts_api decimal` |
  | `FORBIDDEN_CALLS` | `eval exec compile __import__ globals locals vars dir getattr setattr hasattr delattr type open print input` |
  | `CONTRACT_ALLOWED_GLOBALS` | `api version display_name summary description tside supported_denominations parameters event_types event_types_groups DEFAULT_ADDRESS DEFAULT_ASSET` |

- **AST visitors to implement**:

  | Visitor method | Rule detected |
  |---|---|
  | `visit_Import` | `FORBIDDEN_IMPORT` — banned module; `UNKNOWN_IMPORT` — not in allowlist |
  | `visit_ImportFrom` | Same as above, for `from X import Y` |
  | `visit_Call` | `FORBIDDEN_CALL` — call name matches forbidden set |
  | `visit_Raise` | `EXCEPTION_CHAINING` — `node.cause is not None` |
  | `visit_FunctionDef` / `visit_AsyncFunctionDef` | Track `_in_function` context |
  | `visit_Assign` | `MUTABLE_GLOBAL` — module-level `list`/`dict`/`set` not in allowed globals |

- **Output format** (one line per violation):
  ```
  contracts/foo.py:12 [FORBIDDEN_IMPORT] import 'os' is not allowed
  contracts/foo.py:34 [FORBIDDEN_CALL] call to 'eval' is not allowed in contracts
  contracts/foo.py:56 [EXCEPTION_CHAINING] 'raise ... from ...' is not allowed in contracts
  ```

- **Exit codes**: `0` = clean, `1` = violations found or file not found

---

### Step 2: Create Bash Wrapper — `.openspec-cli/commands/os-vault-lint`

- **File**: `.openspec-cli/commands/os-vault-lint`
- **Purpose**: CLI entry point consistent with the existing `os-vault-*` command family.
  Wraps `vault_lint.py` using `$OS_PYTHON` and the shared `colors.sh` / `config.sh`
  helpers already used by `os-vault-test`.
- **Behaviour**:
  - Default target: `contracts/` (the whole directory)
  - Accepts a single optional positional argument for a specific file or directory
  - Calls `os_print_header`, `os_print_info`, `os_step`, `os_print_success` /
    `os_print_error` from `colors.sh`
  - Exits `1` if `vault_lint.py` exits non-zero
  - Must be marked executable: `chmod +x .openspec-cli/commands/os-vault-lint`
- **Shebang / options**: `#!/usr/bin/env bash` + `set -euo pipefail`

---

### Step 3: Modify `os-vault-test` — Add Lint Pre-Check

- **File**: `.openspec-cli/commands/os-vault-test`
- **Change**: Insert a call to `os-vault-lint` immediately before the
  `os_step "Running tests..."` block.
- **Behaviour**: If lint fails, print an error and `exit 1` — tests never run.
- **Target passed to lint**: same `$TEST_TARGET` variable already resolved in the script
  (defaults to `tests/`, but the lint target should be `contracts/` since that is what
  is scanned; use `contracts/` as the hardcoded default for the lint call, not
  `$TEST_TARGET`).

---

### Step 4: Modify CI — `.github/workflows/ci.yml`

- **File**: `.github/workflows/ci.yml`
- **Change**: Add a new step named `Run Vault lint (sandbox restriction check)`
  immediately **before** the `Run Vault Smart Contract tests` step.
- **Command in the new step**:
  ```
  python .openspec-cli/lib/vault_lint.py contracts/
  ```
- **Effect**: CI fails fast on sandbox violations before spinning up pytest; the
  existing test step and coverage upload are unchanged.

---

### Step 5: Create Unit Tests — `tests/test_vault_lint.py`

- **File**: `tests/test_vault_lint.py`
- **Tool**: `pytest` (sync — no async needed; `ast` parsing is synchronous)
- **Pattern**: AAA (Arrange / Act / Assert)
- **Naming convention**: `test_should_<result>_when_<condition>`
- **Helper approach**: define a `lint_source(code: str) -> list[Violation]` fixture
  helper that writes a temp file (via `tmp_path`) and calls `lint_file()` — avoids
  real filesystem assumptions in unit tests.

- **Cases to cover**:

  | Test name | Expected |
  |---|---|
  | `test_should_pass_when_contract_has_no_violations` | `[]` |
  | `test_should_pass_when_contract_imports_contracts_api_and_decimal_only` | `[]` |
  | `test_should_pass_for_existing_savings_product_contract` | `[]` on `contracts/savings_product.py` |
  | `test_should_fail_when_contract_imports_os` | 1 × `FORBIDDEN_IMPORT` |
  | `test_should_fail_when_contract_imports_json` | 1 × `FORBIDDEN_IMPORT` |
  | `test_should_fail_when_contract_uses_from_datetime_import` | 1 × `FORBIDDEN_IMPORT` |
  | `test_should_fail_when_contract_calls_eval` | 1 × `FORBIDDEN_CALL` |
  | `test_should_fail_when_contract_calls_exec` | 1 × `FORBIDDEN_CALL` |
  | `test_should_fail_when_contract_calls_print` | 1 × `FORBIDDEN_CALL` |
  | `test_should_fail_when_contract_calls_getattr` | 1 × `FORBIDDEN_CALL` |
  | `test_should_fail_when_contract_calls_open` | 1 × `FORBIDDEN_CALL` |
  | `test_should_fail_when_contract_uses_raise_from` | 1 × `EXCEPTION_CHAINING` |
  | `test_should_fail_when_contract_has_mutable_global_dict` | 1 × `MUTABLE_GLOBAL` |
  | `test_should_fail_when_contract_has_mutable_global_list` | 1 × `MUTABLE_GLOBAL` |
  | `test_should_report_correct_line_number_for_violation` | `violation.line` matches |
  | `test_should_report_multiple_violations_in_single_file` | all violations returned |
  | `test_should_lint_directory_and_aggregate_violations_across_files` | violations from all `.py` files |
  | `test_main_should_return_0_when_no_violations` | `main()` exit code `0` |
  | `test_main_should_return_1_when_violations_found` | `main()` exit code `1` |

- **Coverage target**: ≥ 90% on `.openspec-cli/lib/vault_lint.py`

---

### Step 6: Update Technical Documentation

- **`ai-specs/changes/KAN-7_backend.md`** — this plan file (already saved)
- **`ai-specs/.agents/stacks/vault-smart-contracts.md`** — no changes needed; the
  forbidden-pattern list is already complete and serves as the single source of truth
  for the linter's rule constants.
- **`ai-specs/specs/development_guide.md`** — add a `## Vault Lint` section under the
  Python/FastAPI section documenting the new `os-vault-lint` command and its usage.

---

## 4. Implementation Order

1. Step 0 — Create feature branch
2. Step 1 — Create `.openspec-cli/lib/vault_lint.py`
3. Step 2 — Create `.openspec-cli/commands/os-vault-lint`
4. Step 3 — Modify `.openspec-cli/commands/os-vault-test`
5. Step 4 — Modify `.github/workflows/ci.yml`
6. Step 5 — Create `tests/test_vault_lint.py`
7. Step 6 — Update documentation

---

## 5. Testing Checklist

- [ ] `pytest tests/test_vault_lint.py -v` passes with 0 failures
- [ ] `pytest --cov=.openspec-cli/lib --cov-report=html --cov-fail-under=90` passes
- [ ] `python .openspec-cli/lib/vault_lint.py contracts/` exits `0` on the existing
      `savings_product.py` (no false positives)
- [ ] Manually introduce a forbidden import in a temp file and verify `os-vault-lint`
      exits `1` with correct `FILE:LINE [RULE] message` output
- [ ] `os-vault-test` aborts before running pytest when a violation is present
- [ ] CI step `Run Vault lint` appears before `Run Vault Smart Contract tests` and
      blocks the pipeline on violations
- [ ] Existing `pytest tests/test_savings_product.py` still passes (no regressions)

---

## 6. Tooling Reference

Commands resolved from `openspec/config.yaml` for the active stack (`python-fastapi`):

| Purpose | Command |
|---|---|
| Build | `pip install -r requirements.txt` |
| Test | `pytest` |
| Run | `uvicorn main:app --reload` |
| Lint | `ruff check .` |
| Coverage | `pytest --cov --cov-report=html` |

Additional commands for this ticket:

| Purpose | Command |
|---|---|
| Run linter on contracts | `python .openspec-cli/lib/vault_lint.py contracts/` |
| Run linter via CLI | `os-vault-lint` |
| Lint coverage (linter only) | `pytest tests/test_vault_lint.py --cov=.openspec-cli/lib/vault_lint --cov-fail-under=90` |
| Type check linter | `mypy .openspec-cli/lib/vault_lint.py --strict` |
| Lint the linter | `ruff check .openspec-cli/lib/vault_lint.py` |

---

## 7. Error Response Format

`os-vault-lint` is a CLI tool — it does not expose HTTP endpoints. Its output contract is:

**Standard output** (one line per violation):
```
<file>:<line> [<RULE_ID>] <human-readable message>
```

**Standard error** (summary, only when violations exist):
```
N violation(s) found.
```

**Exit codes**:
- `0` — no violations
- `1` — violations found, or target file/directory not found

---

## 8. Dependencies

No new `pip` dependencies are required.

`vault_lint.py` uses only Python 3.12 standard library modules:
- `ast` — AST parsing and traversal
- `sys` — exit codes, stderr
- `pathlib` — file/directory operations
- `argparse` — CLI argument parsing
- `dataclasses` — `Violation` dataclass

`tests/test_vault_lint.py` uses only `pytest` (already installed via
`pip install -r requirements.txt`). No additional packages needed.

---

## 9. Notes

- **No false positives on `savings_product.py`**: the existing contract uses
  `from contracts_api import BalanceCoordinate` inside a function body (line 90).
  `visit_ImportFrom` must treat this as an allowed import because `contracts_api` is
  in `ALLOWED_TOP_LEVEL_IMPORTS` — verify that the visitor does not flag it.
- **`type` is forbidden**: the call-name check catches the built-in `type(obj)`.
  However, `type` is also used legitimately in `isinstance()` checks — only direct
  `type(obj)` calls (i.e., `ast.Call` whose `func` is an `ast.Name` with `id="type"`)
  should be flagged, not references to `type` as a value inside `isinstance`.
  The `visit_Call` visitor naturally handles this correctly since `isinstance(obj, type)`
  has `func.id == "isinstance"`, not `"type"`.
- **Mutable global detection scope**: the `visit_Assign` visitor must only flag
  assignments at module level (not inside functions or classes). Track
  `_in_function`/`_in_class` state via the function visitor methods.
- **`string` module not imported in linter**: the draft enriched ticket referenced
  `string.ascii_uppercase` inside `visit_Assign` — this is a bug (the linter itself
  cannot import `string` without that being caught by its own rules if applied to
  itself, though `vault_lint.py` is not a contract). Implement the ALL_CAPS constant
  check using `target.id[0].isupper()` or `target.id == target.id.upper()` instead.
- **Branch**: `feature/KAN-7-backend`
- **Commit convention**: `feat(vault-lint): add os-vault-lint for sandbox restriction validation`

---

## 10. Implementation Verification Checklist

- [ ] **Code quality**: `ruff check .openspec-cli/lib/vault_lint.py` passes; `mypy --strict` passes
- [ ] **No runtime deps**: `vault_lint.py` imports only standard library modules
- [ ] **CLI contract**: `os-vault-lint` exits `0` on clean contracts, `1` on violations
- [ ] **Pre-test gate**: `os-vault-test` runs lint first and aborts if lint fails
- [ ] **CI gate**: `Run Vault lint` step precedes `Run Vault Smart Contract tests` in `ci.yml`
- [ ] **Tests**: all cases in Step 5 are green; coverage ≥ 90% on `vault_lint.py`
- [ ] **No regressions**: existing `test_savings_product.py` suite still passes
- [ ] **Documentation**: `development_guide.md` updated with `os-vault-lint` usage
