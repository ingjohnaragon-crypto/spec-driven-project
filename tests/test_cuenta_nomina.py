# tests/test_cuenta_nomina.py
# API 4.0 — Cuenta para pago de nómina: pruebas unitarias

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from contracts_api import (
    ActivationHookArguments,
    Balance,
    BalanceCoordinate,
    BalanceDefaultDict,
    Phase,
    PostPostingHookArguments,
    PrePostingHookArguments,
    RejectionReason,
    ScheduledEventHookArguments,
    Tside,
)

import contracts.cuenta_nomina as contrato

UTC = ZoneInfo("UTC")
DENOMINACION = "GBP"
ACTIVACION = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
EVENTO_MENSUAL = datetime(2024, 3, 1, 0, 0, tzinfo=UTC)
DIA_EPOCA_EVENTO = contrato._dia_epoca_de(EVENTO_MENSUAL)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def crear_balances(
    saldo: Decimal = Decimal("1000.00"),
    seguimiento: Decimal = Decimal("0"),
    denominacion: str = DENOMINACION,
) -> BalanceDefaultDict:
    balances = BalanceDefaultDict()
    for direccion, importe in [
        (contrato.DEFAULT_ADDRESS, saldo),
        (contrato.SEGUIMIENTO_NOMINA, seguimiento),
    ]:
        clave = BalanceCoordinate(
            account_address=direccion,
            asset=contrato.DEFAULT_ASSET,
            denomination=denominacion,
            phase=Phase.COMMITTED,
        )
        credito = importe if importe >= 0 else Decimal("0")
        debito = Decimal("0") if importe >= 0 else abs(importe)
        balances[clave] = Balance(net=importe, credit=credito, debit=debito)
    return balances


def crear_vault(
    saldo: Decimal = Decimal("1000.00"),
    seguimiento: Decimal = Decimal("0"),
    denominacion: str = DENOMINACION,
    comision: Decimal = Decimal("5.00"),
    dia_cobro: Decimal = Decimal("1"),
    minimo_nomina: Decimal = Decimal("100.00"),
) -> MagicMock:
    vault = MagicMock()
    vault.account_id = "cuenta-nomina-001"
    parametros = {
        "denominacion": denominacion,
        "importe_comision_mantenimiento": comision,
        "dia_cobro_comision": dia_cobro,
        "importe_minimo_nomina": minimo_nomina,
    }
    vault.get_parameter_timeseries.side_effect = lambda name: MagicMock(
        latest=MagicMock(return_value=parametros[name])
    )
    observacion = MagicMock()
    observacion.balances = crear_balances(saldo, seguimiento, denominacion)
    vault.get_balances_observation.return_value = observacion
    vault.get_hook_execution_id.return_value = "ejecucion-001"
    return vault


def crear_posting(
    importe: Decimal,
    credito: bool = True,
    denominacion: str = DENOMINACION,
    direccion: str = contrato.DEFAULT_ADDRESS,
    detalles=None,
) -> MagicMock:
    posting = MagicMock()
    posting.denomination = denominacion
    posting.instruction_details = detalles or {}
    clave = BalanceCoordinate(
        account_address=direccion,
        asset=contrato.DEFAULT_ASSET,
        denomination=denominacion,
        phase=Phase.COMMITTED,
    )
    neto = importe if credito else -importe
    balances = BalanceDefaultDict()
    balances[clave] = Balance(
        net=neto,
        credit=importe if credito else Decimal("0"),
        debit=Decimal("0") if credito else importe,
    )
    posting.balances.return_value = balances
    return posting


def posting_nomina(importe: Decimal, denominacion: str = DENOMINACION) -> MagicMock:
    return crear_posting(
        importe,
        credito=True,
        denominacion=denominacion,
        detalles={contrato.CLAVE_TIPO_TRANSACCION: contrato.MARCADOR_NOMINA},
    )


