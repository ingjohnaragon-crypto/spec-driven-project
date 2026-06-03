from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from typing import List, Dict, Iterator, Optional, Union, Type

from .account_notification_directive import AccountNotificationDirective
from .event_types import ScheduledEvent
from .parameters import OptionalValue, UnionItemValue
from .plan_notification_directive import PlanNotificationDirective

from .postings import PostingInstructionEnrichment


from .posting_instructions_directive import PostingInstructionsDirective
from .rejection import Rejection


from .update_account_event_type_directive import UpdateAccountEventTypeDirective
from .update_plan_event_type_directive import UpdatePlanEventTypeDirective

from ...common.docs import (
    _common_docs_path,
    _smart_contracts_docs_path,
    _supervisor_contracts_docs_path,
)
from .....utils import symbols, types_utils
from .....utils.exceptions import InvalidSmartContractError
from .....utils.feature_flags import (
    is_fflag_enabled,
    EXPECTED_PID_REJECTIONS,
    REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS,
    ENRICH_POSTING_INSTRUCTIONS,
)


def validate_account_directives(
    *,
    account_directives: Optional[List[AccountNotificationDirective]] = None,
    posting_directives: Optional[List[PostingInstructionsDirective]] = None,
    update_events: Optional[List[UpdateAccountEventTypeDirective]] = None,
    is_scheduled_event_hook: bool = False,
):
    if account_directives is not None:
        _validate_account_directives(
            account_directives, AccountNotificationDirective, "account_directives"
        )
    if posting_directives is not None:
        _validate_account_directives(
            posting_directives, PostingInstructionsDirective, "posting_directives"
        )
        if not is_scheduled_event_hook and is_fflag_enabled(EXPECTED_PID_REJECTIONS):
            for posting_directive in posting_directives:
                if len(posting_directive.non_blocking_rejection_reasons) > 0:
                    raise InvalidSmartContractError(
                        "PostingInstructionsDirective.non_blocking_rejection_reasons can "
                        "only be populated in Scheduled Event Hook Results"
                    )

    if update_events is None:
        return
    _validate_account_event_types(update_events)


def validate_scheduled_events(scheduled_events: Dict[str, ScheduledEvent], prefix=None):
    if prefix:
        prefix += " key"
    types_utils.validate_type(scheduled_events, dict)
    for event_name in scheduled_events:
        types_utils.validate_type(
            event_name, str, check_empty=True, is_optional=False, prefix=prefix
        )
        types_utils.validate_type(scheduled_events[event_name], ScheduledEvent)


def validate_plan_directives(
    plan_notification_directives: Optional[List[PlanNotificationDirective]] = None,
    update_events: Optional[List[UpdatePlanEventTypeDirective]] = None,
):
    type_hint = "PlanNotificationDirective"
    if plan_notification_directives is not None:
        iterator = types_utils.get_iterator(
            plan_notification_directives, type_hint, "plan_notification_directives"
        )
        for directive in iterator:
            types_utils.validate_type(
                directive, PlanNotificationDirective, hint=f"List[{type_hint}]"
            )
    if update_events is None:
        return
    _validate_plan_event_types(update_events)


def validate_supervisee_directives(
    supervisee_account_directives: Dict[str, List[AccountNotificationDirective]],
    supervisee_posting_directives: Dict[str, List[PostingInstructionsDirective]],
    supervisee_update_account_directives: Dict[str, List[UpdateAccountEventTypeDirective]],
    is_scheduled_event_hook: bool = False,
):
    _validate_supervisee_directives(
        supervisee_account_directives,
        AccountNotificationDirective,
        "supervisee_account_notification_directives",
    )
    _validate_supervisee_directives(
        supervisee_posting_directives,
        PostingInstructionsDirective,
        "supervisee_posting_instructions_directives",
    )
    if not is_scheduled_event_hook and is_fflag_enabled(EXPECTED_PID_REJECTIONS):
        for posting_directives in supervisee_posting_directives.values():
            for posting_directive in posting_directives:
                if len(posting_directive.non_blocking_rejection_reasons) > 0:
                    raise InvalidSmartContractError(
                        "PostingInstructionsDirective.non_blocking_rejection_reasons can "
                        "only be populated in Scheduled Event Hook Results"
                    )
    types_utils.validate_type(
        supervisee_update_account_directives,
        dict,
        prefix="supervisee_update_account_event_type_directives",
    )
    for directives in supervisee_update_account_directives.values():
        _validate_account_event_types(directives)


def _validate_account_directives(
    directives: Union[List[AccountNotificationDirective], List[PostingInstructionsDirective]],
    expected_class: Union[Type[AccountNotificationDirective], Type[PostingInstructionsDirective]],
    name: str,
):
    type_hint = f"{expected_class.__name__}"
    iterator = types_utils.get_iterator(directives, type_hint, name)
    for directive in iterator:
        types_utils.validate_type(directive, expected_class, hint=f"List[{type_hint}]")


