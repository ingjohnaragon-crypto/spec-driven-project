# Vault Implementation Plan: KAN-13 Cuenta para pago de nómina

## Estimación de puntos de historia
```markdown
<!-- STORY_POINTS:8 -->
**8** — Nuevo producto de pasivo con cuatro hooks (activación con schedule mensual parametrizado, pre/post-posting con validación de saldo y denominación, evento mensual de comisión condicionado a la nómina), persistencia de la fecha de la última nómina en una dirección interna sin estado global, cobro parcial con protección de saldo y una suite de más de 20 pruebas más simulación. Sin intereses ni desembolsos, lo que lo mantiene por debajo de 13.
<!-- /STORY_POINTS -->
```

## 1. Resumen

Implementar un Smart Contract Vault (Contracts Language API 4.0) llamado `cuenta_nomina`,
de tipo `Tside.LIABILITY`, con una única denominación por cuenta y saldo inicial cero.

Comportamiento del producto:

- **`activation_hook`** — valida `dia_cobro_comision` y agenda el evento programado mensual
  `COBRO_COMISION_MANTENIMIENTO` en ese día. No genera postings (saldo inicial cero).
- **`pre_posting_hook`** — rechaza postings en denominación distinta a la de la cuenta
  (`RejectionReason.WRONG_DENOMINATION`) y rechaza cualquier instrucción cuyo efecto neto
  deje el saldo `Phase.COMMITTED` de `DEFAULT` por debajo de cero
  (`RejectionReason.INSUFFICIENT_FUNDS`). No hay descubierto. El límite en cero es inclusivo.
- **`post_posting_hook`** — si el lote aprobado contiene al menos un abono de nómina válido
  (crédito al `DEFAULT_ADDRESS`, marcador `instruction_details["tipo_transaccion"] == "NOMINA"`
  e importe abonado `>= importe_minimo_nomina`, en la denominación de la cuenta), registra la
  fecha de ese abono en la dirección interna `SEGUIMIENTO_NOMINA` mediante una
  `CustomInstruction` balanceada contra `SEGUIMIENTO_NOMINA_OFFSET`.
- **`scheduled_event_hook`** — evento `COBRO_COMISION_MANTENIMIENTO`: si hubo un abono de
  nómina en los últimos 31 días (comparando la fecha registrada con
  `hook_arguments.effective_datetime`), no cobra nada; si no, emite una `CustomInstruction`
  que debita `importe_comision_mantenimiento` de `DEFAULT` y acredita la dirección de
  ingreso interna `COMISION_INGRESO` (nunca el `DEFAULT` del cliente). El cobro nunca deja
  el saldo por debajo de cero: si el saldo disponible es menor que la comisión se cobra solo
  hasta dejar el saldo en cero y se omite el resto (documentado en el código).

Stack activo: `vault-smart-contracts`. Se aplican todas las restricciones del sandbox de
Vault (sin stdlib, sin I/O, sin `float`, sin estado global mutable) y la semántica de
`contracts_api` 4.0. Los nombres de hook son `activation_hook`, `pre_posting_hook`,
`post_posting_hook` y `scheduled_event_hook`; nunca `*_code`.

## 2. Contexto de arquitectura

- Active stack: `vault-smart-contracts`
- Golden reference: `contracts/fixed_term_deposit.py` (+ `tests/test_fixed_term_deposit.py`)
- Referencias adicionales:
  - `contracts/cuenta_joven.py` (+ tests) — patrón de contador persistente con dirección
    interna y dirección compensatoria (`OFFSET`), y schedules con `ScheduleExpression` /
    `EndOfMonthSchedule`.
  - `contracts/savings_product.py` — evento mensual único con `@requires` /
    `@fetch_account_data` por `event_type`.
  - `contracts/current_account.py` — validación de saldo con `_posting_net_effect`.
  - `ai-specs/specs/stacks/vault-core-api-gotchas.md` — hallazgos de deploy/simulate.
- Files:
  - `contracts/cuenta_nomina.py` — Smart Contract API 4.0 (crear)
  - `tests/test_cuenta_nomina.py` — unit tests con mocks de `contracts_api` (crear)
  - Tooling: `os-vault-lint`, `os-vault-test`, opcionalmente `os-vault-simulate`

## 2.1 Decisiones bloqueadas

