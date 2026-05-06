# develop-backend

Analyze and implement the Jira ticket: $ARGUMENTS

## Pre-flight checklist (run before writing any code)

1. Read `openspec/config.yaml` and resolve:
   - Active stack (`stack:` key)
   - Stack agent path (`stacks.<stack>.agent`)
   - Stack standards path (`stacks.<stack>.standards`)
   - Tooling commands: `build_command`, `test_command`, `run_command`, `coverage_command`
2. Load and internalize the resolved stack agent and standards files
3. Read `ai-specs/specs/base-standards.mdc`
4. Read `ai-specs/specs/documentation-standards.mdc`
5. If a plan already exists at `ai-specs/changes/<ticket-id>_backend.md`, read it before starting

## Implementation steps

### Step 0 — Create feature branch
```bash
git checkout main && git pull origin main
git checkout -b feature/<ticket-id>-backend
git branch  # verify
```

### Step 1 — Understand the ticket
- Use Jira MCP to fetch ticket details if available; otherwise read from the plan file
- Identify all affected layers: Domain, Application, Presentation, Infrastructure

### Step 2 — Write tests first (TDD)
- Write failing unit tests for the business logic **before** any implementation
- Write failing controller slice tests for the new endpoint **before** the controller exists
- Run tests and confirm they fail for the right reason:
  ```bash
  {{test_command}}
  ```

### Step 3 — Implement to make tests pass
- Follow the implementation order defined in the plan file
- Use only the tooling commands from `openspec/config.yaml` for the active stack
- Never hardcode build tool commands (e.g. `./gradlew`, `npm`, `pytest`) — always use the resolved variable

### Step 4 — Verify build and coverage
```bash
{{build_command}}
{{coverage_command}}
```
Coverage must be >= 90%. If it is not, add tests before continuing.

### Step 5 — Manual endpoint testing
Test all HTTP status codes for every new or modified endpoint:
- Happy path (200 / 201)
- Validation error (400)
- Not found (404)
- Conflict (409) — if applicable
- Server error (500) — if applicable

Document the curl commands used in a comment block in the plan file.

### Step 6 — Update technical documentation
Run the update-docs command:
```
/update-docs
```
Minimum files to review and update:
- `ai-specs/specs/data-model.md` — if schema changed
- `ai-specs/specs/api-spec.yml` — if endpoints changed
- `ai-specs/specs/stacks/<stack>-standards.mdc` — if libraries or patterns changed

### Step 7 — Commit and open PR
Stage only the files affected by this ticket:
```bash
git add <affected files only>
```
Use a descriptive commit message (conventional commits format, English):
```
feat(<scope>): <short imperative description>

- <what changed and why>
- Resolves <ticket-id>
```
Push and open a PR using GitHub CLI:
```bash
git push -u origin feature/<ticket-id>-backend
gh pr create --title "[<ticket-id>] <summary>" --body "<description>"
```

## Rules
- **Never skip Step 0** (branch) or Step 6 (docs)
- **TDD is mandatory** — tests before implementation, always
- **Use resolved tooling commands** from `openspec/config.yaml` — never hardcode
- All code, comments, and commit messages must be in English
- Do not commit unrelated files; stage only what belongs to this ticket
