from datetime import datetime
from functools import lru_cache
from typing import Optional

from .postings import CustomInstruction
from .enums import (
    PostingInstructionType,
    PostingInstructionRejectionReason,
)

from ...common.docs import _common_docs_path
from .....utils import symbols, types_utils, exceptions
from .....utils.feature_flags import (
    is_fflag_enabled,
    
    EXPECTED_PID_REJECTIONS,
)
from .....utils.timezone_utils import validate_timezone_is_utc


class PostingInstructionsDirective(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        posting_instructions: list[CustomInstruction],
        client_batch_id: Optional[str] = None,
        value_datetime: Optional[datetime] = None,
        booking_datetime: Optional[datetime] = None,
        batch_details: Optional[dict[str, str]] = None,
        non_blocking_rejection_reasons: Optional[set[PostingInstructionRejectionReason]] = None,
        _from_proto=False,
    ):
        self.posting_instructions = posting_instructions
        self.client_batch_id = client_batch_id
        self.value_datetime = value_datetime
        self.booking_datetime = booking_datetime
        self.batch_details = batch_details
        if is_fflag_enabled(EXPECTED_PID_REJECTIONS):
            self.non_blocking_rejection_reasons = (
                non_blocking_rejection_reasons
                if non_blocking_rejection_reasons is not None
                else set()
            )
        elif non_blocking_rejection_reasons is not None:
            raise exceptions.IllegalPython(
                "PostingInstructionsDirective.__init__() got unexpected keyword argument "
                "'non_blocking_rejection_reasons'"
            )
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        iterator = types_utils.get_iterator(
            self.posting_instructions, "CustomInstruction", "posting_instructions", check_empty=True
        )
        if len(self.posting_instructions) > 64:
            raise exceptions.InvalidSmartContractError(
                "Too many posting instructions submitted in the Posting Instructions Directive. "
                f"Number submitted: {len(self.posting_instructions)}. Limit: 64.",
            )
        for pi in iterator:
            types_utils.validate_type(pi, CustomInstruction, hint="List[CustomInstruction]")
            if pi.type != PostingInstructionType.CUSTOM_INSTRUCTION:
                raise exceptions.InvalidSmartContractError(
                    f"Posting instruction of type {pi.type} cannot be instructed from a Contract."
                )
            pi._validate_postings_and_zero_net_sum()  # noqa: SLF001
            pi._validate_postings_internal_account_id_and_processing_label()  # noqa: SLF001

        if self.value_datetime is not None:
            types_utils.validate_type(self.value_datetime, datetime)
            validate_timezone_is_utc(
                self.value_datetime,
                "value_datetime",
                "PostingInstructionsDirective",
            )
        if self.booking_datetime is not None:
            types_utils.validate_type(self.booking_datetime, datetime)
            validate_timezone_is_utc(
                self.booking_datetime,
                "booking_datetime",
                "PostingInstructionsDirective",
            )

        if self.batch_details is not None:
            types_utils.validate_type(
                self.batch_details,
                dict,
                hint="Dict[str, str]",
                is_optional=True,
                prefix="PostingInstructionsDirective.batch_details",
            )

        if is_fflag_enabled(EXPECTED_PID_REJECTIONS):
            types_utils.validate_type(
                item=self.non_blocking_rejection_reasons,
                expected=set,
                hint="Set[PostingInstructionRejectionReason] for 'PostingInstructionsDirective.non_blocking_rejection_reasons'",
            )

            iterator = types_utils.get_iterator(
                self.non_blocking_rejection_reasons,
                hint="PostingInstructionRejectionReason",
                name="PostingInstructionsDirective.non_blocking_rejection_reasons",
                iterable_hint="set",
            )
            for index, non_blocking_rejection_reasons in enumerate(iterator):
                types_utils.validate_type(
                    item=non_blocking_rejection_reasons,
                    expected=PostingInstructionRejectionReason,
                    hint="PostingInstructionRejectionReason",
                    prefix=(
                        f"PostingInstructionsDirective." f"non_blocking_rejection_reasons[{index}]"
                    ),
                )
        elif (
            hasattr(self, "non_blocking_rejection_reasons")
            and self.non_blocking_rejection_reasons != set()
        ):
            raise exceptions.InvalidSmartContractError(
                "PostingInstructionsDirective.non_blocking_rejection_reasons is not supported"
            )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        return types_utils.ClassSpec(
            name="PostingInstructionsDirective",
            docstring=f"""
                A hook directive that instructs a list of posting instructions. Currently only
                [CustomInstruction]({_common_docs_path}classes/#CustomInstruction)s are supported as hook directives.
            """,
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new PostingInstructionsDirective",
                args=cls._public_attributes(language_code),
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        booking_datetime_docstring = """
            Deprecated as of Vault Core 5.5., and will be removed no earlier than Vault Core 7.0.
            Specifies the datetime against which all committed postings of all posting instructions
            in this directive will be booked.
        """

        
        booking_datetime_docstring += """
            `booking_datetime` should either be set on the `CustomInstruction` (recommended)
            or on the `PostingInstructionsDirective` level (deprecated). `booking_datetime`
            set on the `PostingInstructionsDirective` level will override any
            values set on `CustomInstruction` level.
            If both `booking_datetime` and `value_datetime` are set, they must be set on
            the same level.
        """
        booking_datetime_docstring += """
            Must be a timezone-aware UTC datetime using the ZoneInfo class.
        """

        public_attributes = [
            types_utils.ValueSpec(
                name="posting_instructions",
                type="List[CustomInstruction]",
                docstring="""
                    A list of posting instructions that will be atomically accepted or rejected.
                    Each `PostingInstructionsDirective` can have up to 64 `CustomInstruction`s.
                """,
            ),
            types_utils.ValueSpec(
                name="client_batch_id",
                type="Optional[str]",
                docstring="""
                    An ID that can be used as a correlation ID across different posting instruction
                    batches. If not provided, defaults to a unique auto-generated UUID.
                """,
            ),
        ]

        public_attributes.extend(
            [
                types_utils.ValueSpec(
                    name="value_datetime",
                    type="Optional[datetime]",
                    docstring="""
                        Deprecated as of Vault Core 5.5, and will be removed no earlier than Vault Core 7.0.
                        Specifies the datetime at which all committed postings of all posting
                        instructions in this directive will affect balances. For most cases,
                        this should not be set and will default to the generated `insertion_datetime`.
                        Must be a timezone-aware UTC datetime using the ZoneInfo class.
                        `value_datetime` should either be set on the `CustomInstruction` level
                        (recommended) or on the `PostingInstructionsDirective` level (deprecated).
                        `value_datetime` set on the `PostingInstructionsDirective` level will override
                        any values set on `CustomInstruction` level.
                        When using `CustomInstruction` level `value_datetime`, posting instructions
                        can be backdated or future-dated.
                        When using `PostingInstructionsDirective` level `value_datetime`, posting
                        instructions can only be backdated; they cannot be future-dated.
                        If both `value_datetime` and `booking_datetime` are set, they must be set on
                        the same level.
                    """,
                )
            ]
        )

        public_attributes.extend(
            [
                types_utils.ValueSpec(
                    name="batch_details",
                    type="Optional[Dict[str, str]]",
                    docstring="""
                    An optional mapping containing batch-level metadata attached to the list of
                    posting instructions that get atomically accepted or rejected.
                """,
                ),
                types_utils.ValueSpec(
                    name="booking_datetime",
                    type="Optional[datetime]",
                    docstring=booking_datetime_docstring,
                ),
            ]
        )
        if is_fflag_enabled(EXPECTED_PID_REJECTIONS):
            public_attributes.extend(
                [
                    types_utils.ValueSpec(
                        name="non_blocking_rejection_reasons",
                        type="Set[PostingInstructionRejectionReason]",
                        docstring="If this field is returned with a non-empty value for any hook "
                        "other than `scheduled_event_hook`, this raises an "
                        "`InvalidSmartContractError`. "
                        "If you experience a posting rejection with a reason within "
                        "this set of `PostingInstructionRejectionReason`s "
                        "while this `PostingInstructionsDirective` is instructed, it will "
                        "not cause the associated schedule job to fail, will not block "
                        "subsequent schedule jobs from being scheduled and other directives "
                        "returned from this hook will be committed.",
                    ),
                ]
            )
        return public_attributes
