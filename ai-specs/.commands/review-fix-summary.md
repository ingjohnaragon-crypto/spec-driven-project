# review-fix-summary

PR Number: $ARGUMENTS

## Goal
After addressing all issues from a code review, generate a structured fix report
that summarises what was resolved and confirms the PR is ready for re-review.
Save the result to `ai-specs/changes/` so the fix cycle is fully traceable.

## Pre-flight checklist

1. Read the original review at `ai-specs/changes/<ticket-id>_review.md`
   — Fall back to `.openspec-cli/.review-output.md` if the archive is not found
2. Read `openspec/config.yaml` — active stack, tooling commands
3. Verify current test status: `{{test_command}}`
4. Verify coverage: `{{coverage_command}}`

## Process

1. Go through each CRITICAL and MAJOR issue from the original review
2. For each issue, confirm the fix is in place (read the relevant code)
3. Note MINOR issues that were also addressed
4. Note any issues intentionally deferred, with justification
5. Record test and coverage results
6. Emit a final verdict: READY FOR RE-REVIEW / NEEDS FURTHER WORK
7. **Save the report** to `ai-specs/changes/<ticket-id>_fix.md`

## Output format

Save a markdown file at `ai-specs/changes/<ticket-id>_fix.md` with this structure:

---

### `# Review Fix Report: PR #<NUMBER> — <TITLE>`

### `## Original Verdict`
The verdict from the previous review (REQUEST CHANGES / COMMENT ONLY).
Review file: `ai-specs/changes/<ticket-id>_review.md`

### `## Issues Addressed`
For each fixed issue:
```
| Severity | File | Original issue | Fix applied |
|---|---|---|---|
| CRITICAL | path/to/file.ext (line N) | Description | What was changed |
```

### `## Issues Deferred`
(Omit section if all issues were fixed)
```
| Severity | Issue | Reason deferred | Planned resolution |
|---|---|---|---|
```

### `## Verification`
- Tests passing: Yes/No — `{{test_command}}`
- Coverage: N% — `{{coverage_command}}`
- Linting clean: Yes/No — `{{lint_command}}`

### `## Verdict After Fixes`
**READY FOR RE-REVIEW** / **NEEDS FURTHER WORK**

Brief explanation of confidence level.

---

## Final message format

> Fix report saved to `ai-specs/changes/<ticket-id>_fix.md`.
> Run `os-review <PR_NUMBER>` to generate a fresh review, then `os-review-apply <PR_NUMBER>`.
