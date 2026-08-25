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
)

import contracts.cuenta_joven as contrato

UTC = ZoneInfo("UTC")
DENOMINACION = "GBP"
ACTIVACION = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)


def crear_balances(
    saldo: Decimal = Decimal("1000.00"),
    acumulado: Decimal = Decimal("0.00"),
    denominacion: str = DENOMINACION,
) -> BalanceDefaultDict:
    balances = BalanceDefaultDict()
    for direccion, importe in [
        (contrato.DEFAULT_ADDRESS, saldo),
        (contrato.DAILY_WITHDRAWALS, acumulado),
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
    acumulado: Decimal = Decimal("0.00"),
    denominacion: str = DENOMINACION,
    limite: Decimal = Decimal("500.00"),
    tasa_estandar: Decimal = Decimal("0.02"),
    tasa_bonificada: Decimal = Decimal("0.05"),
    minimo_saldo: Decimal = Decimal("1000.00"),
    minimo_ahorro: Decimal = Decimal("500.00"),
) -> MagicMock:
    vault = MagicMock()
    vault.account_id = "cuenta-joven-001"
    parametros = {
        "denomination": denominacion,
        "daily_withdrawal_limit": limite,
        "standard_interest_rate": tasa_estandar,
        "bonus_interest_rate": tasa_bonificada,
        "bonus_minimum_balance": minimo_saldo,
        "bonus_minimum_savings": minimo_ahorro,
    }
    vault.get_parameter_timeseries.side_effect = lambda name: MagicMock(
        latest=MagicMock(return_value=parametros[name])
    )
    observacion = MagicMock()
    observacion.balances = crear_balances(saldo, acumulado, denominacion)
    vault.get_balances_observation.return_value = observacion
    vault.get_hook_execution_id.return_value = "ejecucion-001"
    return vault


def crear_posting(
    importe: Decimal,
    credito: bool = False,
    denominacion: str = DENOMINACION,
    direccion: str = contrato.DEFAULT_ADDRESS,
) -> MagicMock:
    posting = MagicMock()
    posting.denomination = denominacion
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


def argumentos_pre(postings) -> PrePostingHookArguments:
    return PrePostingHookArguments(
        effective_datetime=ACTIVACION,
        posting_instructions=postings,
        client_transactions={},
    )


def argumentos_post(postings) -> PostPostingHookArguments:
    return PostPostingHookArguments(
        effective_datetime=ACTIVACION,
        posting_instructions=postings,
        client_transactions={},
    )


def argumentos_evento(evento: str) -> ScheduledEventHookArguments:
    return ScheduledEventHookArguments(
        effective_datetime=ACTIVACION,
        event_type=evento,
    )


class TestActivacion:
    def test_registra_reset_diario_e_interes_mensual(self):
        resultado = contrato.activation_hook(
            crear_vault(), ActivationHookArguments(effective_datetime=ACTIVACION)
        )
        assert set(resultado.scheduled_events_return_value) == {
            contrato.DAILY_WITHDRAWAL_RESET,
            contrato.MONTHLY_INTEREST,
        }

    @pytest.mark.parametrize(
        "nombre,valor",
        [
            ("daily_withdrawal_limit", Decimal("-0.01")),
            ("bonus_minimum_balance", Decimal("-0.01")),
            ("bonus_minimum_savings", Decimal("-0.01")),
            ("standard_interest_rate", Decimal("1.01")),
        ],
    )
    def test_rechaza_parametro_invalido(self, nombre, valor):
        vault = crear_vault()
        vault.get_parameter_timeseries.side_effect = lambda name: MagicMock(
            latest=MagicMock(
                return_value=valor if name == nombre else {
                    "denomination": "GBP",
                    "daily_withdrawal_limit": Decimal("500"),
                    "standard_interest_rate": Decimal("0.02"),
                    "bonus_interest_rate": Decimal("0.05"),
                    "bonus_minimum_balance": Decimal("1000"),
                    "bonus_minimum_savings": Decimal("500"),
                }[name]
            )
        )
        with pytest.raises(ValueError, match="Invalid account parameters"):
            contrato.activation_hook(
                vault, ActivationHookArguments(effective_datetime=ACTIVACION)
            )

    def test_rechaza_bonificacion_menor_que_estandar(self):
        vault = crear_vault(tasa_estandar=Decimal("0.05"), tasa_bonificada=Decimal("0.02"))
        with pytest.raises(ValueError, match="Invalid account parameters"):
            contrato.activation_hook(
                vault, ActivationHookArguments(effective_datetime=ACTIVACION)
            )


