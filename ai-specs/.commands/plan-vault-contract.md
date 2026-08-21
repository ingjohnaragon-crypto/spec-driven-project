# plan-vault-contract

Ticket ID: $ARGUMENTS

## Goal

Generate a step-by-step Vault Smart Contract implementation plan for a Jira ticket,
ready for **autonomous, uninterrupted** implementation with `os-develop`
(no mid-flight questions to the human).

## Pre-flight checklist

1. Read `openspec/config.yaml` and resolve stack agent, standards, and tooling commands
2. Read `ai-specs/specs/base-standards.mdc`
3. Read existing plans under `ai-specs/changes/planes/` for related contracts
4. Read at least one golden contract as pattern reference:
   - Prefer `contracts/fixed_term_deposit.py` + `tests/test_fixed_term_deposit.py`
   - Also check `contracts/savings_product.py` / `contracts/current_account.py` if relevant
5. Use the Jira ticket content provided in the prompt (do not re-fetch)

## Process

1. Adopt the role in `ai-specs/.agents/stacks/vault-smart-contracts.md`
2. Identify hooks, parameters, postings, schedules, and test cases required
3. **Lock every product/design decision** in the plan (see section 2.1). Never leave
   "decidir", "confirmar", "elegir entre (a)/(b)", or "TODO de diseño".
4. Propose the plan using the output format below
5. Save at `ai-specs/changes/planes/<ticket-id>/<ticket-id>_backend.md`
6. **Plan only — do not write contract or test code**

## Hard rules for this plan (mandatory)

- The plan must be executable by Copilot/Cursor/Claude **without asking the user**.
- If the ticket is ambiguous, **choose** the option that best matches:
  1. Vault sandbox + API 4.0 conventions in the golden contract (`fixed_term_deposit`)
  2. Predictable customer UX
  3. Testability
- Document the choice under `## 2.1 Decisiones bloqueadas` with one-line rationale.
- Require implementation quality ≥ golden contract: real `parameters = [...]`,
  correct hook names (`pre_posting_hook` / `post_posting_hook`, never `*_code`),
  no `try/except` around `contracts_api` imports, no skeleton/TODO stubs left in
  the final delivery.
- Tests must follow the golden style: `MagicMock` vault, typed hook args,
  class-grouped cases, coverage of happy + rejection + edge + multi-denomination.
  Target **≥ 20 focused tests** for a full product (or justify fewer if trivial).

## Language

Write the entire plan in the Active Language from the prompt.
When Active Language is Spanish, translate section headers (e.g. `## 1. Resumen`).
Keep Vault hook names and `contracts_api` types in English.

## Output format

Save `ai-specs/changes/planes/<ticket-id>/<ticket-id>_backend.md`:

---

### `# Vault Implementation Plan: <TICKET-ID> <Feature Name>`

### `## Estimación de puntos de historia`
```markdown
<!-- STORY_POINTS:<N> -->
**N** — one-line justification (Fibonacci 1|2|3|5|8|13).
<!-- /STORY_POINTS -->
```

### `## 1. Resumen`

Product behaviour, hooks involved, sandbox constraints. State active stack.

### `## 2. Contexto de arquitectura`

- Active stack: `vault-smart-contracts`
- Golden reference: `contracts/fixed_term_deposit.py` (+ its tests)
- Files:
  - `contracts/<product_name>.py` — Smart Contract (API 4.0)
  - `tests/test_<product_name>.py` — unit tests with `contracts_api` SDK mocks
  - Tooling: `os-vault-lint`, `os-vault-test`, optional `os-vault-simulate`

### `## 2.1 Decisiones bloqueadas` (mandatory — no open questions)

Table or bullet list. Every ambiguous product rule must appear here as a
**final** choice. Examples of topics to lock when relevant:

