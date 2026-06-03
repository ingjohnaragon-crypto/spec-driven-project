from abc import abstractmethod, ABC
from datetime import datetime
from functools import lru_cache
from typing import List

from ....utils import symbols, types_utils
from ..common import lib as common_lib, types as common_types
from ..common.docs import _common_docs_path

from ....utils.feature_flags import (
    is_fflag_enabled,
    GET_HOOK_NAME,
)


ALLOWED_BUILTINS = common_lib.ALLOWED_BUILTINS
ALLOWED_NATIVES = common_lib.ALLOWED_NATIVES


class VaultFunctionsABC(ABC):
    @abstractmethod
    def get_plan_opening_datetime(self) -> datetime:
        pass

    @abstractmethod
    def get_hook_execution_id(self) -> str:
        pass

    @abstractmethod
    def get_hook_name(self) -> common_types.HookName:
        pass

    @abstractmethod
    def get_calendar_events(self, *, calendar_ids: List[str]) -> common_types.CalendarEvents:
        pass

    @classmethod
    @lru_cache()
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
        spec.public_attributes["plan_id"] = types_utils.ValueSpec(
            name="plan_id", type="str", docstring="The ID of the Plan currently being executed."
        )
        spec.public_attributes["supervisees"] = types_utils.ValueSpec(
            name="supervisees",
            type="Dict[str, Vault]",
            docstring="""
                A dictionary which maps the supervised Account IDs to their
                [Vault](../../smart_contracts_api_reference4xx/vault) objects. These objects can
                be used to retrieve account data, and to retrieve or commit Hook Directives.
                The allowed API functions of the Supervisee Vault objects per hook can be found
                [here](../../smart_contracts_api_reference4xx/hooks/).
            """,
        )
        spec.public_attributes["events_timezone"] = types_utils.ValueSpec(
            name="events_timezone",
            type="ZoneInfo",
            docstring="""
                The timezone in which this Plan operates.  If the plan **belongs to a
                [Processing Group](/reference/processing_groups/)** which has a timezone
                declared, this will be the timezone used. If there is **no Processing Group timezone set**, the
                `events_timezone`
                [metadata](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/metadata/#events_timezone)
                in the Contract will be used. If **neither of these is set**, the timezone defaults to UTC.
            """,
        )
        spec.public_methods["get_hook_execution_id"] = types_utils.MethodSpec(
            name="get_hook_execution_id",
            docstring="""
                Returns a unique-enough string that can be used in generating unique IDs for
                attaching to Hook Directives objects. The string returned is a combination of
                `plan_id`, `hook_id`, `event_type` and `effective_datetime`. Note: this string is
                unique for the Plan hook execution and it should not be used for multiple
                Supervisee Hook Directives, unless modified.
            """,
            args=[],
            return_value=types_utils.ReturnValueSpec(docstring="The unique-enough ID.", type="str"),
        )
        spec.public_methods["get_plan_opening_datetime"] = types_utils.MethodSpec(
            name="get_plan_opening_datetime",
            docstring="Returns the opening date of the Plan currently being executed.",
            args=[],
            return_value=types_utils.ReturnValueSpec(
                docstring="The date the Plan was opened as a timezone-aware UTC datetime.",
                type="datetime",
            ),
        )
        spec.public_methods["get_calendar_events"] = types_utils.MethodSpec(
            name="get_calendar_events",
            docstring=f"""
                Returns a [CalendarEvents]({_common_docs_path}classes/#CalendarEvents) object with the
                chronologically ordered list of [CalendarEvent]({_common_docs_path}classes/#CalendarEvent)
                that exist in the Vault calendars with the given `calendar_ids`. These
                `calendar_ids` have to be requested using the hook '@requires' decorator.
                For information about the time range of events returned,
                see [calendar](/reference/contracts/contracts_api_4xx/supervisor_contracts_api_reference4xx/hook_requirements/#calendar)
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
        )

        if is_fflag_enabled(GET_HOOK_NAME):
            spec.public_methods["get_hook_name"] = types_utils.MethodSpec(
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

        return spec
