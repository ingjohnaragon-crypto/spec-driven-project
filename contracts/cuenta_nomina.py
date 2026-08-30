# contracts/cuenta_nomina.py
# Vault Smart Contract — Cuenta para pago de nómina
# Contracts Language API 4.0

from contracts_api import (
    ParameterUpdatePermission,
    ActivationHookArguments,
    ActivationHookResult,
    BalanceCoordinate,
    BalanceDefaultDict,
    BalancesObservationFetcher,
    CustomInstruction,
    DefinedDateTime,
    DenominationShape,
    NumberShape,
    Parameter,
    ParameterLevel,
    Phase,
    Posting,
    PostingInstructionsDirective,
    PostPostingHookArguments,
    PostPostingHookResult,
    PrePostingHookArguments,
    PrePostingHookResult,
    Rejection,
    RejectionReason,
    ScheduledEvent,
    ScheduleExpression,
    ScheduledEventHookArguments,
    ScheduledEventHookResult,
    SmartContractEventType,
    Tside,
    fetch_account_data,
    requires,
)
from decimal import Decimal, ROUND_HALF_UP

api          = "4.0.0"
version      = "1.0.0"
display_name = "Cuenta de nómina"
summary      = "Cuenta de pasivo para pago de nómina con comisión de mantenimiento condicionada"
description  = (
    "Cuenta de pasivo con una única denominación por cuenta y saldo inicial cero. "
    "Cobra una comisión mensual de mantenimiento salvo que se haya recibido un abono "
    "de nómina en los últimos 31 días. No admite descubierto: ningún posting ni el "
    "cobro de la comisión pueden dejar el saldo por debajo de cero."
)
tside                   = Tside.LIABILITY
supported_denominations = ["GBP", "USD", "EUR", "COP"]

DEFAULT_ADDRESS           = "DEFAULT"
DEFAULT_ASSET             = "COMMERCIAL_BANK_MONEY"
COMISION_INGRESO          = "COMISION_INGRESO"
SEGUIMIENTO_NOMINA        = "SEGUIMIENTO_NOMINA"
SEGUIMIENTO_NOMINA_OFFSET = "SEGUIMIENTO_NOMINA_OFFSET"
MARCADOR_NOMINA           = "NOMINA"
CLAVE_TIPO_TRANSACCION    = "tipo_transaccion"
EVENTO_COMISION           = "COBRO_COMISION_MANTENIMIENTO"
VENTANA_NOMINA_DIAS       = 31

parameters = [
    Parameter(
        name="denominacion",
        shape=DenominationShape(permitted_denominations=supported_denominations),
        level=ParameterLevel.INSTANCE,
        update_permission=ParameterUpdatePermission.USER_EDITABLE,
        display_name="Denominación",
        description="Denominación de la cuenta. Una sola divisa por cuenta.",
        default_value="GBP",
    ),
    Parameter(
        name="importe_comision_mantenimiento",
        shape=NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01")),
        level=ParameterLevel.TEMPLATE,
        display_name="Importe de la comisión de mantenimiento",
        description=(
            "Comisión mensual de mantenimiento que se cobra cuando no hubo un abono "
            "de nómina en los últimos 31 días."
        ),
        default_value=Decimal("5.00"),
    ),
    Parameter(
        name="dia_cobro_comision",
        shape=NumberShape(
            min_value=Decimal("1"), max_value=Decimal("28"), step=Decimal("1")
        ),
        level=ParameterLevel.TEMPLATE,
        display_name="Día de cobro de la comisión",
        description=(
            "Día del mes (1-28) en que se agenda el cobro de la comisión de "
            "mantenimiento. Se limita a 28 para evitar meses cortos."
        ),
        default_value=Decimal("1"),
    ),
    Parameter(
        name="importe_minimo_nomina",
        shape=NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01")),
        level=ParameterLevel.TEMPLATE,
        display_name="Importe mínimo de nómina",
        description=(
            "Importe mínimo de un abono marcado como NOMINA para que cuente como "
            "nómina reciente y exima del cobro de la comisión."
        ),
        default_value=Decimal("100.00"),
    ),
]

event_types = [
    # Sin scheduler_tag_ids: un tag referenciado inexistente hace fallar
    # POST /v1/accounts con TAG_NOT_FOUND (ver savings_product.py).
    SmartContractEventType(name=EVENTO_COMISION),
]
event_types_groups = []

# API 4.0: los hooks que llaman get_balances_observation() declaran el fetcher
# aquí y lo solicitan con @fetch_account_data. La lista se llama data_fetchers.
data_fetchers = [
    BalancesObservationFetcher(fetcher_id="live_balances", at=DefinedDateTime.LIVE),
]


# ── Helpers puros ─────────────────────────────────────────────────────────────

def _quantizar(importe: Decimal) -> Decimal:
    return importe.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _parametro(vault, nombre: str):
    return vault.get_parameter_timeseries(name=nombre).latest()


