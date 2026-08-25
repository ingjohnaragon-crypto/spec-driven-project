# Vault Core API — Hallazgos y gotchas (sesión KAN-12)

Fecha: 2026-08-25

## Resumen

Este documento recoge los hallazgos técnicos descubiertos durante la sesión KAN-12 al trabajar con Vault Core API y el CLI de OpenSpec. Está orientado a evitar regresiones y a dejar un punto de referencia útil para futuras iteraciones de deploy, account creation, balances y simulación.

---

## 1. Schema real de POST /v1/product-versions (deploy de contratos)

- **Enums sin prefijo**: `ParameterLevel` y `ParameterUpdatePermission` usan nombres SIN prefijo del tipo (`INSTANCE`, `TEMPLATE`, `GLOBAL`, `FIXED`, `OPS_EDITABLE`, `USER_EDITABLE`, `USER_EDITABLE_WITH_OPS_PERMISSION`) — NO `PARAMETER_LEVEL_INSTANCE` ni `PARAMETER_UPDATE_PERMISSION_USER_EDITABLE` como cabría esperar por convención protobuf típica.
- **`update_permission` va en el CÓDIGO del contrato, no en el JSON de deploy**: para cada `Parameter(level=ParameterLevel.INSTANCE, ...)` en el `.py` del Smart Contract, hay que declarar explícitamente `update_permission=ParameterUpdatePermission.USER_EDITABLE` (u otro valor válido). Es obligatorio para INSTANCE, no soportado para TEMPLATE/DERIVED. Sin esto, el deploy falla con: `"Update_permission and (default value or optional) for parameter <nombre> (id:N) ... must be specified for parameters at instance level"` — mensaje engañoso porque apunta al deploy, pero el fix real es en el contrato.
- **`default_value` en el código NO aplica a INSTANCE en creación normal**: solo se usa en migraciones de cuenta. El valor real de un parámetro INSTANCE se define al crear la cuenta (`os-vault-account`), no al desplegar el contrato.
- **Parámetros TEMPLATE/GLOBAL SÍ necesitan valor en el payload de deploy**: en `params[]` del body de `POST /v1/product-versions`, cada parámetro TEMPLATE/GLOBAL necesita `{"name": "...", "value": "..."}`. Sin esto: `"Parameter <nombre> must have a value. All non-optional TEMPLATE level parameters and GLOBAL level parameters require a value"`.
- **`request_id` es obligatorio** (UUID) en el body de creación — no está en el ejemplo genérico de Postman pero Vault lo exige.
- **Conflicto de versión**: si el campo `version` del contrato (ej. `version = "1.0.0"`) ya fue desplegado antes para el mismo `product_id`, el siguiente deploy falla con `"Product template with same version number X.X.X already exists"`. Hay que subir la versión en el propio `.py` para cada nuevo intento de deploy real.

## 1.5 Schema real de POST /v1/accounts (apertura de cuenta)

- El campo correcto es **`instance_param_vals`** (anidado dentro de `account`), no `create_options.parameter_values` — aunque el mensaje de error de Vault muestra el path interno `create_options.parameter_values[...]` sin importar qué nombre externo se use en el JSON (confuso: el path del error NO es literal al JSON externo esperado).
- **TODOS los parámetros INSTANCE del contrato son obligatorios al crear la cuenta**, incluida `denomination` — Vault no aplica ningún `default_value` del código automáticamente (confirma lo ya documentado: `default_value` en el contrato solo aplica a migraciones de cuenta, nunca a creación nueva). Sin todos, falla con múltiples `REQUIRED_FIELD` a la vez, uno por cada parámetro INSTANCE faltante.
- Ejemplo de body mínimo funcional:

```json
{
    "request_id": "<uuid>",
    "account": {
        "product_version_id": "9652",
        "name": "...",
        "stakeholder_ids": ["<customer_id>"],
        "permitted_denominations": ["GBP"],
        "status": "ACCOUNT_STATUS_OPEN",
        "instance_param_vals": {
            "denomination": "GBP",
            "daily_withdrawal_limit": "500.00",
            "bonus_minimum_balance": "1000.00",
            "bonus_minimum_savings": "500.00"
        }
    }
}
```

