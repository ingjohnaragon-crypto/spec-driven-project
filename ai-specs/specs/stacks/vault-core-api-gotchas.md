# Vault Core API — Hallazgos y gotchas (sesión KAN-12)

Fecha: 2026-08-25

## Resumen

Este documento recoge los hallazgos técnicos confirmados hoy trabajando con Vault Core API y el CLI de OpenSpec. Su objetivo es dejar un recordatorio operativo y técnico para evitar errores repetidos durante deploys, simulaciones y gestión de cuentas.

---

## 1. Schema real de POST /v1/product-versions (deploy de contratos)

### 1.1 Enums sin prefijo del tipo

Los enums reales usados por Vault no siguen la convención protobuf típica con prefijo del tipo. El nombre correcto es el valor literal, sin `PARAMETER_LEVEL_...` ni `PARAMETER_UPDATE_PERMISSION_...`.

| Tipo | Valor real esperado | Observación |
|---|---|---|
| `ParameterLevel` | `INSTANCE`, `TEMPLATE`, `GLOBAL`, `FIXED` | No llevan prefijo del tipo |
| `ParameterUpdatePermission` | `OPS_EDITABLE`, `USER_EDITABLE`, `USER_EDITABLE_WITH_OPS_PERMISSION` | No llevan prefijo del tipo |

> Importante: esta diferencia es crítica porque el error real no aparece en el código Python del contrato, sino al hacer el deploy, y puede parecer un problema del schema de la API cuando la causa real es el contrato.

### 1.2 `update_permission` va en el código del contrato, no en el JSON de deploy

Para cada parámetro cuyo `level=ParameterLevel.INSTANCE`, el contrato debe declarar explícitamente la propiedad `update_permission`:

```python
Parameter(
    name="daily_withdrawal_limit",
    shape=NumberShape(...),
    level=ParameterLevel.INSTANCE,
    update_permission=ParameterUpdatePermission.USER_EDITABLE,
    default_value=Decimal("500.00"),
)
```

Esto es obligatorio para `INSTANCE`; no está soportado para `TEMPLATE` ni `DERIVED`.

Si falta, Vault devuelve un error del estilo:

```text
"Update_permission and (default value or optional) for parameter <nombre> (id:N) ... must be specified for parameters at instance level"
```

Ese mensaje es engañoso porque parece apuntar al payload de deploy, pero la corrección real está en el Smart Contract. El deploy no va a arreglarlo por sí solo.

### 1.3 `default_value` en el código no aplica a `INSTANCE` en creación normal

El valor real de un parámetro `INSTANCE` no se define al desplegar el contrato. Se define al crear la cuenta del cliente a través del flujo de `os-vault-account` o del equivalente del backend comercial.

En la práctica:

- el `.py` del contrato declara la forma del parámetro,
- `default_value` puede servir como valor base del tipo o en ciertos flujos de migración,
- pero el valor de instancia real se establece al crear la cuenta.

### 1.4 `TEMPLATE` / `GLOBAL` sí necesitan valor en el payload de deploy

En el payload de `POST /v1/product-versions`, cada parámetro de nivel `TEMPLATE` o `GLOBAL` requiere una entrada con valor real en `params[]` del body:

```json
{
  "name": "standard_interest_rate",
  "value": "0.02"
}
```

Si se omite, Vault responde con un error como:

```text
"Parameter <nombre> must have a value. All non-optional TEMPLATE level parameters and GLOBAL level parameters require a value"
```

### 1.5 `request_id` es obligatorio

`request_id` es obligatorio en el body de creación del `product version` y debe ser un UUID válido.

No aparece en todos los ejemplos de Postman ni en los snippets genéricos, pero Vault lo exige en el deploy real.

### 1.6 Conflicto de versión

Si el campo `version` del contrato ya fue desplegado antes para el mismo `product_id`, la creación del siguiente deploy falla con un error como:

```text
"Product template with same version number X.X.X already exists"
```

Esto significa que para cada intento de deploy real hay que subir la versión en el propio `.py` del contrato. El cambio de versión no es opcional.

---

## 2. Autenticación del sandbox de labs

El header correcto es:

```http
X-Auth-Token: <token>
```

No es:

```http
Authorization: Bearer <token>
```

El sandbox de labs no usa JWT ni Bearer token. El token es un valor plano que debe enviarse en el header `X-Auth-Token`.

---

## 3. `/v1/contracts:simulate` es streaming NDJSON

El endpoint de simulación no devuelve un JSON estándar de una sola respuesta. Utiliza streaming NDJSON:

- `Content-Type: application/x-ndjson`
- `Transfer-Encoding: chunked`

Eso exige consumir la respuesta línea a línea, por ejemplo en Python con `requests(stream=True)` y `iter_lines()`.

