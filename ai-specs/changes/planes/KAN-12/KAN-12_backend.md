# Vault Implementation Plan: KAN-12 Cuenta joven con límites de retiro diario y tasa bonificada

## Estimación de puntos de historia
```markdown
<!-- STORY_POINTS:8 -->
**8** — Nuevo producto de pasivo con estado diario persistente mediante balances internos, reinicio programado, doble regla de elegibilidad de intereses y una suite de pruebas superior a 20 casos.
<!-- /STORY_POINTS -->
```

## 1. Resumen

Implementar un Smart Contract Vault API 4.0 para una cuenta joven de pasivo (`tside = Tside.LIABILITY`). El producto permitirá depósitos y retiros en una única denominación por cuenta, limitará el importe total retirado durante cada día calendario y aplicará una tasa estándar o bonificada en el evento mensual de intereses.

Los retiros se validarán en `pre_posting_hook` y se registrarán en `post_posting_hook` mediante balances internos, sin estado global mutable. `scheduled_event_hook` ejecutará un evento diario a medianoche para vaciar el acumulado y un evento mensual para calcular y abonar intereses. Los importes, tasas y redondeos usarán exclusivamente `Decimal` con `ROUND_HALF_UP`.

Stack activo: `vault-smart-contracts`, con restricciones del sandbox de Vault y semántica de contracts_api 4.0. La implementación debe usar nombres de hook `activation_hook`, `pre_posting_hook`, `post_posting_hook` y `scheduled_event_hook`; nunca `*_code`.

## 2. Contexto de arquitectura

- Active stack: `vault-smart-contracts`
- Golden reference: `contracts/fixed_term_deposit.py` (+ `tests/test_fixed_term_deposit.py`)
- Referencias adicionales: `contracts/savings_product.py` para intereses y `contracts/current_account.py` para validación de saldo.
- Files:
  - `contracts/cuenta_joven.py` — Smart Contract API 4.0
  - `tests/test_cuenta_joven.py` — unit tests con mocks `contracts_api`
  - `contracts/__init__.py` — no modificar salvo que el paquete requiera registro explícito
  - Tooling: `os-vault-lint`, `os-vault-test`, opcionalmente `os-vault-simulate`

### 2.1 Decisiones bloqueadas

