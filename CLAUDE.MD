# OpenSpec — Contexto del proyecto para Claude Code

Este archivo es leído automáticamente por Claude Code al abrir este repositorio.
Contiene todo el contexto necesario para continuar el desarrollo sin re-explicar nada.

---

## Qué es este proyecto

**OpenSpec** es un framework spec-driven que conecta Jira, el repositorio y el agente
de IA en un flujo de desarrollo unificado. Desarrollado por John Aragón como MVP para
el **Accelerathon GFT × Thought Machine**.

El problema que resuelve: los agentes de IA no conocen los patrones del proyecto
(arquitectura, stack, convenciones, Vault Smart Contracts). OpenSpec almacena ese
contexto como specs estructurados en el repositorio y lo entrega automáticamente
al agente en cada comando.

---

## Stack y estructura del repo

```
open-spec/
├── openspec/config.yaml              # Stack activo + agente activo
├── ai-specs/
│   ├── .agents/stacks/
│   │   └── vault-smart-contracts.md  ← único agente (API 4.0 verificada)
│   ├── specs/stacks/
│   │   ├── vault-smart-contracts-standards.mdc
│   │   └── vault-core-api-gotchas.md   # hallazgos Core API (deploy/account/balances)
│   ├── .commands/                    # Plantillas de prompt (plan/develop/review/enrich vault)
│   └── changes/planes|enriquecimientos/KAN-XX/   # planes y enriquecimientos por ticket
├── contracts/                        # 5 Smart Contracts (savings, current_account,
│   │                                #   fixed_term_deposit, personal_loan, cuenta_joven)
├── tests/                            # 135 tests de contratos + 54 de vault_lint ✅
├── contracts_sdk/                    # SDK Thought Machine (local)
│   └── contracts_sdk/                # py -m pip install . desde aquí
├── .openspec-cli/
│   ├── install.sh                    # sh .openspec-cli/install.sh
│   ├── lib/
│   │   ├── config.sh
│   │   ├── agent.sh
│   │   ├── jira.sh                   # incluye os_jira_create_ticket, os_jira_list_tickets
│   │   ├── parse_config.py
│   │   ├── parse_agent.py
│   │   ├── parse_stack.py
│   │   ├── vault_simulate.py         # POST /v1/contracts:simulate (streaming NDJSON)
│   │   └── vault_deploy_payload.py
│   └── commands/                     # 23 comandos os-*
└── .github/workflows/ci.yml          # CI con contracts_api SDK
```

---

## Comandos CLI

### Configuración
```bash
os-stack --list                        # muestra el stack (solo vault-smart-contracts)
os-stack vault-smart-contracts         # activar stack
os-agent --list                        # listar agentes
os-agent claude-code                   # activar agente (o copilot)
os-language --list                     # listar idiomas de salida
os-language es                         # generar planes, Jira, commits y PRs en español
```

### Gestión de Jira
```bash
os-tickets                             # ver todos los tickets del proyecto
os-tickets "Por hacer"                 # filtrar por estado
os-create-ticket --hu                  # crear ticket con HU generada por IA
os-create-ticket "titulo" Task         # crear ticket rápido
os-transition KAN-XX --list            # ver transiciones disponibles
os-transition KAN-XX "En curso"        # mover ticket de estado
```

### Workflow principal
```bash
os-enrich KAN-XX                       # enriquecer ticket con contexto técnico
os-enrich-apply KAN-XX                 # subir enriquecimiento a Jira
os-plan KAN-XX                         # generar plan → ai-specs/changes/planes/KAN-XX/KAN-XX_backend.md
os-develop KAN-XX                      # crear rama feature/KAN-XX-backend + implementar
os-commit KAN-XX                       # commit + push + PR → develop (NUNCA a main/develop directo)
os-review PR_NUMBER                    # generar code review del PR
os-review-apply PR_NUMBER              # publicar review en GitHub
os-review-fix PR_NUMBER                # fix automático si REQUEST CHANGES + re-review
```

### Vault Smart Contracts
```bash
os-vault-test                          # correr todos los tests con SDK local
os-vault-test --coverage               # con cobertura ≥ 90%
os-vault-test tests/test_savings_product.py    # archivo específico
os-vault-simulate contracts/<product>.py <start> <end> '<params>'
os-vault-deploy contracts/<product>.py <product_id> "<display name>"
os-vault-products                      # sin banderas = --mine (sandbox compartido entre equipos)
os-vault-products --mine --all         # incluye versiones no vigentes, solo mis productos
os-vault-products --all-unsafe         # TODO el sandbox compartido -- pide confirmación con el conteo
os-vault-products --id savings_product # consulta un producto puntual por id (repetible: --id a --id b)
os-vault-products --backfill           # registra en el log --mine los productos existentes (allowlist / prefijo openspec_)
os-vault-products --prune              # limpia del log --mine cualquier producto que no sea mío (hace backup .bak)
os-vault-account <product_version_id> <customer_id>
os-vault-balances <account_id>
```

