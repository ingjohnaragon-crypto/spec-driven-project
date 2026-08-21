Please enrich the Jira ticket: $ARGUMENTS.

Follow these steps:

1. The ticket details are already provided above under `## Jira Ticket: $ARGUMENTS` — use that as source of truth. Do not fetch Jira again.
2. Act as a product expert with technical knowledge of Vault Smart Contracts (API 4.0).
3. Improve the story so a developer can implement it without back-and-forth.
4. Include only what is needed: clear behaviour, hooks, parameters/types, files, acceptance criteria, key tests, sandbox constraints, **and a Fibonacci story-points estimate**.
5. If subtasks are listed under `## Subtasks`, enrich each one that lacks detail (including its own story points). Do not invent subtasks.
6. Do NOT update Jira and do NOT transition status (`os-enrich-apply` / `os-transition` are separate steps).

## Language for section headers (mandatory)

**All section headers MUST use the Active Language.**

Spanish (`es`):

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
| Puntos de historia | `## Puntos de historia` |
| Subtareas | `## Subtareas` |

English (`en`):

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
| Story points | `## Story Points` |
| Subtasks | `## Subtasks` |

## Output document structure

Return ONE markdown document with this shape (headers already localized above).
**Story points are mandatory** — wrap the estimate in `<!-- STORY_POINTS:<N> -->` …
`<!-- /STORY_POINTS -->` so `os-enrich-apply` can write the Jira Story Points field.

```markdown
# Ticket enriquecido: <TICKET-ID> — <Summary>

## Descripción original
<!-- jira-skip -->
(breve copia limpia de la descripción original — archivo local only)
<!-- /jira-skip -->

## Descripción mejorada
2-4 párrafos cortos: comportamiento del producto, cuándo corre cada hook,
y qué cambia en saldos / postings. Sin pegar el agent stack completo.

## Criterios de aceptación
- [ ] Criterio de negocio observable
- [ ] ...
- [ ] os-vault-test pasa
- [ ] os-vault-test --coverage pasa (>= 90%)

## Campos, hooks y tipos
- Hooks: ...
- Parámetros: ...
- Tipos contracts_api: ...

## Archivos a crear o modificar
| Archivo | Capa | Acción |
|---|---|---|
| `contracts/<name>.py` | Contract | Create |
| `tests/test_<name>.py` | Tests | Create |

## Casos de prueba unitarios
- Happy path
- Validación / rechazo
- Edge cases (prepago, denominación, etc.)

## Requisitos no funcionales
Sandbox Vault, Decimal, ZoneInfo, sin I/O.

## Puntos de historia
<!-- STORY_POINTS:<N> -->
Estimate using Fibonacci (1, 2, 3, 5, 8, 13). One short justification line.
Example: **5** — posting + schedule + tests; no new vault accounts.
<!-- /STORY_POINTS -->

## Subtareas
(solo si existen en el contexto)

<!-- SUBTASK:<SUBTASK-KEY> -->
### Subtarea: <SUBTASK-KEY> — <Summary>

#### Descripción original
<!-- jira-skip -->
(copy)
<!-- /jira-skip -->

#### Descripción mejorada
Refined, technically detailed description.

#### Criterios de aceptación
- [ ] Criterion 1

#### Puntos de historia
<!-- STORY_POINTS:<N> -->
Fibonacci estimate for this subtask only.
<!-- /STORY_POINTS -->
<!-- /SUBTASK:<SUBTASK-KEY> -->
```

## Style for Copilot / clipboard agents

- Short paragraphs (1-3 sentences).
- One bullet per idea.
- No giant code blocks; at most one small example if essential.
- No tables of unrelated stacks (Java/Spring, etc.).
- No repeating the prompt or cheatsheet verbatim.
- Readable in Jira after `os-enrich-apply`.
- Always include `<!-- STORY_POINTS:<N> -->` on the parent ticket and on each refined subtask.