class TestRetiros:
    @pytest.mark.parametrize("importe", [Decimal("100"), Decimal("500")])
    def test_aprueba_retiro_dentro_o_en_limite(self, importe):
        resultado = contrato.pre_posting_hook(
            crear_vault(limite=Decimal("500")), argumentos_pre([crear_posting(importe)])
        )
        assert resultado.rejection is None

    def test_rechaza_retiro_que_supera_limite(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(limite=Decimal("500"), acumulado=Decimal("400")),
            argumentos_pre([crear_posting(Decimal("100.01"))]),
        )
        assert resultado.rejection.reason_code == RejectionReason.AGAINST_TNC
        assert "Daily withdrawal limit exceeded" in resultado.rejection.message

    def test_rechaza_segundo_retiro_que_supera_acumulado(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(limite=Decimal("500"), acumulado=Decimal("450")),
            argumentos_pre([crear_posting(Decimal("50.01"))]),
        )
        assert resultado.rejection.reason_code == RejectionReason.AGAINST_TNC

    def test_suma_postings_de_una_solicitud(self):
        postings = [crear_posting(Decimal("200")), crear_posting(Decimal("301"))]
        resultado = contrato.pre_posting_hook(crear_vault(), argumentos_pre(postings))
        assert resultado.rejection.reason_code == RejectionReason.AGAINST_TNC

    def test_deposito_no_consume_limite(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(acumulado=Decimal("500")),
            argumentos_pre([crear_posting(Decimal("100"), credito=True)]),
        )
        assert resultado.rejection is None

    def test_rechaza_saldo_insuficiente(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(saldo=Decimal("10")), argumentos_pre([crear_posting(Decimal("10.01"))])
        )
        assert resultado.rejection.reason_code == RejectionReason.INSUFFICIENT_FUNDS

    def test_rechaza_retiro_cero(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(), argumentos_pre([crear_posting(Decimal("0.00"))])
        )
        assert resultado.rejection.reason_code == RejectionReason.AGAINST_TNC

    def test_rechaza_denominacion_incorrecta(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(denominacion="GBP"),
            argumentos_pre([crear_posting(Decimal("10"), denominacion="USD")]),
        )
        assert resultado.rejection.reason_code == RejectionReason.WRONG_DENOMINATION

    def test_denominaciones_no_mezclan_acumulados(self):
        resultado = contrato.pre_posting_hook(
            crear_vault(denominacion="USD", acumulado=Decimal("400"), limite=Decimal("500")),
            argumentos_pre([crear_posting(Decimal("100"), denominacion="USD")]),
        )
        assert resultado.rejection is None