def _saldo_comprometido(
    balances: BalanceDefaultDict,
    direccion: str,
    denominacion: str,
) -> Decimal:
    clave = BalanceCoordinate(
        account_address=direccion,
        asset=DEFAULT_ASSET,
        denomination=denominacion,
        phase=Phase.COMMITTED,
    )
    return balances[clave].net


def _efecto_neto_committed(
    posting_instructions,
    direccion: str,
    denominacion: str,
) -> Decimal:
    """Suma el efecto neto COMMITTED sobre una dirección en la denominación dada.
    API 4.0: la fase se lee del BalanceCoordinate (clave), nunca del Balance (valor).
    """
    total = Decimal("0")
    for posting in posting_instructions:
        for coordenada, balance in posting.balances().items():
            if (
                coordenada.phase == Phase.COMMITTED
                and coordenada.account_address == direccion
                and coordenada.denomination == denominacion
            ):
                total += balance.net
    return total


def _dias_desde_epoca(anio: int, mes: int, dia: int) -> int:
    """Días transcurridos desde 1970-01-01 (día 0).

    Algoritmo Gregoriano puro `days_from_civil` de Howard Hinnant, solo aritmética
    entera. Permite restar dos fechas de forma exacta sin usar la stdlib.
    """
    a = anio - (1 if mes <= 2 else 0)
    era = (a if a >= 0 else a - 399) // 400
    yoe = a - era * 400
    doy = (153 * (mes + (-3 if mes > 2 else 9)) + 2) // 5 + dia - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def _dia_epoca_de(momento) -> int:
    return _dias_desde_epoca(momento.year, momento.month, momento.day)


def _credito_nomina_del_lote(
    posting_instructions,
    denominacion: str,
    importe_minimo: Decimal,
) -> Decimal:
    """Mayor crédito committed a DEFAULT marcado como nómina y >= importe_minimo.

    Devuelve Decimal('0') si el lote no contiene ninguna nómina válida. El marcado
    solo alimenta la lógica de comisión; nunca sirve para rechazar un posting.
    """
    creditos = []
    for posting in posting_instructions:
        detalles = posting.instruction_details or {}
        if detalles.get(CLAVE_TIPO_TRANSACCION) != MARCADOR_NOMINA:
            continue
        credito = _efecto_neto_committed([posting], DEFAULT_ADDRESS, denominacion)
        if credito > Decimal("0") and credito >= importe_minimo:
            creditos.append(credito)
    if not creditos:
        return Decimal("0")
    return max(creditos)