| Tema | Decisión final | Rationale |
|---|---|---|
| Nombre de archivos | `contracts/cuenta_nomina.py` y `tests/test_cuenta_nomina.py` | snake_case; coincide con el nombre funcional del ticket |
| Idioma de identificadores | Identificadores, helpers, parámetros, constantes de dominio y mensajes en **español** (`denominacion`, `importe_comision_mantenimiento`, `_saldo_comprometido`, …). Se mantienen en inglés solo los nombres reservados de Vault/`contracts_api` y los hooks (`DEFAULT_ADDRESS`, `DEFAULT_ASSET`, `Phase`, `pre_posting_hook`, …) | Active Language = Español; el enriquecimiento del ticket fija nombres de parámetros y constantes en español |
| `tside` | `Tside.LIABILITY` | Cuenta de pasivo, paridad con los demás productos |
| Denominaciones | `supported_denominations = ["GBP", "USD", "EUR", "COP"]`; una sola por cuenta; default `"GBP"` | Paridad con los contratos existentes |
| Convención de importes | Todos los importes monetarios son `Decimal`; redondeo financiero explícito con `ROUND_HALF_UP` cuantizado a `Decimal("0.01")` | Restricción del sandbox y consistencia con los golden |
| Saldo inicial | Cero; `activation_hook` no emite ningún posting | AC explícito |
| Parámetro `denominacion` | `DenominationShape(permitted_denominations=supported_denominations)`, `ParameterLevel.INSTANCE`, `update_permission=ParameterUpdatePermission.USER_EDITABLE`, `default_value="GBP"` | API 4.0: INSTANCE exige `update_permission`; enriquecimiento del ticket |
| Parámetro `importe_comision_mantenimiento` | `NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01"))`, `ParameterLevel.TEMPLATE`, `default_value=Decimal("5.00")` | Configurable a nivel producto; TEMPLATE nunca declara `update_permission` |
| Parámetro `dia_cobro_comision` | `NumberShape(min_value=Decimal("1"), max_value=Decimal("28"), step=Decimal("1"))`, `ParameterLevel.TEMPLATE`, `default_value=Decimal("1")` | Limitar a 28 evita meses cortos; parámetro de producto |
| Parámetro `importe_minimo_nomina` | `NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01"))`, `ParameterLevel.TEMPLATE`, `default_value=Decimal("100.00")` | Umbral de negocio del producto |
| Parámetro derivado `fecha_ultima_nomina` | **No se implementa.** El estado real vive en la dirección `SEGUIMIENTO_NOMINA`; ningún AC exige exponer la fecha por parámetro derivado | Reduce alcance y superficie de hooks; el ticket lo marca "(Opcional)" |
| Persistencia de la fecha de última nómina | Se codifica como **número de días desde una época fija** (algoritmo Gregoriano puro `days_from_civil`) en el balance neto de la dirección interna `SEGUIMIENTO_NOMINA`, ajustado mediante `CustomInstruction` balanceada contra `SEGUIMIENTO_NOMINA_OFFSET` | Los balances persisten entre hooks; `instruction_details` no es legible con el fetcher `live_balances`. Codificar la fecha como entero permite una resta exacta de días y es determinista y testeable. Es la "Alternativa aceptada" del ticket adaptada al fetcher de balances |
| Época de referencia | `1970-01-01` = día 0 (el algoritmo `days_from_civil` resta `719468`) | Constante y arbitraria; solo importa la diferencia entre dos días |
| Detección de nómina | En `post_posting_hook`, un `PostingInstruction` es nómina si `instruction_details.get("tipo_transaccion") == "NOMINA"` **y** su crédito neto committed a `DEFAULT_ADDRESS` en la denominación de la cuenta es `>= importe_minimo_nomina`. Si el lote tiene ≥ 1 nómina válida, se toma el crédito máximo entre ellas para el registro | Definición precisa y verificable; el marcado solo alimenta la comisión, nunca rechaza |
| Marcador y clave | Constantes de módulo `MARCADOR_NOMINA = "NOMINA"` y `CLAVE_TIPO_TRANSACCION = "tipo_transaccion"` | Evita literales dispersos |
| Efecto de un abono no-nómina | Se acepta con normalidad en `pre_posting_hook` (solo importan saldo y denominación); `post_posting_hook` no actualiza `SEGUIMIENTO_NOMINA` | AC explícito |
| Regla de saldo negativo | `pre_posting_hook` rechaza si `saldo_committed_DEFAULT + efecto_neto_committed_DEFAULT < Decimal("0")` (estrictamente menor; el débito exacto a cero se acepta) | AC: "límite inclusivo en cero" |
| Ventana de nómina reciente | `VENTANA_NOMINA_DIAS = 31`; NO se cobra comisión si `SEGUIMIENTO_NOMINA > 0` **y** `dia_epoca_hoy - SEGUIMIENTO_NOMINA <= 31` (inclusive) | AC: "en los últimos 31 días", comparado contra `effective_datetime` |
| Sin nómina registrada | `SEGUIMIENTO_NOMINA == 0` (nunca hubo abono de nómina) ⇒ se cobra comisión | AC: "si no (…) o nunca" |
| Cobro con saldo insuficiente | `comision_efectiva = min(importe_comision_mantenimiento, max(saldo_committed_DEFAULT, Decimal("0")))`. Si `comision_efectiva <= 0` no se emite ninguna `CustomInstruction`. El resto no cobrado se omite (MVP) y se documenta en el código con un comentario | AC: "el cobro nunca puede dejar saldo negativo; se cobra solo hasta dejar el saldo en cero y se omite el resto" |
| Dirección de ingreso de la comisión | `COMISION_INGRESO = "COMISION_INGRESO"`; el crédito de la comisión siempre va a esta dirección interna, nunca a `DEFAULT` del cliente | AC explícito + stack standard "never credit DEFAULT for income" |
| Schedule del evento mensual | `ScheduledEvent(start_datetime=hook_arguments.effective_datetime, expression=ScheduleExpression(day=str(int(dia_cobro_comision)), hour="0", minute="0", second="0"))` | `ScheduleExpression(day=N)` es un cron mensual inequívoco para 1..28; mismo patrón que `cuenta_joven.py`. Evita las particularidades de recorte de `EndOfMonthSchedule` |
| `event_types` | `[SmartContractEventType(name=EVENTO_COMISION)]` sin `scheduler_tag_ids` | Un tag referenciado inexistente hace fallar `POST /v1/accounts` con `TAG_NOT_FOUND` (ver comentario en `savings_product.py`) |
| Validación en `activation_hook` | Si `dia_cobro_comision` no está en `[1, 28]`, `raise ValueError("dia_cobro_comision debe estar entre 1 y 28.")` | Igual que la validación de `maturity_date` en el golden; el `NumberShape` ya lo acota pero se valida por robustez |
| Decoradores de datos | `activation_hook`: `@requires(parameters=True)`. `pre_posting_hook`: `@requires(parameters=True)` + `@fetch_account_data(balances=["live_balances"])`. `post_posting_hook`: `@requires(parameters=True)` + `@fetch_account_data(balances=["live_balances"])`. `scheduled_event_hook`: `@requires(event_type="COBRO_COMISION_MANTENIMIENTO", parameters=True)` + `@fetch_account_data(event_type="COBRO_COMISION_MANTENIMIENTO", balances=["live_balances"])` | Unión de lo que cada hook y sus helpers tocan; exigido por `vault_lint.py` y `os-vault-simulate` |
| Lista de fetchers | `data_fetchers = [BalancesObservationFetcher(fetcher_id="live_balances", at=DefinedDateTime.LIVE)]` | Nombre `data_fetchers` (no `balance_observation_fetchers`) |
| Traceabilidad | Todo `CustomInstruction` lleva `instruction_details` con `description`, `hook_execution_id` (str) y `event_type` cuando aplique; nunca `client_transaction_id` | API 4.0 |
| Rechazos | Se devuelven vía `PrePostingHookResult(rejection=Rejection(...))`; nunca `raise Rejected` | API 4.0 |
| `derived_parameter_hook` | No se implementa | Ningún parámetro `derived=True` |

