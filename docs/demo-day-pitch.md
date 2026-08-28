# OpenSpec — Material para el pitch de Demo Day

**Accelerathon GFT × Thought Machine** · Autor: John Aragón
Repo: `https://github.com/ingjohnaragon-crypto/spec-driven-project`

> Este documento es la fuente para armar la presentación. Tiene el guion, los
> números verificados, el script de demo en vivo, los mensajes clave y una
> descripción de los gráficos a diseñar. No es la presentación final —
> es la materia prima.

---

## 1. El pitch en una frase

**OpenSpec convierte el conocimiento de un experto en Vault en algo que el
agente de IA obedece — no que ignora.**

Alternativas de una línea según el ángulo:

- *"Un framework spec-driven que conecta Jira, el repo y la IA en un solo flujo
  para construir Smart Contracts de Thought Machine Vault."*
- *"Los tests con mocks te dicen que tu contrato está bien. OpenSpec te dice si
  Vault lo va a aceptar."*
- *"El linter, el simulador y los specs forman un bucle que aprende de cada
  sesión y no vuelve a cometer el mismo error."*

---

## 2. El problema (30–45 s en tarima)

Un agente de IA sabe escribir Python. **No sabe que Vault no ejecuta Python
estándar.**

El sandbox de Vault Smart Contracts:

- prohíbe toda la stdlib (`os`, `json`, `datetime`, `re`, …), `print`, `open`,
  `eval`, estado global mutable, `float`
- exige `Decimal` para todo el dinero, `ZoneInfo` (no `timezone.utc`)
- cambió medio API entre 3.x y 4.0: `Rejection` en vez de `raise`, `phase` en la
  clave y no en el valor, `update_permission` obligatorio en cada parámetro
  INSTANCE, y **cada hook debe declarar qué datos lee**

**Resultado sin OpenSpec:** el agente genera un contrato que pasa el linter de
Python y los tests unitarios… y Vault lo rechaza al cargarlo o al desplegarlo.
El desarrollador re-explica las mismas reglas en cada prompt. El conocimiento
vive en la cabeza de una persona y en hilos de Slack.

### El momento "ajá" para la tarima

> Escribimos 5 contratos con **189 tests en verde y 90 % de cobertura**.
> Los pasamos por el simulador contra el Vault real y **4 de 5 fallaron** —
> `InvalidSmartContractError`. Los tests con mocks no podían verlo.
> OpenSpec ahora lo bloquea antes de que llegues a Vault.

---

## 3. La solución (45–60 s)

OpenSpec guarda las reglas del stack como **specs estructurados en el repo** y
se los entrega al agente automáticamente en cada comando.

```
Ticket de Jira
      +
Specs de Vault  (reglas del sandbox, cambios de API 4.0, hallazgos de Core API)
      +
Agente activo   (Copilot / Claude Code / Cursor / Aider)
      ↓
  un comando
      ↓
Prompt con todo el contexto  →  IA genera plan / contrato / review
      ↓
os-vault-lint (9 reglas)  +  pytest ≥ 90 %  +  os-vault-simulate (Vault real)
```

Tres piezas que se refuerzan:

| Pieza | Qué hace | Por qué importa |
|---|---|---|
| **Specs** (`ai-specs/`) | Rol del agente, standards, y `vault-core-api-gotchas.md` con hallazgos de sesiones reales | El agente parte del conocimiento correcto, no de suposiciones |
| **`vault_lint.py`** | Análisis estático AST — 9 reglas del sandbox de Vault | Falla el build antes de tocar Vault |
| **`os-vault-simulate`** | Ejecuta los hooks contra un Vault en memoria (Core API real) | Atrapa lo que los mocks no pueden: requirements faltantes, errores de carga |

**El bucle (el diferenciador):** cada hallazgo de una sesión real —"el header
es `X-Auth-Token` no `Bearer`", "`DateShape` va como fecha pelada"— se escribe
en el spec, **y** se convierte en regla del linter, **y** entra al agente.
La siguiente persona no tropieza con lo mismo.

---

## 4. Qué está construido (el MVP)

Cifras **verificadas en el repo** (28-ago-2026):

| Métrica | Valor |
|---|---|
| Comandos CLI `os-*` | **23** |
| Smart Contracts (API 4.0) | **5** · ~1.900 líneas |
| Tests | **189** (135 de contratos + 54 del linter) · cobertura ≥ 90 % |
| Reglas de sandbox en `vault_lint.py` | **9** |
| Contratos que simulan limpio contra el sandbox real | **5 / 5** |
| Tickets llevados de HU → Done por el flujo | **6** (KAN-6, 7, 8, 10, 11, 12) |
| Duración del MVP | mar → ago 2026 · 149 commits |

### Los 5 contratos