def _transferencia_interna(
    importe: Decimal,
    denominacion: str,
    direccion_debito: str,
    direccion_credito: str,
    descripcion: str,
    hook_id: str,
    account_id: str,
    event_type: str = "",
    detalles_adicionales=None,
) -> CustomInstruction:
    detalles = {
        "description": descripcion,
        "hook_execution_id": hook_id,
    }
    if event_type:
        detalles["event_type"] = event_type
    if detalles_adicionales:
        for clave, valor in detalles_adicionales.items():
            detalles[clave] = valor
    return CustomInstruction(
        postings=[
            Posting(
                credit=False,
                amount=importe,
                denomination=denominacion,
                account_id=account_id,
                account_address=direccion_debito,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
            Posting(
                credit=True,
                amount=importe,
                denomination=denominacion,
                account_id=account_id,
                account_address=direccion_credito,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
        ],
        instruction_details=detalles,
    )


def _schedule_comision(effective_datetime, dia_cobro: int) -> dict:
    return {
        EVENTO_COMISION: ScheduledEvent(
            start_datetime=effective_datetime,
            expression=ScheduleExpression(
                day=str(dia_cobro),
                hour="0",
                minute="0",
                second="0",
            ),
        )
    }


# ── Hooks ────────────────────────────────────────────────────────────────────

@requires(parameters=True)
def activation_hook(
    vault, hook_arguments: ActivationHookArguments
) -> ActivationHookResult:
    dia_cobro = int(_parametro(vault, "dia_cobro_comision"))
    if dia_cobro < 1 or dia_cobro > 28:
        raise ValueError("dia_cobro_comision debe estar entre 1 y 28.")
    # Saldo inicial cero: la activación no emite ningún posting, solo agenda el
    # evento mensual de cobro de la comisión de mantenimiento.
    return ActivationHookResult(
        scheduled_events_return_value=_schedule_comision(
            hook_arguments.effective_datetime, dia_cobro
        )
    )


@requires(parameters=True)
@fetch_account_data(balances=["live_balances"])
def pre_posting_hook(
    vault, hook_arguments: PrePostingHookArguments
) -> PrePostingHookResult:
    denominacion = _parametro(vault, "denominacion")
    balances = vault.get_balances_observation(fetcher_id="live_balances").balances

    for posting in hook_arguments.posting_instructions:
        if posting.denomination != denominacion:
            return PrePostingHookResult(
                rejection=Rejection(
                    message=(
                        f"Posting denomination {posting.denomination} does not match "
                        f"account denomination {denominacion}."
                    ),
                    reason_code=RejectionReason.WRONG_DENOMINATION,
                )
            )

    saldo = _saldo_comprometido(balances, DEFAULT_ADDRESS, denominacion)
    efecto = _efecto_neto_committed(
        hook_arguments.posting_instructions, DEFAULT_ADDRESS, denominacion
    )
    # Sin descubierto: el débito exacto a cero se acepta (límite inclusivo).
    if saldo + efecto < Decimal("0"):
        return PrePostingHookResult(
            rejection=Rejection(
                message=(
                    f"Insufficient funds: balance {saldo} {denominacion}, "
                    f"attempted {abs(efecto)} {denominacion} debit."
                ),
                reason_code=RejectionReason.INSUFFICIENT_FUNDS,
            )
        )
    return PrePostingHookResult()


@requires(parameters=True)
@fetch_account_data(balances=["live_balances"])
def post_posting_hook(
    vault, hook_arguments: PostPostingHookArguments
) -> PostPostingHookResult:
    denominacion = _parametro(vault, "denominacion")
    importe_minimo = _parametro(vault, "importe_minimo_nomina")
    credito = _credito_nomina_del_lote(
        hook_arguments.posting_instructions, denominacion, importe_minimo
    )
    if credito <= Decimal("0"):
        return PostPostingHookResult(posting_instructions_directives=[])

    # La fecha del último abono de nómina se persiste como número de días desde
    # 1970-01-01 en el saldo neto de SEGUIMIENTO_NOMINA (el sandbox no permite
    # estado global mutable). El schedule reconstruye la fecha leyendo ese saldo.
    hoy = _dia_epoca_de(hook_arguments.effective_datetime)
    balances = vault.get_balances_observation(fetcher_id="live_balances").balances
    registro_actual = _saldo_comprometido(balances, SEGUIMIENTO_NOMINA, denominacion)
    delta = Decimal(str(hoy)) - registro_actual
    if delta == Decimal("0"):
        return PostPostingHookResult(posting_instructions_directives=[])

    if delta > Decimal("0"):
        direccion_debito = SEGUIMIENTO_NOMINA_OFFSET
        direccion_credito = SEGUIMIENTO_NOMINA
        importe = delta
    else:
        # El registro nunca debería retroceder, pero se contempla por robustez:
        # se mueve exactamente a "hoy", no se acumula.
        direccion_debito = SEGUIMIENTO_NOMINA
        direccion_credito = SEGUIMIENTO_NOMINA_OFFSET
        importe = -delta

    instruccion = _transferencia_interna(
        importe,
        denominacion,
        direccion_debito,
        direccion_credito,
        "Registro de la fecha del último abono de nómina",
        str(vault.get_hook_execution_id()),
        vault.account_id,
        detalles_adicionales={"dia_epoca_nomina": str(hoy)},
    )
    return PostPostingHookResult(
        posting_instructions_directives=[
            PostingInstructionsDirective(posting_instructions=[instruccion])
        ]
    )


@requires(event_type="COBRO_COMISION_MANTENIMIENTO", parameters=True)
@fetch_account_data(
    event_type="COBRO_COMISION_MANTENIMIENTO", balances=["live_balances"]
)
def scheduled_event_hook(
    vault, hook_arguments: ScheduledEventHookArguments
) -> ScheduledEventHookResult:
    if hook_arguments.event_type != EVENTO_COMISION:
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )

    denominacion = _parametro(vault, "denominacion")
    comision = _parametro(vault, "importe_comision_mantenimiento")
    balances = vault.get_balances_observation(fetcher_id="live_balances").balances
    saldo = _saldo_comprometido(balances, DEFAULT_ADDRESS, denominacion)
    registro = _saldo_comprometido(balances, SEGUIMIENTO_NOMINA, denominacion)
    hoy = _dia_epoca_de(hook_arguments.effective_datetime)

    # Nómina reciente: si hubo un abono de nómina en los últimos 31 días
    # (comparado contra effective_datetime) no se cobra nada.
    if registro > Decimal("0") and hoy - int(registro) <= VENTANA_NOMINA_DIAS:
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )

    # El cobro nunca puede dejar el saldo por debajo de cero. MVP: si el saldo
    # disponible es menor que la comisión se cobra solo hasta dejar el saldo en
    # cero y se omite el resto (no se acumula deuda).
    comision_efectiva = _quantizar(min(comision, max(saldo, Decimal("0"))))
    if comision_efectiva <= Decimal("0"):
        # MVP: saldo insuficiente; no se cobra nada y se omite el resto.
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )

    # MVP: si comision_efectiva < comision es un cobro parcial hasta dejar el
    # saldo en cero; el resto no cobrado se omite.
    instruccion = _transferencia_interna(
        comision_efectiva,
        denominacion,
        DEFAULT_ADDRESS,
        COMISION_INGRESO,
        "Cobro de comisión de mantenimiento",
        str(vault.get_hook_execution_id()),
        vault.account_id,
        event_type=EVENTO_COMISION,
    )
    return ScheduledEventHookResult(
        posting_instructions_directives=[
            PostingInstructionsDirective(posting_instructions=[instruccion])
        ],
        update_account_event_type_directives=[],
    )
