from abc import abstractmethod, ABC
from collections.abc import Mapping
from datetime import datetime
from typing import Dict, List, Optional, Union


from ..common import lib as common_lib, types as common_types
from ..common.docs import _common_docs_path
from ....utils import symbols, types_utils
from ....utils.feature_flags import (
    is_fflag_enabled,
    
    CALENDAR_FETCHERS,
    SCHEDULER_EXECUTION_TIMES,
    
    BACKDATED_ACCOUNT_OPENING,
    GET_HOOK_NAME,
    BALANCES_DISCRETE_INTERVAL_FETCHER,
)


ALLOWED_BUILTINS = common_lib.ALLOWED_BUILTINS
ALLOWED_NATIVES = common_lib.ALLOWED_NATIVES


class VaultFunctionsABC(ABC):
    @abstractmethod
    def get_last_execution_datetime(self, *, event_type: str) -> Optional[datetime]:
        pass

    @abstractmethod
    def get_posting_instructions(
        self, *, fetcher_id: Optional[str] = None
    ) -> common_types.postings.PITypes:
        pass

    @abstractmethod
    def get_client_transactions(
        self, *, fetcher_id: Optional[str] = None
    ) -> Dict[str, common_types.ClientTransaction]:
        pass

    @abstractmethod
    def get_account_creation_datetime(self) -> Optional[datetime]:
        pass

    @abstractmethod
    def get_account_activation_datetime(self) -> datetime:
        pass

    

    @abstractmethod
    def get_balances_timeseries(
        self, *, fetcher_id: Optional[str] = None
    ) -> Mapping[common_types.BalanceCoordinate, common_types.BalanceTimeseries]:
        pass

    @abstractmethod
    def get_balances_discrete_timeseries(
        self, *, fetcher_id: str
    ) -> Mapping[common_types.BalanceCoordinate, common_types.BalanceDiscreteTimeseries]:
        pass

    @abstractmethod
    def get_hook_execution_id(self) -> str:
        pass

    @abstractmethod
    def get_hook_name(self) -> common_types.HookName:
        pass

    @abstractmethod
    def get_parameter_timeseries(
        self,
        *,
        name: Optional[str] = None,
        fetcher_id: Optional[str] = None,
    ) -> Union[common_types.ParameterTimeseries, Dict[str, common_types.ParameterValueTimeseries]]:
        pass

    @abstractmethod
    def get_parameters_observation(self, *, fetcher_id: str) -> common_types.ParametersObservation:
        pass

    @abstractmethod
    def get_flags_observation(self, *, fetcher_id: str) -> common_types.FlagsObservation:
        pass

    @abstractmethod
    def get_flag_timeseries(self, *, flag: str) -> common_types.FlagTimeseries:
        pass

    @abstractmethod
    def get_flags_timeseries(
        self, *, fetcher_id: str
    ) -> dict[str, common_types.FlagValueTimeseries]:
        pass

    @abstractmethod
    def get_hook_result(
        self,
    ) -> Union[
        common_types.PostPostingHookResult,
        common_types.PrePostingHookResult,
        common_types.ScheduledEventHookResult,
    ]:
        pass

    @abstractmethod
    def get_alias(self) -> str:
        pass

    @abstractmethod
    def get_permitted_denominations(self) -> List[str]:
        pass

    @abstractmethod
    def get_calendar_events(self, *, calendar_ids: List[str]) -> common_types.CalendarEvents:
        pass

    @abstractmethod
    def get_balances_observation(self, *, fetcher_id: str) -> common_types.BalancesObservation:
        pass

    

    @abstractmethod
    def get_calendars_observation(self, *, fetcher_id: str) -> common_types.CalendarsObservation:
        pass

    @abstractmethod
    def get_calendars_timeseries(
        self, *, fetcher_id: str
    ) -> dict[str, common_types.CalendarTimeseries]:
        pass

    @abstractmethod
    def get_last_scheduled_event_datetimes_observation(
        self, *, fetcher_id: str
    ) -> common_types.LastScheduledEventDateTimesObservation:
        pass

    

    @classmethod
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        spec = types_utils.ClassSpec(
            name="VaultFunctions",
            docstring="""
                The Vault object is present during the execution of every hook and is accessible
                via the `vault` variable.

                Apart from hook-specific arguments and return values, the Vault object is the sole
                method of fetching information from Vault or communicating "hook directives" back
                to Vault.

                All information fetched from the `vault` object must have been statically declared
                at the top of a hook using the `@requires` decorator, and is fetched in a batch
                before the hook starts executing.

                All hook directives are batched until the hook finishes executing, and then
                implemented in Vault at the same time.
            """,
        )
        public_attributes = [
            types_utils.ValueSpec(
                name="account_id",
                type="str",
                docstring="The id of the Account currently being executed.",
            ),
            types_utils.ValueSpec(
                name="tside",
                type="Tside",
                docstring=f"""
                    The treasury side of the Account. It determines the Account
                    [Balance]({_common_docs_path}classes/#Balance) net sign.
                """,
            ),
            types_utils.ValueSpec(
                name="events_timezone",
                type="ZoneInfo",
                docstring="""
                    The timezone in which this Account operates.  If the account **belongs to a
                    [Processing Group](/reference/processing_groups/)** which has a timezone
                    declared, this will be the timezone used. If there is **no Processing Group timezone set**, the
                    `events_timezone`
                    [metadata](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/metadata/#events_timezone)
                    in the Contract will be used. If **neither of these is set**, the timezone defaults to UTC.
                """,
            ),
        ]
        
        

        public_attributes.sort(key=lambda x: x.name)
        for attr in public_attributes:
            spec.public_attributes[attr.name] = attr
        public_methods = [
            types_utils.MethodSpec(
                name="get_last_execution_datetime",
                docstring="""
                    Returns the effective/logical timestamp of the last successful
                    scheduled event hook execution for the given `event_type`.
                """,
                args=[
                    types_utils.ValueSpec(
                        name="event_type",
                        type="str",
                        docstring="The event type for which to fetch the last effective datetime.",
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring="""
                            The last `effective_datetime` of the last successful execution of
                            link:{baseURL}/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/hooks#scheduled_event_hook[scheduled_event_hook]
                            as a timezone-aware UTC datetime.

                            If the `event_type` has never executed successfully, returns `None`.
                        """,
                    type="Optional[datetime]",
                ),
                examples=[
                    types_utils.Example(
                        title="A simple example",
                        code="vault.get_last_execution_datetime(event_type='SERVICE_CHARGE')",
                    )
                ],
            ),
            types_utils.MethodSpec(
                name="get_posting_instructions",
                docstring=f"""
                    Gets a list of posting instruction objects, whose `value_datetime` fall within
                    the requested time window, and their covering posting instructions.
                    The default ordering of the list is by `value_datetime`; you can order/filter
                    further using the sorted builtin and other builtin mechanisms.

                    There are two main scenarios where `get_posting_instructions` can be called
                    and slightly different behaviors are expected for each:

                    **When called in a Smart Contract hook using `@fetch_account_data` decorator**,
                    only the posting instructions that fall into the requested time range and their
                    covering posting instructions are returned. A `fetcher_id` must be specified in
                    the [postings](../account_fetcher_requirements/#postings) argument of the
                    `@fetch_account_data` decorator and passed as an argument in the
                    `get_posting_instructions` function call. The time window must be specified in
                    the definition of the
                    [PostingsIntervalFetcher]({_common_docs_path}classes/#PostingsIntervalFetcher)
                    with the specified `fetcher_id` in the
                    [data_fetchers](../../smart_contracts_api_reference4xx/metadata/#data_fetchers)
                    list of the Contract metadata.

                    **When called in a Supervisor Contract hook using `@requires` decorator, on a
                    supervisee vault object**, it returns the posting instructions that falls
                    into the requested time range and their covering posting instructions. If called
                    in the pre/post posting hooks it also returns the covering posting instructions
                    for the proposed posting instructions. A `fetcher_id` must not be passed.

                    If a duration is specified in the `@requires` decorator, the time window
                    size is in the range
                    `[hook_effective_date - requirement_duration, hook_effective_date]`.
                """,
                args=[
                    types_utils.ValueSpec(
                        name="fetcher_id",
                        type="Optional[str]",
                        docstring=f"""
                            The id of the
                            [PostingsIntervalFetcher]({_common_docs_path}classes/#PostingsIntervalFetcher).
                            1. Define the fetcher in the [Contract Metadata](../metadata/)
                            [data_fetchers](../../smart_contracts_api_reference4xx/metadata/#data_fetchers)
                            list. 2. Define the fetcher
                            id in the postings argument in the `@fetch_account_data` decorator.
                            Required when the `@fetch_account_data` decorator is used, must be None
                            otherwise.
                        """,
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring="""
                        The sorted list of posting instructions.
                    """,
                    type=common_types.postings._PITypes_str,  # noqa: SLF001
                ),
                examples=[
                    types_utils.Example(
                        title="An example with `@fetch_account_data` decorator in Smart Contracts",
                        code="""
                            @fetch_account_data(postings=["fetcher_id"])
                            def post_posting_hook(vault, hook_arguments):
                                # Raises InvalidSmartContractError
                                vault.get_posting_instructions()
                                # Returns posting instructions in the range defined in the fetcher
                                # and their covering posting instructions.
                                vault.get_posting_instructions(fetcher_id="fetcher_id")
                                # Raises InvalidSmartContractError
                                vault.get_posting_instructions(fetcher_id="fetcher_not_in_decorator")
                        """,
                    ),
                    types_utils.Example(
                        title="An example with no decorator in Smart Contracts",
                        code="""
                            def post_posting_hook(vault, hook_arguments):
                                # Raises InvalidSmartContractError
                                vault.get_posting_instructions()
                                # Raises InvalidSmartContractError
                                vault.get_posting_instructions(fetcher_id="fetcher_id")
                        """,
                    ),
                    types_utils.Example(
                        title="An example with `@requires` decorator in Supervisor Contracts",
                        code="""
                            @requires(postings="1 month", data_scope="invoked")
                            def post_posting_hook(vault, hook_arguments):
                                for account_id, supervisee in vault.supervisees.items():
                                    # Returns the posting instructions in the required range and
                                    # their covering posting instructions.
                                    # In the pre/post posting hooks, it also returns any covering
                                    # posting instructions of the proposed posting instructions.
                                    vault.get_posting_instructions()
                                    # Raises InvalidSmartContractError
                                    vault.get_posting_instructions(fetcher_id="fetcher_id")
                        """,
                    ),
                    types_utils.Example(
                        title="An example with no decorator in Supervisor Contracts",
                        code="""
                            def post_posting_hook(vault, hook_arguments):
                                for account_id, supervisee in vault.supervisees.items():
                                    # In the pre/post posting hooks, it returns any covering
                                    # posting instructions of the proposed posting instruction.
                                    # In any other hooks, it returns an empty list.
                                    supervisee.get_posting_instructions()
                                    # Raises InvalidSmartContractError.
                                    supervisee.get_posting_instructions(fetcher_id="fetcher_id")
                        """,
                    ),
                ],
            ),
            types_utils.MethodSpec(
                name="get_client_transactions",
                docstring=f"""
                    Gets a map of the `unique_client_transaction_id` to
                    [ClientTransaction]({_common_docs_path}classes/#ClientTransaction) objects,
                    with the `value_datetime` of at least one of its posting instructions falling
                    in the requested time window. Note that each posting instruction class instance
                    has the read-only `unique_client_transaction_id` attribute, representing
                    the ClientTransaction that a posting instruction is impacting, which can be used
                    as key in this map. However, the `unique_client_transaction_id` value is
                    not deterministic and therefore is not guaranteed to be consistent between
                    different contract executions for the same ClientTransaction.
                    If a duration is specified in the `@requires` decorator, the time window size is
                    in the range
                    `[hook_effective_date - requirement_duration, hook_effective_date]`.
                    If a `fetcher_id` is specified in the
                    [postings](../account_fetcher_requirements/#postings) argument of the
                    `@fetch_account_data` decorator and passed as an argument in the
                    `get_client_transactions` function call, then the time window is specified in
                    the definition of the
                    [PostingsIntervalFetcher]({_common_docs_path}classes/#PostingsIntervalFetcher) with the
                    specified `fetcher_id` in the
                    [data_fetchers](../../smart_contracts_api_reference4xx/metadata/#data_fetchers)
                    list of the Contract metadata. If `fetcher_id` is not provided in the Smart Contract, an
                    `InvalidSmartContractError` is raised. The default ordering of the list of
                    posting instructions in each
                    [ClientTransaction]({_common_docs_path}classes/#ClientTransaction), is by
                    `value_datetime`; you can order/filter further using the sorted builtin and
                    other builtin mechanisms.
                    A [PostingIntervalFetcher]({_common_docs_path}classes/#PostingsIntervalFetcher)
                    only fetches postings that have been committed. Before postings are committed,
                    the `pre_posting_hook` is run. At this point, in `pre_posting_hook`, `PostingsIntervalFetcher`
                    does not return the proposed postings as they are not committed yet - you access them through
                    the hook arguments. After postings are committed, in `post_posting_hook`, committed postings
                    are returned if they fall inside the fetcher window; you can also access them through hook arguments.
                """,
                args=[
                    types_utils.ValueSpec(
                        name="fetcher_id",
                        type="Optional[str]",
                        docstring=f"""
                            The id of the
                            [PostingsIntervalFetcher]({_common_docs_path}classes/#PostingsIntervalFetcher).
                            1. Define the fetcher in the [Contract Metadata](../metadata/)
                            [data_fetchers](../../smart_contracts_api_reference4xx/metadata/#data_fetchers)
                            list. 2. Define the fetcher id in the postings argument in the
                            `@fetch_account_data` decorator. If this function is called using a
                            supervisee Vault object, the population
                            of this argument will raise an `InvalidSmartContractError`.
                        """,
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring=f"""
                        The [ClientTransaction]({_common_docs_path}classes/#ClientTransaction) dictionary,
                        keyed by the `unique_client_transaction_id`.
                    """,
                    type="Dict[str, ClientTransaction]",
                ),
                examples=[],
            ),
            types_utils.MethodSpec(
                name="get_account_creation_datetime",
                docstring="""
                    Returns the date that the Account was created.

                    If the Account has not yet been created, this will return `None` in the
                    `activation_hook` but will return a timestamp in all other hooks.

                    If the Account has been created, this returns the `source_create_timestamp`
                    field of the v2 account resource. In the v1 account resource, the timestamp
                    does not correspond to any specific field.

                    **Note**: If the Account was migrated using the
                    link:{baseURL}/environment_and_installation/migrating_to_vault/migrating_using_the_data_loader_api[Data Loader],
                    this is the date the account was created in the legacy core,
                    not when it was migrated and inserted into Vault Core.
                """,
                args=[],
                return_value=types_utils.ReturnValueSpec(
                    docstring="""
                        The Account creation date as a timezone-aware UTC datetime.
                        The return value from this method will never be later than the
                        `effective_datetime` of a Smart Contract hook, including the
                        `activation_hook`. Do not use this method as the `start_datetime`
                        for any schedules returned by any hooks; instead use a future
                        datetime for schedule `start_datetime`s.

                        If the account is created in PENDING first and then updated into the OPEN
                        state, then OPEN will cause this method to return a datetime in the
                        `activation_hook`. If the account is created via the v2 endpoints, and
                        in the OPEN state directly, then this method will return `None` in the
                        `activation_hook`, but will return a datetime in all other hooks.

                        It is encouraged to replace all usage of `get_account_creation_datetime` with
                        `get_account_activation_datetime` instead, as the latter returns when the Account
                        first became active, irrespective of how it was created.
                        """,
                    type="Optional[datetime]",
                ),
            ),
            types_utils.MethodSpec(
                name="get_balances_timeseries",
                docstring=f"""
                    Returns a Python mapping object, mapping
                    [BalanceCoordinate]({_common_docs_path}classes/#BalanceCoordinate) to
                    [BalanceTimeseries]({_common_docs_path}classes/#BalanceTimeseries) covering
                    all balances over the time period specified by the hook decorator.

                    There are three main scenarios where `get_balances_timeseries` can be
                    called and slightly different behaviors are expected for each:

                    **When called in a Smart Contract hook using `@fetch_account_data`
                    decorator**, a `fetcher_id` must be specified in the
                    [balances](../account_fetcher_requirements/#balances) argument of the
                    `@fetch_account_data` decorator and passed as an argument in the function call
                    and the time window is specified in the definition of the
                    [BalancesIntervalFetcher]({_common_docs_path}classes/#BalancesIntervalFetcher)
                    with the specified `fetcher_id` in the
                    [data_fetchers](../../smart_contracts_api_reference4xx/metadata/#data_fetchers)
                    list of the Contract metadata.

                    **When called in a Supervisor Contract hook using `@fetch_account_data`
                    decorator, on a supervisee vault object**, a `fetcher_id` must be passed as
                    an argument.

                    **When called in a Supervisor Contract hook using `@requires` decorator, on a
                    supervisee vault object**, `fetcher_id` must not be passed as an argument. When
                    a duration is specified in the `@requires` decorator, the time window size is in
                    the range
                    `[hook_effective_date - requirement_duration, hook_effective_date]`.

                    Note that, for performance reasons, each timeseries is lazy evaluated. Whilst it
                    is possible, iterating over all keys/items is not recommended. If a given
                    BalanceCoordinate object does not exist in the mapping, an empty
                    BalanceTimeseries will be returned.
                """,
                args=[
                    types_utils.ValueSpec(
                        name="fetcher_id",
                        type="Optional[Union[str, Dict[str,list[str]]]",
                        docstring=f"""
                            The id of the
                            [BalancesIntervalFetcher]({_common_docs_path}classes/#BalancesIntervalFetcher).
                            1. Define the fetcher in the [Contract Metadata](../metadata/)
                            [data_fetchers](../../smart_contracts_api_reference4xx/metadata/#data_fetchers)
                            list.
                            2. Define the fetcher id in the balances argument in the
                            `@fetch_account_data` decorator.
                            Required when the `@fetch_account_data` decorator is used, must be None
                            otherwise.
                        """,
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring="A dictionary of balance coordinates to timeseries of balances.",
                    type="Mapping[BalanceCoordinate, BalanceTimeseries]",
                ),
                examples=[
                    types_utils.Example(
                        title="An example with `@fetch_account_data` decorator in Smart Contracts",
                        code="""
                            @fetch_account_data(balances=["fetcher_id"])
                            def conversion_hook(vault, hook_arguments):
                                # Raises InvalidSmartContractError.
                                vault.get_balances_timeseries()
                                # Returns defaultdict[BalanceCoordinate, BalanceTimeseries]
                                # in range defined in the fetcher.
                                vault.get_balances_timeseries(fetcher_id="fetcher_id")
                                # Raises InvalidSmartContractError.
                                vault.get_balances_timeseries(fetcher_id="fetcher_not_in_decorator")
                        """,
                    ),
                    types_utils.Example(
                        title="An example with no decorator in Smart Contracts",
                        code="""
                            def conversion_hook(vault, hook_arguments):
                                # Raises InvalidSmartContractError.
                                vault.get_balances_timeseries()
                                # Raises InvalidSmartContractError.
                                vault.get_balances_timeseries(fetcher_id="fetcher_id")
                        """,
                    ),
                    types_utils.Example(
                        title="""
                        An example with `@fetch_account_data` decorator in Supervisor Contracts
                        pre_posting_hook
                        """,
                        code="""
                            @fetch_account_data(balances={"alias1": ["bif_s1"]})
                            def pre_posting_hook(vault, hook_arguments):
                                for account_id, supervisee in vault.supervisees.items():
                                    # Returns defaultdict[BalanceCoordinate, BalanceTimeseries]
                                    # in required range.
                                    supervisee.get_balances_timeseries(fetcher_id="bif_s1")
                                    # Raises InvalidSmartContractError.
                                    supervisee.get_balances_timeseries(fetcher_id="bif_s2")
                                    # Raises InvalidSmartContractError.
                                    supervisee.get_balances_timeseries()
                        """,
                    ),
                    types_utils.Example(
                        title="An example with `@requires` decorator in Supervisor Contracts",
                        code="""
                            @requires(data_scope="all", balances="1 month")
                            def conversion_hook(vault, hook_arguments):
                                for account_id, supervisee in vault.supervisees.items():
                                    # Returns defaultdict[BalanceCoordinate, BalanceTimeseries]
                                    # in required range.
                                    supervisee.get_balances_timeseries()
                                    # Raises InvalidSmartContractError.
                                    supervisee.get_balances_timeseries(fetcher_id="fetcher_id")
                        """,
                    ),
                    types_utils.Example(
                        title="An example with no decorator in Supervisor Contracts",
                        code="""
                            def conversion_hook(vault, hook_arguments):
                                for account_id, supervisee in vault.supervisees.items():
                                    # Returns empty results.
                                    supervisee.get_balances_timeseries()
                                    # Raises InvalidSmartContractError.
                                    supervisee.get_balances_timeseries(fetcher_id="fetcher_id")
                        """,
                    ),
                ],
            ),
            types_utils.MethodSpec(
                name="get_hook_execution_id",
                docstring="""
                    Returns a string used in generating unique-enough ids
                    for attaching to side-effect
                    objects. The string returned is a combination of
                    account_id, hook, and effective_datetime.
                """,
                args=[],
                return_value=types_utils.ReturnValueSpec(
                    docstring="The unique-enough id.", type="str"
                ),
            ),
            types_utils.MethodSpec(
                name="get_flags_observation",
                docstring=f"""
                    Returns the
                    [FlagsObservation]({_common_docs_path}classes/#FlagsObservation)
                    at the datetime defined by the
                    [FlagsObservationFetcher]({_common_docs_path}classes/#FlagsObservationFetcher)
                    whose id is provided in the
                    [flags](../account_fetcher_requirements/#flags) argument of the
                    `@fetch_account_data` decorator.
                """,
                args=[
                    types_utils.ValueSpec(
                        name="fetcher_id",
                        type="str",
                        docstring=f"The id of the [FlagsObservationFetcher]({_common_docs_path}classes/#FlagsObservationFetcher).",
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring=f"""
                    The observation which includes the flag values and the datetime at which the values apply.
                    The flags attribute of the [FlagsObservation]({_common_docs_path}classes/#FlagsObservation)
                    has type defaultdict if the
                    [FlagsObservationFetcher]({_common_docs_path}classes/#FlagsObservationFetcher) did not
                    specify a [FlagsFilter]({_common_docs_path}classes/#FlagsFilter). Otherwise, the flags
                    attribute has type dict, containing an entry for each of the flag definition ids specified
                    in the [FlagsFilter]({_common_docs_path}classes/#FlagsFilter).
                    """,
                    type="FlagsObservation",
                ),
                examples=[
                    types_utils.Example(
                        title="An example with @fetch_account_data decorator",
                        code="""
                        @fetch_account_data(flags=["flags_observation_fetcher"])
                        def post_posting_hook(vault, hook_arguments):
                            # Raises InvalidSmartContractError.
                            vault.get_flags_observation()
                            # Returns FlagsObservation for flags specified in the observation fetcher.
                            vault.get_flags_observation(fetcher_id="flags_observation_fetcher")
                            # Raises InvalidSmartContractError.
                            vault.get_flags_observation(fetcher_id="fetcher_not_in_decorator")
                    """,
                    ),
                ],
            ),
            types_utils.MethodSpec(
                name="get_flags_timeseries",
                docstring=f"""
                    Returns the
                    [FlagValueTimeseries]({_common_docs_path}classes/#FlagValueTimeseries)
                    at the datetime defined by the
                    [FlagsIntervalFetcher]({_common_docs_path}classes/#FlagsIntervalFetcher)
                    whose id is provided in the
                    [flags](../account_fetcher_requirements/#flags) argument of the
                    `@fetch_account_data` decorator.
                """,
                args=[
                    types_utils.ValueSpec(
                        name="fetcher_id",
                        type="str",
                        docstring=f"The id of the [FlagsIntervalFetcher]({_common_docs_path}classes/#FlagsIntervalFetcher). "
                        "If the provided fetcher_id is not defined in the @fetch_account_data "
                        "decorator, an `InvalidSmartContractError` will be raised.",
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring=f"""
                    A dictionary mapping the flag definition ids to the FlagValueTimeseries. The dictionary
                    has type defaultdict if the
                    [FlagsIntervalFetcher]({_common_docs_path}classes/#FlagsIntervalFetcher) did not specify
                    a [FlagsFilter]({_common_docs_path}classes/#FlagsFilter). Otherwise, the dictionary has
                    type dict, containing an entry for each of the flag definition ids specified in the
                    [FlagsFilter]({_common_docs_path}classes/#FlagsFilter). In either case, the default value
                    stored in the dictionary is a
                    [FlagValueTimeseries]({_common_docs_path}classes/#FlagValueTimeseries) containing a
                    [TimeseriesItem]({_common_docs_path}classes/#TimeseriesItem) with value False effective
                    from the start time defined in the fetcher.
                    """,
                    type="Union[dict[str, FlagValueTimeseries], defaultdict[str, FlagValueTimeseries]]",
                ),
                examples=[
                    types_utils.Example(
                        title="An example with `@fetch_account_data` decorator",
                        code="""
                        @fetch_account_data(flags=["flags_interval_fetcher"])
                        def post_posting_hook(vault, hook_arguments):
                            # Raises InvalidSmartContractError.
                            vault.get_flags_timeseries()
                            # Returns Dict[str, FlagValueTimeseries] for flags specified in the interval fetcher.
                            vault.get_flags_timeseries(fetcher_id="flags_interval_fetcher")
                            # Raises InvalidSmartContractError.
                            vault.get_flags_timeseries(fetcher_id="fetcher_not_in_decorator")
                    """,
                    ),
                ],
            ),
            types_utils.MethodSpec(
                name="get_parameter_timeseries",
                docstring=f"""
                    Get a timeseries of parameter values for parameters defined and/or used by
                    this Smart Contract.

                    If `name` is provided as an argument, the timeseries returned will be of
                    type [ParameterTimeseries]({_common_docs_path}classes/#ParameterTimeseries). In this
                    case, `parameters=True` must also be specified in the `@requires` decorator,
                    otherwise any call to this function will fail.

                    If `fetcher_id` is provided as an argument, this returns a map of parameter
                    id to [ParameterValueTimeseries]({_common_docs_path}classes/#ParameterValueTimeseries)
                    within the time interval defined by the
                    [ParametersIntervalFetcher]({_common_docs_path}classes/#ParametersIntervalFetcher)
                    whose id is provided in the
                    [parameters](../account_fetcher_requirements/#parameters) argument of the
                    `@fetch_account_data` decorator. If the matching `ParametersIntervalFetcher`
                    does not have a defined `ParametersFilter`, all of the `expected_parameters`
                    defined in the contract will be retrieved.

                    Values for derived parameters are not returned from this function.
                """,
                args=[
                    types_utils.ValueSpec(
                        name="name",
                        type="Optional[str]",
                        docstring=f"""
                            The name of the [Parameter]({_common_docs_path}classes/#Parameter). One of
                            `name` or `fetcher_id` must be provided.
                        """,
                    ),
                    types_utils.ValueSpec(
                        name="fetcher_id",
                        type="Optional[str]",
                        docstring=f"""
                            The id of the
                            [ParametersIntervalFetcher]({_common_docs_path}classes/#ParametersIntervalFetcher).
                            One of `name` or `fetcher_id` must be provided.
                        """,
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring=f"""
                        The timeseries of parameters. If `name` is provided, the timeseries will
                        be of type
                        [ParameterTimeseries]({_common_docs_path}classes/#ParameterTimeseries).
                        If `fetcher_id` is provided, the timeseries will be a map of parameter IDs to
                        [ParameterValueTimeseries]({_common_docs_path}classes/#ParameterValueTimeseries).
                    """,
                    type="Union[ParameterTimeseries, Dict[str, ParameterValueTimeseries]]",
                ),
            ),
            types_utils.MethodSpec(
                name="get_parameters_observation",
                docstring=f"""
                    Returns the
                    [ParametersObservation]({_common_docs_path}classes/#ParametersObservation)
                    at the datetime defined by the
                    [ParametersObservationFetcher]({_common_docs_path}classes/#ParametersObservationFetcher)
                    whose id is provided in the
                    [parameters](../account_fetcher_requirements/#parameters) argument of the
                    `@fetch_account_data` decorator.
                """,
                args=[
                    types_utils.ValueSpec(
                        name="fetcher_id",
                        type="str",
                        docstring=f"""
                            The id of the
                            [ParametersObservationFetcher]({_common_docs_path}classes/#ParametersObservationFetcher).
                        """,
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring="""
                        The observation which includes the parameter values and the datetime at
                        which the values apply.
                    """,
                    type="ParametersObservation",
                ),
            ),
            types_utils.MethodSpec(
                name="get_flag_timeseries",
                docstring="""
                    Get the FlagTimeseries for a given flag definition.

                    If `flags=True` is not specified in the `@requires` decorator, any call
                    to this function will return an empty FlagTimeseries.
                """,
                args=[
                    types_utils.ValueSpec(
                        name="flag",
                        type="str",
                        docstring="The `flag_definition_id` to get the timeseries for.",
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring="The timeseries of flags.", type="FlagTimeseries"
                ),
            ),
            types_utils.MethodSpec(
                name="get_hook_result",
                docstring="""
                    Returns the Supervisee Hook Result. Available for use only on the Supervisees
                    [Vault](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/)
                    object. This function allows the Supervisor Hook to access any Supervisee Hook
                    uncommitted `HookDirectives`, `Rejections` or Return Data.
                """,
                args=[],
                return_value=types_utils.ReturnValueSpec(
                    docstring="The Supervisee Hook Result",
                    type="Union[PostPostingHookResult, PrePostingHookResult, "
                    "ScheduledEventHookResult]",
                ),
                examples=[
                    types_utils.Example(
                        title="An example with Rejection.",
                        code="""
                        # Supervisor Hook.
                        def pre_posting_hook(vault, hook_arguments):
                            for account_id, supervisee in vault.supervisees.items():
                                supervisee_hook_result = supervisee.get_hook_result()
                                # Check if Supervisee Hook returned Rejection.
                                if supervisee_hook_result.rejection:
                                    return SupervisorPrePostingHookResult(
                                        rejection=Rejection(
                                            message=(
                                                f"Supervisee Hook with account_id {account_id} "
                                                "Returned Rejection"
                                            ),
                                            reason_code=RejectionReason.AGAINST_TNC
                                        )
                                    )
                        """,
                    ),
                    types_utils.Example(
                        title="An example with Directives.",
                        code="""
                        # Supervisor Hook.
                        def scheduled_event_hook(vault, hook_arguments):
                            # Access and re-instruct Supervisee Hook Directives.
                            supervisee_posting_instructions_directives = {}
                            for account_id, supervisee in vault.supervisees.items():
                                supervisee_posting_instructions_directives[account_id] = []
                                supervisee_hook_result = supervisee.get_hook_result()
                                for (
                                    posting_instruction_directive
                                    in supervisee_hook_result.posting_instructions_directives
                                ):
                                    supervisee_posting_instructions_directives[account_id].append(
                                        posting_instructions_directive
                                    )

                            return SupervisorScheduledEventHookResult(
                                supervisee_posting_instructions_directives=(
                                    supervisee_posting_instructions_directives
                                )
                            )
                        """,
                    ),
                ],
            ),
            types_utils.MethodSpec(
                name="get_alias",
                docstring=f"""
                    Returns the alias value set for the Smart Contract Version in the Supervisor
                    [SmartContractDescriptor]({_common_docs_path}classes/#SmartContractDescriptor)
                    object. Available in Supervisor Contract code for use on the Supervisee's
                    [Vault](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/)
                    object only. If no aliases are defined in the
                    Supervisor Contract metadata, then 'None' is returned. It cannot be used on a
                    non-supervised Vault object.
                """,
                args=[],
                return_value=types_utils.ReturnValueSpec(
                    docstring="The Supervisee Smart Contract Version alias.", type="str"
                ),
            ),
            types_utils.MethodSpec(
                name="get_permitted_denominations",
                docstring="""
                    Returns the permitted denominations of the account.
                """,
                args=[],
                return_value=types_utils.ReturnValueSpec(
                    docstring="A list of denominations.", type="List[str]"
                ),
            ),
            types_utils.MethodSpec(
                name="get_calendar_events",
                docstring=f"""
                    Returns a [CalendarEvents]({_common_docs_path}classes/#CalendarEvents) object with the
                    chronologically ordered list of [CalendarEvent]({_common_docs_path}classes/#CalendarEvent)
                    that exist in the Vault calendars with the given `calendar_ids`. These
                    `calendar_ids` have to be requested using the hook '@requires' decorator.
                    For information about the time range of events returned,
                    see [calendar](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/hook_requirements/#calendar)
                """,
                args=[
                    types_utils.ValueSpec(
                        name="calendar_ids", type="List[str]", docstring="List of Calendar Ids"
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring=f"""
                        The chronologically ordered list of
                        [CalendarEvent]({_common_docs_path}classes/#CalendarEvent) objects.
                    """,
                    type="CalendarEvents",
                ),
                examples=[
                    types_utils.Example(
                        title="The Vault calendar usage example",
                        code="""
                        @requires(calendar=["WEEKENDS", "BANK_HOLIDAYS", "PROMOTION_DAYS"])
                        def activation_hook(vault, hook_arguments):
                            vault.get_calendar_events(calendar_ids=["WEEKENDS", "BANK_HOLIDAYS"])
                        """,
                    )
                ],
            ),
            types_utils.MethodSpec(
                name="get_balances_observation",
                docstring=f"""
                    Returns the [BalancesObservation]({_common_docs_path}classes/#BalancesObservation) at the
                    datetime defined by the
                    [BalancesObservationFetcher]({_common_docs_path}classes/#BalancesObservationFetcher)
                    whose id is provided in the
                    [balances](../account_fetcher_requirements/#balances) argument of the
                    `@fetch_account_data` decorator.
                """,
                args=[
                    types_utils.ValueSpec(
                        name="fetcher_id",
                        type="str",
                        docstring=f"""
                            The id of the
                            [BalancesObservationFetcher]({_common_docs_path}classes/#BalancesObservationFetcher).
                            1. Define the fetcher in the [Contract Metadata](../metadata/)
                            [data_fetchers](../../smart_contracts_api_reference4xx/metadata/#data_fetchers)
                            list. 2. Define the fetcher id in the balances argument in the
                            `@fetch_account_data` decorator.
                        """,
                    ),
                ],
                return_value=types_utils.ReturnValueSpec(
                    docstring="""
                        The observation which includes the Balances and the datetime at which the
                        values apply.
                    """,
                    type="BalancesObservation",
                ),
                examples=[
                    types_utils.Example(
                        title="An example with no decorator",
                        code="""
                            def activation_hook(vault, hook_arguments):
                                # Raises InvalidSmartContractError
                                vault.get_balances_observation()
                                # Raises InvalidSmartContractError
                                vault.get_balances_observation(fetcher_id="fetcher_id")
                        """,
                    ),
                    types_utils.Example(
                        title="An example with @requires decorator",
                        code="""
                            @requires(balances="1 month")
                            def activation_hook(vault, hook_arguments):
                                # Raises InvalidSmartContractError
                                vault.get_balances_observation()
                                # Raises InvalidSmartContractError
                                vault.get_balances_observation(fetcher_id="fetcher_id")
                        """,
                    ),
                    types_utils.Example(
                        title="An example with `@fetch_account_data` decorator",
                        code="""
                            @fetch_account_data(balances=["fetcher_id"])
                            def activation_hook(vault, hook_arguments):
                                # Raises InvalidSmartContractError
                                vault.get_balances_observation()
                                # Returns BalancesObservation at the datetime defined in the
                                # fetcher
                                vault.get_balances_observation(fetcher_id="fetcher_id")
                                # Raises InvalidSmartContractError
                                vault.get_balances_observation(fetcher_id="fetcher_not_in_decorator")
                        """,
                    ),
                ],
            ),
        ]
        

        if is_fflag_enabled(CALENDAR_FETCHERS):
            public_methods += [
                types_utils.MethodSpec(
                    name="get_calendars_observation",
                    docstring=f"""
                        Returns the
                        [CalendarsObservation]({_common_docs_path}classes/#CalendarsObservation)
                        at the datetime defined by the
                        [CalendarsObservationFetcher]({_common_docs_path}classes/#CalendarsObservationFetcher)
                        whose id is provided in the
                        [calendars](../account_fetcher_requirements/#calendars) argument of the
                        `@fetch_account_data` decorator.
                    """,
                    args=[
                        types_utils.ValueSpec(
                            name="fetcher_id",
                            type="str",
                            docstring=f"The id of the [CalendarsObservationFetcher]({_common_docs_path}classes/#CalendarsObservationFetcher).",
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        docstring="""
                            The observation which includes the active calendar events and the datetime at which the
                            values apply.
                        """,
                        type="CalendarsObservation",
                    ),
                    examples=[
                        types_utils.Example(
                            title="An example with @fetch_account_data decorator",
                            code="""
                                @fetch_account_data(calendars=["calendars_observation_fetcher"])
                                def post_posting_hook(vault, hook_arguments):
                                    # Raises InvalidSmartContractError.
                                    vault.get_calendars_observation()
                                    # Returns CalendarsObservation for calendars specified in the observation fetcher.
                                    vault.get_calendars_observation(fetcher_id="calendars_observation_fetcher")
                                    # Raises InvalidSmartContractError.
                                    vault.get_calendars_observation(fetcher_id="fetcher_not_in_decorator")
                            """,
                        ),
                    ],
                ),
                types_utils.MethodSpec(
                    name="get_calendars_timeseries",
                    docstring=f"""
                        Returns the
                        [CalendarTimeseries]({_common_docs_path}classes/#CalendarTimeseries)
                        for the interval defined by the
                        [CalendarsIntervalFetcher]({_common_docs_path}classes/#CalendarsIntervalFetcher)
                        whose id is provided in the
                        [calendars](../account_fetcher_requirements/#calendars) argument of the
                        `@fetch_account_data` decorator.
                    """,
                    args=[
                        types_utils.ValueSpec(
                            name="fetcher_id",
                            type="str",
                            docstring=f"The id of the [CalendarsIntervalFetcher]({_common_docs_path}classes/#CalendarsIntervalFetcher).",
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        docstring="A dictionary mapping the calendar IDs to the CalendarTimeseries.",
                        type="Dict[str, CalendarTimeseries]",
                    ),
                    examples=[
                        types_utils.Example(
                            title="An example with `@fetch_account_data` decorator",
                            code="""
                        @fetch_account_data(calendars=["calendars_interval_fetcher"])
                        def post_posting_hook(vault, hook_arguments):
                            # Raises InvalidSmartContractError.
                            vault.get_calendars_timeseries()
                            # Returns Dict[str, CalendarTimeseries] for calendars specified in the interval fetcher.
                            vault.get_calendars_timeseries(fetcher_id="calendars_interval_fetcher")
                            # Raises InvalidSmartContractError.
                            vault.get_calendars_timeseries(fetcher_id="fetcher_not_in_decorator")
                    """,
                        ),
                    ],
                ),
            ]

        if is_fflag_enabled(SCHEDULER_EXECUTION_TIMES):
            public_methods += [
                types_utils.MethodSpec(
                    name="get_last_scheduled_event_datetimes_observation",
                    docstring=f"""
                        Returns the [LastScheduledEventDateTimesObservation]({_common_docs_path}classes/#LastScheduledEventDateTimesObservation) at the
                        datetime defined by the
                        [LastScheduledEventDateTimesObservationFetcher]({_common_docs_path}classes/#LastScheduledEventDateTimesObservation)
                        whose id is provided in the
                        [last_scheduled_event_datetimes](../account_fetcher_requirements/#last_scheduled_event_datetimes) argument of the
                        `@fetch_account_data` decorator.

                        [IMPORTANT]
                        ====
                        Existing Customer Accounts cannot be converted to a Smart Contract with
                        [LastScheduledEventDateTimesObservationFetcher]({_common_docs_path}classes/#LastScheduledEventDateTimesObservationFetcher)
                        if their current Smart Contract is not already using it, due to data access limitations.
                        Future Vault Core improvements aim to address these limitations.
                        ====
                    """,
                    args=[
                        types_utils.ValueSpec(
                            name="fetcher_id",
                            type="str",
                            docstring=f"""
                                The id of the
                                [LastScheduledEventDateTimesObservationFetcher]({_common_docs_path}classes/#LastScheduledEventDateTimesObservationFetcher).
                                1. Define the fetcher in the [Contract Metadata](../metadata/)
                                [data_fetchers](../../smart_contracts_api_reference4xx/metadata/#data_fetchers) list.
                                2. Define the fetcher id in the last_scheduled_event_datetimes argument in the `@fetch_account_data` decorator.
                            """,
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        docstring="""
                            The observation which includes the last scheduled event datetimes and the datetime at
                            which the values apply.
                        """,
                        type="LastScheduledEventDateTimesObservation",
                    ),
                    examples=[
                        types_utils.Example(
                            title="An example with @fetch_account_data decorator",
                            code="""
                                @fetch_account_data(last_scheduled_event_datetimes=["fetcher_id"])
                                def post_posting_hook(vault, hook_arguments):
                                    # Raises InvalidSmartContractError.
                                    vault.get_last_scheduled_event_datetimes_observation()
                                    # Returns LastScheduledEventDateTimesObservation for event types specified in the observation fetcher.
                                    vault.get_last_scheduled_event_datetimes_observation(fetcher_id="fetcher_id")
                                    # Raises InvalidSmartContractError.
                                    vault.get_last_scheduled_event_datetimes_observation(fetcher_id="fetcher_not_in_decorator")
                            """,
                        ),
                    ],
                ),
            ]

        if is_fflag_enabled(BACKDATED_ACCOUNT_OPENING):
            public_methods.append(
                types_utils.MethodSpec(
                    name="get_account_activation_datetime",
                    docstring="""
                    Returns the Account's activation date, stored in the `activation_timestamp` field.
                    """,
                    args=[],
                    return_value=types_utils.ReturnValueSpec(
                        docstring="""
                        The Account's `activation_timestamp` is a timezone-aware UTC datetime, and it's equivalent to the `effective_datetime` of the Smart Contract's `activation_hook`'s `ActivationHookArguments`. The `activation_timestamp` can be set to a time in the past when creating an account. The `start_datetime` of any schedules for this Account must be greater than or equal to the `activation_timestamp`.

                        Best practice is to use `get_account_activation_datetime` instead of `get_account_creation_datetime` in contracts. This ensures you get the Account's actual activation time, regardless of how it was created.
                        """,
                        type="datetime",
                    ),
                ),
            )

        if is_fflag_enabled(GET_HOOK_NAME):
            public_methods.append(
                types_utils.MethodSpec(
                    name="get_hook_name",
                    docstring="""
                        Returns an enum that indicates which hook is currently being executed.
                        See the list of possible values [here](/reference/contracts/contracts_api_4xx/common_types_4xx/enums/#HookName).
                    """,
                    args=[],
                    return_value=types_utils.ReturnValueSpec(
                        docstring="The HookType enum.", type="enum"
                    ),
                    examples=[
                        types_utils.Example(
                            title="Using get_hook_name in a contract level utility.",
                            code="""
                                from contracts_api import HookName

                                def do_something(vault):
                                    hook_name = vault.get_hook_name()
                                    if hook_name == HookName.SCHEDULED_EVENT_HOOK:
                                        # do something based on specific business requirements on the scheduled event hook.
                                    else:
                                        # do something else.
                            """,
                        ),
                    ],
                )
            )

        if is_fflag_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER):
            public_methods.append(
                types_utils.MethodSpec(
                    name="get_balances_discrete_timeseries",
                    docstring=f"""
                        Returns a Python mapping object, mapping
                        [BalanceCoordinate]({_common_docs_path}classes/#BalanceCoordinate) to
                        [BalanceDiscreteTimeseries]({_common_docs_path}classes/#BalanceDiscreteTimeseries) covering
                        the balances at the periodical datetimes laying over the interval defined by the
                        [BalancesDiscreteIntervalFetcher]({_common_docs_path}classes/#BalancesDiscreteIntervalFetcher).
                        **Note**: For performance reasons, each timeseries is lazy evaluated. Whilst it
                        is possible, iterating over all keys/items is not recommended. If a given
                        BalanceCoordinate object does not exist in the mapping, an empty
                        BalanceDiscreteTimeseries will be returned.
                    """,
                    args=[
                        types_utils.ValueSpec(
                            name="fetcher_id",
                            type="str",
                            docstring=f"""
                                The id of the
                                [BalancesDiscreteIntervalFetcher]({_common_docs_path}classes/#BalancesDiscreteIntervalFetcher).
                                1. The fetcher must be defined in the [Contract Metadata](../metadata/)
                                [data_fetchers](../../smart_contracts_api_reference4xx/metadata/#data_fetchers)
                                list. 2. The fetcher id must be defined in the balances argument in the
                                `@fetch_account_data` decorator.
                            """,
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        docstring="A dictionary of balance coordinates to discrete timeseries of balances.",
                        type="Mapping[BalanceCoordinate, BalanceDiscreteTimeseries]",
                    ),
                    examples=[
                        types_utils.Example(
                            title="An example with no decorator",
                            code="""
                                def post_posting_hook(vault, hook_arguments):
                                    # Raises InvalidSmartContractError
                                    vault.get_balances_discrete_timeseries()
                                    # Raises InvalidSmartContractError
                                    vault.get_balances_discrete_timeseries(fetcher_id="fetcher_id")
                            """,
                        ),
                        types_utils.Example(
                            title="An example with @requires decorator",
                            code="""
                                @requires(balances="1 month")
                                def post_posting_hook(vault, hook_arguments):
                                    # Raises InvalidSmartContractError
                                    vault.get_balances_discrete_timeseries()
                                    # Raises InvalidSmartContractError
                                    vault.get_balances_discrete_timeseries(fetcher_id="fetcher_id")
                            """,
                        ),
                        types_utils.Example(
                            title="An example with `@fetch_account_data` decorator",
                            code="""
                                @fetch_account_data(balances=["fetcher_id"])
                                def post_posting_hook(vault, hook_arguments):
                                    # Raises InvalidSmartContractError.
                                    vault.get_balances_discrete_timeseries()
                                    # Returns defaultdict[BalanceCoordinate, BalanceDiscreteTimeseries] for balances specified in the discrete interval fetcher.
                                    vault.get_balances_discrete_timeseries(fetcher_id="fetcher_id")
                                    # Raises InvalidSmartContractError.
                                    vault.get_balances_discrete_timeseries(fetcher_id="fetcher_not_in_decorator")
                            """,
                        ),
                    ],
                ),
            )

        
        public_methods.sort(key=lambda x: x.name)
        for method in public_methods:
            spec.public_methods[method.name] = method
        return spec