| Contrato | Producto | Tests | Qué ejercita |
|---|---|---:|---|
| `savings_product.py` | Basic Savings Account | 23 | Devengo mensual de interés (`EndOfMonthSchedule`) |
| `current_account.py` | Current Account with Overdraft | 23 | Sobregiro configurable, rechazo de débitos |
| `fixed_term_deposit.py` | Fixed-Term Deposit | 34 | Devengo diario, vencimiento, cierre anticipado con penalidad, parámetros derivados |
| `personal_loan.py` | Personal Loan | 23 | Amortización, cuota mensual, penalidad por prepago, desembolso de principal |
| `cuenta_joven.py` | Cuenta Joven | 27 | Límite diario de retiro + tasa bonificada, dos schedules |

### Integraciones

- **Jira** (proyecto `KAN`): fetch de ticket, creación con HU generada por IA,
  transición de estado, enriquecimiento técnico que se sube al ticket.
- **GitHub**: rama feature automática desde `develop`, PR, code review por IA,
  loop de corrección automática si hay REQUEST CHANGES, merge.
- **Vault Core API**: simulate (streaming NDJSON), deploy de product version,
  creación de cliente y cuenta, consulta de balances y productos.

### Multi-agente

Copilot, Cursor, Windsurf (portapapeles) · Claude Code, Aider (CLI directo).
Cambias con `os-agent <nombre>`. El mismo flujo, cualquier asistente.

---

## 5. Script de demo en vivo (~4 min)

> Objetivo: mostrar el flujo completo HU → contrato → Vault. Tener la VPN activa
> (simulate la necesita) y `.env` cargado.

**[0:00] Contexto (hablado, sin pantalla)**
"Voy a construir un producto de Vault desde un ticket de Jira sin explicarle
nada al agente sobre Vault."

**[0:20] El ticket**
```bash
os-tickets "Por hacer"
os-enrich KAN-20            # la IA enriquece la HU con hooks, parámetros, riesgos
os-enrich-apply KAN-20     # se sube a Jira → mostrar el ticket actualizado
```
*Punto a decir:* el prompt lleva el agente de Vault, los standards y los
gotchas de Core API — el presentador no escribió nada de eso.

**[1:15] El plan y la implementación**
```bash
os-plan KAN-20             # plan técnico en ai-specs/changes/planes/KAN-20/
os-develop KAN-20          # crea feature/KAN-20 + implementa el contrato + tests
```

**[2:00] Las tres compuertas de calidad**
```bash
os-vault-test --coverage   # 9 reglas de linter + pytest ≥ 90 %
```
*Mostrar el checklist:* `✔ 9/9 Vault rules — CLEAN`. Señalar
`Hooks declare their data requirements` y `INSTANCE params declare update_permission`
— reglas que salieron de errores reales.

**[2:45] El simulador — el momento fuerte**
```bash
os-vault-simulate contracts/<producto>.py 2024-01-01T00:00:00Z 2024-04-01T00:00:00Z
```
Se ve el stream NDJSON del Vault real: `created account`, `created N scheduled
event jobs`, `processed scheduled event "..."` día a día. **HTTP 200, sin
excepción.**
*Punto a decir:* "esto se ejecutó contra la Core API de Thought Machine, no
contra un mock."

**[3:30] El PR**
```bash
os-commit KAN-20           # commit + push + PR a develop
os-review <PR> && os-review-apply <PR>   # code review por IA publicado en GitHub
```

**[3:50] Cierre**
`os-transition KAN-20 "Done"` — el ciclo se cerró solo.

### Plan B si falla la red / VPN

Tener grabada (asciinema o video) una corrida de `os-vault-simulate` de los 5
contratos. El output ya está documentado en el repo
(`ai-specs/specs/stacks/vault-core-api-gotchas.md` §3.1).

---

## 6. Prueba de que funciona: las 5 simulaciones

Corridas reales contra `core-api.tm.blx-demo.com`, 28-ago-2026:

| Contrato | HTTP | Qué se observó |
|---|---|---|
| `savings_product` | 200 | `INTEREST_ACCRUAL` fin de mes ×3, sin excepción |
| `current_account` | 200 | Cuenta + parámetros; sin schedules |
| `cuenta_joven` | 200 | `DAILY_WITHDRAWAL_RESET` diario + `MONTHLY_INTEREST` el 28 — 65 eventos |
| `personal_loan` | 200 | Desembolso del principal (posting real) + `MONTHLY_REPAYMENT` mensual |
| `fixed_term_deposit` | 200 | `DAILY_ACCRUAL` cada noche + `MATURITY_EVENT` exacto en la fecha |

Antes de OpenSpec: 4 de estos 5 lanzaban `InvalidSmartContractError: Timeseries
'<param>' not found`. Los 189 tests con mocks pasaban igual.

