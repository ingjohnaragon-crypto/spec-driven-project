from .....utils.symbols import DefinedDateTime, ScheduleFailover
from .....utils import types_utils


DefinedDateTime = types_utils.transform_const_enum(
    name="DefinedDateTime",
    const_enum=DefinedDateTime,
    docstring=(
        "A datetime that is defined within Vault. This datetime can be used in the "
        "Observation and Interval Fetchers, which are included in the "
        "[data_fetchers](../../smart_contracts_api_reference3xx/metadata/#data_fetchers) "
        "of the Contracts Metadata.\n\n* `EFFECTIVE_DATETIME` maps to the `effective_datetime`"
        " of the hook that is using a Data Fetcher.\n* `INTERVAL_START` can be used as an "
        "origin of the [RelativeDateTime](#classes-RelativeDateTime) to define the start "
        "of an Interval Fetcher, as evaluated at the runtime of the hook.\n* `LIVE` maps to "
        "the actual runtime of the hook (`UTC NOW()`) that is using a Data Fetcher, which "
        "can be after the hook `effective_datetime`."
    ),
    hide_keys=("EFFECTIVE_DATETIME"),
)

ScheduleFailover = types_utils.transform_const_enum(
    name="ScheduleFailover",
    const_enum=ScheduleFailover,
    docstring="Specify the failover strategy for this schedule.",
)
