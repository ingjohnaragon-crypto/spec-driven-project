Please analyze and fix the Jira ticket: $ARGUMENTS.

Follow these steps:

1. The ticket's details (type, status, summary, assignee, description) are already provided above under `## Jira Ticket: $ARGUMENTS` — use that content as the source of truth. Do not attempt to fetch it again via Jira MCP or any other tool; none is available in this context.
2. You will act as a product expert with technical knowledge
3. Understand the problem described in the ticket
4. Decide whether or not the User Story is completely detailed according to product's best practices: Include a full description of the functionality, Vault hooks involved, `contracts_api` types, files to create or modify, acceptance criteria, unit/simulation tests, and non-functional requirements (sandbox restrictions, posting invariants, etc.)
5. If the user story lacks the technical and specific detail necessary to allow the developer to be fully autonomous when completing it, provide an improved story that is clearer, more specific, and more concise in line with product best practices described in step 4. Use the technical context you will find in
@documentation. Return it in markdown format.
6. Do NOT update Jira yourself — do not call any Jira tool or MCP. Writing back to Jira is a separate, human-confirmed step handled by `os-enrich-apply` after you finish. Your only job here is to produce the markdown described below and save it to disk.
7. Do NOT transition the ticket's status. Status transitions are handled separately via `os-transition`, not as part of this task.
8. Look at the `## Subtasks` context block provided (fetched from Jira via `parent = <ticket-id>`). For each subtask listed there, apply the same detail bar as step 4: if its description lacks the technical specifics needed for autonomous implementation, write an enhanced version following step 5's criteria, scoped to that subtask. If a subtask is already sufficiently detailed, or if no subtasks exist, skip it — do not invent subtasks that aren't in the context block.

## Language for section headers (mandatory)

**All section headers in the saved file MUST be written in the Active Language**
(see `## Active Language` in the prompt). Do **not** copy English headers when the
active language is Spanish (or vice versa).

Use exactly these headers when Active Language is Spanish (`es`):

| Sección | Encabezado obligatorio |
|---|---|
| Título | `# Ticket enriquecido: <TICKET-ID> — <Summary>` |
| Descripción original | `## Descripción original` |
| Descripción mejorada | `## Descripción mejorada` |
| Criterios de aceptación | `## Criterios de aceptación` |
| Hooks y tipos | `## Campos, hooks y tipos` |
| Archivos | `## Archivos a crear o modificar` |
| Pruebas | `## Casos de prueba unitarios` |
| No funcionales | `## Requisitos no funcionales` |
| Subtareas | `## Subtareas` |

Use exactly these headers when Active Language is English (`en`):

| Section | Required header |
|---|---|
| Title | `# Enriched Ticket: <TICKET-ID> — <Summary>` |
| Original | `## Original Description` |
| Enhanced | `## Enhanced Description` |
| AC | `## Acceptance Criteria` |
| Hooks | `## Fields, Hooks & Types` |
| Files | `## Files to Create or Modify` |
| Tests | `## Unit Test Cases` |
| NFR | `## Non-Functional Requirements` |
| Subtasks | `## Subtasks` |

## Output

Save the enriched content as a markdown file at `ai-specs/changes/enriquecimientos/$ARGUMENTS/$ARGUMENTS_enriched.md`
using this structure:

---

### `# Enriched Ticket: <TICKET-ID> — <Summary>`

### `## Original Description`
(copy of the original ticket description)

### `## Enhanced Description`
Full description of the functionality as refined. For Vault contracts include posting
behaviour, schedules, and sandbox constraints.

### `## Acceptance Criteria`
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] os-vault-test passes
- [ ] os-vault-test --coverage passes (>= 90%)

### `## Fields, Hooks & Types`
Vault hooks involved, `contracts_api` types, parameters, and posting/account shapes.

### `## Files to Create or Modify`
| File | Layer | Action |
|---|---|---|
| `contracts/<name>.py` | Contract | Create / Modify |
| `tests/test_<name>.py` | Tests | Create / Modify |

### `## Unit Test Cases`
- Happy path
- Validation / rejection
- Edge cases
- Simulation / balances where relevant

### `## Non-Functional Requirements`
Sandbox restrictions, performance, validation constraints.

### `## Subtasks`
Only include this section if the `## Subtasks` context block lists at least one
subtask. For each subtask that needed refinement:

#### Subtask: `<SUBTASK-KEY>` — `<Summary>`
Enhanced description, acceptance criteria, and files scoped to that subtask.

---

## Final message format

> Enriched content saved to `ai-specs/changes/enriquecimientos/<ticket-id>/<ticket-id>_enriched.md`.
> Run `os-enrich-apply <TICKET-ID>` to upload it to Jira.
