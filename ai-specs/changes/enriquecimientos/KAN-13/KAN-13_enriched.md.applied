# Ticket enriquecido: KAN-13 — Crear cuenta para pago de nómina

## Descripción original
<!-- jira-skip -->
Como responsable de producto de banca de nómina, quiero un producto de cuenta para el pago de nómina en Vault, para que las empresas puedan abonar los salarios de sus empleados y estos dispongan del dinero de forma inmediata y sin comisiones.

Hoy no existe un producto específico para domiciliar la nómina; los abonos de salario se tratan como transferencias genéricas sin reglas propias. El negocio necesita una cuenta que identifique el abono de nómina, no cobre comisión de mantenimiento mientras la nómina esté activa y evite descubiertos no autorizados.

Criterios originales: cuenta con denominación única y saldo inicial cero; acepta abonos marcados como nómina y rechaza cualquier posting que deje el saldo negativo; sin comisión si hubo al menos un abono de nómina en el último mes, en caso contrario comisión mensual configurada; comisión cobrada por evento programado mensual; parámetros de negocio configurables; `os-vault-test` y cobertura ≥ 90% en verde; respeto del sandbox Python de Vault.
<!-- /jira-skip -->

## Descripción mejorada
Se implementará un Smart Contract Vault (API 4.0) `cuenta_nomina` de tipo `Tside.LIABILITY`, con una única denominación por cuenta. El `activation_hook` fija la denominación efectiva y agenda el evento programado mensual `COBRO_COMISION_MANTENIMIENTO` en el día configurado (`dia_cobro_comision`), sin generar postings en la activación (saldo inicial cero).

El `pre_posting_hook` valida cada posting entrante: rechaza denominación distinta a la de la cuenta (`RejectionReason.WRONG_DENOMINATION`) y rechaza cualquier instrucción cuyo efecto neto deje el saldo COMMITTED por debajo de cero (`RejectionReason.INSUFFICIENT_FUNDS`) — no hay descubierto. Los abonos entrantes se consideran nómina cuando `instruction_details` contiene el marcador `tipo_transaccion == "NOMINA"` y el importe abonado es ≥ `importe_minimo_nomina`; ese marcado solo alimenta la lógica de comisión, no sirve para rechazar (un abono no-nómina que respeta saldo y denominación se acepta con normalidad).

El `post_posting_hook` detecta si en el lote hay al menos un abono de nómina válido (crédito al `DEFAULT_ADDRESS`, marcador de nómina, importe ≥ mínimo) y, en ese caso, registra la fecha del último abono. Como el sandbox no permite estado global mutable, la fecha se persiste mediante una `CustomInstruction` sobre una dirección interna de tracking (`SEGUIMIENTO_NOMINA`, importe simbólico) con el timestamp en `instruction_details`, de forma que el schedule pueda reconstruir la fecha leyendo esa dirección. Alternativa aceptada: parámetro `derived=True` calculado desde el histórico de postings.

El `scheduled_event_hook` corre mensualmente para `COBRO_COMISION_MANTENIMIENTO`: si hubo al menos un abono de nómina en los últimos 31 días (comparando la fecha registrada con `hook_arguments.effective_datetime`), no cobra nada; si no, emite una `CustomInstruction` que debita `importe_comision_mantenimiento` del `DEFAULT_ADDRESS` del cliente y acredita la dirección de ingreso interna `COMISION_INGRESO` (nunca se acredita al `DEFAULT` del cliente). El cobro nunca puede dejar saldo negativo: para el MVP, si el saldo disponible es menor que la comisión se cobra solo hasta dejar el saldo en cero y se omite el resto (documentar en el código).

