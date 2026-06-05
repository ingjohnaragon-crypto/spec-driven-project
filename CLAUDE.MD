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
│   │   ├── vault-smart-contracts.md  ← agente principal (API 4.0 verificada)
│   │   ├── java-spring.md
│   │   ├── python-fastapi.md
│   │   └── ...
│   ├── specs/stacks/
│   │   └── vault-smart-contracts-standards.mdc
│   ├── .commands/                    # Plantillas de prompt
│   └── changes/                      # Planes generados por ticket
├── contracts/
│   ├── savings_product.py            # Smart Contract cuenta de ahorros
│   └── current_account.py            # Smart Contract cuenta corriente con sobregiro
├── tests/
│   ├── test_savings_product.py       # 18 tests ✅
│   └── test_current_account.py       # 20 tests ✅
├── contracts_sdk/                    # SDK Thought Machine (local)
│   └── contracts_sdk/                # py -m pip install . desde aquí
├── .openspec-cli/
│   ├── install.sh                    # sh .openspec-cli/install.sh
│   ├── lib/
│   │   ├── config.sh
│   │   ├── agent.sh
│   │   ├── jira.sh                   # incluye os_jira_create_ticket, os_jira_list_tickets
│   │   ├── vault.sh
│   │   ├── parse_config.py
│   │   ├── parse_agent.py
│   │   ├── parse_stack.py
│   │   ├── vault_simulate_payload.py
│   │   └── vault_deploy_payload.py
│   └── commands/                     # 16 comandos os-*
└── .github/workflows/ci.yml          # CI con contracts_api SDK
```

---

## 16 Comandos CLI

### Configuración
```bash
os-stack --list                        # listar stacks disponibles
os-stack vault-smart-contracts         # activar stack
os-agent --list                        # listar agentes
os-agent claude-code                   # activar agente (o copilot)
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
os-plan KAN-XX                         # generar plan → ai-specs/changes/KAN-XX_backend.md
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
                                  # guarda output en ai-specs/changes/KAN-XX_backend.md

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

## Stacks soportados

```yaml
vault-smart-contracts   # Thought Machine Vault API 4.0 (stack principal)
java-spring             # Java 17 + Spring Boot
python-fastapi          # Python 3.12 + FastAPI
node-express            # Node.js + Express
go-gin                  # Go + Gin
frontend-react          # React + Vite
frontend-angular        # Angular
```

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
raise X from Y
GLOBAL_MUTABLE = {}  # no estado global mutable
requests.get()       # no red
```

### PERMITIDO
```python
from decimal import Decimal, ROUND_HALF_UP   # obligatorio para dinero
from contracts_api import (...)              # único módulo externo
str, int, list, dict, sorted(), sum()        # built-ins básicos
hook_arguments.effective_datetime            # así se obtiene la fecha
```

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
```

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
- CLI con 16 comandos operativos
- 7 stacks configurados
- Integración Jira completa (fetch, create, transition, list, enrich)
- Integración GitHub (PR, review, merge)
- Stack vault-smart-contracts con restricciones Python de Vault documentadas
- Vault Core API integrada (simulate, deploy, account, balances)
- `savings_product.py` — 18 tests verdes, API 4.0 verificada
- `current_account.py` — sobregiro configurable, 20 tests verdes
- CI GitHub Actions con contracts_api SDK (18+20 tests)
- `os-review-fix` — loop automático de corrección + re-review
- `os-commit` protege develop/main (siempre crea feature branch)
- CLAUDE.md con contexto completo del proyecto

### Pendiente ⏳
- Prueba E2E contra Vault Sandbox (requiere acceso GFT/TM)
- `os-vault-simulate` y `os-vault-deploy` (requieren sandbox)
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