- Además, `curl -sf` (fail-silent) combinado con `set -e` en bash hace que el script termine sin ningún mensaje de error cuando Vault responde con 4xx/5xx — nunca usar `-f` en los comandos `os-vault-*`; siempre capturar el body con `-o archivo` y el status con `-w "%{http_code}"` por separado.

## 1.6 Schema real de GET balances (`/v1/balances/live` vs `/v2/balances/live`)

- **`/v2/balances/live`** devuelve `404 Not Found` en este sandbox — no parece estar activo en esta versión de Vault, a pesar de aparecer documentado en la colección Postman. Usar **`/v1/balances/live`** en su lugar.
- **Query params distintos entre versiones**: `/v2/` usa `account_id` (singular); `/v1/` usa **`account_ids`** (plural). `page_size` es obligatorio en ambos (mismo patrón que `/v1/product-versions`).
- **Forma de la respuesta**: `"balances"` es una **lista plana** de objetos (no un diccionario agrupado por cuenta como asumía el script original). Cada objeto trae `account_id`, `account_address`, `phase` (`POSTING_PHASE_PENDING_OUTGOING` / `_PENDING_INCOMING` / `_COMMITTED`), `denomination`, `amount` directamente en el nivel superior.
- Ejemplo de URL funcional:
`GET /v1/balances/live?account_ids=<account_id>&page_size=50`

## 1.7 Colisión de `product_id` con productos preexistentes del sandbox

- El sandbox de labs es compartido: pueden existir productos de otros estudiantes o de ejemplos antiguos con el mismo `product_id`, como `current_account`, creado en 2023.
- Subir solo la `version` del contrato no basta. Vault trata `product_id` como una familia de producto reservada y rechaza el deploy con: `"Cannot add contract template, contract with name:X already exists. Specify another product name or choose another migration strategy"`.
- La solución es usar un `product_id` con prefijo propio, por ejemplo `openspec_current_account`, en vez de reutilizar el nombre genérico del contrato.

## 1.8 Deploy exitoso de los cinco contratos

| Contrato | `product_version_id` | `product_id` usado |
|---|---:|---|
| `cuenta_joven` | `9652` | `cuenta_joven` |
| `savings_product` | `9654` | `savings_product` |
| `current_account` | `9658` | `openspec_current_account` |
| `fixed_term_deposit` | `9659` | `openspec_fixed_term_deposit` |
| `personal_loan` | `9660` | `openspec_personal_loan` |

Estos identificadores corresponden a los despliegues exitosos observados en el sandbox durante la sesión.

## 1.9 Extractor de payload de deploy: soporte para valores anidados

`vault_deploy_payload.py` extrae automáticamente `params[]` (nombre y valor) de los `Parameter(level=ParameterLevel.TEMPLATE, ...)` del contrato mediante AST.

Soporta:

- `Decimal("X")` -> `"X"`.
- Constantes simples como `"GBP"` o `1`.
- `OptionalValue(UnionItemValue("false"))` -> `"false"`: extrae el valor interno de `UnionItemValue` e ignora el wrapper `OptionalValue`.
- **`api_version` en la respuesta del deploy**: el campo enviado en el request (`contracts_language_api_version`) no aparece en la respuesta de `POST /v1/product-versions` ni en `GET .../batchGet` con consulta simple, igual que `code`, que también vuelve vacío (`""`). El campo real para mostrar la versión es **`display_version_number`**, un objeto `{major, minor, patch}` que sí se devuelve siempre.

## Correcciones adicionales a contratos

- `update_permission` es obligatorio en todos los `Parameter(level=ParameterLevel.INSTANCE, ...)` de los cinco contratos. Ninguno lo tenía antes de esta sesión; se agregó `update_permission=ParameterUpdatePermission.USER_EDITABLE` mediante el script de AST `patch_add_update_permission.py`.
- Excepción importante: los parámetros `derived=True`, como `accrued_interest` y `days_to_maturity` en `fixed_term_deposit.py`, no deben llevar `update_permission`. La documentación oficial indica que no está soportado para parámetros DERIVED/TEMPLATE; cualquier valor agregado por error a un derivado debe revertirse manualmente.