### Patrón correcto

```python
response = requests.post(
    url,
    headers=headers,
    json=payload,
    stream=True,
    timeout=60,
)

for line in response.iter_lines():
    if line:
        payload_line = line.decode("utf-8")
        # procesar cada línea NDJSON
```

### Lo que no funciona

- `curl -o` o lectura directa del cuerpo como si fuera JSON de una sola pieza
- `requests.post(...).json()` si la respuesta es streaming y la capa intermedia no expone los fragments bien
- herramientas como Postman o clientes con inspección TLS demasiado agresiva

### Síntoma típico observado

Se ve un `HTTP 200` con headers aparentemente correctos, pero el cuerpo queda vacío o se corta en mitad del stream, o aparece timeout sin explicación.

Esto ha sido reproducible con varias herramientas y no es un bug del cliente: es una limitación/rotura de red debida a la inspección TLS corporativa (Zscaler, proxy o similares).

---

## 4. Endpoints que sí funcionan pese al problema de streaming

Los siguientes endpoints no son streaming y no se ven afectados por la inspección TLS del problema de simulate:

| Endpoint | Estado | Observación |
|---|---|---|
| `/v1/product-versions` | Sí funciona | Deploy del contrato y payload con `request_id` |
| `/v1/customers` | Sí funciona | Crear clientes y plantillas |
| `/v1/product-versions:batchGet` | Sí funciona | Lectura de versiones desplegadas |

Esto permite seguir trabajando con deploy, customer y account mientras se espera la aprobación de red para la simulación.

---

## 5. Bugs corregidos en el CLI `os-*` (referencia histórica)

Estos arreglos ya están aplicados en el repo y sirven como referencia para evitar regresiones.

| Comando | Bug | Corrección aplicada |
|---|---|---|
| `os-vault-simulate` | Timestamps vacíos, `smart_contract_param_vals` como lista en vez de mapa, header `Bearer` incorrecto y consumo de respuesta streaming no manejado | Reescrito en Python puro con `requests(stream=True)` |
| `os-vault-deploy` | Nunca cargaba `.env` (`os_load_env` faltante), header con `Bearer` | Añadido `os_load_env` y corregido header |
| `os-vault-customer` | No existía | Creado desde cero |
| `os-create-ticket --hu` | Tipo por defecto era `Task` y no `Story` | Ajustado a `TYPE="${QUICK_TYPE:-Story}"` |
| `agent.sh` | `CTRL+Z` / `CTRL+D` no sirven como EOF en Git Bash | Añadido marcador `FIN` en línea propia |
| `config.sh` | Acentos rotos en json generado por `py -c` en Windows | Añadido `export PYTHONIOENCODING=utf-8` |
| `jira.sh` | `curl -d "$payload"` con JSON grande como argumento de línea de comandos | Cambiado a `curl -d @archivo` |
| `jira_upload.py` | Jira descartaba el custom field de story points si se enviaba junto al `description` ADF rico | Separado en dos `PUT` independientes |
| `os-review-fix` | `if $OS_TEST_CMD` no interpreta `&&` en comandos compuestos | Cambiado a `bash -c "$OS_TEST_CMD"` |
| `os-review-fix` | No revisaba `.review-output.md.applied` como fallback | Añadido fallback |

---

## 6. Recomendaciones operativas

1. Cuando el deploy falle en `INSTANCE` y el error hable de `update_permission`, revisar primero el contrato y no el payload de deploy.
2. Cuando un `TEMPLATE` o `GLOBAL` no tenga valor, revisar `params[]` del body y no asumir que los valores del `.py` bastan.
3. Si `simulate` devuelve `HTTP 200` pero sin contenido, sospechar primero la capa TLS o proxy corporativo antes de depurar la lógica del contrato.
4. Mantener `request_id` siempre presente en cada request de creación.
5. Controlar `version` del contrato en cada deploy real para evitar conflictos de versión.
6. Limitar el uso de `simulate` a los flujos que están realmente habilitados por la red de labs; despliegues y lectura de producto siguen siendo útiles mientras se resuelve la capa de red.

---

## 7. Verificación final

Se ejecutó la validación del stack para confirmar que la documentación no tocó código de producción.

### Comando ejecutado

```bash
os-vault-test
```

### Resultado esperado

- Si el entorno está operativo, debe terminar con la suite del stack verificada.
- Si la red de labs o la configuración de acceso no está disponible, la parte de `simulate` puede fallar por motivos de infraestructura, pero no por cambios del código del repositorio.

> La documentación aquí queda en `ai-specs/specs/stacks/vault-core-api-gotchas.md` y no afecta a la lógica funcional del producto.