| Tema | Decisión final | Rationale |
|---|---|---|
| Nombre de archivos | `contracts/cuenta_joven.py` y `tests/test_cuenta_joven.py` | Coincide con el nombre funcional del ticket y la convención snake_case |
| Convención de tasas | Fracción `Decimal`: `0.05` representa 5%; no porcentajes enteros | Consistencia con los contratos dorados y evita conversiones ambiguas |
| Denominaciones | `supported_denominations = ["GBP", "USD", "EUR", "COP"]`; una sola denominación por cuenta; default `GBP` | Paridad con los productos existentes |
| Límite diario | Parámetro de instancia `daily_withdrawal_limit`, `Decimal >= 0`, expresado en unidades de la denominación | El límite pertenece a cada cuenta y es comprobable por instancia |
| Estado del acumulado | Address interno `DAILY_WITHDRAWALS` con un balance por `BalanceCoordinate`; address compensatorio `DAILY_WITHDRAWALS_OFFSET` | Los balances persisten entre hooks y la coordenada separa cuenta, asset, fase y denominación |
| Registro del retiro | `post_posting_hook` crea un `CustomInstruction` que acredita el importe en `DAILY_WITHDRAWALS` y debita el mismo importe en `DAILY_WITHDRAWALS_OFFSET` | `pre_posting_hook` valida pero no debe mutar estado; el registro ocurre después de aprobarse el posting |
| Qué consume el límite | Solo el efecto neto negativo en `DEFAULT`, en fase `Phase.COMMITTED`, para la denominación de la cuenta | Depósitos y operaciones positivas no consumen el límite; los postings mixtos cuentan por su débito neto |
| Retiros simultáneos | Se suma el importe de todos los postings de la solicitud antes de comparar con el acumulado | Evita aprobar una solicitud por evaluar cada posting de forma aislada |
| Importe cero | Se rechaza cualquier retiro cuyo importe de débito sea `<= 0` cuando la operación se identifica como retiro | Evita operaciones ambiguas y cumple la validación de importes inválidos |
| Saldo insuficiente | Se valida contra el saldo comprometido de `DEFAULT`; un saldo resultante negativo se rechaza con `INSUFFICIENT_FUNDS` | El contrato protege la cuenta aunque el core también aplique controles |
| Reinicio diario | Evento `DAILY_WITHDRAWAL_RESET` a las `00:00:00` de cada día calendario, usando `ScheduleExpression`; vacía `DAILY_WITHDRAWALS` hacia `DAILY_WITHDRAWALS_OFFSET` | Reinicio determinista sin fecha almacenada ni estado mutable; la zona efectiva la proporciona Vault |
| Primera fecha del schedule diario | El schedule empieza en `hook_arguments.effective_datetime` de activación y ejecuta el siguiente cambio de fecha | Evita contar dos veces el acumulado del día de activación |
| Periodicidad de intereses | Evento `MONTHLY_INTEREST` con `EndOfMonthSchedule(day=28)` | Patrón ya usado por `savings_product.py`, estable para todos los meses |
| Base de intereses | Saldo comprometido positivo de `DEFAULT` observado en la fecha efectiva del evento; no se remunera saldo negativo | UX predecible y protección de la cuenta |
| Elegibilidad bonificada | Se exige simultáneamente `balance >= bonus_minimum_balance` y `balance >= bonus_minimum_savings`; un umbral igual a cero desactiva esa condición | Las dos condiciones del ticket son explícitas y la regla AND es fácil de probar |
| Tasa aplicada | Si ambas condiciones están satisfechas se aplica `bonus_interest_rate`; en cualquier otro caso `standard_interest_rate` | Regla binaria clara para el cliente |
| Abono de intereses | Un `CustomInstruction` acredita el interés en `DEFAULT` y debita `INTEREST_EXPENSE`; no se usa un saldo de interés acumulado | El evento es un abono periódico directo y conserva el balance contable |
| Cálculo | `balance * annual_rate / 12`, cuantizado a `Decimal("0.01")` con `ROUND_HALF_UP` | Periodicidad mensual explícita y redondeo financiero reproducible |
| Parámetros de tasa | `standard_interest_rate` y `bonus_interest_rate` son fracciones entre `0` y `1`, ambos `ParameterLevel.TEMPLATE`, con defaults `0.02` y `0.05` | Permite configurar el producto sin cambiar cada cuenta |
| Parámetros de elegibilidad | `bonus_minimum_balance` y `bonus_minimum_savings` son `ParameterLevel.INSTANCE`, `Decimal >= 0`, default `Decimal("0.00")` | Las condiciones pueden variar por cuenta y cero desactiva cada requisito |
| Parámetro de denominación | `denomination` es `ParameterLevel.INSTANCE`, `DenominationShape`, default `GBP` | Alineado con API 4.0 y los contratos existentes |
| Tasa superior | Se rechaza la activación si `bonus_interest_rate < standard_interest_rate` no es válido para el producto | Una bonificación nunca puede pagar menos que la tasa estándar |
| Penalizaciones | No hay penalización por retiro; el único control es el límite diario | El ticket no define una penalización y eliminarla reduce comportamiento inesperado |
| Rechazo | Usar `PrePostingHookResult(rejection=Rejection(...))`; límite, importe inválido y reglas de producto usan `RejectionReason.AGAINST_TNC`; saldo insuficiente usa `INSUFFICIENT_FUNDS`; denominación incorrecta usa `WRONG_DENOMINATION` | Enum y mensajes estables, sin lanzar excepciones de rechazo |
| Traceabilidad | Todos los `CustomInstruction` incluyen `instruction_details` con `description`, `hook_execution_id` y `event_type` cuando corresponda | API 4.0 no admite `client_transaction_id` |

## 3. Pasos de implementación

### Step 0: Feature branch

- Branch: `feature/KAN-12-backend` (creada por `os-develop` desde `develop`).

### Step 1: Contract scaffold

- Crear `contracts/cuenta_joven.py` con metadata API 4.0:
  - `api = "4.0.0"`, versión semántica inicial, `display_name`, `summary`, `description`.
  - `tside = Tside.LIABILITY`.
  - `supported_denominations = ["GBP", "USD", "EUR", "COP"]`.
- Importar directamente desde `contracts_api` y `decimal`; no envolver imports en `try/except`.
- Declarar `parameters = [...]` completos:
  - `denomination` (`DenominationShape`, INSTANCE, default `"GBP"`).
  - `daily_withdrawal_limit` (`NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01")`, INSTANCE).
  - `standard_interest_rate` y `bonus_interest_rate` (`NumberShape(0..1, step=Decimal("0.0001"))`, TEMPLATE).
  - `bonus_minimum_balance` y `bonus_minimum_savings` (`NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01")`, INSTANCE).