---

## Flujo completo para un ticket (HU → Done)

```bash
os-stack vault-smart-contracts
os-agent claude-code              # o copilot

os-create-ticket --hu             # crea ticket con HU en Jira

os-enrich KAN-XX                  # prompt al portapapeles → pega en agente
                                  # guarda output en .openspec-cli/.enriched-content.md
os-enrich-apply KAN-XX            # sube a Jira

os-plan KAN-XX                    # prompt al portapapeles → pega en agente
                                  # guarda output en ai-specs/changes/planes/KAN-XX/KAN-XX_backend.md

os-develop KAN-XX                 # crea branch desde develop + implementa

os-vault-test --coverage          # debe pasar ≥ 90%

os-commit KAN-XX                  # commit + PR → develop

os-review PR_NUMBER               # prompt al portapapeles → pega en agente
                                  # guarda output en .openspec-cli/.review-output.md
os-review-apply PR_NUMBER         # publica en GitHub

# Si REQUEST CHANGES:
os-review-fix PR_NUMBER           # fix automático + re-review + re-publish

os-transition KAN-XX "Done"       # cierra el ticket en Jira
```

---

## Stack

```yaml
vault-smart-contracts   # Thought Machine Vault API 4.0 — único stack del repo
```

`openspec/config.yaml` mantiene la forma de "registry" por si se añade otro stack
más adelante, pero hoy solo existe el de Vault.

---

## Agentes soportados

| Agente | Entrega | Notas |
|---|---|---|
| `copilot` | Portapapeles | Pegar manualmente en VS Code Copilot Chat |
| `claude-code` | CLI directo | Totalmente automático sin copy-paste |
| `cursor` | Portapapeles | Pegar manualmente en Cursor |
| `windsurf` | Portapapeles | Pegar manualmente en Windsurf |
| `aider` | CLI directo | Automático via terminal |

---

## Vault Smart Contracts — restricciones críticas de Python

Vault NO usa Python estándar. Su sandbox restringe:

### PROHIBIDO
```python
import os, sys, json, re, math, datetime, collections  # ninguna stdlib
eval(), exec(), __import__(), globals(), locals()
print(), open(), input()
getattr(), setattr(), type(), dir()
raise ValueError(...), raise Exception(...), raise X from Y   # ninguna excepción
GLOBAL_MUTABLE = {}  # no estado global mutable
requests.get()       # no red
float(), 1.5          # nada de float — Decimal siempre
```

### PERMITIDO
```python
from decimal import Decimal, ROUND_HALF_UP   # obligatorio para dinero
from zoneinfo import ZoneInfo                # para datetimes UTC
from contracts_api import (...)              # único módulo de dominio
str, int, list, dict, sorted(), sum()        # built-ins básicos
hook_arguments.effective_datetime            # así se obtiene la fecha
assert condicion, "mensaje"                  # única forma de abortar un hook
```

### Validación en hooks: `assert`, nunca `raise`

`raise ValueError(...)` (o cualquier excepción) → `InvalidSmartContractError:
"Unsupported builtin used"` en runtime — el sandbox no expone clases de
excepción. Los tests mockeados NO lo ven. Usar `assert <condición>, "mensaje"`
(el `AssertionError` se propaga con el mensaje intacto). `vault_lint.py` lo
verifica: regla `RAISE_STATEMENT`. Detalle: `vault-core-api-gotchas.md` §3.5.

### Cambios críticos API 4.0 vs 3.x

```python
# Datetime: ZoneInfo requerido (NO timezone.utc)
from zoneinfo import ZoneInfo
dt = datetime(2024, 1, 1, tzinfo=ZoneInfo("UTC"))  # ✅
dt = datetime(2024, 1, 1, tzinfo=timezone.utc)      # ❌ InvalidSmartContractError

# Phase en BalanceCoordinate (key), NO en Balance (value)
for coord, balance in posting.balances().items():
    if coord.phase == Phase.COMMITTED:    # ✅
        total += balance.net
# balance.phase → ❌ AttributeError

# Rejection (no raise, no Rejected)
return PrePostingHookResult(              # ✅
    rejection=Rejection(
        message="Insufficient funds",
        reason_code=RejectionReason.INSUFFICIENT_FUNDS,
    )
)
raise Rejected("...")                     # ❌ API 3.x

# CustomInstruction sin client_transaction_id
CustomInstruction(                        # ✅
    postings=[...],
    instruction_details={
        "description": "...",
        "hook_execution_id": str(vault.get_hook_execution_id()),
    },
)
CustomInstruction(client_transaction_id="...")  # ❌

# PrePostingHookArguments requiere client_transactions
PrePostingHookArguments(
    effective_datetime=dt,
    posting_instructions=[posting],
    client_transactions={},               # ✅ requerido en API 4.0
)

# get_balances_observation (no get_balance_timeseries)
balances = vault.get_balances_observation(fetcher_id="live_balances").balances  # ✅
balances = vault.get_balance_timeseries().latest()  # ❌ API 3.x

# update_permission obligatorio en TODO Parameter(level=ParameterLevel.INSTANCE)
Parameter(name="denomination", level=ParameterLevel.INSTANCE,
          update_permission=ParameterUpdatePermission.USER_EDITABLE, ...)  # ✅
# ❌ sin update_permission → el DEPLOY falla ("must be specified for parameters at instance level")
# ❌ update_permission en un param derived=True o TEMPLATE → rechazado
# vault_lint.py lo verifica: reglas INSTANCE_UPDATE_PERMISSION / DERIVED_UPDATE_PERMISSION

# Todo hook que lee parámetros/balances DEBE declarar el requirement
from contracts_api import BalancesObservationFetcher, DefinedDateTime, fetch_account_data, requires
data_fetchers = [BalancesObservationFetcher(fetcher_id="live_balances", at=DefinedDateTime.LIVE)]  # NO balance_observation_fetchers
@requires(parameters=True)                          # get_parameter_timeseries()
@fetch_account_data(balances=["live_balances"])     # get_balances_observation()
def pre_posting_hook(vault, hook_arguments): ...
# ❌ sin decoradores → InvalidSmartContractError: Timeseries 'x' not found (los tests mockeados NO lo ven)
# scheduled_event_hook: un @requires + un @fetch_account_data por cada event_type
# vault_lint.py lo verifica: MISSING_PARAMETERS_REQUIREMENT / MISSING_BALANCES_FETCHER
```