---

## 7. El diferenciador (para preguntas de jurado)

**No es tooling específico de Vault. Es una metodología.**

- El registro de stacks (`openspec/config.yaml`) está diseñado para añadir otro
  stack; hoy sólo trae Vault porque es el foco del Accelerathon.
- El valor no está en los 5 contratos — está en **el bucle**: linter + simulador
  + specs que se retroalimentan. Cada equipo que use OpenSpec hereda los
  hallazgos de los anteriores.
- Los tests con mocks son necesarios pero mienten sobre la integración.
  OpenSpec añade la capa que los mocks no pueden dar: ejecución real contra la
  Core API en cada iteración.

### Manejo de objeciones

| Objeción | Respuesta |
|---|---|
| "Esto lo hace cualquier linter" | Un linter de Python valida sintaxis. `vault_lint` valida el subconjunto restringido de Vault + reglas de deploy de Core API que ni siquiera están en la doc oficial. |
| "¿Por qué no solo más tests?" | Los tests mockean `vault`. Un requirement de datos faltante pasa el 100 % de los tests y falla en Vault. Lo demostramos con 4 de 5 contratos. |
| "Depende de que la IA no alucine" | Por eso hay tres compuertas determinísticas después del agente: linter, cobertura, simulador. Si el agente se equivoca, no llega al PR. |
| "¿Escala a un banco real?" | El flujo es idéntico: ticket → specs → agente → compuertas → PR. Lo que escala es el repositorio de specs, que crece con cada equipo. |

---

## 8. Qué sigue (Fase 2)

- **Dashboard de métricas de adopción** — cuántos tickets pasan por el flujo,
  tasa de PRs que pasan las compuertas a la primera, tiempo HU → Done.
- **Repositorio de specs base GFT reutilizables** — que un equipo nuevo arranque
  con las convenciones GFT ya cargadas.
- **E2E completo contra sandbox** — deploy → cuenta → balances en verde de punta
  a punta (simulate ya está; falta el resto del ciclo con la excepción de red).
- Más stacks en el registro (el andamiaje ya lo soporta).

---

## 9. Frases para diapositivas (soundbites)

- "Los mocks te dicen que el código está bien. OpenSpec te dice si Vault lo acepta."
- "5 contratos. 189 tests verdes. 4 rechazados por Vault. El simulador lo encontró en 3 segundos."
- "Cada error que cometemos una vez se convierte en una regla que nadie más comete."
- "El agente no sabía nada de Vault. El repo sí."
- "De Historia de Usuario a Smart Contract desplegable en un flujo, sin re-explicar el contexto."
- "9 reglas de sandbox. Ninguna está en un tutorial — todas salieron de romper cosas contra el Vault real."

---

## 10. Gráficos a diseñar (para el amigo en web)

1. **Diagrama del flujo** (el bloque de la §3): Jira + Specs + Agente → un
   comando → Prompt → IA → 3 compuertas → PR. Horizontal, izquierda a derecha.
2. **El bucle de retroalimentación**: un ciclo — *sesión real* → *hallazgo* →
   (*spec* + *regla de linter* + *agente*) → *siguiente sesión*. Circular.
3. **Antes / Después**: dos columnas.
   - *Antes*: "189 tests ✓ · 90 % cobertura ✓ · Vault: ✗ ✗ ✗ ✗ ✓"
   - *Después*: "linter 9/9 ✓ · simulate 5/5 ✓ · Vault ✓"
4. **Slide de números** (la tabla de la §4): 23 comandos · 5 contratos ·
   189 tests · 9 reglas · 5/5 simulados · 6 tickets HU→Done.
5. **Screenshot real**: el output de `os-vault-simulate` con las líneas
   `processed scheduled event "..."` y `✔ 9/9 Vault rules — CLEAN`.
   (pedirlo al presentador, es lo más convincente)
6. **Arquitectura del repo** (opcional, para técnicos):
   `openspec/config.yaml` · `ai-specs/` (agente + standards + gotchas) ·
   `.openspec-cli/` (23 comandos + `vault_lint.py`) · `contracts/` + `tests/` ·
   `contracts_sdk/` (SDK local de Thought Machine).

---

## 11. Datos de contacto / recursos

- Repo: `https://github.com/ingjohnaragon-crypto/spec-driven-project`
- Contexto técnico completo: `CLAUDE.md` y `README.md` del repo
- Hallazgos de Core API: `ai-specs/specs/stacks/vault-core-api-gotchas.md`
- Reglas del agente de Vault: `ai-specs/.agents/stacks/vault-smart-contracts.md`
- Jira: proyecto `KAN` en `ingjohnaragon.atlassian.net`