- Declarar constantes `DEFAULT_ADDRESS`, `DEFAULT_ASSET`, `DAILY_WITHDRAWALS`, `DAILY_WITHDRAWALS_OFFSET`, `INTEREST_EXPENSE`, `DAILY_WITHDRAWAL_RESET` y `MONTHLY_INTEREST`.
- Registrar ambos `SmartContractEventType` y `event_types_groups = []`.

### Step 2: Pure helper functions

Implementar helpers tipados y sin efectos secundarios:

- `_quantize_money(amount: Decimal) -> Decimal`: cuantizar a `Decimal("0.01")` con `ROUND_HALF_UP`.
- `_get_committed_balance(balances: BalanceDefaultDict, address: str, denomination: str) -> Decimal`: crear `BalanceCoordinate` explícito y leer `Phase.COMMITTED` desde la clave.
- `_posting_net_effect(posting_instructions, address: str, denomination: str) -> Decimal`: recorrer `posting.balances().items()` y sumar solo coordenadas committed del address y denominación indicados.
- `_get_withdrawal_amount(posting_instructions, denomination: str) -> Decimal`: devolver el valor absoluto del efecto negativo neto de `DEFAULT`; devolver cero para abonos u operaciones no correspondientes a retiro.
- `_calculate_bonus_eligibility(balance: Decimal, minimum_balance: Decimal, minimum_savings: Decimal) -> bool`: aplicar la regla AND, con umbrales cero desactivados.
- `_calculate_interest(balance: Decimal, annual_rate: Decimal) -> Decimal`: aplicar `/ Decimal("12")` y redondeo financiero explícito.
- `_build_internal_transfer(...) -> CustomInstruction`: construir postings balanceados entre `DAILY_WITHDRAWALS` y `DAILY_WITHDRAWALS_OFFSET`, o entre `INTEREST_EXPENSE` y `DEFAULT`, siempre con `instruction_details`.
- `_build_schedule(effective_datetime) -> dict`: crear los eventos diario y mensual con `ScheduledEvent`, `ScheduleExpression` y `EndOfMonthSchedule(day=28)`.

Los helpers no deben leer Vault, mutar colecciones globales, usar `float`, importar stdlib adicional ni inspeccionar objetos con `getattr`, `type` o `isinstance`.

### Step 3: Hook implementation

- `activation_hook(vault, hook_arguments: ActivationHookArguments) -> ActivationHookResult`:
  - Leer tasas y parámetros configurados.
  - Validar `daily_withdrawal_limit >= 0`, umbrales `>= 0`, tasas en rango y `bonus_interest_rate >= standard_interest_rate`.
  - Devolver los schedules `DAILY_WITHDRAWAL_RESET` y `MONTHLY_INTEREST` empezando en `effective_datetime`.
  - No usar I/O ni crear estado global.

- `pre_posting_hook(vault, hook_arguments: PrePostingHookArguments) -> PrePostingHookResult`:
  - Leer `denomination`, `daily_withdrawal_limit`, balances live y el acumulado en `DAILY_WITHDRAWALS` para la denominación.
  - Rechazar postings cuya denominación no coincida con la cuenta con `WRONG_DENOMINATION`.
  - Calcular el efecto committed de `DEFAULT` y detectar retiros netos.
  - Rechazar retiro cero o negativo cuando corresponda, con mensaje claro y `AGAINST_TNC`.
  - Rechazar si `current_balance + posting_effect < 0`, con `INSUFFICIENT_FUNDS`.
  - Rechazar si `accumulated_withdrawals + withdrawal_amount > daily_withdrawal_limit`, con mensaje que identifique el límite diario superado y `AGAINST_TNC`.
  - Aprobar depósitos, operaciones sin efecto en `DEFAULT` y retiros dentro del límite con `PrePostingHookResult()`.
  - No actualizar el acumulado en este hook.

- `post_posting_hook(vault, hook_arguments: PostPostingHookArguments) -> PostPostingHookResult`:
  - Calcular el retiro neto committed de los postings aprobados.
  - Si es cero, devolver directives vacías.
  - Si es positivo, emitir un `PostingInstructionsDirective` con un `CustomInstruction` que acredite `DAILY_WITHDRAWALS` y debite `DAILY_WITHDRAWALS_OFFSET` por la misma cantidad y denominación.
  - Incluir `hook_execution_id` y descripción estable.