### Deploy al sandbox compartido (hallazgos sesión KAN-12)

- `product_id` con prefijo propio (`openspec_<nombre>`); el nombre pelado choca con productos preexistentes
- Subir `version` en el `.py` en cada intento de deploy real
- Parámetros TEMPLATE/GLOBAL necesitan `value` en el payload; los INSTANCE no (van al crear la cuenta)
- Header `X-Auth-Token: <token>` (token plano), NO `Authorization: Bearer`
- `/v1/contracts:simulate` es NDJSON en streaming y **funciona con la VPN corporativa activa**
  (sin VPN el `connect()` al host hace timeout). `os-vault-simulate` abre la cuenta dentro
  de la simulación; `DateShape` va como `"YYYY-MM-DD"` (un datetime provoca HTTP 500)
- Detalle completo: `ai-specs/specs/stacks/vault-core-api-gotchas.md`

---

## Variables de entorno (.env)

```bash
# Jira
JIRA_BASE_URL=https://ingjohnaragon.atlassian.net
JIRA_EMAIL=ingjohnaragon@gmail.com
JIRA_TOKEN=<token>
JIRA_PROJECT_KEY=KAN

# Vault Core API (cuando tengas acceso al sandbox)
VAULT_BASE_URL=https://your-vault-instance.thought-machine.net
VAULT_TOKEN=your_vault_api_token
VAULT_DEFAULT_DENOMINATION=GBP
```

---

## Estado actual del proyecto

### Completado ✅
- CLI de comandos `os-*` operativa (config, Jira, workflow, Vault)
- Repo enfocado 100% en Vault (stacks no-Vault retirados)
- Integración Jira completa (fetch, create, transition, list, enrich)
- Integración GitHub (PR, review, merge)
- `vault_lint.py` — 9 reglas de sandbox (`update_permission` en INSTANCE, data requirements por hook)
- Vault Core API integrada (simulate, deploy, account, balances, customer, products)
- 5 contratos con 135 tests verdes + 54 de vault_lint, API 4.0 verificada
- Hallazgos Core API (KAN-12 + sesión simulate 2026-08-28) en agente + standards + linter
- `os-vault-simulate` operativo (streaming NDJSON con VPN); los 5 contratos simulan limpio
- CI GitHub Actions con contracts_api SDK
- `os-review-fix` — loop automático de corrección + re-review
- `os-commit` protege develop/main (siempre crea feature branch)

### Pendiente ⏳
- Prueba E2E completa contra Vault Sandbox: simulate ✅ (con VPN); falta deploy→account→balances en verde de punta a punta
- Dashboard de métricas de adopción (Fase 2)
- Repositorio de specs base GFT reutilizables

### Rama activa
`develop` (feature branches se crean desde aquí automáticamente)

### Repo
`https://github.com/ingjohnaragon-crypto/spec-driven-project`

---

## Cómo preguntarme desde Claude Code

```bash
# Desde la terminal de VS Code con Claude Code activo:
"genera un Smart Contract de préstamo personal con cuotas mensuales"
"crea los tests para contracts/current_account.py"
"qué hooks necesita un producto de depósito a plazo en Vault"
"revisa contracts/savings_product.py y detecta violaciones del sandbox"
"planifica el ticket KAN-20 para Vault"
"por qué falla este test de pre_posting_hook"
"explica la diferencia entre API 3.x y 4.0 en Vault"
```

El contexto del proyecto, los stacks, las restricciones de Vault y el estado
actual están cargados. No necesitas re-explicar nada.