## Criterios de aceptación
- [ ] La cuenta se abre con una única denominación (parámetro `denominacion`) y saldo inicial cero (sin postings en activación).
- [ ] El `activation_hook` agenda el evento mensual `COBRO_COMISION_MANTENIMIENTO` en el día `dia_cobro_comision`.
- [ ] `pre_posting_hook` rechaza postings con denominación distinta a la de la cuenta.
- [ ] `pre_posting_hook` rechaza cualquier instrucción cuyo efecto neto deje el saldo COMMITTED por debajo de cero (sin descubierto).
- [ ] Un abono entrante con `instruction_details["tipo_transaccion"] == "NOMINA"` e importe ≥ `importe_minimo_nomina` se acepta y queda registrado como última nómina.
- [ ] `post_posting_hook` actualiza la fecha del último abono de nómina cuando el lote contiene un abono de nómina válido.
- [ ] En el evento mensual, si hubo abono de nómina en los últimos 31 días, NO se cobra comisión de mantenimiento.
- [ ] En el evento mensual, si NO hubo abono de nómina en ese periodo, se debita `importe_comision_mantenimiento` y se acredita la dirección de ingreso interna (nunca el `DEFAULT` del cliente).
- [ ] El cobro de comisión nunca deja el saldo del cliente por debajo de cero.
- [ ] Todos los parámetros de negocio (`denominacion`, `importe_comision_mantenimiento`, `dia_cobro_comision`, `importe_minimo_nomina`) son configurables por `Parameter`.
- [ ] `os-vault-test` pasa (todos los tests en verde, incluido `vault_lint`).
- [ ] `os-vault-test --coverage` pasa (≥ 90%).
- [ ] `os-vault-simulate contracts/cuenta_nomina.py` corre sin errores de carga ni de data requirements.
- [ ] El contrato respeta el sandbox Python de Vault (sin stdlib, sin I/O, sin float, sin estado global mutable).

## Campos, hooks y tipos
- **Hooks:**
  - `activation_hook` — fija denominación efectiva y agenda `COBRO_COMISION_MANTENIMIENTO` (mensual; `EndOfMonthSchedule` o schedule con `day=dia_cobro_comision`). `@requires(parameters=True)`.
  - `pre_posting_hook` — valida denominación y bloquea saldo negativo. `@requires(parameters=True)` + `@fetch_account_data(balances=["live_balances"])`.
  - `post_posting_hook` — registra fecha del último abono de nómina si el lote contiene uno válido. `@requires(parameters=True)` + `@fetch_account_data(balances=["live_balances"])` si lee balances/tracking.
  - `scheduled_event_hook` — evento `COBRO_COMISION_MANTENIMIENTO`: cobra comisión si no hubo nómina reciente. `@requires(event_type="COBRO_COMISION_MANTENIMIENTO", parameters=True)` + `@fetch_account_data(event_type="COBRO_COMISION_MANTENIMIENTO", balances=["live_balances"])`.
- **Parámetros:**
  - `denominacion` — `DenominationShape(permitted_denominations=supported_denominations)`, `ParameterLevel.INSTANCE`, `update_permission=ParameterUpdatePermission.USER_EDITABLE`, `default_value="GBP"`.
  - `importe_comision_mantenimiento` — `NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01"))`, `ParameterLevel.TEMPLATE`, `default_value=Decimal("5.00")`.
  - `dia_cobro_comision` — `NumberShape(min_value=Decimal("1"), max_value=Decimal("28"), step=Decimal("1"))`, `ParameterLevel.TEMPLATE`, `default_value=Decimal("1")` (limitar a 28 para evitar meses cortos).
  - `importe_minimo_nomina` — `NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01"))`, `ParameterLevel.TEMPLATE`, `default_value=Decimal("100.00")`.
  - (Opcional) `fecha_ultima_nomina` — `Parameter(..., derived=True)` sin `update_permission`, expuesto vía `derived_parameter_hook` para inspección; el estado real vive en la dirección de tracking.
- **Tipos `contracts_api`:** `Parameter`, `ParameterLevel`, `ParameterUpdatePermission`, `NumberShape`, `DenominationShape`, `Tside`, `Phase`, `BalanceCoordinate`, `BalanceDefaultDict`, `BalancesObservationFetcher`, `DefinedDateTime`, `Posting`, `CustomInstruction`, `PostingInstructionsDirective`, `Rejection`, `RejectionReason`, `ScheduledEvent`, `SmartContractEventType`, `EndOfMonthSchedule`, `ActivationHookArguments`/`Result`, `PrePostingHookArguments`/`Result`, `PostPostingHookArguments`/`Result`, `ScheduledEventHookArguments`/`Result`, `requires`, `fetch_account_data`.
- **Constantes de módulo:** `DEFAULT_ADDRESS = "DEFAULT"`, `DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"`, `COMISION_INGRESO = "COMISION_INGRESO"`, `SEGUIMIENTO_NOMINA = "SEGUIMIENTO_NOMINA"`, `MARCADOR_NOMINA = "NOMINA"`.
- **Datos:** `data_fetchers = [BalancesObservationFetcher(fetcher_id="live_balances", at=DefinedDateTime.LIVE)]`. Fechas siempre vía `hook_arguments.effective_datetime` (ZoneInfo-aware). Dinero siempre `Decimal`.

