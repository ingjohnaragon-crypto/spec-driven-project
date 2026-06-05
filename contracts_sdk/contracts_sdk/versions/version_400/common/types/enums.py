from enum import Enum
from functools import lru_cache

from ..docs import _common_docs_path, _smart_contracts_docs_path
from .....utils import symbols
from .....utils.types_utils import EnumSpec, EnumRepr, enum_members
from .....utils.feature_flags import (
    BALANCES_DISCRETE_INTERVAL_FETCHER,
    is_fflag_enabled,
)


class RejectionReason(EnumRepr, Enum):
    UNKNOWN_REASON = symbols.VaultRejectionReasonCode.UNKNOWN_REASON
    INSUFFICIENT_FUNDS = symbols.VaultRejectionReasonCode.INSUFFICIENT_FUNDS
    WRONG_DENOMINATION = symbols.VaultRejectionReasonCode.WRONG_DENOMINATION
    AGAINST_TNC = symbols.VaultRejectionReasonCode.AGAINST_TNC
    CLIENT_CUSTOM_REASON = symbols.VaultRejectionReasonCode.CLIENT_CUSTOM_REASON

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring=(
                "May optionally be used as the `reason_code` parameter on the "
                f"[Rejection]({_common_docs_path}classes/#Rejection)"
                " class."
            ),
            members=enum_members(cls),
            show_values=False,
        )


class Tside(EnumRepr, Enum):
    ASSET = symbols.Tside.ASSET
    LIABILITY = symbols.Tside.LIABILITY

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring=(
                "Account treasury side - determine account"
                f" [Balance]({_common_docs_path}classes/#Balance) "
                "net sign."
            ),
            members=enum_members(cls),
            show_values=False,
        )


class Phase(EnumRepr, Enum):
    COMMITTED = symbols.Phase.COMMITTED
    PENDING_IN = symbols.Phase.PENDING_IN
    PENDING_OUT = symbols.Phase.PENDING_OUT

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring="The availability of a given Balance.",
            members=enum_members(cls),
            show_values=False,
        )


class ParameterLevel(EnumRepr, Enum):
    GLOBAL = symbols.ContractParameterLevel.GLOBAL
    TEMPLATE = symbols.ContractParameterLevel.TEMPLATE
    INSTANCE = symbols.ContractParameterLevel.INSTANCE

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring="Different levels of visibility for Parameter objects.",
            members=enum_members(cls),
            show_values=False,
        )


class ParameterUpdatePermission(EnumRepr, Enum):
    PERMISSION_UNKNOWN = symbols.ContractParameterUpdatePermission.PERMISSION_UNKNOWN
    FIXED = symbols.ContractParameterUpdatePermission.FIXED
    OPS_EDITABLE = symbols.ContractParameterUpdatePermission.OPS_EDITABLE
    USER_EDITABLE = symbols.ContractParameterUpdatePermission.USER_EDITABLE
    USER_EDITABLE_WITH_OPS_PERMISSION = (
        symbols.ContractParameterUpdatePermission.USER_EDITABLE_WITH_OPS_PERMISSION
    )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring="Specifies who can edit a parameter.",
            members=enum_members(cls),
            show_values=False,
        )


class DefinedDateTime(EnumRepr, Enum):
    LIVE = symbols.DefinedDateTime.LIVE
    # EFFECTIVE_TIME = 1  Removed in v4
    INTERVAL_START = symbols.DefinedDateTime.INTERVAL_START
    EFFECTIVE_DATETIME = symbols.DefinedDateTime.EFFECTIVE_DATETIME

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring=(
                "A datetime that is defined within Vault. This datetime can be used in the "
                "Observation and Interval Fetchers, which are included in the "
                "[data_fetchers](../../smart_contracts_api_reference4xx/metadata/#data_fetchers) "
                "of the Contracts Metadata.\n\n* `EFFECTIVE_DATETIME` maps to the `effective_datetime`"
                " of the hook that is using a Data Fetcher.\n* `INTERVAL_START` can be used as an "
                "origin of the [RelativeDateTime](../classes/#RelativeDateTime) to define the start "
                "of an Interval Fetcher, as evaluated at the runtime of the hook.\n* `LIVE` maps to "
                "the actual runtime of the hook(`UTC NOW()`) that is using a Data Fetcher, which "
                "can be after the hook `effective_datetime`."
            ),
            members=enum_members(cls),
            show_values=False,
        )


class ScheduleFailover(EnumRepr, Enum):
    FIRST_VALID_DAY_BEFORE = symbols.ScheduleFailover.FIRST_VALID_DAY_BEFORE
    FIRST_VALID_DAY_AFTER = symbols.ScheduleFailover.FIRST_VALID_DAY_AFTER

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring="Specifies the failover strategy for this schedule.",
            members=enum_members(cls),
            show_values=False,
        )


