from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from typing import Dict, Optional, Union


from ...common.docs import _common_docs_path, _smart_contracts_docs_path

from .....utils import symbols, types_utils
from .....utils.timezone_utils import validate_timezone_is_utc
from .....utils.feature_flags import (
    is_fflag_enabled,
    ACCOUNTS_V2,
    CONTRACTS_BOOKING_PERIODS,
    
)
from .enums import Timeline
from .event_types import (
    ScheduledEvent,
)
from .parameters import (
    OptionalValue,
    UnionItemValue,
)

from .postings import (
    _PITypes_str,
    
    ClientTransaction,
)


class HookArguments(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        effective_datetime: datetime,
        _from_proto: bool = False,
    ):
        self.effective_datetime = effective_datetime
        if not _from_proto:
            self._validate_hook_attributes()

    def _validate_hook_attributes(self):
        validate_timezone_is_utc(
            self.effective_datetime,
            "effective_datetime",
            self.__class__.__name__,
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="effective_datetime",
                type="datetime",
                docstring=(
                    "The logical datetime the hook is being run against. "
                    "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                ),
            ),
        ]


class DeactivationHookArguments(HookArguments):
    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="DeactivationHookArguments",
            docstring="The hook arguments of `deactivation_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new DeactivationHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        effective_datetime_docstring = """
            The logical datetime the hook is being run against. Must be a timezone-aware UTC
            datetime using the ZoneInfo class.<br>

            The `effective_datetime` in the deactivation hook is derived from the time that the
            hook was triggered.
        """
        return _update_effective_datetime(
            super()._public_attributes(language_code), effective_datetime_docstring
        )


class DerivedParameterHookArguments(HookArguments):
    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="DerivedParameterHookArguments",
            docstring="The hook arguments of the `derived_parameter_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new DerivedParameterHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )


class ActivationHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        
    ):
        super().__init__(effective_datetime)
        

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ActivationHookArguments",
            docstring="The hook arguments of `activation_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new ActivationHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        effective_datetime_docstring = """
            The logical datetime the hook is being run against. Must be a timezone-aware UTC
            datetime using the ZoneInfo class.<br>

            When an account is opened, `effective_datetime` will be set to the `opening_timestamp`
            for /v1/accounts requests or `activation_timestamp` for /v2/accounts requests.
            The `effective_datetime` can optionally be backdated by setting these fields to a
            backdated value on the request to open the Account. If they are not backdated then
            they default to the date and time that the request is processed.
        """
        attrs = _update_effective_datetime(
            super()._public_attributes(language_code), effective_datetime_docstring
        )
        
        return attrs


class ConversionHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        existing_schedules: Dict[str, ScheduledEvent],
    ):
        super().__init__(effective_datetime)
        self.existing_schedules = existing_schedules

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ConversionHookArguments",
            docstring="The hook arguments of `conversion_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new ConversionHookArguments object.",
                args=super()._public_attributes(language_code)
                + cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        effective_datetime_docstring = """
            The logical datetime the hook is being run against. Must be a timezone-aware UTC
            datetime using the ZoneInfo class.<br>

            **V2 Accounts**<br>
            The `effective_datetime` is set to the time that the hook is executed.<br>

            **V1 Accounts**<br>
            The `effective_datetime` is set to the time that the `AccountUpdate` is created
        """

        attrs = _update_effective_datetime(
            super()._public_attributes(language_code), effective_datetime_docstring
        )
        return attrs + [
            types_utils.ValueSpec(
                name="existing_schedules",
                type="Dict[str, ScheduledEvent]",
                docstring="""
                     A dictionary of EventType name to ScheduledEvent,
                    containing the existing ScheduledEvents associated
                    with the contract. Does not include disabled schedules.
                """,
            ),
        ]


class PostParameterChangeHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        old_parameter_values: Dict[
            str,
            Optional[
                Union[
                    datetime,
                    Decimal,
                    int,
                    OptionalValue,
                    str,
                    UnionItemValue,
                ]
            ],
        ],
        updated_parameter_values: Dict[
            str,
            Optional[
                Union[
                    datetime,
                    Decimal,
                    int,
                    OptionalValue,
                    str,
                    UnionItemValue,
                ]
            ],
        ],
    ):
        super().__init__(effective_datetime)
        self.old_parameter_values = old_parameter_values
        self.updated_parameter_values = updated_parameter_values

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PostParameterChangeHookArguments",
            docstring="The hook arguments of `post_parameter_change_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PostParameterChangeHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        type_str = (
            "Dict[str, Optional[Union[datetime, Decimal, int, OptionalValue, str, UnionItemValue]]]"
        )
        return [
            x for x in super()._public_attributes(language_code) if x.name != "effective_datetime"
        ] + [
            types_utils.ValueSpec(
                name="effective_datetime",
                type="datetime",
                docstring=(
                    "The logical datetime the hook is being run against. "
                    "This is the time at which the new value(s) became effective. "
                    "This is a timezone-aware UTC datetime using the ZoneInfo class."
                ),
            ),
            types_utils.ValueSpec(
                name="old_parameter_values",
                type=type_str,
                docstring=(
                    "The old parameter values prior to the change. This is a mapping of parameter "
                    "name (for `INSTANCE` parameters) or ID (for `Expected` parameters) to parameter "
                    "value and contains only those parameters that have changed. To access the value "
                    "of any other parameter, you must fetch the Vault data using hook data "
                    "requirements and use the relevant Vault methods."
                ),
            ),
            types_utils.ValueSpec(
                name="updated_parameter_values",
                type=type_str,
                docstring=(
                    "The updated parameter values after the change. This is a mapping of parameter "
                    "name (for `INSTANCE` parameters) or ID (for `Expected` parameters) to parameter "
                    "value and contains only those parameters that have changed. To access the value "
                    "of any other parameter, you must fetch the Vault data using hook data "
                    "requirements and use the relevant Vault methods."
                ),
            ),
        ]


class PostPostingHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        posting_instructions: _PITypes_str,  # type: ignore[valid-type]
        client_transactions: Dict[str, ClientTransaction],
    ):
        super().__init__(effective_datetime)
        self.posting_instructions = posting_instructions
        self.client_transactions = client_transactions

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PostPostingHookArguments",
            docstring="The hook arguments of `post_posting_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PostPostingHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        return [
            types_utils.ValueSpec(
                name="effective_datetime",
                type="datetime",
                docstring="""
                    The logical datetime that the hook is being run against. Must be a
                    timezone-aware UTC datetime using the ZoneInfo class. This datetime is equal to
                    the `value_timestamp` of the Posting Instructions, if set at the
                    `posting_instruction_batch` level within the [Postings API](/api/postings_api) request. Otherwise,
                    it is the `insertion_timestamp` of the Posting Instructions.
                """,
            ),
            types_utils.ValueSpec(
                name="posting_instructions",
                type=f"{_PITypes_str}",
                docstring="""
                    The list of posting instructions that have just been atomically committed
                    to the ledger.
                """,
            ),
            types_utils.ValueSpec(
                name="client_transactions",
                type="Dict[str, ClientTransaction]",
                docstring=f"""
                    The `ClientTransaction`s affected by the proposed posting instructions
                    that have just been committed to the ledger. Note that all the posting
                    instructions from the `hook_arguments.posting_instructions` attribute are
                    also present in the `ClientTransaction` objects in this mapping.
                    However, there may be additional posting instructions within these
                    `ClientTransaction`s (for example, `InboundAuthorisation` for proposed
                    `Settlement`), because they include all posting instructions
                    targeting the same `ClientTransaction`.
                    Returns a map of `unique_client_transaction_id` to a
                    [ClientTransaction]({_common_docs_path}classes/#ClientTransaction)
                    object, where the `unique_client_transaction_id` is the globally unique ID
                    of the `ClientTransaction`.
                    Note that each posting instruction class instance
                    has the read-only `unique_client_transaction_id` attribute, which represents
                    the `ClientTransaction` that a posting instruction is impacting. However,
                    this value is not deterministic and therefore is
                    not guaranteed to be consistent between different contract executions for
                    the same `ClientTransaction`.
                """,
            ),
        ]


class PrePostingHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        posting_instructions: _PITypes_str,  # type: ignore[valid-type]
        client_transactions: dict[str, ClientTransaction],
    ):
        super().__init__(effective_datetime)
        self.posting_instructions = posting_instructions
        self.client_transactions = client_transactions

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PrePostingHookArguments",
            docstring="The hook arguments of `pre_posting_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PrePostingHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="effective_datetime",
                type="datetime",
                docstring="""
                    The logical datetime that the hook is being run against. Must be a
                    timezone-aware UTC datetime using the ZoneInfo class. This datetime is equal to
                    the `value_timestamp` of the Posting Instructions, if set at the
                    `posting_instruction_batch` level within the [Postings API](/api/postings_api) request.
                    Otherwise, it will be equal to processing time of the Posting Instructions, which
                    will be slightly earlier than the `insertion_timestamp`.
                """,
            ),
            types_utils.ValueSpec(
                name="posting_instructions",
                type=f"{_PITypes_str}",
                docstring="""
                    The proposed list of posting instructions to be
                    committed to the ledger.
                """,
            ),
            types_utils.ValueSpec(
                name="client_transactions",
                type="Dict[str, ClientTransaction]",
                docstring=f"""
                    The `ClientTransaction`s affected by the proposed posting instructions
                    to be committed to the ledger. Note that all the posting instructions from the
                    `hook_arguments.posting_instructions` attribute are also present in
                    the `ClientTransaction` objects in this mapping. However, there may be
                    additional posting instructions within these `ClientTransaction`s
                    (for example, `InboundAuthorisation` for proposed `Settlement`), as they include
                    all posting instructions targeting the same `ClientTransaction`.
                    Returns a map of `unique_client_transaction_id` to a
                    [ClientTransaction]({_common_docs_path}classes/#ClientTransaction)
                    object, where the `unique_client_transaction_id` is the globally unique ID
                    of the `ClientTransaction`.
                    Note that each posting instruction class instance
                    has the read-only `unique_client_transaction_id` attribute, which represents
                    the `ClientTransaction` that a posting instruction is impacting. However,
                    this value is not deterministic and therefore is
                    not guaranteed to be consistent between different contract executions for
                    the same `ClientTransaction`.
                """,
            ),
        ]


class PreParameterChangeHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        updated_parameter_values: Dict[
            str,
            Optional[
                Union[
                    datetime,
                    Decimal,
                    int,
                    OptionalValue,
                    str,
                    UnionItemValue,
                ]
            ],
        ],
        effective_in: Timeline = Timeline.PRESENT,
        is_cancellation: bool = False,
    ):
        super().__init__(effective_datetime)
        self.updated_parameter_values = updated_parameter_values
        self.effective_in = effective_in
        self.is_cancellation = is_cancellation

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PreParameterChangeHookArguments",
            docstring="The hook arguments of `pre_parameter_change_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PreParameterChangeHookArguments object.",
                args=super()._public_attributes(language_code)
                + cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        effective_datetime_str = """
            The logical datetime the hook is being run against.
            The values' effective time will be within 5 seconds of this, or the same if future-dating.
            This is a timezone-aware UTC datetime using the ZoneInfo class.
        """

        update_parameter_values_str = """
            The proposed parameter value updates. This is a mapping of parameter name (for
            `INSTANCE` parameters) or ID (for `Expected` parameters) to parameter value, which may
                be None for an Optional `Expected` parameter. These values are pending and have not
                yet been committed. When the `is_cancellation` argument is `True`, the map contains the new value that
            will take effect after the parameter value is cancelled, if the cancellation is not
            rejected by the hook.
        """

        type_str = (
            "Dict[str, Optional[Union[datetime, Decimal, int, OptionalValue, str, UnionItemValue]]]"
        )

        public_attributes = [
            types_utils.ValueSpec(
                name="effective_datetime",
                type="datetime",
                docstring=effective_datetime_str,
            ),
            types_utils.ValueSpec(
                name="updated_parameter_values",
                type=type_str,
                docstring=update_parameter_values_str,
            ),
            types_utils.ValueSpec(
                name="effective_in",
                type="Timeline",
                docstring="""
                    Defines when the parameter value update is effective. For future-dated
                    parameter value updates and cancellations, this argument is set to
                    `Timeline.FUTURE`. When the update is effective in the future, the data
                    requirements and data fetchers are ignored and any calls to the Vault
                    API functions to access Vault data will raise an
                    `InvalidSmartContractError`. Defaults to `Timeline.PRESENT`.
                """,
            ),
            types_utils.ValueSpec(
                name="is_cancellation",
                type="bool",
                docstring="""
                    Defines whether the parameter value update is a cancellation of a
                    future-dated value. Defaults to `False`. When true, the `effective_in`
                    argument is always set to `Timeline.FUTURE`.
                """,
            ),
        ]

        return [
            x for x in super()._public_attributes(language_code) if x.name != "effective_datetime"
        ] + public_attributes


class ScheduledEventHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        event_type: str,
        pause_at_datetime: Optional[datetime] = None,
        
        _from_proto: bool = False,
    ):
        super().__init__(effective_datetime)
        self.event_type = event_type
        self.pause_at_datetime = pause_at_datetime
        
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        if self.pause_at_datetime is not None:
            types_utils.validate_type(
                self.pause_at_datetime,
                datetime,
                prefix="pause_at_datetime",
            )
            validate_timezone_is_utc(
                self.pause_at_datetime,
                "pause_at_datetime",
                "ScheduledEventHookArguments",
            )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ScheduledEventHookArguments",
            docstring="The hook arguments of `scheduled_event_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new ScheduledEventHookArguments object.",
                args=super()._public_attributes(language_code)
                + cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        public_attributes = super()._public_attributes(language_code) + [
            types_utils.ValueSpec(
                name="event_type",
                type="str",
                docstring="""
                    The event type for which the hook is being called. Event types are defined in
                    `activation_hook` and `conversion_hook`.
                """,
            ),
            types_utils.ValueSpec(
                name="pause_at_datetime",
                type="Optional[datetime]",
                docstring=f"""
                    The `test_pause_at_timestamp` attribute value set in
                    [AccountScheduleTag](/api/core_api/#Account_schedule_tags-AccountScheduleTag)
                    to pause the account scheduled events.
                    If multiple tags are set with different values for
                    `test_pause_at_timestamp`, the earliest datetime is used.
                    Defaults to None, if the attribute is not set or the account
                    [SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType)
                    has no `scheduler_tag_ids` applied.
                    Must be a timezone-aware UTC datetime using the ZoneInfo class.
                    Note that if an account hook is triggered via a supervisor, then the
                    supervisee `pause_at_datetime` has the value of `test_pause_at_timestamp` set on
                    the supervisor scheduled event, which overrides the account event.
                """,
            ),
        ]
        
        return public_attributes


class SupervisorPostPostingHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        supervisee_posting_instructions: Dict[str, _PITypes_str],  # type: ignore[valid-type]
        supervisee_client_transactions: Dict[str, Dict[str, ClientTransaction]],
    ):
        super().__init__(effective_datetime)
        self.supervisee_posting_instructions = supervisee_posting_instructions
        self.supervisee_client_transactions = supervisee_client_transactions

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorPostPostingHookArguments",
            docstring="The hook arguments of `post_posting_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorPostPostingHookArguments object.",
                args=super()._public_attributes(language_code)
                + cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        return super()._public_attributes(language_code) + [
            types_utils.ValueSpec(
                name="supervisee_posting_instructions",
                type=f"Dict[str, {_PITypes_str}]",
                docstring="""
                    Mapping of Supervisee Account ID to committed posting instructions list. The
                    list contains successfully committed posting instructions targetting
                    the supervisee.
                """,
            ),
            types_utils.ValueSpec(
                name="supervisee_client_transactions",
                type="Dict[str, Dict[str, ClientTransaction]]",
                docstring=f"""
                    Mapping of Supervisee Account ID to the ClientTransactions
                    that are affected by the posting instructions which just have been
                    committed. The ClientTransactions for each Supervisee is itself a map
                    of `unique_client_transaction_id` to a
                    [ClientTransaction]({_common_docs_path}classes/#ClientTransaction)
                    object, where the `unique_client_transaction_id` is the globally unique ID
                    of the ClientTransaction.
                    Note that each posting instruction class instance
                    has the read-only `unique_client_transaction_id` attribute, which represents
                    the ClientTransaction that a posting instruction is impacting. However,
                    this value is not deterministic and therefore is
                    not guaranteed to be consistent between different contract executions for
                    the same ClientTransaction.
                """,
            ),
        ]


class SupervisorPrePostingHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        supervisee_posting_instructions: Dict[str, _PITypes_str],  # type: ignore[valid-type]
        supervisee_client_transactions: Dict[str, Dict[str, ClientTransaction]],
    ):
        super().__init__(effective_datetime)
        self.supervisee_posting_instructions = supervisee_posting_instructions
        self.supervisee_client_transactions = supervisee_client_transactions

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorPrePostingHookArguments",
            docstring="The hook arguments of `pre_posting_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorPrePostingHookArguments object.",
                args=super()._public_attributes(language_code)
                + cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return super()._public_attributes(language_code) + [
            types_utils.ValueSpec(
                name="supervisee_posting_instructions",
                type=f"Dict[str, {_PITypes_str}]",
                docstring="""
                    Mapping of Supervisee Account ID to proposed list of
                    posting instructions to be committed to the ledger.
                """,
            ),
            types_utils.ValueSpec(
                name="supervisee_client_transactions",
                type="Dict[str, Dict[str, ClientTransaction]]",
                docstring=f"""
                    Mapping of Supervisee Account ID to the ClientTransactions
                    that are affected by the proposed posting instructions to be
                    committed to the ledger. The ClientTransactions for each Supervisee is
                    itself a map of `unique_client_transaction_id` to a
                    [ClientTransaction]({_common_docs_path}classes/#ClientTransaction)
                    object, where the `unique_client_transaction_id` is the globally unique ID
                    of the ClientTransaction.
                    Note that each posting instruction class instance
                    has the read-only `unique_client_transaction_id` attribute, which represents
                    the ClientTransaction that a posting instruction is impacting. However,
                    this value is not deterministic and therefore is
                    not guaranteed to be consistent between different contract executions for
                    the same ClientTransaction.
                """,
            ),
        ]


class SupervisorScheduledEventHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        event_type: str,
        supervisee_pause_at_datetime: Dict[str, Optional[datetime]],
        pause_at_datetime: Optional[datetime] = None,
        
        _from_proto: bool = False,
    ):
        super().__init__(effective_datetime)
        self.event_type = event_type
        self.supervisee_pause_at_datetime = supervisee_pause_at_datetime
        self.pause_at_datetime = pause_at_datetime
        
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        if self.pause_at_datetime is not None:
            types_utils.validate_type(
                self.pause_at_datetime,
                datetime,
                prefix="pause_at_datetime",
            )
            validate_timezone_is_utc(
                self.pause_at_datetime,
                "pause_at_datetime",
                "SupervisorScheduledEventHookArguments",
            )
        for key, supervisee_datetime in self.supervisee_pause_at_datetime.items():
            if supervisee_datetime is not None:
                types_utils.validate_type(
                    supervisee_datetime,
                    datetime,
                    prefix="supervisee_pause_at_datetime['" + key + "']",
                )
                validate_timezone_is_utc(
                    self.supervisee_pause_at_datetime[key],
                    "supervisee_pause_at_datetime['" + key + "']",
                    "SupervisorScheduledEventHookArguments",
                )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorScheduledEventHookArguments",
            docstring="The hook arguments of `scheduled_event_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorScheduledEventHookArguments object.",
                args=super()._public_attributes(language_code)
                + cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        public_attributes = super()._public_attributes(language_code) + [
            types_utils.ValueSpec(
                name="event_type",
                type="str",
                docstring="""
                    The event type for which the hook is being called. Event types are defined in
                    `activation_hook` and `conversion_hook`.
                """,
            ),
            types_utils.ValueSpec(
                name="pause_at_datetime",
                type="Optional[datetime]",
                docstring=f"""
                    The `test_pause_at_timestamp` attribute value set in
                    [AccountScheduleTag](/api/core_api/#Account_schedule_tags-AccountScheduleTag)
                    to pause the plan scheduled events.
                    If multiple tags are set with different values for
                    `test_pause_at_timestamp`, the earliest datetime is used.
                    Defaults to None if the attribute is not set or the plan
                    [SupervisorContractEventType]({_common_docs_path}classes/#SmartContractEventType)
                    has no `scheduler_tag_ids` applied.
                    Must be a timezone-aware UTC datetime using the ZoneInfo class.
                """,
            ),
            types_utils.ValueSpec(
                name="supervisee_pause_at_datetime",
                type="Dict[str, Optional[datetime]]",
                docstring="""
                    If the
                    [supervisee_hook_directives](/reference/contracts/contracts_api_4xx/supervisor_contracts_api_reference4xx/hook_requirements/#supervisee_hook_directives)
                    is set to `all`, this mapping has all the
                    Supervisee Account IDs for which `scheduled_event_hook` execution
                    was triggered, and the `pause_at_datetime` values that were used to execute the
                    supervisee `scheduled_event_hooks`. The `pause_at_datetime` values in this
                    Supervisee mapping are the same as the `test_pause_at_timestamp` set on the
                    [AccountScheduleTag](/api/core_api/#Account_schedule_tags-AccountScheduleTag)
                    to pause the plan scheduled events.
                    Supervisee datetimes must be timezone-aware and UTC using the ZoneInfo class.
                """,
            ),
        ]
        
        return public_attributes


class SupervisorActivationHookArguments(HookArguments):
    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorActivationHookArguments",
            docstring="The hook arguments of `activation_hook` for supervisors.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorActivationHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
        )


class SupervisorConversionHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        existing_schedules: Dict[str, ScheduledEvent],
    ):
        super().__init__(effective_datetime)
        self.existing_schedules = existing_schedules

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorConversionHookArguments",
            docstring="The hook arguments of `conversion_hook` for supervisors.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorConversionHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        public_attributes = super()._public_attributes(language_code)
        return public_attributes + [
            types_utils.ValueSpec(
                name="existing_schedules",
                type="Dict[str, ScheduledEvent]",
                docstring="""
                    A dictionary of EventType name to ScheduledEvent,
                    containing the existing ScheduledEvents associated
                    with the contract. Does not include disabled schedules.
                """,
            ),
        ]


class AttributeHookArguments(HookArguments):
    def __init__(self, effective_datetime: datetime, attribute_name: str):
        super().__init__(effective_datetime)
        self.attribute_name = attribute_name

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="AttributeHookArguments",
            docstring="The hook arguments of `attribute_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new AttributeHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="effective_datetime",
                type="datetime",
                docstring=f"""
                    The logical datetime that the hook is being run against. Must be a
                    timezone-aware UTC datetime using the ZoneInfo class. This corresponds to
                    the `effective_timestamps` value(s) passed to the [ListAccountAttributeValues](api/core_api#_core_api_v1_account_attributes_ListAccountAttributeValuesResponse_ListAccountAttributeValues)
                    request that is currently being processed. If there are multiple values in
                    `effective_timestamps`, the [attribute_hook]({_smart_contracts_docs_path}hooks/#attribute_hook)
                    will execute once for each value, resulting in different `effective_datetime` values
                    for each hook execution.
                """,
            ),
            types_utils.ValueSpec(
                name="attribute_name",
                type="str",
                docstring=f"""
                    The name of the [Attribute]({_common_docs_path}classes/#Attribute) that the hook is being executed for.
                    This corresponds to the `attribute_names` value(s) passed to the [ListAccountAttributeValues](api/core_api#_core_api_v1_account_attributes_ListAccountAttributeValuesResponse_ListAccountAttributeValues)
                    request that is currently being processed. If there are multiple values in
                    `attribute_names`, the [attribute_hook]({_smart_contracts_docs_path}hooks/#attribute_hook)
                    will execute once for each value, resulting in different `attribute_names` values
                    for each hook execution.
                """,
            ),
        ]





class PostParameterChangeAdjustmentHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        old_parameter_values: Dict[
            str, Optional[Union[datetime, Decimal, int, OptionalValue, str, UnionItemValue]]
        ],
        updated_parameter_values: Dict[
            str, Union[datetime, Decimal, int, OptionalValue, str, UnionItemValue]
        ],
    ):
        super().__init__(effective_datetime)
        self.old_parameter_values = old_parameter_values
        self.updated_parameter_values = updated_parameter_values

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PostParameterChangeAdjustmentHookArguments",
            docstring="The hook arguments of `post_parameter_change_adjustment_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PostParameterChangeAdjustmentHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        type_str = "Dict[str, Union[datetime, Decimal, int, OptionalValue, str, UnionItemValue]"
        old_parameter_values_type_str = type_str
        updated_parameter_values_type_str = type_str
        if is_fflag_enabled(ACCOUNTS_V2):
            old_parameter_values_type_str = (
                "Dict[str, Optional[Union[datetime, Decimal, int, OptionalValue, str, "
                "UnionItemValue]]"
            )
            updated_parameter_values_type_str = (
                "Dict[str, Union[datetime, Decimal, int, OptionalValue, str, UnionItemValue]"
            )

        return [
            x for x in super()._public_attributes(language_code) if x.name != "effective_datetime"
        ] + [
            types_utils.ValueSpec(
                name="effective_datetime",
                type="datetime",
                docstring=(
                    "The logical datetime the hook is being run against. "
                    "This is the time at which the new value(s) became effective. "
                    "This is a timezone-aware UTC datetime using the ZoneInfo class."
                ),
            ),
            types_utils.ValueSpec(
                name="old_parameter_values",
                type=old_parameter_values_type_str,
                docstring=(
                    "The old parameter values prior to the change. This is a mapping of parameter "
                    "name (for `INSTANCE` parameters) or ID (for `Expected` parameters) to parameter "
                    "value and contains only those parameters that have changed. To access the value "
                    "of any other parameter, you must fetch the Vault data using hook data "
                    "requirements and use the relevant Vault methods."
                ),
            ),
            types_utils.ValueSpec(
                name="updated_parameter_values",
                type=updated_parameter_values_type_str,
                docstring=(
                    "The updated parameter values after the change. This is a mapping of parameter "
                    "name (for `INSTANCE` parameters) or ID (for `Expected` parameters) to parameter "
                    "value and contains only those parameters that have changed. To access the value "
                    "of any other parameter, you must fetch the Vault data using hook data "
                    "requirements and use the relevant Vault methods."
                ),
            ),
        ]


class PostPostingAdjustmentHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        posting_instructions: _PITypes_str,  # type: ignore[valid-type]
        client_transactions: Dict[str, ClientTransaction],
    ):
        super().__init__(effective_datetime)
        self.posting_instructions = posting_instructions
        self.client_transactions = client_transactions

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PostPostingAdjustmentHookArguments",
            docstring="The hook arguments of `post_posting_adjustment_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PostPostingAdjustmentHookArguments object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        return [
            types_utils.ValueSpec(
                name="effective_datetime",
                type="datetime",
                docstring="""
                    The logical datetime that the hook is being run against. Must be a
                    timezone-aware UTC datetime using the ZoneInfo class. This datetime is equal to
                    the value timestamp of the posting instruction.
                """,
            ),
            types_utils.ValueSpec(
                name="posting_instructions",
                type=f"{_PITypes_str}",
                docstring="""
                    The list of posting instructions that have been atomically committed to the ledger.
                """,
            ),
            types_utils.ValueSpec(
                name="client_transactions",
                type="Dict[str, ClientTransaction]",
                docstring=f"""
                    The `ClientTransaction`s affected by the proposed posting instructions
                    that have been committed to the ledger. Note that all the posting
                    instructions from the `hook_arguments.posting_instructions` attribute are
                    also present in the `ClientTransaction` objects in this mapping.
                    However, there may be additional posting instructions within these
                    `ClientTransaction`s (for example, `InboundAuthorisation` for proposed
                    `Settlement`), because they include all posting instructions
                    targeting the same `ClientTransaction`.
                    Returns a map of `unique_client_transaction_id` to a
                    [ClientTransaction]({_common_docs_path}classes/#ClientTransaction)
                    object, where the `unique_client_transaction_id` is the globally unique ID
                    of the `ClientTransaction`.
                    Note that each posting instruction class instance
                    has the read-only `unique_client_transaction_id` attribute, which represents
                    the `ClientTransaction` that a posting instruction is impacting. However,
                    this value is not deterministic and therefore is
                    not guaranteed to be consistent between different contract executions for
                    the same `ClientTransaction`.
                """,
            ),
        ]


class ScheduledEventAdjustmentHookArguments(HookArguments):
    def __init__(
        self,
        effective_datetime: datetime,
        event_type: str,
        pause_at_datetime: Optional[datetime] = None,
        
        _from_proto: bool = False,
    ):
        super().__init__(effective_datetime)
        self.event_type = event_type
        self.pause_at_datetime = pause_at_datetime
        
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        if self.pause_at_datetime is not None:
            types_utils.validate_type(
                self.pause_at_datetime,
                datetime,
                prefix="pause_at_datetime",
            )
            validate_timezone_is_utc(
                self.pause_at_datetime,
                "pause_at_datetime",
                "ScheduledEventAdjustmentHookArguments",
            )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ScheduledEventAdjustmentHookArguments",
            docstring="The hook arguments of `scheduled_event_adjustment_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new ScheduledEventAdjustmentHookArguments object.",
                args=cls._public_attributes(language_code),
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        public_attributes = super()._public_attributes(language_code) + [
            types_utils.ValueSpec(
                name="event_type",
                type="str",
                docstring="""
                    The event type for which the hook is being called. Event types are defined in
                    `activation_hook` and `conversion_hook`.
                """,
            ),
            types_utils.ValueSpec(
                name="pause_at_datetime",
                type="Optional[datetime]",
                docstring=f"""
                    The `test_pause_at_timestamp` attribute value set in
                    [AccountScheduleTag](/api/core_api/#Account_schedule_tags-AccountScheduleTag)
                    to pause the account scheduled events.
                    If multiple tags are set with different values for
                    `test_pause_at_timestamp`, the earliest datetime is used.
                    Defaults to None, if the attribute is not set or the account
                    [SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType)
                    has no `scheduler_tag_ids` applied.
                    Must be a timezone-aware UTC datetime using the ZoneInfo class.
                    Note that if an account hook is triggered via a supervisor, then the
                    supervisee `pause_at_datetime` has the value of `test_pause_at_timestamp` set on
                    the supervisor scheduled event, which overrides the account event.
                """,
            ),
        ]
        
        return public_attributes


def _update_effective_datetime(attributes, new_docstring):
    return [attr for attr in attributes if attr.name != "effective_datetime"] + [
        types_utils.ValueSpec(
            name="effective_datetime",
            type="datetime",
            docstring=new_docstring,
        ),
    ]