## 3. Pasos de implementación

### Step 0: Feature branch

- Branch: `feature/KAN-13-backend` (creada por `os-develop` desde `develop`).

### Step 1: Contract scaffold

Crear `contracts/cuenta_nomina.py`:

- Imports directos desde `contracts_api` (sin `try/except`) — al menos:
  `ParameterUpdatePermission, ActivationHookArguments, ActivationHookResult,
  BalanceCoordinate, BalanceDefaultDict, BalancesObservationFetcher, CustomInstruction,
  DefinedDateTime, DenominationShape, NumberShape, Parameter, ParameterLevel, Phase,
  Posting, PostingInstructionsDirective, PostPostingHookArguments, PostPostingHookResult,
  PrePostingHookArguments, PrePostingHookResult, Rejection, RejectionReason,
  ScheduledEvent, ScheduleExpression, ScheduledEventHookArguments, ScheduledEventHookResult,
  SmartContractEventType, Tside, fetch_account_data, requires`.
- `from decimal import Decimal, ROUND_HALF_UP`.
- Metadata: `api = "4.0.0"`, `version = "1.0.0"`, `display_name = "Cuenta de nómina"`,
  `summary`, `description`, `tside = Tside.LIABILITY`,
  `supported_denominations = ["GBP", "USD", "EUR", "COP"]`.
