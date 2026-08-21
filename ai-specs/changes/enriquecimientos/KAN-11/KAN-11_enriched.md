# Ticket enriquecido: KAN-11 — Prestamo personal con amortización mensual y penalización por prepago

## Descripción original
Como cliente bancario, quiero un **préstamo personal** con amortización mensual y penalización por prepago, para financiar necesidades personales con cuotas predecibles y reglas claras si adelanto pagos.

El producto debe desembolsar un principal, generar cuotas mensuales y permitir prepago parcial o total con penalización configurable y recálculo del saldo restante.

## Descripción mejorada
Se implementará un Smart Contract Vault (API 4.0) de préstamo personal. En la activación se registra el desembolso del principal y se agenda un evento mensual de amortización. Cada ciclo aplica interés y capital según el plan vigente, actualizando saldos con Decimal y la denominación del producto.

El cliente puede prepagar de forma parcial o total. En el prepago se valida la operación, se calcula y aplica la penalización configurada por parámetros, se reduce el saldo y se recalcula el calendario restante. El contrato debe rechazar prepagos inválidos (monto, denominación o estado de cuenta) mediante Rejection en pre_posting_code.

## Criterios de aceptación
- [ ] El contrato desembolsa el principal en activación y deja la cuenta lista para amortizar
- [ ] Existe un schedule mensual que aplica interés y capital según el plan de amortización
- [ ] El prepago parcial o total está permitido y aplica una penalización configurable
- [ ] Tras un prepago, el saldo pendiente y el calendario restante se recalculan correctamente
- [ ] Se soporta la denominación del producto (GBP, USD, EUR o COP según parámetros)
- [ ] Prepagos inválidos se rechazan con mensaje claro (sin lanzar excepciones 3.x)
- [ ] os-vault-test pasa (todos los tests en verde)
- [ ] os-vault-test --coverage pasa (>= 90%)
- [ ] El contrato respeta el sandbox Python de Vault

## Campos, hooks y tipos
- Hooks: ctivation_hook, pre_posting_code, post_posting_code, scheduled_event_hook
- Parámetros sugeridos: principal, tasa de interés, día de cobro mensual, porcentaje/monto de penalización por prepago, denominación
- Tipos contracts_api: Parameter, NumberShape, DenominationShape, ScheduledEvent, EndOfMonthSchedule (o schedule equivalente), Posting, CustomInstruction, Rejection, RejectionReason, BalanceCoordinate, BalanceDefaultDict
- Dinero siempre con Decimal; fechas vía hook_arguments.effective_datetime (ZoneInfo)

## Archivos a crear o modificar
| Archivo | Capa | Acción |
|---|---|---|
| contracts/personal_loan.py | Contract | Create |
| 	ests/test_personal_loan.py | Tests | Create |

## Casos de prueba unitarios
- Activación con desembolso del principal
- Amortización mensual (interés + capital) en fecha de schedule
- Prepago parcial con penalización y recálculo de saldo
- Prepago total con cierre del plan
- Rechazo de prepago inválido (monto/denominación)
- Denominación distinta a la configurada

## Requisitos no funcionales
- Sin imports prohibidos del sandbox (os, sys, json, datetime, I/O, red)
- Sin loat para dinero; usar Decimal
- API 4.0: devolver Rejection (no 
aise Rejected); sin client_transaction_id en CustomInstruction
- Cobertura de tests >= 90% antes del PR

## Puntos de historia
<!-- STORY_POINTS:8 -->
**8** — contrato Vault con activacion, schedule mensual, prepago con penalizacion y recalculo, tests >=90%.
<!-- /STORY_POINTS -->
