from abc import abstractmethod
from functools import lru_cache
from typing import List

from . import types as smart_contract_types
from ....utils import symbols, types_utils
from ...version_360.smart_contracts import lib as v360_lib
from ..common import lib as common_lib


types_registry = smart_contract_types.types_registry

ALLOWED_BUILTINS = common_lib.ALLOWED_BUILTINS


class VaultFunctionsABC(v360_lib.VaultFunctionsABC):
    @abstractmethod
    def get_calendar_events(self, *, calendar_ids: List[str]):
        pass

    @abstractmethod
    def make_internal_transfer_instructions(
        self,
        *,
        amount,
        denomination,
        client_transaction_id,
        from_account_id,
        from_account_address=None,
        to_account_id,
        to_account_address=None,
        pics=None,
        override_all_restrictions=False,
        instruction_details=None,
        transaction_code=None,
        asset=symbols.DEFAULT_ASSET,
    ):
        pass

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        spec = super()._spec(language_code)
        spec.public_methods["get_calendar_events"] = types_utils.MethodSpec(
            name="get_calendar_events",
            docstring="""
                    Returns a [CalendarEvents](/reference/contracts/contracts_api_3xx/contract_modules_api_reference3xx/types/#classes-CalendarEvents) object with the
                    chronologically ordered list of [CalendarEvent](/reference/contracts/contracts_api_3xx/contract_modules_api_reference3xx/types/#classes-CalendarEvent)
                    that exist in the Vault calendars with the given `calendar_ids`. These
                    `calendar_ids` have to be requested using the hook '@requires' decorator.
                    For information about the time range of events returned,
                    see [calendar](/reference/contracts/contracts_api_3xx/smart_contracts_api_reference3xx/hook_requirements/#calendar)
                    **Only available in version 3.7+.**
            """,
            args=[
                types_utils.ValueSpec(
                    name="calendar_ids", type="List[str]", docstring="List of Calendar Ids"
                ),
            ],
            return_value=types_utils.ReturnValueSpec(
                docstring="""
                    The chronologically ordered list of
                    [CalendarEvent](../types/#classes-CalendarEvent) objects.
                """,
                type="CalendarEvents",
            ),
            examples=[
                types_utils.Example(
                    title="The Vault calendar usage example",
                    code="""
                    @requires(calendar=["WEEKENDS", "BANK_HOLIDAYS", "PROMOTION_DAYS"])
                    def execution_schedules():
                        vault.get_calendar_events(calendar_ids=["WEEKENDS", "BANK_HOLIDAYS"])
                    """,
                )
            ],
        )
        key = "make_internal_transfer_instructions"
        arg = "transaction_code"
        spec.public_methods[key].args[arg] = types_utils.ValueSpec(
            name="transaction_code",
            type="Optional[TransactionCode]",
            docstring="""
                Optional ``[./TransactionCode]`` attribute to be attached to the created PostingInstruction.
                **Only available in version 3.7.0+**.
            """,
        )

        return spec