def argumentos_pre(postings) -> PrePostingHookArguments:
    return PrePostingHookArguments(
        effective_datetime=ACTIVACION,
        posting_instructions=postings,
        client_transactions={},
    )


def argumentos_post(postings, momento=ACTIVACION) -> PostPostingHookArguments:
    return PostPostingHookArguments(
        effective_datetime=momento,
        posting_instructions=postings,
        client_transactions={},
    )


def argumentos_evento(
    evento: str = contrato.EVENTO_COMISION, momento=EVENTO_MENSUAL
) -> ScheduledEventHookArguments:
    return ScheduledEventHookArguments(effective_datetime=momento, event_type=evento)


def _legs(resultado):
    return resultado.posting_instructions_directives[0].posting_instructions[0].postings


# ── activation_hook ──────────────────────────────────────────────────────────

class TestActivationHook:
    def test_agenda_evento_comision_mensual(self):
        resultado = contrato.activation_hook(
            crear_vault(), ActivationHookArguments(effective_datetime=ACTIVACION)
        )
        assert set(resultado.scheduled_events_return_value) == {contrato.EVENTO_COMISION}

    def test_activacion_no_emite_postings(self):
        resultado = contrato.activation_hook(
            crear_vault(), ActivationHookArguments(effective_datetime=ACTIVACION)
        )
        assert resultado.posting_instructions_directives == []

    def test_schedule_usa_dia_cobro_comision(self):
        resultado = contrato.activation_hook(
            crear_vault(dia_cobro=Decimal("5")),
            ActivationHookArguments(effective_datetime=ACTIVACION),
        )
        schedule = resultado.scheduled_events_return_value[contrato.EVENTO_COMISION]
        assert schedule.expression.day == "5"
        assert schedule.expression.hour == "0"
        assert schedule.start_datetime == ACTIVACION

    def test_activacion_rechaza_dia_fuera_de_rango_bajo(self):
        with pytest.raises(ValueError, match="entre 1 y 28"):
            contrato.activation_hook(
                crear_vault(dia_cobro=Decimal("0")),
                ActivationHookArguments(effective_datetime=ACTIVACION),
            )

    def test_activacion_rechaza_dia_fuera_de_rango_alto(self):
        with pytest.raises(ValueError, match="entre 1 y 28"):
            contrato.activation_hook(
                crear_vault(dia_cobro=Decimal("29")),
                ActivationHookArguments(effective_datetime=ACTIVACION),
            )


# ── pre_posting_hook: denominación ───────────────────────────────────────────

class TestPrePostingDenominacion:
    def test_rechaza_denominacion_distinta(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(denominacion="GBP"),
            argumentos_pre([crear_posting(Decimal("50"), denominacion="USD")]),
        )
        assert resultado.rejection.reason_code == RejectionReason.WRONG_DENOMINATION

    def test_acepta_credito_misma_denominacion(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(), argumentos_pre([crear_posting(Decimal("50"))])
        )
        assert resultado.rejection is None

    def test_acepta_deposito_usd_en_cuenta_usd(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(denominacion="USD"),
            argumentos_pre([crear_posting(Decimal("50"), denominacion="USD")]),
        )
        assert resultado.rejection is None

    def test_acepta_deposito_cop_en_cuenta_cop(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(denominacion="COP"),
            argumentos_pre([crear_posting(Decimal("50000"), denominacion="COP")]),
        )
        assert resultado.rejection is None


# ── pre_posting_hook: saldo ──────────────────────────────────────────────────

