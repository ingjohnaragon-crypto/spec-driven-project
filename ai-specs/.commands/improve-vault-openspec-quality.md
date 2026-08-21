# improve-vault-openspec-quality

## Goal

You are closing out the Vault Smart Contracts + OpenSpec CLI hardening after ticket
**KAN-11 (personal_loan)**. Copilot previously produced weak develop/review output.
Your job is to **audit the repo and apply concrete quality fixes** so the next
`os-plan` → `os-develop` → `os-vault-test` → `os-commit` → `os-review` cycle works
reliably with Copilot (clipboard agent) and Claude-quality bar.

## Autonomy rules (mandatory)

- **Do not ask the human questions.** Do not reopen product decisions.
- Treat plan decisions in `ai-specs/changes/planes/KAN-11/KAN-11_backend.md` §2.1 as final.
- Golden reference is always:
  - `contracts/fixed_term_deposit.py`
  - `tests/test_fixed_term_deposit.py`
- Prefer parity with FTD + Vault API 4.0 over inventing new patterns.
- Deliver **file changes + a short report**. Last message = summary of what you changed
  and how to verify — never a question list.

## Context — failures observed with Copilot (must not recur)

### Develop failures
1. Skeleton contracts with wrong hooks (`pre_posting_code` instead of `pre_posting_hook`)
2. `try/except` fallbacks around `contracts_api` imports
3. Empty/incomplete `parameters`, weak helpers, no FTD-level tests
4. Mid-flight questions about product decisions already answerable from the plan
5. Lower quality than Claude’s FTD implementation

### Review failures
1. Review described **obsolete skeleton** while current code was already API 4.0
2. Re-opened locked decisions (keep-term vs shorten-term; percent vs fixed penalty)
3. No `## Final Verdict` with `**APPROVE**` / `**REQUEST CHANGES**` / `**COMMENT ONLY**`
4. Did not write `.openspec-cli/.review-output.md` (clipboard capture stayed empty)
5. Soft “notes for reviewers” instead of structured Vault review checklist

### Commit / PR failures
1. Generic PR Summary (“Implements KAN-11…”) without plan content
2. Skipped `ai-specs/changes/planes/` and `enriquecimientos/` (docs not versioned)
3. Mojibake on Windows (`pr├®stamo`) when passing Spanish body via shell `--body`

### Tooling / CI failures
1. Windows PATH: `WindowsApps\bash` WSL stub broke `os-vault-*`
2. `os-vault-test` missing `os_load_config` → `OS_PYTHON` unbound
3. `vault_lint` silent “No violations” / then ANSI garbage / then color helpers uncovered
4. CI hard-coded product tests; new `personal_loan.py` at 0% collapsed `--cov=contracts` to ~58%

### Fixes already in the branch (do not regress)
- `ai-specs/.commands/plan-vault-contract.md` — locked decisions §2.1
- `ai-specs/.commands/develop-vault-contract.md` — no questions; FTD parity
- `ai-specs/.commands/review-vault-pr.md` — autonomy + Final Verdict
- `.openspec-cli/commands/os-commit` + `lib/build_pr_body.py` + `lib/commit_docs.sh`
  — stage ticket docs; UTF-8 `--body-file`
- `.openspec-cli/commands/os-review` + `lib/agent.sh` — verdict validation
- `.openspec-cli/lib/vault_lint.py` — 7-rule checklist
- `.openspec-cli/commands/os-vault-lint` / `os-vault-test` — Python discovery; scoped cov
- `.github/workflows/ci.yml` + `lib/check_contract_tests.py` — pairing + discover all tests
- `contracts/personal_loan.py` + `tests/test_personal_loan.py` — FTD-style rewrite

## Your audit & improve task

Work on branch `feature/KAN-11-backend` (or current feature branch). Read the files
above, then implement the improvements below **in priority order**. Skip anything
already done; do not rewrite personal_loan unless you find a real defect vs the plan.