class SupervisionExecutionMode(EnumRepr, Enum):
    OVERRIDE = symbols.SupervisionExecutionMode.OVERRIDE
    INVOKED = symbols.SupervisionExecutionMode.INVOKED

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring=(
                "Determines the execution of a supervisee's hook when triggered by an incoming "
                "request. If INVOKED, this executes the supervised account first, triggered by the "
                "incoming request, and provides the results to the supervisor. If OVERRIDE, this "
                "executes the supervisor hook instead of the supervisee's hook."
            ),
            members=enum_members(cls),
            show_values=False,
        )


class PostingInstructionType(EnumRepr, Enum):
    OUTBOUND_AUTHORISATION = symbols.PostingInstructionType.OUTBOUND_AUTHORISATION
    INBOUND_AUTHORISATION = symbols.PostingInstructionType.INBOUND_AUTHORISATION
    AUTHORISATION = symbols.PostingInstructionType.AUTHORISATION
    AUTHORISATION_ADJUSTMENT = symbols.PostingInstructionType.AUTHORISATION_ADJUSTMENT
    CUSTOM_INSTRUCTION = symbols.PostingInstructionType.CUSTOM_INSTRUCTION
    OUTBOUND_HARD_SETTLEMENT = symbols.PostingInstructionType.OUTBOUND_HARD_SETTLEMENT
    INBOUND_HARD_SETTLEMENT = symbols.PostingInstructionType.INBOUND_HARD_SETTLEMENT
    HARD_SETTLEMENT = symbols.PostingInstructionType.HARD_SETTLEMENT
    RELEASE = symbols.PostingInstructionType.RELEASE
    SETTLEMENT = symbols.PostingInstructionType.SETTLEMENT
    TRANSFER = symbols.PostingInstructionType.TRANSFER

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring="The type of the PostingInstruction.",
            members=enum_members(cls),
            show_values=False,
        )


class DateTimePrecision(EnumRepr, Enum):
    MINUTE = symbols.DateTimePrecision.MINUTE
    DAY = symbols.DateTimePrecision.DAY

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring="Determines the precision of a DateTime parameter value.",
            members=enum_members(cls),
            show_values=False,
        )


class Timeline(EnumRepr, Enum):
    PRESENT = symbols.Timeline.PRESENT
    FUTURE = symbols.Timeline.FUTURE

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring="A point in time, on which events are taking place.",
            members=enum_members(cls),
            show_values=False,
        )


class AdjustmentStrategy(EnumRepr, Enum):
    SCHEDULE_TRIGGERED = symbols.AdjustmentStrategy.SCHEDULE_TRIGGERED

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring=(
                "Specifies the adjustment strategy to use. "
                "`SCHEDULE_TRIGGERED` indicates that the adjustment process will be tied to one or "
                "more schedules. "
                "The adjustment process will run before a scheduled event is executed. "
                "If the `SCHEDULE_TRIGGERED` strategy is specified, then there must be at least one "
                f"[SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType) "
                f"defined in the [event_types]({_smart_contracts_docs_path}metadata#event_types) metadata "
                "with `adjustment_point = True`. "
            ),
            members=enum_members(cls),
            show_values=False,
        )


class DateTimeView(EnumRepr, Enum):
    VALUE_DATETIME = symbols.DateTimeView.VALUE_DATETIME
    BOOKING_DATETIME = symbols.DateTimeView.BOOKING_DATETIME

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        fetcher_docstrings = [
            f"[BalancesObservationFetcher]({_common_docs_path}classes/#BalancesObservationFetcher)",
            f"[BalancesIntervalFetcher]({_common_docs_path}classes/#BalancesIntervalFetcher)",
        ]
        if is_fflag_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER):
            fetcher_docstrings.append(
                f"[BalancesDiscreteIntervalFetcher]({_common_docs_path}classes/#BalancesDiscreteIntervalFetcher)"
            )
        fetcher_docstring = " or a ".join(fetcher_docstrings)
        return EnumSpec(
            name=cls.__name__,
            docstring=f"Used in a {fetcher_docstring} to "
            f"specify whether to fetch based on value datetime or booking datetime.",
            members=enum_members(cls),
            show_values=False,
        )