def _validate_account_event_types(
    update_event_type_directives: Optional[List[UpdateAccountEventTypeDirective]],
):
    if update_event_type_directives is None:
        return
    iterator = types_utils.get_iterator(
        update_event_type_directives,
        UpdateAccountEventTypeDirective.__name__,
        "update_event_type_directives",
    )
    _validate_unique_event_type_directives(iterator, UpdateAccountEventTypeDirective)


def _validate_plan_event_types(
    update_event_type_directives: Optional[List[UpdatePlanEventTypeDirective]],
):
    if update_event_type_directives is None:
        return
    iterator = types_utils.get_iterator(
        update_event_type_directives,
        UpdatePlanEventTypeDirective.__name__,
        "update_event_type_directives",
    )
    _validate_unique_event_type_directives(iterator, UpdatePlanEventTypeDirective)


def _validate_unique_event_type_directives(
    event_type_directives_iterator: Iterator,
    event_class: Union[Type[UpdateAccountEventTypeDirective], Type[UpdatePlanEventTypeDirective]],
):
    seen_updated_event_types = set()
    for update_event_type_directive in event_type_directives_iterator:
        types_utils.validate_type(update_event_type_directive, event_class)
        event_type = update_event_type_directive.event_type
        if event_type in seen_updated_event_types:
            raise InvalidSmartContractError(
                f"Event type '{event_type}' cannot be updated more than once in a hook"
            )
        seen_updated_event_types.add(event_type)


def _validate_supervisee_directives(
    supervisee_directives: Union[
        Dict[str, List[AccountNotificationDirective]],
        Dict[str, List[PostingInstructionsDirective]],
    ],
    expected_class: Type[Union[AccountNotificationDirective, PostingInstructionsDirective]],
    hint: str,
):
    types_utils.validate_type(supervisee_directives, dict, hint=hint)
    for directives in supervisee_directives.values():
        _validate_account_directives(directives, expected_class, hint)


def validate_posting_instruction_enrichment(enrichment, prefix):
    if enrichment is None:
        return
    types_utils.validate_type(
        enrichment,
        dict,
        is_optional=True,
        hint="dict[str, PostingInstructionEnrichment]",
        prefix=prefix,
    )
    for key, value in enrichment.items():
        types_utils.validate_type(key, str, prefix=f"{prefix}.key")
        types_utils.validate_type(value, PostingInstructionEnrichment, prefix=f"{prefix}.value")





class DerivedParameterHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        parameters_return_value: Dict[
            str, Union[Decimal, str, datetime, OptionalValue, UnionItemValue, int]
        ],
    ):
        self.parameters_return_value = parameters_return_value
        self._validate_attributes()

    def _validate_attributes(self):
        types_utils.validate_type(
            self.parameters_return_value, dict, prefix="parameters_return_value"
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="DerivedParameterHookResult",
            docstring="The hook result of the `derived_parameter_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new DerivedParameterHookResult object.",
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
                name="parameters_return_value",
                type="Dict[str, Union[Decimal, str, datetime, OptionalValue, UnionItemValue, int]]",
                docstring="""
                    A dictionary with values keyed by parameter name for all
                    [derived parameters](/reference/contracts/contracts_api_4xx/concepts/#contract_parameters)
                    defined in the Smart Contract Metadata. An entry in the dictionary needs to exist
                    for all defined derived parameters. Values that are allowed to be returned by
                    Parameter Shape: NumberShape: Decimal or int, StringShape: str, AccountIdShape:
                    str, DenominationShape: str, DateShape: datetime, OptionalShape: OptionalValue,
                UnionShape: UnionItemValue with key in the set of valid keys of the UnionShape.
                """,
            )
        ]


class DeactivationHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        account_notification_directives: Optional[List[AccountNotificationDirective]] = None,
        posting_instructions_directives: Optional[List[PostingInstructionsDirective]] = None,
        update_account_event_type_directives: Optional[
            List[UpdateAccountEventTypeDirective]
        ] = None,
        rejection: Optional[Rejection] = None,
    ):
        self.account_notification_directives = account_notification_directives or []
        self.posting_instructions_directives = posting_instructions_directives or []
        self.update_account_event_type_directives = update_account_event_type_directives or []
        self.rejection = rejection
        self._validate_attributes()

    def _validate_attributes(self):
        if self.rejection is not None:
            types_utils.validate_type(self.rejection, Rejection, prefix="rejection")
            # Either Directives or rejection can be populated, not both.
            if (
                self.account_notification_directives
                or self.posting_instructions_directives
                or self.update_account_event_type_directives
            ):
                raise InvalidSmartContractError(
                    "DeactivationHookResult allows the population of directives or rejection, "
                    "but not both"
                )
        validate_account_directives(
            account_directives=self.account_notification_directives,
            posting_directives=self.posting_instructions_directives,
            update_events=self.update_account_event_type_directives,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="DeactivationHookResult",
            docstring="The hook result of the `deactivation_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="""
                Constructs a new DeactivationHookResult object. It allows the population of
                directives or rejection, but not both.
                """,
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
                name="account_notification_directives",
                type="Optional[List[AccountNotificationDirective]]",
                docstring=f"""
                A list of
                [AccountNotificationDirective]({_common_docs_path}classes/#AccountNotificationDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="posting_instructions_directives",
                type="Optional[List[PostingInstructionsDirective]]",
                docstring=f"""
                A list of
                [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="update_account_event_type_directives",
                type="Optional[List[UpdateAccountEventTypeDirective]]",
                docstring=f"""
                A list of
                [UpdateAccountEventTypeDirective]({_common_docs_path}classes/#UpdateAccountEventTypeDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="rejection",
                type="Optional[Rejection]",
                docstring=f"""
A Hook [Rejection]({_common_docs_path}classes/#Rejection).
 If returned, the account cannot be closed.
                """,
            ),
        ]


class ActivationHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        account_notification_directives: Optional[List[AccountNotificationDirective]] = None,
        posting_instructions_directives: Optional[List[PostingInstructionsDirective]] = None,
        scheduled_events_return_value: Optional[Dict[str, ScheduledEvent]] = None,
        rejection: Optional[Rejection] = None,
    ):
        self.account_notification_directives = account_notification_directives or []
        self.posting_instructions_directives = posting_instructions_directives or []
        self.scheduled_events_return_value = scheduled_events_return_value or {}
        if is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            self.rejection = rejection
        elif rejection:
            raise InvalidSmartContractError("ActivationHookResult does not accept Rejections")
        self._validate_attributes()

    def _validate_attributes(self):
        validate_account_directives(
            account_directives=self.account_notification_directives,
            posting_directives=self.posting_instructions_directives,
        )
        validate_scheduled_events(self.scheduled_events_return_value)
        if not is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            return
        if self.rejection is None:
            return
        if (
            self.account_notification_directives
            or self.posting_instructions_directives
            or self.scheduled_events_return_value
        ):
            raise InvalidSmartContractError(
                "ActivationHookResult allows the population of directives/events or rejection, "
                "but not both"
            )
        types_utils.validate_type(self.rejection, Rejection, prefix="rejection")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ActivationHookResult",
            docstring="The hook result of the `activation_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new ActivationHookResult object",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        public_attributes = [
            types_utils.ValueSpec(
                name="account_notification_directives",
                type="Optional[List[AccountNotificationDirective]]",
                docstring=f"""
                A list of
                [AccountNotificationDirective]({_common_docs_path}classes/#AccountNotificationDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="posting_instructions_directives",
                type="Optional[List[PostingInstructionsDirective]]",
                docstring=f"""
                A list of
                [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="scheduled_events_return_value",
                type="Optional[Dict[str, ScheduledEvent]]",
                docstring=f"""
                A dictionary containing
                [ScheduledEvent]({_common_docs_path}classes/#ScheduledEvent)s
                by name returned by the hook.
                For `event_types` returned in this mapping, you cannot set `ScheduledEvent`
                `start_datetime` to before the hook `effective_datetime`.
                """,
            ),
        ]
        if is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            public_attributes.append(
                types_utils.ValueSpec(
                    name="rejection",
                    type="Optional[Rejection]",
                    docstring=f"""
A Hook [Rejection]({_common_docs_path}classes/#Rejection).
 If returned, the account will not be opened. **Only available in Vault version 5.0+**.
                    """,
                ),
            )
        return public_attributes


class PostParameterChangeHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        account_notification_directives: Optional[List[AccountNotificationDirective]] = None,
        posting_instructions_directives: Optional[List[PostingInstructionsDirective]] = None,
        update_account_event_type_directives: Optional[
            List[UpdateAccountEventTypeDirective]
        ] = None,
    ):
        self.account_notification_directives = account_notification_directives or []
        self.posting_instructions_directives = posting_instructions_directives or []
        self.update_account_event_type_directives = update_account_event_type_directives or []
        self._validate_attributes()

    def _validate_attributes(self):
        validate_account_directives(
            account_directives=self.account_notification_directives,
            posting_directives=self.posting_instructions_directives,
            update_events=self.update_account_event_type_directives,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PostParameterChangeHookResult",
            docstring="The hook result of the `post_parameter_change_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PostParameterChangeHookResult object",
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
                name="account_notification_directives",
                type="Optional[List[AccountNotificationDirective]]",
                docstring=f"""
                A list of
                [AccountNotificationDirective]({_common_docs_path}classes/#AccountNotificationDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="posting_instructions_directives",
                type="Optional[List[PostingInstructionsDirective]]",
                docstring=f"""
                A list of
                [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="update_account_event_type_directives",
                type="Optional[List[UpdateAccountEventTypeDirective]]",
                docstring=f"""
                A list of
                [UpdateAccountEventTypeDirective]({_common_docs_path}classes/#UpdateAccountEventTypeDirective)s
                to be instructed by the hook.
                """,
            ),
        ]


class PostPostingHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        account_notification_directives: Optional[List[AccountNotificationDirective]] = None,
        posting_instructions_directives: Optional[List[PostingInstructionsDirective]] = None,
        update_account_event_type_directives: Optional[
            List[UpdateAccountEventTypeDirective]
        ] = None,
        _from_proto: Optional[bool] = False,
    ):
        self.account_notification_directives = account_notification_directives or []
        self.posting_instructions_directives = posting_instructions_directives or []
        self.update_account_event_type_directives = update_account_event_type_directives or []
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        validate_account_directives(
            account_directives=self.account_notification_directives,
            posting_directives=self.posting_instructions_directives,
            update_events=self.update_account_event_type_directives,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PostPostingHookResult",
            docstring="The hook result of the `post_posting_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PostPostingHookResult object",
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
                name="account_notification_directives",
                type="Optional[List[AccountNotificationDirective]]",
                docstring=f"""
                A list of [AccountNotificationDirective]({_common_docs_path}classes/#AccountNotificationDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="posting_instructions_directives",
                type="Optional[List[PostingInstructionsDirective]]",
                docstring=f"""
                A list of [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="update_account_event_type_directives",
                type="Optional[List[UpdateAccountEventTypeDirective]]",
                docstring=f"""
                A list of [UpdateAccountEventTypeDirective]({_common_docs_path}classes/#UpdateAccountEventTypeDirective)s
                to be instructed by the hook.
                """,
            ),
        ]


class PreParameterChangeHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(self, *, rejection: Optional[Rejection] = None):
        self.rejection = rejection
        self._validate_attributes()

    def _validate_attributes(self):
        if self.rejection is not None:
            types_utils.validate_type(self.rejection, Rejection, prefix="rejection")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PreParameterChangeHookResult",
            docstring="The hook result of the `pre_parameter_change_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PreParameterChangeHookResult object",
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
                name="rejection",
                type="Optional[Rejection]",
                docstring=f"""
A Hook [Rejection]({_common_docs_path}classes/#Rejection).
 If returned, the parameter update is rejected.
                """,
            )
        ]


class PrePostingHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        rejection: Optional[Rejection] = None,
        enrichment_details: Optional[dict[str, PostingInstructionEnrichment]] = None,
        _from_proto: Optional[bool] = False,
    ):
        self.rejection = rejection
        if is_fflag_enabled(ENRICH_POSTING_INSTRUCTIONS):
            self.enrichment_details = enrichment_details
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        if self.rejection is not None:
            types_utils.validate_type(self.rejection, Rejection, prefix="rejection")
        if is_fflag_enabled(ENRICH_POSTING_INSTRUCTIONS):
            validate_posting_instruction_enrichment(self.enrichment_details, "enrichment_details")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PrePostingHookResult",
            docstring="The hook result of the `pre_posting_hook`",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PrePostingHookResult object",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        public_attributes = [
            types_utils.ValueSpec(
                name="rejection",
                type="Optional[Rejection]",
                docstring=f"""
                A Hook [Rejection]({_common_docs_path}classes/#Rejection).
                If returned, the proposed Postings will not be committed.
                """,
            ),
        ]

        if is_fflag_enabled(ENRICH_POSTING_INSTRUCTIONS):
            public_attributes.append(
                types_utils.ValueSpec(
                    name="enrichment_details",
                    type="Optional[dict[str, PostingInstructionEnrichment]]",
                    docstring=f"""
                        An optional mapping of Posting Instruction `id` to
                        [PostingInstructionEnrichment]({_common_docs_path}classes/#PostingInstructionEnrichment).
                        Each `id` must belong to one of the proposed Posting Instructions.
                        Note: If the Smart Contract rejects a Posting Instruction then Vault Core ignores `enrichment`
                        (if you have set `enrichment` and `rejection`) and does not save any enrichment details.
                    """,
                )
            )
        return public_attributes


class ScheduledEventHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        account_notification_directives: Optional[List[AccountNotificationDirective]] = None,
        posting_instructions_directives: Optional[List[PostingInstructionsDirective]] = None,
        update_account_event_type_directives: Optional[
            List[UpdateAccountEventTypeDirective]
        ] = None,
        _from_proto: Optional[bool] = False,
    ):
        self.account_notification_directives = account_notification_directives or []
        self.posting_instructions_directives = posting_instructions_directives or []
        self.update_account_event_type_directives = update_account_event_type_directives or []
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        validate_account_directives(
            account_directives=self.account_notification_directives,
            posting_directives=self.posting_instructions_directives,
            update_events=self.update_account_event_type_directives,
            is_scheduled_event_hook=True,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ScheduledEventHookResult",
            docstring="The hook result of the `scheduled_event_hook`",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="",
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
                name="account_notification_directives",
                type="Optional[List[AccountNotificationDirective]]",
                docstring=f"""
                A list of [AccountNotificationDirective]({_common_docs_path}classes/#AccountNotificationDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="posting_instructions_directives",
                type="Optional[List[PostingInstructionsDirective]]",
                docstring=f"""
                A list of [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="update_account_event_type_directives",
                type="Optional[List[UpdateAccountEventTypeDirective]]",
                docstring=f"""
                A list of [UpdateAccountEventTypeDirective]({_common_docs_path}classes/#UpdateAccountEventTypeDirective)s
                to be instructed by the hook.
                """,
            ),
        ]


class SupervisorPostPostingHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        # Plan Directives
        plan_notification_directives: Optional[List[PlanNotificationDirective]] = None,
        update_plan_event_type_directives: Optional[List[UpdatePlanEventTypeDirective]] = None,
        # Supervisee Directives
        supervisee_account_notification_directives: Optional[
            Dict[str, List[AccountNotificationDirective]]
        ] = None,
        supervisee_posting_instructions_directives: Optional[
            Dict[str, List[PostingInstructionsDirective]]
        ] = None,
        supervisee_update_account_event_type_directives: Optional[
            Dict[str, List[UpdateAccountEventTypeDirective]]
        ] = None,
    ):
        self.plan_notification_directives = plan_notification_directives or []
        self.update_plan_event_type_directives = update_plan_event_type_directives or []
        self.supervisee_account_notification_directives = (
            supervisee_account_notification_directives or defaultdict(list)
        )
        self.supervisee_posting_instructions_directives = (
            supervisee_posting_instructions_directives or defaultdict(list)
        )
        self.supervisee_update_account_event_type_directives = (
            supervisee_update_account_event_type_directives or defaultdict(list)
        )
        self._validate_attributes()

    def _validate_attributes(self):
        validate_plan_directives(
            self.plan_notification_directives, self.update_plan_event_type_directives
        )
        validate_supervisee_directives(
            self.supervisee_account_notification_directives,
            self.supervisee_posting_instructions_directives,
            self.supervisee_update_account_event_type_directives,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorPostPostingHookResult",
            docstring="The hook result of the Supervisor `post_posting_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorPostPostingHookResult object.",
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
                name="plan_notification_directives",
                type="Optional[List[PlanNotificationDirective]]",
                docstring=f"""
                A list of [PlanNotificationDirective]({_common_docs_path}classes/#PlanNotificationDirective)s
                to be instructed by the Supervisor hook.
                """,
            ),
            types_utils.ValueSpec(
                name="update_plan_event_type_directives",
                type="Optional[List[UpdatePlanEventTypeDirective]]",
                docstring=f"""
                A list of [UpdatePlanEventTypeDirective]({_common_docs_path}classes/#UpdatePlanEventTypeDirective)s
                to be instructed by the Supervisor hook.
                """,
            ),
            types_utils.ValueSpec(
                name="supervisee_account_notification_directives",
                type="Optional[Dict[str, List[AccountNotificationDirective]]]",
                docstring=f"""
                A dictionary containing Lists of
                [AccountNotificationDirective]({_common_docs_path}classes/#AccountNotificationDirective)s
                keyed by Supervisee account id, returned by the Supervisor hook.
                """,
            ),
            types_utils.ValueSpec(
                name="supervisee_posting_instructions_directives",
                type="Optional[Dict[str, List[PostingInstructionsDirective]]]",
                docstring=f"""
                A dictionary containing Lists of
                [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                keyed by Supervisee account id, returned by the Supervisor hook.
                """,
            ),
            types_utils.ValueSpec(
                name="supervisee_update_account_event_type_directives",
                type="Optional[Dict[str, List[UpdateAccountEventTypeDirective]]]",
                docstring=f"""
                A dictionary containing Lists of
                [UpdateAccountEventTypeDirective]({_common_docs_path}classes/#UpdateAccountEventTypeDirective)s
                keyed by Supervisee account id, returned by the Supervisor hook.
                """,
            ),
        ]


class SupervisorPrePostingHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        rejection: Optional[Rejection] = None,
        enrichment_details: Optional[dict[str, dict[str, PostingInstructionEnrichment]]] = None,
    ):
        self.rejection = rejection
        if is_fflag_enabled(ENRICH_POSTING_INSTRUCTIONS):
            self.enrichment_details = enrichment_details
        self._validate_attributes()

    def _validate_attributes(self):
        if self.rejection is not None:
            types_utils.validate_type(self.rejection, Rejection, prefix="rejection")
        if is_fflag_enabled(ENRICH_POSTING_INSTRUCTIONS):
            if self.enrichment_details is not None:
                types_utils.validate_type(
                    self.enrichment_details,
                    dict,
                    is_optional=True,
                    hint="dict[str, dict[str, PostingInstructionEnrichment]]",
                    prefix="enrichment_details",
                )
                for key, value in self.enrichment_details.items():
                    types_utils.validate_type(key, str, prefix="enrichment_details.key")
                    validate_posting_instruction_enrichment(value, "enrichment_details.value")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorPrePostingHookResult",
            docstring="The hook result of the Supervisor `pre_posting_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorPrePostingHookResult object",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        public_attributes = [
            types_utils.ValueSpec(
                name="rejection",
                type="Optional[Rejection]",
                docstring=f"""
A Hook [Rejection]({_common_docs_path}classes/#Rejection).
 If returned, the proposed Postings will not be committed.
                """,
            )
        ]
        if is_fflag_enabled(ENRICH_POSTING_INSTRUCTIONS):
            public_attributes.append(
                types_utils.ValueSpec(
                    name="enrichment_details",
                    type="Optional[dict[str, dict[str, PostingInstructionEnrichment]]]",
                    docstring=f"""
                        An optional dictionary, mapping the Supervisee Account ID to a dictionary
                        that, in turn, maps proposed Posting Instruction IDs to the required
                        [PostingInstructionEnrichment]({_common_docs_path}classes/#PostingInstructionEnrichment).
                        Note: If the Smart Contract rejects a Posting Instruction then Vault Core ignores `enrichment`
                        (if you have set `enrichment` and `rejection`) and does not save any enrichment details.
                    """,
                )
            )
        return public_attributes


class SupervisorActivationHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        scheduled_events_return_value: Optional[Dict[str, ScheduledEvent]] = None,
        rejection: Optional[Rejection] = None,
    ):
        self.scheduled_events_return_value = scheduled_events_return_value or {}
        if is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            self.rejection = rejection
        elif rejection:
            raise InvalidSmartContractError(
                "SupervisorActivationHookResult does not accept Rejections"
            )
        self._validate_attributes()

    def _validate_attributes(self):
        validate_scheduled_events(self.scheduled_events_return_value)
        if not is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            return
        if self.rejection is None:
            return
        if self.scheduled_events_return_value:
            raise InvalidSmartContractError(
                "SupervisorActivationHookResult allows the population of events or rejection, "
                "but not both"
            )
        types_utils.validate_type(self.rejection, Rejection, prefix="rejection")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorActivationHookResult",
            docstring="The hook result of the Supervisor `activation_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorActivationHookResult object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        public_attributes = [
            types_utils.ValueSpec(
                name="scheduled_events_return_value",
                type="Optional[Dict[str, ScheduledEvent]]",
                docstring=f"""
                A dictionary containing [ScheduledEvent]({_common_docs_path}classes/#ScheduledEvent)s
                keyed by name returned by the Supervisor hook.
                For `event_types` returned in this mapping, you cannot set `ScheduledEvent`
                `start_datetime` to before the hook `effective_datetime`.
                """,  # noqa: 501
            ),
        ]
        if is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            public_attributes.append(
                types_utils.ValueSpec(
                    name="rejection",
                    type="Optional[Rejection]",
                    docstring=f"""
A Hook [Rejection]({_common_docs_path}classes/#Rejection).
If returned, the plan will not be opened. **Only available in Vault version 5.0+**.
                    """,
                ),
            )
        return public_attributes


class SupervisorConversionHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        scheduled_events_return_value: Optional[Dict[str, ScheduledEvent]] = None,
        rejection: Optional[Rejection] = None,
    ):
        self.scheduled_events_return_value = scheduled_events_return_value or {}
        if is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            self.rejection = rejection
        elif rejection:
            raise InvalidSmartContractError(
                "SupervisorConversionHookResult does not accept Rejections"
            )
        self._validate_attributes()

    def _validate_attributes(self):
        validate_scheduled_events(self.scheduled_events_return_value)
        if not is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            return
        if self.rejection is None:
            return
        if self.scheduled_events_return_value:
            raise InvalidSmartContractError(
                "SupervisorConversionHookResult allows the population of scheduled events or "
                "rejection, but not both"
            )
        types_utils.validate_type(
            self.rejection,
            Rejection,
            prefix="SupervisorConversionHookResult.rejection",
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorConversionHookResult",
            docstring="The hook result of the Supervisor `conversion_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorConversionHookResult object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        public_attributes = [
            types_utils.ValueSpec(
                name="scheduled_events_return_value",
                type="Optional[Dict[str, ScheduledEvent]]",
                docstring=f"""
                A dictionary containing [ScheduledEvent]({_common_docs_path}classes/#ScheduledEvent)s
                keyed by name returned by the Supervisor hook.
                For any new [event_types]({_supervisor_contracts_docs_path}metadata/#event_types) in
                this Contract returned in this mapping, you cannot set `ScheduledEvent`
                `start_datetime` to before the hook `effective_datetime`. For any `event_types` that
                exist in the previous Contract and are returned in this mapping, the
                `ScheduledEvent` `start_datetime` is disregarded and defaults to the last run time
                of the existing `event_type` schedule. Because of this, the start_datetime for the
                existing schedules must be set to None or remain unchanged, as any other values will
                result in an error. This attribute is only optional if no `event_types` are defined
                in this Contract. Additionally, all `event_types` in this Contract must be included
                in the `scheduled_events_return_value`.
                """,
            ),
        ]
        if is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            public_attributes.append(
                types_utils.ValueSpec(
                    name="rejection",
                    type="Optional[Rejection]",
                    docstring=f"""
A Hook [Rejection]({_common_docs_path}classes/#Rejection).
 If returned, the plan will not be converted to the new Supervisor Contract version.
 **Only available in Vault version 5.0+**.
                    """,
                ),
            )
        return public_attributes


class SupervisorScheduledEventHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        # Plan Directives
        plan_notification_directives: Optional[List[PlanNotificationDirective]] = None,
        update_plan_event_type_directives: Optional[List[UpdatePlanEventTypeDirective]] = None,
        # Supervisee Directives
        supervisee_account_notification_directives: Optional[
            Dict[str, List[AccountNotificationDirective]]
        ] = None,
        supervisee_posting_instructions_directives: Optional[
            Dict[str, List[PostingInstructionsDirective]]
        ] = None,
        supervisee_update_account_event_type_directives: Optional[
            Dict[str, List[UpdateAccountEventTypeDirective]]
        ] = None,
    ):
        self.plan_notification_directives = plan_notification_directives or []
        self.update_plan_event_type_directives = update_plan_event_type_directives or []
        self.supervisee_account_notification_directives = (
            supervisee_account_notification_directives or defaultdict(list)
        )
        self.supervisee_posting_instructions_directives = (
            supervisee_posting_instructions_directives or defaultdict(list)
        )
        self.supervisee_update_account_event_type_directives = (
            supervisee_update_account_event_type_directives or defaultdict(list)
        )
        self._validate_attributes()

    def _validate_attributes(self):
        validate_plan_directives(
            self.plan_notification_directives, self.update_plan_event_type_directives
        )
        validate_supervisee_directives(
            self.supervisee_account_notification_directives,
            self.supervisee_posting_instructions_directives,
            self.supervisee_update_account_event_type_directives,
            is_scheduled_event_hook=True,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorScheduledEventHookResult",
            docstring="The hook result of the Supervisor `scheduled_event_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorScheduledEventHookResult object.",
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
                name="plan_notification_directives",
                type="Optional[List[PlanNotificationDirective]]",
                docstring=f"""
                A list of [PlanNotificationDirective]({_common_docs_path}classes/#PlanNotificationDirective)s
                to be instructed by the Supervisor hook.
                """,
            ),
            types_utils.ValueSpec(
                name="update_plan_event_type_directives",
                type="Optional[List[UpdatePlanEventTypeDirective]]",
                docstring=f"""
                A list of [UpdatePlanEventTypeDirective]({_common_docs_path}classes/#UpdatePlanEventTypeDirective)s
                to be instructed by the Supervisor hook.
                """,
            ),
            types_utils.ValueSpec(
                name="supervisee_account_notification_directives",
                type="Optional[Dict[str, List[AccountNotificationDirective]]]",
                docstring=f"""
                A dictionary containing Lists of
                [AccountNotificationDirective]({_common_docs_path}classes/#AccountNotificationDirective)s
                keyed by Supervisee account id, returned by the Supervisor hook.
                """,
            ),
            types_utils.ValueSpec(
                name="supervisee_posting_instructions_directives",
                type="Optional[Dict[str, List[PostingInstructionsDirective]]]",
                docstring=f"""
                A dictionary containing Lists of
                [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                keyed by Supervisee account id, returned by the Supervisor hook.
                """,
            ),
            types_utils.ValueSpec(
                name="supervisee_update_account_event_type_directives",
                type="Optional[Dict[str, List[UpdateAccountEventTypeDirective]]]",
                docstring=f"""
                A dictionary containing Lists of
                [UpdateAccountEventTypeDirective]({_common_docs_path}classes/#UpdateAccountEventTypeDirective)s
                keyed by Supervisee account id, returned by the Supervisor hook.
                """,
            ),
        ]


class ConversionHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        account_notification_directives: Optional[List[AccountNotificationDirective]] = None,
        posting_instructions_directives: Optional[List[PostingInstructionsDirective]] = None,
        scheduled_events_return_value: Optional[Dict[str, ScheduledEvent]] = None,
        rejection: Optional[Rejection] = None,
    ):
        self.account_notification_directives = account_notification_directives or []
        self.posting_instructions_directives = posting_instructions_directives or []
        self.scheduled_events_return_value = scheduled_events_return_value or {}
        if is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            self.rejection = rejection
        elif rejection:
            raise InvalidSmartContractError("ConversionHookResult does not accept Rejections")
        self._validate_attributes()

    def _validate_attributes(self):
        validate_account_directives(
            account_directives=self.account_notification_directives,
            posting_directives=self.posting_instructions_directives,
        )
        validate_scheduled_events(self.scheduled_events_return_value)
        if not is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            return
        if self.rejection is None:
            return
        if (
            self.account_notification_directives
            or self.posting_instructions_directives
            or self.scheduled_events_return_value
        ):
            raise InvalidSmartContractError(
                "ConversionHookResult allows the population of directives/events or rejection, "
                "but not both"
            )
        types_utils.validate_type(self.rejection, Rejection, prefix="rejection")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ConversionHookResult",
            docstring="The hook result of the `conversion_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new ConversionHookResult object",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        public_attributes = [
            types_utils.ValueSpec(
                name="account_notification_directives",
                type="Optional[List[AccountNotificationDirective]]",
                docstring=f"""
                A list of [AccountNotificationDirective]({_common_docs_path}classes/#AccountNotificationDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="posting_instructions_directives",
                type="Optional[List[PostingInstructionsDirective]]",
                docstring=f"""
                A list of [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                to be instructed by the hook.
                """,
            ),
            types_utils.ValueSpec(
                name="scheduled_events_return_value",
                type="Optional[Dict[str, ScheduledEvent]]",
                docstring=f"""
                A dictionary containing [ScheduledEvent]({_common_docs_path}classes/#ScheduledEvent)s
                by name returned by the hook.
                For any new [event_types]({_smart_contracts_docs_path}metadata/#event_types) in this
                Contract returned in this mapping, you cannot set `ScheduledEvent` `start_datetime`
                to before the hook `effective_datetime`. For any `event_types` that exist in the
                previous Contract and are returned in this mapping, the `ScheduledEvent`
                `start_datetime` is disregarded and defaults to the last run time of the existing
                `event_type` schedule. Because of this, the start_datetime for the existing
                schedules must be set to None or remain unchanged, as any other values will result
                in an error. This attribute is only optional if no `event_types` are defined in this
                Contract. Additionally, all `event_types` in this Contract must be included in the
                `scheduled_events_return_value`.
                """,
            ),
        ]
        if is_fflag_enabled(REJECTION_FROM_ACTIVATION_CONVERSION_HOOKS):
            public_attributes.append(
                types_utils.ValueSpec(
                    name="rejection",
                    type="Optional[Rejection]",
                    docstring=f"""
A Hook [Rejection]({_common_docs_path}classes/#Rejection).
If returned, the account will not be converted. **Only available in Vault version 5.0+**.
                    """,
                ),
            )
        return public_attributes


class AttributeHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        attribute_value: Optional[Union[Decimal, datetime, str]] = None,
    ):
        self.attribute_value = attribute_value
        self._validate_attributes()

    def _validate_attributes(self):
        types_utils.validate_type(
            self.attribute_value,
            (Decimal, datetime, str),
            is_optional=True,
            prefix="attribute_value",
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="AttributeHookResult",
            docstring="""
                The expected return type of [attribute_hook](../../smart_contracts_api_reference4xx/hooks/#attribute_hook).
            """,
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="",
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
                name="attribute_value",
                type="Optional[Decimal, datetime, str]",
                docstring=f"""
                    The returned value of the [Attribute]({_common_docs_path}classes/#Attribute).
                    The type of the value must match the corresponding [type]({_common_docs_path}classes/#AttributeDecimalType)
                    of the attribute with the associated name as defined in Contract metadata.
                    If the returned value is not of the correct type, a runtime error will occur.
                """,
            ),
        ]



class PostParameterChangeAdjustmentHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        posting_instructions_directives: Optional[List[PostingInstructionsDirective]] = None,
    ):
        self.posting_instructions_directives = posting_instructions_directives or []
        self._validate_attributes()

    def _validate_attributes(self):
        validate_account_directives(
            posting_directives=self.posting_instructions_directives,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PostParameterChangeAdjustmentHookResult",
            docstring="The hook result of the `post_parameter_change_adjustment_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PostParameterChangeAdjustmentHookResult object",
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
                name="posting_instructions_directives",
                type="Optional[List[PostingInstructionsDirective]]",
                docstring=f"""
                A list of
                [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                to be instructed by the hook.
                """,
            ),
        ]


class PostPostingAdjustmentHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        posting_instructions_directives: Optional[List[PostingInstructionsDirective]] = None,
        _from_proto: Optional[bool] = False,
    ):
        self.posting_instructions_directives = posting_instructions_directives or []
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        validate_account_directives(
            posting_directives=self.posting_instructions_directives,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="PostPostingAdjustmentHookResult",
            docstring="The hook result of the `post_posting_adjustment_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PostPostingAdjustmentHookResult object",
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
                name="posting_instructions_directives",
                type="Optional[List[PostingInstructionsDirective]]",
                docstring=f"""
                A list of [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                to be instructed by the hook.
                """,
            ),
        ]


class ScheduledEventAdjustmentHookResult(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        posting_instructions_directives: Optional[List[PostingInstructionsDirective]] = None,
        _from_proto: Optional[bool] = False,
    ):
        self.posting_instructions_directives = posting_instructions_directives or []
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        validate_account_directives(
            posting_directives=self.posting_instructions_directives,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ScheduledEventAdjustmentHookResult",
            docstring="The hook result of the `scheduled_event_adjustment_hook`.",
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="",
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
                name="posting_instructions_directives",
                type="Optional[List[PostingInstructionsDirective]]",
                docstring=f"""
                A list of [PostingInstructionsDirective]({_common_docs_path}classes/#PostingInstructionsDirective)s
                to be instructed by the hook.
                """,
            ),
        ]