- `scheduled_event_hook(vault, hook_arguments: ScheduledEventHookArguments) -> ScheduledEventHookResult`:
  - Para `DAILY_WITHDRAWAL_RESET`, leer el acumulado; si es positivo, emitir transferencia inversa a `DAILY_WITHDRAWALS_OFFSET`; si es cero, no emitir postings.
  - Para `MONTHLY_INTEREST`, leer saldo `DEFAULT`, tasas y umbrales; seleccionar la tasa bonificada solo cuando la elegibilidad AND sea verdadera.
  - Calcular interés mensual; si el interés es cero, devolver directives vacías.
  - Si es positivo, emitir `CustomInstruction` debitando `INTEREST_EXPENSE` y acreditando `DEFAULT` con redondeo a dos decimales.
  - Para un event type desconocido devolver resultado vacío sin error.

- No implementar `derived_parameter_hook`, porque ninguna información derivada es necesaria para cumplir el ticket.

### Step 4: Unit tests (TDD order)

- Crear `tests/test_cuenta_joven.py` siguiendo `tests/test_fixed_term_deposit.py`: `MagicMock` para Vault, argumentos tipados, `ZoneInfo("UTC")`, `BalanceDefaultDict` y clases agrupadas por hook/comportamiento.
- Crear fixtures para balance default, acumulado diario, denominación, parámetros de tasas y argumentos de `PrePostingHookArguments`, `PostPostingHookArguments`, `ActivationHookArguments` y `ScheduledEventHookArguments`.
- Implementar al menos estos 26 casos explícitos:
  - Activación: defaults/schedules; parámetros válidos; límite negativo; umbral negativo; tasa fuera de rango; tasa bonificada inferior a la estándar.
  - Retiros: menor que el límite; exactamente el límite; supera por `0.01`; segundo retiro que supera; varios retiros dentro del mismo día; retiro en nuevo día con acumulado reiniciado.
  - Aislamiento: cuentas distintas no comparten acumulado; GBP y USD no mezclan acumulados; denominación incorrecta rechazada.
  - Operaciones: abono no consume límite; operación sin efecto committed no consume límite; retiro cero rechazado; retiro con saldo insuficiente rechazado.
  - Registro/reset: `post_posting_hook` crea ambas legs del contador; operación no retirada no crea directive; reset vacía ambas legs; reset con cero es no-op.
  - Intereses: elegibilidad bonificada cumplida; saldo mínimo no cumplido usa estándar; ahorro mínimo no cumplido usa estándar; ambos mínimos cero aplican bonus; cálculo decimal y `ROUND_HALF_UP`; interés cero no crea instruction; `MONTHLY_INTEREST` registra ambas legs; event type desconocido es no-op.
- En cada `CustomInstruction`, verificar monto, denominación, dirección, crédito/débito e `instruction_details`; verificar especialmente ambas legs de cada transferencia.
- Mantener objetivo de cobertura del contrato de al menos 90%.

### Step 5: Sandbox lint and test gate

Ejecutar desde la raíz:

```bash
python .openspec-cli/lib/vault_lint.py contracts/
python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v
python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v --cov=contracts --cov-report=html --cov-fail-under=90
```

Corregir primero cualquier violación del sandbox, después fallos de `tests/test_cuenta_joven.py` y finalmente regresiones de la suite completa.

### Step 6: Documentation

- No actualizar estándares salvo que durante la implementación aparezca un patrón reutilizable y verificable para contadores persistentes mediante balances internos.
- Si aparece ese patrón, documentarlo únicamente después de que el lint y la suite completa estén verdes.

## 4. Orden de implementación

1. Step 0: crear `feature/KAN-12-backend` desde `develop`.
2. Step 1: crear scaffold, parámetros, constantes y eventos en `contracts/cuenta_joven.py`.
3. Step 2: implementar y probar helpers puros.
4. Step 4: escribir primero los tests fallantes agrupados por comportamiento.
5. Step 3: implementar `activation_hook`, `pre_posting_hook`, `post_posting_hook` y `scheduled_event_hook` hasta satisfacer los tests.
6. Step 5: ejecutar lint, suite completa y cobertura mínima.
7. Step 6: revisar si existe documentación reutilizable que deba actualizarse y preparar handoff para `os-commit`.

## 5. Checklist de pruebas

- [ ] `python .openspec-cli/lib/vault_lint.py contracts/` — cero violaciones.
- [ ] `python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v` — todos los tests verdes.
- [ ] `python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v --cov=contracts --cov-report=html --cov-fail-under=90` — cobertura >= 90%.
- [ ] Al menos 20 tests enfocados, incluyendo happy path, rechazo, borde y multi-denominación.
- [ ] Rejection paths verificados con `WRONG_DENOMINATION`, `INSUFFICIENT_FUNDS` y `AGAINST_TNC`.
- [ ] Las operaciones aprobadas actualizan el contador mediante `post_posting_hook`.
- [ ] El reinicio diario verifica ambas legs y el no-op cuando el acumulado es cero.
- [ ] Los intereses verifican tasa estándar, bonificada, condiciones AND y redondeo.
- [ ] Los tests existentes de los demás contratos no se rompen.
- [ ] No queda ningún skeleton, `TODO`, `*_code` ni stub en contrato o tests.