class TestPrePostingSaldo:
    def test_rechaza_debito_mayor_que_saldo(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(saldo=Decimal("100")),
            argumentos_pre([crear_posting(Decimal("100.01"), credito=False)]),
        )
        assert resultado.rejection.reason_code == RejectionReason.INSUFFICIENT_FUNDS
        assert "Insufficient funds" in resultado.rejection.message

    def test_acepta_debito_exacto_a_cero(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(saldo=Decimal("100")),
            argumentos_pre([crear_posting(Decimal("100"), credito=False)]),
        )
        assert resultado.rejection is None

    def test_acepta_debito_menor_que_saldo(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(saldo=Decimal("100")),
            argumentos_pre([crear_posting(Decimal("40"), credito=False)]),
        )
        assert resultado.rejection is None

    def test_acepta_credito_con_saldo_cero(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(saldo=Decimal("0")),
            argumentos_pre([crear_posting(Decimal("250"), credito=True)]),
        )
        assert resultado.rejection is None

    def test_acepta_posting_importe_cero(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(saldo=Decimal("0")),
            argumentos_pre([crear_posting(Decimal("0"), credito=False)]),
        )
        assert resultado.rejection is None


# ── post_posting_hook: registro de nómina ────────────────────────────────────

class TestPostPostingNomina:
    def test_nomina_valida_registra_fecha(self):
        resultado = contrato.post_posting_hook(
            crear_vault(seguimiento=Decimal("0")),
            argumentos_post([posting_nomina(Decimal("1500.00"))]),
        )
        postings = _legs(resultado)
        assert len(postings) == 2
        assert {p.account_address for p in postings} == {
            contrato.SEGUIMIENTO_NOMINA,
            contrato.SEGUIMIENTO_NOMINA_OFFSET,
        }
        credito = next(p for p in postings if p.credit)
        debito = next(p for p in postings if not p.credit)
        assert credito.account_address == contrato.SEGUIMIENTO_NOMINA
        assert debito.account_address == contrato.SEGUIMIENTO_NOMINA_OFFSET
        dia_hoy = contrato._dia_epoca_de(ACTIVACION)
        assert credito.amount == Decimal(str(dia_hoy))
        assert debito.amount == Decimal(str(dia_hoy))

    def test_nomina_bajo_minimo_no_registra(self):
        resultado = contrato.post_posting_hook(
            crear_vault(minimo_nomina=Decimal("100.00")),
            argumentos_post([posting_nomina(Decimal("99.99"))]),
        )
        assert resultado.posting_instructions_directives == []

    def test_credito_sin_marcador_no_registra(self):
        resultado = contrato.post_posting_hook(
            crear_vault(),
            argumentos_post([crear_posting(Decimal("1500.00"), credito=True)]),
        )
        assert resultado.posting_instructions_directives == []

    def test_debito_no_registra(self):
        resultado = contrato.post_posting_hook(
            crear_vault(),
            argumentos_post(
                [
                    crear_posting(
                        Decimal("1500.00"),
                        credito=False,
                        detalles={
                            contrato.CLAVE_TIPO_TRANSACCION: contrato.MARCADOR_NOMINA
                        },
                    )
                ]
            ),
        )
        assert resultado.posting_instructions_directives == []

    def test_nomina_marcador_pero_denominacion_distinta_no_registra(self):
        resultado = contrato.post_posting_hook(
            crear_vault(denominacion="GBP"),
            argumentos_post([posting_nomina(Decimal("1500.00"), denominacion="USD")]),
        )
        assert resultado.posting_instructions_directives == []

    def test_registro_mueve_a_hoy_no_acumula(self):
        previo = contrato._dia_epoca_de(datetime(2023, 12, 15, tzinfo=UTC))
        resultado = contrato.post_posting_hook(
            crear_vault(seguimiento=Decimal(str(previo))),
            argumentos_post([posting_nomina(Decimal("1500.00"))]),
        )
        postings = _legs(resultado)
        hoy = contrato._dia_epoca_de(ACTIVACION)
        assert all(p.amount == Decimal(str(hoy - previo)) for p in postings)
        assert hoy - previo == 31

    def test_instruction_details_incluye_hook_execution_id_y_dia_epoca(self):
        resultado = contrato.post_posting_hook(
            crear_vault(),
            argumentos_post([posting_nomina(Decimal("1500.00"))]),
        )
        instruccion = resultado.posting_instructions_directives[0].posting_instructions[0]
        hoy = contrato._dia_epoca_de(ACTIVACION)
        assert instruccion.instruction_details["hook_execution_id"] == "ejecucion-001"
        assert instruccion.instruction_details["dia_epoca_nomina"] == str(hoy)

    def test_varias_nominas_en_lote_toma_el_credito_maximo(self):
        resultado = contrato.post_posting_hook(
            crear_vault(seguimiento=Decimal("0")),
            argumentos_post(
                [posting_nomina(Decimal("500.00")), posting_nomina(Decimal("2000.00"))]
            ),
        )
        # El registro es un entero de días; el crédito máximo solo decide si hay
        # nómina válida, no el importe registrado.
        postings = _legs(resultado)
        hoy = contrato._dia_epoca_de(ACTIVACION)
        assert all(p.amount == Decimal(str(hoy)) for p in postings)
        assert contrato._credito_nomina_del_lote(
            [posting_nomina(Decimal("500.00")), posting_nomina(Decimal("2000.00"))],
            "GBP",
            Decimal("100.00"),
        ) == Decimal("2000.00")

    def test_registro_futuro_se_corrige_hacia_hoy(self):
        # Robustez: si el registro quedara por delante de "hoy" el ajuste lo
        # devuelve exactamente a la fecha efectiva (invierte las patas).
        futuro = contrato._dia_epoca_de(datetime(2024, 2, 15, tzinfo=UTC))
        resultado = contrato.post_posting_hook(
            crear_vault(seguimiento=Decimal(str(futuro))),
            argumentos_post([posting_nomina(Decimal("1500.00"))]),
        )
        postings = _legs(resultado)
        hoy = contrato._dia_epoca_de(ACTIVACION)
        debito = next(p for p in postings if not p.credit)
        credito = next(p for p in postings if p.credit)
        assert debito.account_address == contrato.SEGUIMIENTO_NOMINA
        assert credito.account_address == contrato.SEGUIMIENTO_NOMINA_OFFSET
        assert all(p.amount == Decimal(str(futuro - hoy)) for p in postings)

    def test_lote_sin_movimiento_de_fecha_es_no_op(self):
        hoy = contrato._dia_epoca_de(ACTIVACION)
        resultado = contrato.post_posting_hook(
            crear_vault(seguimiento=Decimal(str(hoy))),
            argumentos_post([posting_nomina(Decimal("1500.00"))]),
        )
        assert resultado.posting_instructions_directives == []