- Constantes de módulo:
  - `DEFAULT_ADDRESS = "DEFAULT"`
  - `DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"`
  - `COMISION_INGRESO = "COMISION_INGRESO"`
  - `SEGUIMIENTO_NOMINA = "SEGUIMIENTO_NOMINA"`
  - `SEGUIMIENTO_NOMINA_OFFSET = "SEGUIMIENTO_NOMINA_OFFSET"`
  - `MARCADOR_NOMINA = "NOMINA"`
  - `CLAVE_TIPO_TRANSACCION = "tipo_transaccion"`
  - `EVENTO_COMISION = "COBRO_COMISION_MANTENIMIENTO"`
  - `VENTANA_NOMINA_DIAS = 31`
- `parameters = [...]` completos según §2.1 (`denominacion`, `importe_comision_mantenimiento`,
  `dia_cobro_comision`, `importe_minimo_nomina`).
- `event_types = [SmartContractEventType(name=EVENTO_COMISION)]`, `event_types_groups = []`.
- `data_fetchers = [BalancesObservationFetcher(fetcher_id="live_balances", at=DefinedDateTime.LIVE)]`.

### Step 2: Pure helper functions

Helpers tipados, sin efectos secundarios, sin `float`, sin stdlib, sin introspección:

- `_saldo_comprometido(balances: BalanceDefaultDict, direccion: str, denominacion: str) -> Decimal`
  — construir `BalanceCoordinate(account_address=direccion, asset=DEFAULT_ASSET,
  denomination=denominacion, phase=Phase.COMMITTED)` y devolver `balances[key].net`.
- `_efecto_neto_committed(posting_instructions, direccion: str, denominacion: str) -> Decimal`
  — recorrer `posting.balances().items()`; sumar `balance.net` solo cuando
  `coord.phase == Phase.COMMITTED and coord.account_address == direccion and
  coord.denomination == denominacion`. La fase se lee de la **clave**.
- `_dias_desde_epoca(anio: int, mes: int, dia: int) -> int` — algoritmo Gregoriano puro
  (`days_from_civil` de Howard Hinnant), solo aritmética entera:
  ```
  a   = anio - (1 if mes <= 2 else 0)
  era = (a if a >= 0 else a - 399) // 400
  yoe = a - era * 400
  doy = (153 * (mes + (-3 if mes > 2 else 9)) + 2) // 5 + dia - 1
  doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
  return era * 146097 + doe - 719468
  ```