### P0 — Copilot prompt/templates (prevent bad develop/review)
1. Audit these templates for remaining “ask the user / confirm decision” language:
   - `ai-specs/.commands/plan-vault-contract.md`
   - `ai-specs/.commands/develop-vault-contract.md`
   - `ai-specs/.commands/review-vault-pr.md`
   - `ai-specs/.commands/review-pr.md`
   - `ai-specs/.commands/enrich-us.md`
   - `.openspec-cli/commands/os-develop`
   - `.openspec-cli/commands/os-review`
   - `.openspec-cli/lib/agent.sh`
2. Ensure each Copilot-facing prompt contains an **Autonomy rules** block and an
   explicit **forbidden outputs** list:
   - no questions
   - no `*_code` hooks
   - no SDK import fallbacks
   - no reopening §2.1
   - review must end with `## Final Verdict` + one of the three verdicts
   - develop must write complete contract+tests files
3. Add a short **Copilot anti-patterns** subsection to
   `ai-specs/.agents/stacks/vault-smart-contracts.md` (or standards) listing the
   failures above as “never do this”.

### P1 — CLI reliability (Windows + clipboard)
1. Confirm `os-commit` always uses `--body-file` UTF-8 (never `--body "$PR_BODY"`).
2. Confirm `os-review` capture instructions mention `# Code Review:` + Final Verdict
   (not enrich headings).
3. Confirm `os-vault-test` calls `os_load_config` and maps
   `contracts/foo.py` → `tests/test_foo.py` with scoped `--cov=contracts.foo`.
4. If any command still assumes WSL bash / unbound `OS_PYTHON`, harden it.
5. Ensure `sh .openspec-cli/install.sh` installs new libs:
   `build_pr_body.py`, `commit_docs.sh`, `check_contract_tests.py`, `vault_lint.py`.

### P2 — CI / quality gates
1. Keep `check_contract_tests.py` + discover-all product tests (no hardcoded list).
2. Add a brief note in `ai-specs/specs/development_guide.md` (or vault standards):
   `--cov=contracts` requires every `contracts/<name>.py` to have
   `tests/test_<name>.py` executed in CI.
3. Optionally add a CI step that fails if any contract still contains
   `pre_posting_code`, `try:`+`contracts_api` fallback, or `client_transaction_id=`
   (can reuse / extend `vault_lint` rules if missing).

### P3 — Documentation closeout for KAN-11
1. Ensure plan + enrichment remain under:
   - `ai-specs/changes/planes/KAN-11/`
   - `ai-specs/changes/enriquecimientos/KAN-11/`
2. Update docs only where needed via `ai-specs/specs/documentation-standards.mdc`
   (patterns learned: locked decisions, FTD parity, CI pairing, review verdict).
3. Do **not** invent new product behaviour for personal_loan.

### P4 — Verification (run locally, report results)
```bash
python .openspec-cli/lib/vault_lint.py contracts/
python .openspec-cli/lib/check_contract_tests.py
pytest tests/test_vault_lint.py -v --cov=vault_lint --cov-fail-under=90
pytest tests/ --ignore=tests/test_vault_lint.py --ignore=tests/test_example.py -v --cov=contracts --cov-fail-under=90
```
If a command fails, fix it — do not ask.

## Output format (write this file)

Save a markdown report to:

`.openspec-cli/.quality-improve-report.md`

Structure:

```markdown
# Quality improve report — Vault OpenSpec (post KAN-11)

## Summary
One paragraph: what was weak with Copilot and what you fixed.

## Findings
| Area | Severity | Finding | Fix applied / skipped |
|------|----------|---------|------------------------|

## Files changed
- path — why

## Verification
Paste command results (pass/fail).

## Remaining risks
Only real residual risks (max 5 bullets). No open product questions.

## Ready for story close
YES/NO + one sentence.
```

## Final message format

> Saved report to `.openspec-cli/.quality-improve-report.md`.
> Applied the listed file changes. Run the verification commands above if you want
> to re-check locally, then `os-commit` / push if not already on the PR branch.