# ── scheduled_event_hook: comisión ───────────────────────────────────────────

class TestScheduledComision:
    def test_no_cobra_si_nomina_dentro_de_31_dias(self):
        registro = DIA_EPOCA_EVENTO - 10
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("1000"), seguimiento=Decimal(str(registro))),
            argumentos_evento(),
        )
        assert resultado.posting_instructions_directives == []

    def test_no_cobra_si_nomina_exactamente_31_dias(self):
        registro = DIA_EPOCA_EVENTO - 31
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("1000"), seguimiento=Decimal(str(registro))),
            argumentos_evento(),
        )
        assert resultado.posting_instructions_directives == []

    def test_cobra_si_nomina_hace_32_dias(self):
        registro = DIA_EPOCA_EVENTO - 32
        resultado = contrato.scheduled_event_hook(
            crear_vault(
                saldo=Decimal("1000"),
                seguimiento=Decimal(str(registro)),
                comision=Decimal("5.00"),
            ),
            argumentos_evento(),
        )
        postings = _legs(resultado)
        assert len(postings) == 2
        debito = next(p for p in postings if not p.credit)
        credito = next(p for p in postings if p.credit)
        assert debito.account_address == contrato.DEFAULT_ADDRESS
        assert credito.account_address == contrato.COMISION_INGRESO
        assert debito.amount == Decimal("5.00")
        assert credito.amount == Decimal("5.00")

    def test_cobra_si_nunca_hubo_nomina(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("1000"), seguimiento=Decimal("0")),
            argumentos_evento(),
        )
        postings = _legs(resultado)
        assert {p.account_address for p in postings} == {
            contrato.DEFAULT_ADDRESS,
            contrato.COMISION_INGRESO,
        }

    def test_cobro_parcial_si_saldo_insuficiente(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(
                saldo=Decimal("2.00"), seguimiento=Decimal("0"), comision=Decimal("5.00")
            ),
            argumentos_evento(),
        )
        postings = _legs(resultado)
        assert all(p.amount == Decimal("2.00") for p in postings)

    def test_no_cobra_si_saldo_cero(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("0"), seguimiento=Decimal("0")),
            argumentos_evento(),
        )
        assert resultado.posting_instructions_directives == []

    def test_no_cobra_si_saldo_negativo(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("-3.00"), seguimiento=Decimal("0")),
            argumentos_evento(),
        )
        assert resultado.posting_instructions_directives == []

    def test_comision_nunca_acredita_default_del_cliente(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("1000"), seguimiento=Decimal("0")),
            argumentos_evento(),
        )
        credito = next(p for p in _legs(resultado) if p.credit)
        assert credito.account_address == contrato.COMISION_INGRESO
        assert credito.account_address != contrato.DEFAULT_ADDRESS

    def test_instruction_details_del_cobro(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("1000"), seguimiento=Decimal("0")),
            argumentos_evento(),
        )
        instruccion = resultado.posting_instructions_directives[0].posting_instructions[0]
        assert instruccion.instruction_details["event_type"] == contrato.EVENTO_COMISION
        assert instruccion.instruction_details["hook_execution_id"] == "ejecucion-001"

    def test_event_type_desconocido_es_noop(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(), argumentos_evento(evento="OTRO_EVENTO")
        )
        assert resultado.posting_instructions_directives == []
        assert resultado.update_account_event_type_directives == []

    def test_cobro_usa_denominacion_de_la_cuenta(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(
                saldo=Decimal("1000"), seguimiento=Decimal("0"), denominacion="EUR"
            ),
            argumentos_evento(),
        )
        assert all(p.denomination == "EUR" for p in _legs(resultado))


