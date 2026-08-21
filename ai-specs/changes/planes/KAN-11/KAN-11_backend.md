# Vault Implementation Plan: KAN-11 Préstamo personal con amortización mensual y prepago

## Estimación de puntos de historia
<!-- STORY_POINTS:8 -->
**8** — contrato asset completo (desembolso, schedule mensual, prepago + penalización, recálculo) + suite de tests al nivel FTD.
<!-- /STORY_POINTS -->

## 1. Resumen

Producto Vault API 4.0 de **préstamo personal** (`tside = Tside.ASSET`):

- En activación desembolsar el principal y registrar el schedule mensual de amortización.
- Cada evento mensual aplica interés + capital (cuota tipo anualidad).
- Permitir prepago parcial/total con penalización configurable y recálculo del plan.
- Rechazar prepagos inválidos con `PrePostingHookResult(rejection=Rejection(...))`.
- Una denominación por cuenta; `supported_denominations = ["GBP", "USD", "EUR", "COP"]`.

Stack activo: `vault-smart-contracts`. Referencia dorada: `contracts/fixed_term_deposit.py` + `tests/test_fixed_term_deposit.py`.

## 2. Contexto de arquitectura

- `contracts/personal_loan.py` — Smart Contract (API 4.0) **completo** (reemplazar el skeleton actual)
- `tests/test_personal_loan.py` — tests estilo FTD (`MagicMock` vault, clases por comportamiento)
- Tooling: `os-vault-lint`, `os-vault-test --coverage`

### 2.1 Decisiones bloqueadas

| Tema | Decisión final | Rationale |
|---|---|---|
| Convención de tasa | `annual_interest_rate` como **fracción** Decimal (`0.12` = 12%), igual que FTD | Consistencia con golden contract |
| Plazo | Parámetro instancia `term_months` (entero ≥ 1) | Necesario para anualidad y tests |
| Principal | Parámetro instancia `principal` (Decimal > 0) | Desembolso en activación |
| Día de cobro | Parámetro template `repayment_day` (1–28) + `ScheduleExpression` mensual | Evita ambigüedad fin de mes |
| Tipo de cuota | Anualidad (cuota casi constante); último periodo ajusta residual de redondeo | Cuotas predecibles |
| Tras prepago | **Mantener el monto de cuota** y **acortar el plazo** (recomputar N restante) | UX predecible; ya recomendado en plan previo |
| Penalización | Un solo parámetro `prepayment_penalty_rate` (fracción Decimal, default `0.02`) sobre el monto prepago; no hay modo fixed en v1 | Una forma = menos ambigüedad; fácil de testear |
| Aplicación de penalización | `CustomInstruction` a dirección interna `PENALTY_INCOME` en `post_posting_hook` tras prepago válido | Misma idea que early closure FTD |
| Detección de prepago | En `pre_posting_hook`: posting neto que **reduce** el principal outstanding (cliente paga) | Claridad de flujo |
| Prepago total | Si monto ≥ outstanding, cerrar: outstanding → 0 y no reprogramar cuotas | Criterio de aceptación |
| Hooks | Solo nombres API 4.0: `activation_hook`, `pre_posting_hook`, `post_posting_hook`, `scheduled_event_hook` | El skeleton con `*_code` debe eliminarse |
| Imports | `from contracts_api import ...` directo; **prohibido** try/except de fallback | Sandbox + paridad FTD |
| Direcciones | `DEFAULT`, `DEFAULT_ASSET=COMMERCIAL_BANK_MONEY`, `PENALTY_INCOME`, evento `MONTHLY_REPAYMENT` | Paridad FTD |
| Redondeo | `ROUND_HALF_UP` a 2 decimales en dinero | Estándar del repo |

## 3. Pasos de implementación

### Step 0: Feature branch
- `feature/KAN-11-backend` (creada por `os-develop`)

### Step 1: Contract scaffold
- Reescribir `contracts/personal_loan.py` al estilo FTD:
  - Metadata: `api`, `version`, `display_name`, `summary`, `description`, `tside=Tside.ASSET`, `supported_denominations`
  - `parameters = [...]` con: `denomination`, `principal`, `annual_interest_rate`, `term_months`, `repayment_day`, `prepayment_penalty_rate`
  - Constantes de address/event