## Archivos a crear o modificar
| Archivo | Capa | Acción |
|---|---|---|
| `contracts/cuenta_nomina.py` | Contract | Crear |
| `tests/test_cuenta_nomina.py` | Tests | Crear |

## Casos de prueba unitarios
- **Activación:** `activation_hook` devuelve `scheduled_events_return_value` con el evento `COBRO_COMISION_MANTENIMIENTO` mensual y no genera postings.
- **Happy path abono de nómina:** crédito con `instruction_details["tipo_transaccion"]="NOMINA"` e importe ≥ mínimo → aceptado; `post_posting_hook` registra la fecha.
- **Abono de nómina por debajo del mínimo:** se acepta como crédito normal pero NO cuenta como nómina para la comisión.
- **Abono genérico (no nómina):** crédito sin marcador → aceptado; no actualiza la fecha de nómina.
- **Rechazo denominación:** posting en denominación distinta → `Rejection` con `RejectionReason.WRONG_DENOMINATION`.
- **Rechazo saldo negativo:** débito mayor que el saldo COMMITTED → `Rejection` con `RejectionReason.INSUFFICIENT_FUNDS`.
- **Débito exacto a cero:** débito igual al saldo → aceptado (límite inclusivo en cero).
- **Comisión NO cobrada:** evento mensual con fecha de última nómina dentro de los últimos 31 días → sin `posting_instructions_directives`.
- **Comisión cobrada:** evento mensual sin nómina reciente (o nunca) → `CustomInstruction` que debita `importe_comision_mantenimiento` del `DEFAULT` y acredita `COMISION_INGRESO`; assert de ambas patas.
- **Comisión con saldo insuficiente:** saldo < comisión → cobro parcial hasta cero (o sin cobro), nunca saldo negativo.
- **Fecha de cobro:** el schedule se agenda en `dia_cobro_comision` (parametrizado, p. ej. día 5).
- **Decoradores / data requirements:** cubierto por `vault_lint` + `os-vault-simulate`.

## Requisitos no funcionales
- Sandbox Vault: solo imports de `contracts_api`, `decimal` y `zoneinfo`. Sin `os`, `sys`, `json`, `re`, `datetime` (stdlib), `math`, red ni I/O (`print`, `open`).
- Sin `float` ni literales decimales para dinero — `Decimal` siempre; redondeo explícito con `ROUND_HALF_UP` si aplica.
- Sin estado global mutable entre hooks; el estado se persiste en balances/direcciones o parámetros.
- API 4.0: devolver `PrePostingHookResult(rejection=Rejection(...))`, nunca `raise Rejected`. `CustomInstruction` sin `client_transaction_id` — trazabilidad en `instruction_details` con `hook_execution_id`.
- `Phase` se lee del `BalanceCoordinate` (key), nunca del `Balance` (value).
- `datetime` de contexto con `ZoneInfo("UTC")`, nunca `timezone.utc`.
- Todo parámetro `INSTANCE` declara `update_permission`; `TEMPLATE` y `derived=True` nunca lo declaran.
- Cada hook que lee parámetros/balances declara `@requires` / `@fetch_account_data`; la lista de fetchers a nivel módulo se llama `data_fetchers`.
- Cobertura de tests ≥ 90% antes del PR. Correr `os-vault-simulate contracts/cuenta_nomina.py` antes de abrir el PR.
- Deploy real (fuera del alcance de este ticket): `product_id` con prefijo `openspec_cuenta_nomina`, subir `version` en cada intento, header `X-Auth-Token`.

## Puntos de historia
<!-- STORY_POINTS:8 -->
**8** — cuatro hooks (activación con schedule, pre/post-posting con validación de saldo y denominación, evento mensual de comisión condicionado a la nómina), persistencia de la fecha de última nómina sin estado global, cobro parcial con protección de saldo, más suite de tests ≥ 90% y simulación. Sin acumulación de intereses ni desembolsos, lo que lo mantiene por debajo de 13.
<!-- /STORY_POINTS -->

## Subtareas
No hay subtareas en el ticket.