# ── Helpers puros ────────────────────────────────────────────────────────────

class TestHelpers:
    def test_dias_desde_epoca_referencia(self):
        assert contrato._dias_desde_epoca(1970, 1, 1) == 0
        assert contrato._dias_desde_epoca(1970, 1, 2) == 1
        assert contrato._dias_desde_epoca(1971, 1, 1) == 365
        assert contrato._dias_desde_epoca(2000, 1, 1) == 10957

    def test_diferencia_de_dias_es_exacta(self):
        a = contrato._dia_epoca_de(datetime(2024, 1, 31, tzinfo=UTC))
        b = contrato._dia_epoca_de(datetime(2024, 3, 1, tzinfo=UTC))
        assert b - a == 30

    def test_saldo_comprometido_aisla_denominacion(self):
        balances = crear_balances(saldo=Decimal("100"), denominacion="GBP")
        assert contrato._saldo_comprometido(
            balances, contrato.DEFAULT_ADDRESS, "GBP"
        ) == Decimal("100")
        assert contrato._saldo_comprometido(
            balances, contrato.DEFAULT_ADDRESS, "USD"
        ) == Decimal("0")


# ── Metadatos ────────────────────────────────────────────────────────────────

class TestMetadata:
    def test_supported_denominations(self):
        assert contrato.supported_denominations == ["GBP", "USD", "EUR", "COP"]

    def test_tside_liability(self):
        assert contrato.tside == Tside.LIABILITY

    def test_api_version(self):
        assert contrato.api == "4.0.0"

    def test_parametros_de_negocio_configurables(self):
        nombres = {p.name for p in contrato.parameters}
        assert {
            "denominacion",
            "importe_comision_mantenimiento",
            "dia_cobro_comision",
            "importe_minimo_nomina",
        } <= nombres