## 6. Referencia de tooling

| Purpose | Command |
| --- | --- |
| Build (SDK) | `pip install -r requirements.txt && pip install contracts_sdk/contracts_sdk/.` |
| Lint | `python .openspec-cli/lib/vault_lint.py contracts/` |
| Test | `python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v` |
| Coverage | `python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v --cov=contracts --cov-report=html --cov-fail-under=90` |
| Simulación opcional | `os-vault-simulate contracts/cuenta_joven.py <inicio> <fin> '<parametros_json>'` |

## 7. Catálogo de rechazos

| `RejectionReason` | Condición | Mensaje estable requerido |
| --- | --- | --- |
| `WRONG_DENOMINATION` | Cualquier posting usa una denominación distinta a la configurada en la cuenta | `Posting denomination <posting> does not match account denomination <account>.` |
| `INSUFFICIENT_FUNDS` | El efecto committed dejaría el saldo de `DEFAULT` por debajo de cero | `Insufficient funds: balance <balance> <denomination>, attempted <amount> <denomination> debit.` |
| `AGAINST_TNC` | El retiro supera el acumulado diario más el límite configurado | `Daily withdrawal limit exceeded: accumulated <accumulated> <denomination>, requested <requested> <denomination>, limit <limit> <denomination>.` |
| `AGAINST_TNC` | Importe de retiro cero o inválido | `Withdrawal amount must be greater than zero.` |
| `AGAINST_TNC` | Parámetros de activación inválidos o tasa bonificada inferior a la estándar | `Invalid account parameters.` |

Los rechazos se devuelven desde `pre_posting_hook` mediante `PrePostingHookResult(rejection=Rejection(...))`; no se debe lanzar una excepción de rechazo.

## 8. Dependencias

- `contracts_api` SDK local desde `contracts_sdk/contracts_sdk/`.
- `decimal.Decimal` y `ROUND_HALF_UP`.
- No usar otras librerías stdlib en el contrato; en particular no importar `os`, `sys`, `json`, `re`, `math`, `datetime` ni acceder a I/O o red.
- Tests con `pytest`, `MagicMock`, `datetime` y `ZoneInfo("UTC")` fuera del código del contrato.

## 9. Notas

- El acumulado es independiente por cuenta porque Vault mantiene los balances por `account_id`; también es independiente por denominación porque la `BalanceCoordinate` incluye `denomination`.
- El reset diario debe ser una transferencia balanceada desde `DAILY_WITHDRAWALS` hacia `DAILY_WITHDRAWALS_OFFSET`; no se debe asignar directamente a un diccionario ni depender de una variable global.
- Todos los postings internos usan `account_id=vault.account_id`, `asset=DEFAULT_ASSET` y `phase=Phase.COMMITTED`.
- El schedule mensual usa `EndOfMonthSchedule(day=28)` y el diario usa `ScheduleExpression` a medianoche; ambos parten de la fecha efectiva de activación.
- Los contratos no deben usar `client_transaction_id`; la trazabilidad va en `instruction_details`.
- El producto admite una moneda por cuenta, aunque la suite debe probar al menos GBP, USD y COP para comprobar que no se mezclan balances.
- No hay decisiones abiertas en esta sección; todas las reglas funcionales están fijadas en §2.1.

## 10. Checklist de verificación

- [ ] Solo imports de `contracts_api` y `decimal` en `contracts/cuenta_joven.py`.
- [ ] No hay estado global mutable, I/O, red, introspección ni `float` para dinero.
- [ ] No se usa `raise` para rechazos de negocio; se devuelve `PrePostingHookResult(rejection=...)`.
- [ ] `Phase` se lee desde `BalanceCoordinate`, nunca desde `Balance`.
- [ ] `CustomInstruction` usa `instruction_details`, nunca `client_transaction_id`.
- [ ] Los hooks tienen nombres correctos `*_hook`.
- [ ] El acumulado diario se actualiza en `post_posting_hook` y se reinicia en `scheduled_event_hook`.
- [ ] La elegibilidad bonificada requiere ambas condiciones configuradas.
- [ ] Se comprueban ambas legs de cada operación interna.
- [ ] Cobertura >= 90% y todos los tests pasan.