class TestRegistroYReinicio:
    def test_post_posting_registra_retiro_en_dos_legs(self):
        resultado = contrato.post_posting_hook(
            crear_vault(), argumentos_post([crear_posting(Decimal("125"))])
        )
        instrucciones = resultado.posting_instructions_directives[0].posting_instructions
        postings = instrucciones[0].postings
        assert len(postings) == 2
        assert {posting.account_address for posting in postings} == {
            contrato.DAILY_WITHDRAWALS,
            contrato.DAILY_WITHDRAWALS_OFFSET,
        }
        assert all(posting.amount == Decimal("125") for posting in postings)

    def test_abono_no_crea_registro(self):
        resultado = contrato.post_posting_hook(
            crear_vault(), argumentos_post([crear_posting(Decimal("125"), credito=True)])
        )
        assert resultado.posting_instructions_directives == []

    def test_reset_vacia_acumulado(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(acumulado=Decimal("125")),
            argumentos_evento(contrato.DAILY_WITHDRAWAL_RESET),
        )
        postings = resultado.posting_instructions_directives[0].posting_instructions[0].postings
        assert {posting.account_address for posting in postings} == {
            contrato.DAILY_WITHDRAWALS,
            contrato.DAILY_WITHDRAWALS_OFFSET,
        }
        assert all(posting.amount == Decimal("125") for posting in postings)

    def test_reset_sin_acumulado_es_no_op(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(acumulado=Decimal("0")),
            argumentos_evento(contrato.DAILY_WITHDRAWAL_RESET),
        )
        assert resultado.posting_instructions_directives == []

    def test_cuenta_y_denominacion_se_aislan_por_coordenada(self):
        balances = crear_balances(acumulado=Decimal("100"), denominacion="GBP")
        assert contrato._get_committed_balance(balances, contrato.DAILY_WITHDRAWALS, "GBP") == Decimal("100")
        assert contrato._get_committed_balance(balances, contrato.DAILY_WITHDRAWALS, "USD") == Decimal("0")


class TestIntereses:
    def test_aplica_tasa_bonificada_con_dos_condiciones(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("1000")), argumentos_evento(contrato.MONTHLY_INTEREST)
        )
        posting = resultado.posting_instructions_directives[0].posting_instructions[0].postings
        credito = next(item for item in posting if item.credit)
        assert credito.amount == Decimal("4.17")
        assert credito.account_address == contrato.DEFAULT_ADDRESS

    @pytest.mark.parametrize(
        "saldo,minimo_saldo,minimo_ahorro",
        [(Decimal("999.99"), Decimal("1000"), Decimal("500")), (Decimal("1000"), Decimal("1000"), Decimal("1001"))],
    )
    def test_aplica_tasa_estandar_si_falta_condicion(self, saldo, minimo_saldo, minimo_ahorro):
        resultado = contrato.scheduled_event_hook(
            crear_vault(
                saldo=saldo,
                minimo_saldo=minimo_saldo,
                minimo_ahorro=minimo_ahorro,
            ),
            argumentos_evento(contrato.MONTHLY_INTEREST),
        )
        credito = next(
            item
            for item in resultado.posting_instructions_directives[0].posting_instructions[0].postings
            if item.credit
        )
        assert credito.amount == (saldo * Decimal("0.02") / Decimal("12")).quantize(Decimal("0.01"))

    def test_umbral_cero_desactiva_condicion(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("1000"), minimo_saldo=Decimal("0"), minimo_ahorro=Decimal("0")),
            argumentos_evento(contrato.MONTHLY_INTEREST),
        )
        assert resultado.posting_instructions_directives[0].posting_instructions[0].postings[0].amount == Decimal("4.17")

    def test_interes_cero_es_no_op(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("0")), argumentos_evento(contrato.MONTHLY_INTEREST)
        )
        assert resultado.posting_instructions_directives == []

    def test_evento_desconocido_es_no_op(self):
        resultado = contrato.scheduled_event_hook(crear_vault(), argumentos_evento("OTRO"))
        assert resultado.posting_instructions_directives == []

    def test_legs_y_traceabilidad_del_abono(self):
        resultado = contrato.scheduled_event_hook(
            crear_vault(saldo=Decimal("1000")), argumentos_evento(contrato.MONTHLY_INTEREST)
        )
        instruccion = resultado.posting_instructions_directives[0].posting_instructions[0]
        assert len(instruccion.postings) == 2
        assert instruccion.instruction_details["hook_execution_id"] == "ejecucion-001"
        assert all(posting.denomination == "GBP" for posting in instruccion.postings)