### Step 2: Helpers puros
- `_quantize(amount) -> Decimal`
- `_monthly_rate(annual_rate) -> Decimal`
- `_build_amortization_schedule(principal, annual_rate, term_months) -> list[dict]`
- `_get_committed_balance(balances, denomination, address=DEFAULT) -> Decimal`
- `_posting_net_effect(posting_instructions, denomination) -> Decimal`
- `_recompute_term_after_prepayment(outstanding, installment, annual_rate) -> int` (mantener cuota, acortar N)

### Step 3: Hooks
- `activation_hook`: validar params; emitir desembolso (`CustomInstruction`); registrar `MONTHLY_REPAYMENT` schedule
- `scheduled_event_hook`: si evento mensual, aplicar interés+capital del periodo según saldo committed y schedule/recompute
- `pre_posting_hook`: validar denominación; si es prepago, validar monto ≤ outstanding (+ tolerancia); rechazar overpay / wrong denom; aceptar prepago válido
- `post_posting_hook`: si hubo prepago, postear penalización a `PENALTY_INCOME` y dejar outstanding actualizado (balances Vault)

### Step 4: Tests (TDD) — `tests/test_personal_loan.py`
Reescribir al estilo FTD. Casos mínimos:

**Activation**
- desembolso crea postings / directives
- registra schedule `MONTHLY_REPAYMENT`
- rechaza `term_months < 1` / `principal <= 0` si aplica validación en activación

**Schedule helper**
- anualidad 12 meses tasa 12%
- tasa cero
- último periodo limpia residual

**Monthly repayment event**
- aplica interés+capital periodo 1
- saldo cero → no-op / sin crash
- event type desconocido → no-op seguro

**Prepayment**
- parcial aceptado
- total aceptado (cierra)
- overpay rechazado
- denom mismatch rechazado
- posting no-prepago pasa

**Penalty**
- `post_posting_hook` aplica `prepayment_penalty_rate * amount`
- tasa 0 → penalty 0

**Denominations**
- GBP/USD/COP smoke (como FTD)

Objetivo: ≥ 20 tests; coverage contrato ≥ 90%.

### Step 5: Gate
```bash
os-vault-lint
os-vault-test --coverage
```

### Step 6: Docs
- Solo si aparece un patrón reutilizable nuevo en standards; si no, no tocar.

## 4. Orden de implementación
0 → 1 scaffold → 2 helpers → 4 tests fallando → 3 hooks → 5 lint/coverage → handoff `os-commit`

## 5. Checklist de pruebas
- [ ] Lint sandbox 0 violaciones
- [ ] Tests verdes
- [ ] Coverage ≥ 90%
- [ ] Sin `pre_posting_code` / skeleton / TODO
- [ ] Suite existente (FTD/savings/current) sigue verde

## 6. Referencia de tooling
| Purpose | Command |
|---|---|
| Lint | `os-vault-lint` |
| Test + coverage | `os-vault-test --coverage` |

## 7. Catálogo de rechazos
| Condición | RejectionReason (sugerido) | Mensaje |
|---|---|---|
| Denominación ≠ cuenta | `AGAINST_TNC` / client custom | wrong denomination |
| Prepago > outstanding | `AGAINST_TNC` | amount exceeds outstanding |
| Principal/plazo inválido en activación | `AGAINST_TNC` | invalid parameters |

(Usar los enum values exactos disponibles en `contracts_api.RejectionReason` del SDK del repo.)

## 8. Dependencias
- SDK local `contracts_sdk/contracts_sdk/`
- Solo `contracts_api` + `decimal` en el contrato

## 9. Notas
- Una moneda por cuenta.
- No hay decisiones abiertas: todo está en §2.1.
- El archivo skeleton actual **debe reemplazarse** por implementación completa.

## 10. Checklist de verificación
- [ ] Imports directos `contracts_api`
- [ ] Hooks con nombres correctos
- [ ] `CustomInstruction` sin `client_transaction_id`
- [ ] Phase en `BalanceCoordinate`
- [ ] Coverage ≥ 90%