- `_dia_epoca_de(dt) -> int` — `return _dias_desde_epoca(dt.year, dt.month, dt.day)`.
- `_quantizar(importe: Decimal) -> Decimal` — `importe.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.
- `_credito_nomina_del_lote(posting_instructions, denominacion: str, importe_minimo: Decimal) -> Decimal`
  — para cada `PostingInstruction` con
  `getattr`-free acceso `pi.instruction_details.get(CLAVE_TIPO_TRANSACCION) == MARCADOR_NOMINA`,
  calcular su crédito neto committed a `DEFAULT_ADDRESS` en `denominacion`
  (usar `_efecto_neto_committed([pi], DEFAULT_ADDRESS, denominacion)`, quedarse con el valor
  si es `> 0`); devolver el máximo de los créditos que además sean `>= importe_minimo`, o
  `Decimal("0")` si no hay ninguno.
  Nota: `instruction_details` es un `dict`; `.get(...)` está permitido (no es introspección).
- `_transferencia_interna(importe, denominacion, direccion_debito, direccion_credito,
  descripcion, hook_id, account_id, event_type=None) -> CustomInstruction`
  — dos `Posting` balanceados (`credit=False` en `direccion_debito`, `credit=True` en
  `direccion_credito`), `asset=DEFAULT_ASSET`, `phase=Phase.COMMITTED`,
  `account_id=account_id`; `instruction_details` con `description`, `hook_execution_id`
  y `event_type` si se pasa.
- `_schedule_comision(effective_datetime, dia_cobro: int) -> dict`
  — `{EVENTO_COMISION: ScheduledEvent(start_datetime=effective_datetime,
  expression=ScheduleExpression(day=str(dia_cobro), hour="0", minute="0", second="0"))}`.
- `_parametro(vault, nombre)` — `return vault.get_parameter_timeseries(name=nombre).latest()`.

### Step 3: Hook implementation

#### `activation_hook(vault, hook_arguments: ActivationHookArguments) -> ActivationHookResult`
`@requires(parameters=True)`
- Leer `dia_cobro_comision` (`Decimal`), convertir a `int`.
- Si no está en `[1, 28]` → `raise ValueError("dia_cobro_comision debe estar entre 1 y 28.")`.
- Devolver `ActivationHookResult(scheduled_events_return_value=_schedule_comision(
  hook_arguments.effective_datetime, dia_cobro))`.
- No emite postings.

#### `pre_posting_hook(vault, hook_arguments: PrePostingHookArguments) -> PrePostingHookResult`
`@requires(parameters=True)` + `@fetch_account_data(balances=["live_balances"])`
- Leer `denominacion`; `balances = vault.get_balances_observation(fetcher_id="live_balances").balances`.
- Para cada posting: si `posting.denomination != denominacion` →
  `PrePostingHookResult(rejection=Rejection(message=..., reason_code=RejectionReason.WRONG_DENOMINATION))`.
- `saldo = _saldo_comprometido(balances, DEFAULT_ADDRESS, denominacion)`.
- `efecto = _efecto_neto_committed(hook_arguments.posting_instructions, DEFAULT_ADDRESS, denominacion)`.
- Si `saldo + efecto < Decimal("0")` →
  `Rejection(..., reason_code=RejectionReason.INSUFFICIENT_FUNDS)` con mensaje que incluya
  saldo y débito intentado.
- En cualquier otro caso → `PrePostingHookResult()`.

#### `post_posting_hook(vault, hook_arguments: PostPostingHookArguments) -> PostPostingHookResult`
`@requires(parameters=True)` + `@fetch_account_data(balances=["live_balances"])`
- Leer `denominacion` e `importe_minimo_nomina`.
- `credito = _credito_nomina_del_lote(hook_arguments.posting_instructions, denominacion, importe_minimo_nomina)`.
- Si `credito <= Decimal("0")` → `PostPostingHookResult(posting_instructions_directives=[])`.
- `hoy = _dia_epoca_de(hook_arguments.effective_datetime)` (entero).
- `balances = vault.get_balances_observation(fetcher_id="live_balances").balances`;
  `registro_actual = _saldo_comprometido(balances, SEGUIMIENTO_NOMINA, denominacion)`.
- `delta = Decimal(str(hoy)) - registro_actual`.
- Si `delta == Decimal("0")` → directives vacías.
- Si `delta > Decimal("0")` → `CustomInstruction` que **acredita** `SEGUIMIENTO_NOMINA` y
  **debita** `SEGUIMIENTO_NOMINA_OFFSET` por `delta`.
- Si `delta < Decimal("0")` → inverso (acredita `OFFSET`, debita `SEGUIMIENTO_NOMINA`) por `abs(delta)`.
- Envolver en `PostingInstructionsDirective(posting_instructions=[instruccion])`.
- `instruction_details` incluye `"dia_epoca_nomina": str(hoy)` para trazabilidad.

#### `scheduled_event_hook(vault, hook_arguments: ScheduledEventHookArguments) -> ScheduledEventHookResult`
`@requires(event_type="COBRO_COMISION_MANTENIMIENTO", parameters=True)`
+ `@fetch_account_data(event_type="COBRO_COMISION_MANTENIMIENTO", balances=["live_balances"])`
- Si `hook_arguments.event_type != EVENTO_COMISION` →
  `ScheduledEventHookResult(posting_instructions_directives=[], update_account_event_type_directives=[])`.
- Leer `denominacion` e `importe_comision_mantenimiento`.
- `balances = ...`; `saldo = _saldo_comprometido(balances, DEFAULT_ADDRESS, denominacion)`;
  `registro = _saldo_comprometido(balances, SEGUIMIENTO_NOMINA, denominacion)`.
- `hoy = _dia_epoca_de(hook_arguments.effective_datetime)`.
- **Nómina reciente**: si `registro > Decimal("0")` y
  `hoy - int(registro) <= VENTANA_NOMINA_DIAS` → directives vacías (no se cobra).
- Si no: `comision_efectiva = min(importe_comision_mantenimiento, max(saldo, Decimal("0")))`.
  - Si `comision_efectiva <= Decimal("0")` → directives vacías
    (comentario en código: "MVP: saldo insuficiente, no se cobra y se omite el resto").
  - Si no → `CustomInstruction` que **debita** `DEFAULT_ADDRESS` y **acredita**
    `COMISION_INGRESO` por `comision_efectiva` (`_quantizar`), con `event_type=EVENTO_COMISION`
    en `instruction_details`.
    Comentario en código si `comision_efectiva < importe_comision_mantenimiento`:
    "MVP: cobro parcial hasta dejar el saldo en cero; el resto se omite".
- `update_account_event_type_directives=[]` en todos los returns.

### Step 4: Unit tests (TDD order)

Crear `tests/test_cuenta_nomina.py` copiando la estructura de
`tests/test_fixed_term_deposit.py`: `MagicMock` para vault, argumentos tipados,
`ZoneInfo("UTC")`, `BalanceDefaultDict` con `BalanceCoordinate`, clases agrupadas.

Fixtures:
- `make_balance_dict(default=Decimal("0"), seguimiento=Decimal("0"), denomination="GBP")`.
- `make_vault(default_balance, seguimiento_balance, denomination, importe_comision,
  dia_cobro, importe_minimo_nomina)` con `get_parameter_timeseries.side_effect` sobre un
  mapa de parámetros y `get_balances_observation.return_value.balances`.
- `make_posting(amount, credit=True, denomination="GBP", instruction_details=None)`
  — `MagicMock` con `.denomination`, `.instruction_details` (dict) y `.balances()` sobre
  `DEFAULT` (net = ±amount).
- `make_pre_posting_args(*postings)`, `make_post_posting_args(*postings)`
  (`client_transactions={}`), `make_scheduled_args(event_type, dt)`,
  `ActivationHookArguments(effective_datetime=...)`.

Casos explícitos (≥ 28):

**`TestActivationHook`**
1. `test_agenda_evento_comision_mensual` — `EVENTO_COMISION` en `scheduled_events_return_value`.
2. `test_activacion_no_emite_postings` — resultado sin directivas de posting.
3. `test_schedule_usa_dia_cobro_comision` — con `dia_cobro=5`, la `ScheduleExpression.day == "5"`.
4. `test_activacion_rechaza_dia_fuera_de_rango_bajo` — `dia_cobro=0` → `ValueError`.
5. `test_activacion_rechaza_dia_fuera_de_rango_alto` — `dia_cobro=29` → `ValueError`.

**`TestPrePostingDenominacion`**
6. `test_rechaza_denominacion_distinta` — posting USD en cuenta GBP → `WRONG_DENOMINATION`.
7. `test_acepta_credito_misma_denominacion`.
8. `test_acepta_deposito_usd_en_cuenta_usd`.
9. `test_acepta_deposito_cop_en_cuenta_cop`.

**`TestPrePostingSaldo`**
10. `test_rechaza_debito_mayor_que_saldo` — `INSUFFICIENT_FUNDS`.
11. `test_acepta_debito_exacto_a_cero` — débito == saldo → aceptado (inclusive).
12. `test_acepta_debito_menor_que_saldo`.
13. `test_acepta_credito_con_saldo_cero` — un abono nunca se rechaza por saldo.
14. `test_acepta_posting_importe_cero`.

**`TestPostPostingNomina`**
15. `test_nomina_valida_registra_fecha` — crédito con marcador e importe ≥ mínimo →
    `CustomInstruction`; ambas legs (`SEGUIMIENTO_NOMINA` crédito, `OFFSET` débito);
    `delta` correcto contra `SEGUIMIENTO_NOMINA` inicial en cero.
16. `test_nomina_bajo_minimo_no_registra` — marcador presente pero importe < mínimo →
    sin directivas.
17. `test_credito_sin_marcador_no_registra`.
18. `test_debito_no_registra` — posting saliente → sin directivas.
19. `test_nomina_marcador_pero_denominacion_distinta_no_registra`.
20. `test_registro_mueve_a_hoy_no_acumula` — `SEGUIMIENTO_NOMINA` ya tiene un valor previo;
    `delta = hoy_epoca - previo`, no acumulativo.
21. `test_instruction_details_incluye_hook_execution_id_y_dia_epoca`.
22. `test_varias_nominas_en_lote_toma_el_credito_maximo`.

**`TestScheduledComision`**
23. `test_no_cobra_si_nomina_dentro_de_31_dias` — `SEGUIMIENTO_NOMINA` = `hoy - 10` →
    sin directivas.
24. `test_no_cobra_si_nomina_exactamente_31_dias` — inclusive → sin directivas.
25. `test_cobra_si_nomina_hace_32_dias` — `CustomInstruction`; debita `DEFAULT`,
    acredita `COMISION_INGRESO`; importe == `importe_comision_mantenimiento`; ambas legs.
26. `test_cobra_si_nunca_hubo_nomina` — `SEGUIMIENTO_NOMINA` == 0 → cobra.
27. `test_cobro_parcial_si_saldo_insuficiente` — `saldo=Decimal("2.00")`,
    `comision=Decimal("5.00")` → importe cobrado == `Decimal("2.00")`, nunca negativo.
28. `test_no_cobra_si_saldo_cero` — sin directivas.
29. `test_comision_nunca_acredita_default_del_cliente` — la leg de crédito tiene
    `account_address == "COMISION_INGRESO"`.
30. `test_event_type_desconocido_es_noop`.

**`TestMetadata`**
31. `test_supported_denominations`.
32. `test_tside_liability`.

Cada `CustomInstruction` verifica importe, denominación, dirección, `credit`/`debit` e
`instruction_details`, y **ambas legs** de cada transferencia.

### Step 5: Sandbox lint and test gate

```bash
python .openspec-cli/lib/vault_lint.py contracts/
python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v
python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v --cov=contracts --cov-report=html --cov-fail-under=90
```

Corregir primero violaciones del sandbox, luego fallos de `tests/test_cuenta_nomina.py`,
finalmente regresiones de la suite completa. Antes del PR:

```bash
os-vault-simulate contracts/cuenta_nomina.py
```

(requiere VPN corporativa; debe cargar sin errores de data requirements).

### Step 6: Documentation

- Actualizar estándares solo si aparece un patrón reutilizable verificado (p. ej. codificar
  una fecha como número de días en un balance interno). Documentar únicamente tras lint +
  suite completa en verde.

## 4. Orden de implementación

1. Step 0 — crear `feature/KAN-13-backend` desde `develop`.
2. Step 1 — scaffold, parámetros, constantes y `event_types` en `contracts/cuenta_nomina.py`.
3. Step 2 — helpers puros (incluido `_dias_desde_epoca`).
4. Step 4 — escribir primero los tests fallantes agrupados por hook.
5. Step 3 — implementar `activation_hook`, `pre_posting_hook`, `post_posting_hook`,
   `scheduled_event_hook` hasta pasar los tests.
6. Step 5 — lint, suite completa, cobertura ≥ 90% y `os-vault-simulate`.
7. Step 6 — revisar documentación reutilizable y preparar handoff para `os-commit`.

## 5. Checklist de pruebas

- [ ] `python .openspec-cli/lib/vault_lint.py contracts/` — cero violaciones.
- [ ] `python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v` — todos los tests verdes.
- [ ] `python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v --cov=contracts --cov-report=html --cov-fail-under=90` — cobertura ≥ 90%.
- [ ] ≥ 20 tests enfocados (happy, rechazo, borde, multi-denominación).
- [ ] Rejection paths verificados con `WRONG_DENOMINATION` e `INSUFFICIENT_FUNDS`.
- [ ] `activation_hook` agenda `COBRO_COMISION_MANTENIMIENTO` en `dia_cobro_comision` y no emite postings.
- [ ] `post_posting_hook` registra la fecha solo con nómina válida y verifica ambas legs.
- [ ] Evento mensual: no cobra con nómina en los últimos 31 días; cobra en caso contrario.
- [ ] El cobro nunca deja el saldo por debajo de cero (cobro parcial verificado).
- [ ] La comisión acredita `COMISION_INGRESO`, nunca el `DEFAULT` del cliente.
- [ ] Los tests existentes de los demás contratos no se rompen.
- [ ] No queda ningún skeleton, `TODO`, `*_code` ni stub.
- [ ] `os-vault-simulate contracts/cuenta_nomina.py` corre sin errores de carga ni de data requirements.

## 6. Referencia de tooling

| Purpose | Command |
| --- | --- |
| Build (SDK) | `pip install -r requirements.txt && pip install contracts_sdk/contracts_sdk/.` |
| Lint | `python .openspec-cli/lib/vault_lint.py contracts/` |
| Test | `python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v` |
| Coverage | `python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v --cov=contracts --cov-report=html --cov-fail-under=90` |
| Simulación | `os-vault-simulate contracts/cuenta_nomina.py` |

## 7. Catálogo de rechazos

| `RejectionReason` | Condición | Mensaje estable requerido |
| --- | --- | --- |
| `WRONG_DENOMINATION` | Cualquier posting usa una denominación distinta a la configurada en la cuenta | `Posting denomination <posting> does not match account denomination <account>.` |
| `INSUFFICIENT_FUNDS` | El efecto neto committed dejaría el saldo de `DEFAULT` por debajo de cero (`< 0`, estricto) | `Insufficient funds: balance <saldo> <denominacion>, attempted <importe> <denominacion> debit.` |

Los rechazos se devuelven desde `pre_posting_hook` con `PrePostingHookResult(rejection=Rejection(...))`.
No hay rechazos en `post_posting_hook` ni en `scheduled_event_hook` (el marcado de nómina
nunca rechaza; el cobro parcial nunca produce saldo negativo).

## 8. Dependencias

- `contracts_api` SDK local desde `contracts_sdk/contracts_sdk/`.
- `decimal.Decimal` y `ROUND_HALF_UP`.
- Sin otras librerías stdlib en el contrato (`os`, `sys`, `json`, `re`, `math`, `datetime`),
  sin I/O ni red.
- Tests con `pytest`, `MagicMock`, `datetime` y `ZoneInfo("UTC")` fuera del código del contrato.

## 9. Notas

- El registro de la última nómina es independiente por cuenta (`account_id`) y por
  denominación (la `BalanceCoordinate` incluye `denomination`).
- `SEGUIMIENTO_NOMINA` guarda un **entero** (días desde 1970-01-01); el `OFFSET` es su
  contrapartida contable. La resta `hoy - registro` es un número exacto de días.
- Todos los postings internos usan `account_id=vault.account_id`, `asset=DEFAULT_ASSET`,
  `phase=Phase.COMMITTED`.
- El schedule mensual usa `ScheduleExpression(day=str(dia_cobro_comision))` y parte de la
  fecha efectiva de activación; si la activación cae en `dia_cobro_comision` la primera
  ejecución puede ser el mes siguiente (comportamiento aceptado para el MVP).
- Una moneda por cuenta; la suite prueba GBP, USD y COP para comprobar que los balances no
  se mezclan.
- `instruction_details` lleva la trazabilidad; nunca `client_transaction_id`.
- No hay decisiones abiertas: todas las reglas funcionales están fijadas en §2.1.

## 10. Checklist de verificación

- [ ] Solo imports de `contracts_api` y `decimal` en `contracts/cuenta_nomina.py`.
- [ ] Sin estado global mutable, I/O, red, introspección (`getattr`/`type`/`isinstance`) ni `float`.
- [ ] No se usa `raise` para rechazos de negocio; se devuelve `PrePostingHookResult(rejection=...)`.
- [ ] `Phase` se lee desde `BalanceCoordinate`, nunca desde `Balance`.
- [ ] `CustomInstruction` usa `instruction_details`, nunca `client_transaction_id`.
- [ ] Nombres de hook correctos (`activation_hook`, `pre_posting_hook`, `post_posting_hook`, `scheduled_event_hook`).
- [ ] Cada hook que lee parámetros/balances declara `@requires` / `@fetch_account_data`; lista `data_fetchers`.
- [ ] Todo parámetro INSTANCE declara `update_permission`; TEMPLATE nunca lo declara.
- [ ] Se comprueban ambas legs de cada operación interna.
- [ ] Cobertura ≥ 90% y todos los tests pasan; `os-vault-simulate` limpio.
