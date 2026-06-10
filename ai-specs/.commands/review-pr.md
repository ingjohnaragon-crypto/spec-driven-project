# review-pr

PR Number: $ARGUMENTS

## Goal
Review a Pull Request against the active stack standards and generate a structured,
actionable code review. Save the result to `ai-specs/changes/` for traceability.

## Pre-flight checklist

1. Read `openspec/config.yaml` and resolve:
   - Active stack and its label
   - Stack agent path — load it
   - Stack standards path — load it
   - Tooling commands: `test_command`, `coverage_command`
2. Read `ai-specs/specs/base-standards.mdc`
3. Fetch PR metadata: title, author, branch, base, additions, deletions, changed files
4. Download the PR diff
5. If the branch contains a ticket ID (e.g. `KAN-XX`), load its plan from
   `ai-specs/changes/<ticket-id>_backend.md` if it exists

## Review areas

1. **Architecture & Design** — DDD layers respected, separation of concerns
2. **Code Quality** — naming, error handling, complexity, code smells
3. **Testing** — coverage >= 90%, AAA pattern, edge cases, error scenarios
4. **Security** — no hardcoded secrets, input validation, no sensitive data in logs
5. **Stack Compliance** — active stack conventions and patterns followed

## Process

1. Analyse the diff holistically — understand intent before finding faults
2. Classify each issue: CRITICAL (blocking), MAJOR (strongly recommended), MINOR (suggestion)
3. Note at least 2-3 positives
4. Issue a final verdict: APPROVE / REQUEST CHANGES / COMMENT ONLY
5. **Save the review** to `ai-specs/changes/<ticket-id>_review.md`
   — If no ticket ID found in the branch name, use `ai-specs/changes/pr-<PR_NUMBER>_review.md`

## Output format

Save a markdown file at `ai-specs/changes/<ticket-id>_review.md` with this structure:

---

### `# Code Review: PR #<NUMBER> — <TITLE>`

### `## Metadata`
- Author: `<author>`
- Branch: `<head>` → `<base>`
- Changes: `+<additions>` / `-<deletions>` across `<N>` files
- Stack: `<active-stack>`
- Date: `<YYYY-MM-DD>`

### `## Summary`
One paragraph overview of the implementation quality and what it achieves.

Overall verdict: **APPROVE** / **REQUEST CHANGES** / **COMMENT ONLY**

### `## Architecture & Design`
- DDD layered architecture respected?
- Separation of concerns correct?
- Any design decisions worth noting?

### `## Code Quality`
- Naming conventions followed?
- Error handling complete and consistent?
- Code smells or unnecessary complexity?

### `## Testing`
- Test coverage sufficient (>= 90%)?
- AAA (Arrange-Act-Assert) pattern used?
- Edge cases and error scenarios covered?

### `## Security`
- Hardcoded secrets or tokens present?
- Input validation in place?
- Sensitive data exposed in logs or responses?

### `## Specific Issues`
For each issue found:
```
- **File**: `path/to/file.ext` (line N) — **Severity**: CRITICAL/MAJOR/MINOR — **Fix**: concrete suggestion
```
If no issues: "No specific issues found."

### `## What's Done Well`
2-3 specific highlights of positive aspects.

### `## Final Verdict`

**APPROVE** / **REQUEST CHANGES** / **COMMENT ONLY**

---

## Final message format

> I've saved the review to `ai-specs/changes/<ticket-id>_review.md`.
> Run `os-review-apply <PR_NUMBER>` to publish it to GitHub.