- Interest rate convention (fraction `0.05` vs percent `5`)
- Schedule timing (day-of-month / end-of-month)
- Prepayment / early closure policy after event
- Penalty shape (percent vs fixed) and precedence
- Internal addresses / tside
- Default denomination and `supported_denominations`

Forbidden in the plan: "pendiente de confirmar", "elegir entre (a)/(b)",
"según prefiera el negocio", "definir en el PR".

### `## 3. Pasos de implementación`

#### Step 0: Feature branch

- Branch: `feature/<ticket-id>-backend` (created by `os-develop` from `develop`)

#### Step 1: Contract scaffold

- File: `contracts/<product_name>.py`
- Mirror golden metadata: `api = "4.0.0"`, `version`, `display_name`, `summary`,
  `description`, `tside`, `supported_denominations = ["GBP", "USD", "EUR", "COP"]`
- Direct imports from `contracts_api` (no try/except fallback wrappers)
- `parameters = [ Parameter(...), ... ]` fully populated from section 2.1
- Constants: `DEFAULT_ADDRESS`, `DEFAULT_ASSET`, internal addresses

#### Step 2: Pure helper functions

- Balance helpers using `BalanceCoordinate` + `Phase.COMMITTED` on the **key**
- Money helpers using `Decimal` only — never `float`
- Pure schedule / penalty helpers with explicit signatures and examples in the plan

#### Step 3: Hook implementation

For each hook: signature, inputs, outputs, business rules (locked):

- `activation_hook`
- `pre_posting_hook` (never `pre_posting_code`)
- `post_posting_hook` (never `post_posting_code`)
- `scheduled_event_hook`
- `derived_parameter_hook` — only if needed (`Parameter(derived=True)`)

#### Step 4: Unit tests (TDD order)

- File: `tests/test_<product_name>.py`
- Pattern: copy structure from `tests/test_fixed_term_deposit.py`
  (fixtures, `MagicMock` vault, grouped test classes)
- Named test cases listed explicitly (happy, rejection, edge, denomination)

#### Step 5: Sandbox lint and test gate

```bash
{{lint_command}}
{{test_command}}
{{coverage_command}}
```

#### Step 6: Documentation

- Update standards only if a reusable new pattern appears

### `## 4. Orden de implementación`

Numbered list from Step 0 through documentation.

### `## 5. Checklist de pruebas`

- [ ] `{{lint_command}}` — zero violations
- [ ] `{{test_command}}` — all tests green
- [ ] `{{coverage_command}}` — coverage >= 90%
- [ ] Rejection paths tested with correct `RejectionReason`
- [ ] Existing contract tests not broken
- [ ] No skeleton/TODO left in contract or tests

### `## 6. Referencia de tooling`

| Purpose | Command |
| --- | --- |
| Build (SDK) | `{{build_command}}` |
| Lint | `{{lint_command}}` |
| Test | `{{test_command}}` |
| Coverage | `{{coverage_command}}` |

### `## 7. Catálogo de rechazos`

List `RejectionReason` + trigger conditions.

### `## 8. Dependencias`

- `contracts_api` SDK from `contracts_sdk/contracts_sdk/`
- No stdlib imports in contract code

### `## 9. Notas`

Posting invariants, schedule timing, denomination policy (one currency per account).
**No open decisions here** — only clarifications of already-locked rules.

### `## 10. Checklist de verificación`

- [ ] Only `contracts_api` and `decimal` imports in contract files
- [ ] No `raise` for business rejections — return `PrePostingHookResult(rejection=...)`
- [ ] Phase read from `BalanceCoordinate`, not `Balance`
- [ ] `CustomInstruction` uses `instruction_details`, not `client_transaction_id`
- [ ] Correct hook names (`*_hook`)
- [ ] Coverage >= 90%; all tests pass

---

## Final message format

> I've created a plan at `ai-specs/changes/planes/<ticket-id>/<ticket-id>_backend.md`.
> Please review it before running `os-develop <ticket-id>`.
> Confirm section 2.1 has **zero** open decisions before develop.
