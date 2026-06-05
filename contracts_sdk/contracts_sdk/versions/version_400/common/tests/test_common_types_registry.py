from unittest import TestCase

from ..types import (
    common_types_registry,
)
from .....utils.feature_flags import (
    
    BALANCES_DISCRETE_INTERVAL_FETCHER,
    disable_fflags,
    skip_if_not_enabled,
)


class TestCommonTypesRegistry(TestCase):
    def test_common_types_registry_non_fflaged_types(self):
        registry = common_types_registry()
        expected_registry = {
            "AccountIdShape",
            "AccountNotificationDirective",
            "AddressDetails",
            "AdjustmentAmount",
            "AuthorisationAdjustment",
            "Balance",
            "BalanceCoordinate",
            "BalanceDefaultDict",
            "BalancesFilter",
            "BalancesIntervalFetcher",
            "BalancesObservation",
            "BalancesObservationFetcher",
            "BalanceTimeseries",
            "CalendarEvent",
            "CalendarEvents",
            "ClientTransaction",
            "ClientTransactionEffects",
            "DeactivationHookArguments",
            "DeactivationHookResult",
            "CustomInstruction",
            "DateShape",
            "DEFAULT_ADDRESS",
            "DEFAULT_ASSET",
            "DefinedDateTime",
            "DenominationShape",
            "DerivedParameterHookArguments",
            "DerivedParameterHookResult",
            "EndOfMonthSchedule",
            "EventTypesGroup",
            "fetch_account_data",
            "FlagTimeseries",
            "Logger",
            "InboundAuthorisation",
            "InboundHardSettlement",
            "Next",
            "NumberShape",
            "OptionalShape",
            "OptionalValue",
            "OutboundAuthorisation",
            "OutboundHardSettlement",
            "Override",
            "Parameter",
            "ParameterLevel",
            "ParameterTimeseries",
            "Phase",
            "PlanNotificationDirective",
            "ActivationHookArguments",
            "ActivationHookResult",
            "Posting",
            "PostingInstructionsDirective",
            "PostingInstructionType",
            "PostingsIntervalFetcher",
            "PostParameterChangeHookArguments",
            "PostParameterChangeHookResult",
            "PostPostingHookArguments",
            "PostPostingHookResult",
            "PrePostingHookResult",
            "PreParameterChangeHookArguments",
            "PreParameterChangeHookResult",
            "PrePostingHookArguments",
            "Previous",
            "Rejection",
            "RejectionReason",
            "RelativeDateTime",
            "Release",
            "requires",
            "ScheduleExpression",
            "ScheduledEventHookArguments",
            "ScheduledEventHookResult",
            "ScheduledEvent",
            "ScheduleFailover",
            "ScheduleSkip",
            "Settlement",
            "Shift",
            "SmartContractDescriptor",
            "SmartContractEventType",
            "StringShape",
            "SupervisedHooks",
            "SupervisionExecutionMode",
            "SupervisorActivationHookArguments",
            "SupervisorActivationHookResult",
            "SupervisorContractEventType",
            "SupervisorConversionHookArguments",
            "SupervisorConversionHookResult",
            "SupervisorPostPostingHookArguments",
            "SupervisorPostPostingHookResult",
            "SupervisorPrePostingHookArguments",
            "SupervisorPrePostingHookResult",
            "SupervisorScheduledEventHookArguments",
            "SupervisorScheduledEventHookResult",
            "Timeline",
            "TimeseriesItem",
            "TransactionCode",
            "TRANSACTION_REFERENCE_FIELD_NAME",
            "Transfer",
            "Tside",
            "UnionItem",
            "UnionItemValue",
            "UnionShape",
            "UpdateAccountEventTypeDirective",
            "ParameterUpdatePermission",
            "UpdatePlanEventTypeDirective",
            "ConversionHookArguments",
            "ConversionHookResult",
            "FlagsFilter",
            "FlagsIntervalFetcher",
            "FlagsObservation",
            "FlagsObservationFetcher",
            "FlagValueTimeseries",
        }
        self.assertTrue(
            expected_registry.issubset(registry.keys()),
            f"The following types do not exist in the registry: {expected_registry.difference(registry.keys())}",
        )

    
    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balances_discrete_interval_fetcher_fflag_enabled(self):
        registry = common_types_registry()
        self.assertIn("BalancesDiscreteIntervalFetcher", registry)
        self.assertIn("BalanceDiscreteTimeseries", registry)
        self.assertIn("DateFailover", registry)
        self.assertIn("Period", registry)

    @disable_fflags([BALANCES_DISCRETE_INTERVAL_FETCHER])
    def test_balances_discrete_interval_fetcher_fflag_disabled(self):
        registry = common_types_registry()
        self.assertNotIn("BalancesDiscreteIntervalFetcher", registry)
        self.assertNotIn("BalanceDiscreteTimeseries", registry)
        self.assertNotIn("DateFailover", registry)
        self.assertNotIn("Period", registry)