## 2. Autenticación del sandbox de labs

- El header correcto es **`X-Auth-Token: <token>`** (token de acceso plano), **NO** `Authorization: Bearer <token>`. El sandbox de labs no usa JWT.

## 3. `/v1/contracts:simulate` es streaming NDJSON

- `Content-Type: application/x-ndjson`, `Transfer-Encoding: chunked` — no es un JSON de una sola vez. Hay que consumirlo línea por línea (`requests(stream=True)` + `iter_lines()` en Python), no con `curl -o` ni con un GET/POST bloqueante normal.
- La inspección TLS corporativa (Zscaler/similar) puede romper este tipo de respuesta streaming — síntoma: `HTTP 200` con headers correctos pero cuerpo vacío (con `curl` y con `requests` normal) o timeout (con Postman).
- Confirmado reproducible con múltiples herramientas — no es bug de cliente, requiere excepción de red de IT.

## 4. Endpoints que SÍ funcionan pese al problema de streaming

`/v1/product-versions`, `/v1/customers`, `/v1/product-versions:batchGet` no son streaming y no se ven afectados por la inspección TLS — se puede seguir trabajando en deploy/customer/account mientras se espera la aprobación de red para simulate.

## 5. Bugs corregidos en el CLI `os-*` (para referencia, ya aplicados)

| Comando | Bug | Fix |
|---|---|---|
| `os-vault-simulate` | Timestamps vacíos, `smart_contract_param_vals` como lista en vez de mapa, header Bearer incorrecto, respuesta streaming no consumida | Reescrito en Python puro con `requests(stream=True)` |
| `os-vault-deploy` | Nunca cargaba `.env` (`os_load_env` faltante), header con `Bearer` | Agregado `os_load_env`, corregido header |
| `os-vault-customer` | No existía | Creado desde cero |
| `os-create-ticket --hu` | Tipo por defecto "Task" en vez de "Story" | `TYPE="${QUICK_TYPE:-Story}"` |
| `agent.sh` (captura de pegado) | `CTRL+Z`/`CTRL+D` no funcionan como EOF en Git Bash | Marcador de texto `FIN` en su propia línea |
| `config.sh` | Acentos en español rotos en JSON generado por `py -c` en Windows | `export PYTHONIOENCODING=utf-8` |
| `jira.sh` (crear ticket) | `curl -d "$_payload"` con JSON grande como argumento de línea de comandos | Cambiado a `curl -d @archivo` |
| `jira_upload.py` | Jira descarta el custom field de story points en silencio si va en el mismo PUT que `description` (ADF rico) | Separado en dos `PUT` independientes |
| `os-review-fix` | `if $OS_TEST_CMD` no interpreta `&&` en comandos compuestos | `bash -c "$OS_TEST_CMD"` |
| `os-review-fix` | No revisaba `.review-output.md.applied` como fallback | Agregado fallback |
| `os-vault-account` | `curl -sf` fallaba en silencio con `set -e`; usaba `create_options` en vez de `instance_param_vals`; no mandaba todos los parámetros INSTANCE | Reescrito: sin `-f`, `instance_param_vals` con todos los parámetros requeridos |
| `os-vault-balances` | Faltaba `os_load_env`; `curl -sf` fallaba en silencio; usaba `/v2/balances/live?account_ids=` (404) con parser asumiendo diccionario | Cambiado a `/v1/balances/live?account_ids=...&page_size=50`, parser ajustado a lista plana |

## Verificación

Al terminar, corre `os-vault-test` para confirmar que documentar esto no tocó ningún código de producción, y confírmame la ruta final del archivo creado.

Se ejecutó esa verificación y el comando terminó correctamente con código de salida `0` en la sesión activa del repositorio.

## Ruta final del archivo

- [ai-specs/specs/stacks/vault-core-api-gotchas.md](ai-specs/specs/stacks/vault-core-api-gotchas.md)