class DateFailover(EnumRepr, Enum):
    FIRST_VALID_DAY_BEFORE = symbols.DateFailover.FIRST_VALID_DAY_BEFORE
    FIRST_VALID_DAY_AFTER = symbols.DateFailover.FIRST_VALID_DAY_AFTER

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring=(
                "Specifies the failover strategy for monthly sampling "
                f"[Period]({_common_docs_path}classes/#Period) in the discrete interval fetcher "
                "when the calendar day falls outside the particular month. "
                "FIRST_VALID_DAY_BEFORE (default) and FIRST_VALID_DAY_AFTER indicate that the "
                "observation point is the first valid day before and after the missing day "
                "in the month, respectively."
            ),
            members=enum_members(cls),
            show_values=False,
        )


class PostingInstructionRejectionReason(EnumRepr, Enum):
    RESTRICTION_PREVENT_DEBITS = (
        symbols.PostingInstructionRejectionReason.RESTRICTION_PREVENT_DEBITS
    )
    RESTRICTION_PREVENT_CREDITS = (
        symbols.PostingInstructionRejectionReason.RESTRICTION_PREVENT_CREDITS
    )
    RESTRICTION_LIMIT_DEBITS = symbols.PostingInstructionRejectionReason.RESTRICTION_LIMIT_DEBITS
    RESTRICTION_LIMIT_CREDITS = symbols.PostingInstructionRejectionReason.RESTRICTION_LIMIT_CREDITS
    RESTRICTION_REVIEW_DEBITS = symbols.PostingInstructionRejectionReason.RESTRICTION_REVIEW_DEBITS
    RESTRICTION_REVIEW_CREDITS = (
        symbols.PostingInstructionRejectionReason.RESTRICTION_REVIEW_CREDITS
    )
    INSUFFICIENT_FUNDS = symbols.PostingInstructionRejectionReason.INSUFFICIENT_FUNDS
    AGAINST_TERMS_AND_CONDITIONS = (
        symbols.PostingInstructionRejectionReason.AGAINST_TERMS_AND_CONDITIONS
    )
    CLIENT_CUSTOM_REASON = symbols.PostingInstructionRejectionReason.CLIENT_CUSTOM_REASON
    ACCOUNT_STATUS_INVALID = symbols.PostingInstructionRejectionReason.ACCOUNT_STATUS_INVALID
    WRONG_DENOMINATION = symbols.PostingInstructionRejectionReason.WRONG_DENOMINATION

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring=(
                "Describes reasons that a PostingInstruction can be rejected by Vault. "
                "The Restriction enums map to the RestrictionTypes on the Core API "
                "[Restriction Resource](/api/core_api/#Restrictions). "
                "INSUFFICIENT_FUNDS, AGAINST_TERMS_AND_CONDITIONS, WRONG_DENOMINATION and CLIENT_CUSTOM_REASON map to the corresponding "
                f"Contracts [RejectionReason]({_common_docs_path}enums/#RejectionReason) enum."
            ),
            members=enum_members(cls),
            show_values=False,
        )


class HookName(EnumRepr, Enum):
    UNKNOWN_HOOK = symbols.HookName.UNKNOWN_HOOK
    ACTIVATION_HOOK = symbols.HookName.ACTIVATION_HOOK
    SCHEDULED_EVENT_HOOK = symbols.HookName.SCHEDULED_EVENT_HOOK
    DEACTIVATION_HOOK = symbols.HookName.DEACTIVATION_HOOK
    CONVERSION_HOOK = symbols.HookName.CONVERSION_HOOK
    POST_PARAMETER_CHANGE_HOOK = symbols.HookName.POST_PARAMETER_CHANGE_HOOK
    PRE_PARAMETER_CHANGE_HOOK = symbols.HookName.PRE_PARAMETER_CHANGE_HOOK
    PRE_POSTING_HOOK = symbols.HookName.PRE_POSTING_HOOK
    POST_POSTING_HOOK = symbols.HookName.POST_POSTING_HOOK
    DERIVED_PARAMETERS_HOOK = symbols.HookName.DERIVED_PARAMETERS_HOOK
    ATTRIBUTE_HOOK = symbols.HookName.ATTRIBUTE_HOOK
    SCHEDULED_EVENT_ADJUSTMENT_HOOK = symbols.HookName.SCHEDULED_EVENT_ADJUSTMENT_HOOK
    POST_POSTING_ADJUSTMENT_HOOK = symbols.HookName.POST_POSTING_ADJUSTMENT_HOOK
    POST_PARAMETER_CHANGE_ADJUSTMENT_HOOK = symbols.HookName.POST_PARAMETER_CHANGE_ADJUSTMENT_HOOK

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH) -> EnumSpec:
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return EnumSpec(
            name=cls.__name__,
            docstring="Describes the type of a Smart Contract hook.",
            members=enum_members(cls),
            show_values=False,
        )
