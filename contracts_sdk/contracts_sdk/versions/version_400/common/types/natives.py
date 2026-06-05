import calendar
import collections
import datetime
import decimal
import json
import math
import typing
import zoneinfo

# Ignore lint checks to enable more generic compatibility of third party module imports
from dateutil import parser, relativedelta  # type: ignore
from .....utils import types_utils

PYTHON_VERSION_WARNING = """Note: This external link takes you to the latest version of
    documentation for Python 3.x. Check the [Contracts Language 4 release
    notes](/reference/contracts/contracts_api_4xx/version_notes/#release_notes) for the version of
    Python supported on your version of Vault, and select the correct Python version on the Python
    documentation page."""

anyObject = types_utils.NativeObjectSpec(
    name="Any",
    object=typing.Any,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Any]"
    "(https://docs.python.org/3/library/typing.html#typing.Any)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Any`",
)

calendarIsleapFunction = types_utils.NativeObjectSpec(
    name="isleap",
    object=calendar.isleap,
    package=calendar,
    docs="[https://docs.python.org/3/library/calendar.html#calendar.isleap]"
    "(https://docs.python.org/3/library/calendar.html#calendar.isleap)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from calendar import isleap`",
)

calendarMonthrangeFunction = types_utils.NativeObjectSpec(
    name="monthrange",
    object=calendar.monthrange,
    package=calendar,
    docs="[https://docs.python.org/3/library/calendar.html#calendar.monthrange]"
    "(https://docs.python.org/3/library/calendar.html#calendar.monthrange)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from calendar import monthrange`",
)

callableObject = types_utils.NativeObjectSpec(
    name="Callable",
    object=typing.Callable,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Callable]"
    "(https://docs.python.org/3/library/typing.html#typing.Callable)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Callable`",
)

datetimeObject = types_utils.NativeObjectSpec(
    name="datetime",
    object=datetime.datetime,
    package=datetime,
    docs="[https://docs.python.org/3/library/datetime#datetime.datetime]"
    "(https://docs.python.org/3/library/datetime#datetime.datetime)",
    description=(
        "Note: `datetime` module `today`, `timetuple`, `strftime` and `strptime` "
        f"methods are not available. \n\n{PYTHON_VERSION_WARNING}"
    ),
    inline_import_example="`from datetime import datetime`",
)

decimalObject = types_utils.NativeObjectSpec(
    name="Decimal",
    object=decimal.Decimal,
    package=decimal,
    docs="[https://docs.python.org/3/library/decimal#decimal.Decimal]"
    "(https://docs.python.org/3/library/decimal#decimal.Decimal)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from decimal import Decimal`",
)

defaultDict = types_utils.NativeObjectSpec(
    name="defaultdict",
    object=collections.defaultdict,
    package=collections,
    docs="[https://docs.python.org/3/library/collections#collections.defaultdict]"
    "(https://docs.python.org/3/library/collections#collections.defaultdict)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from collections import defaultdict`",
)

defaultDictObject = types_utils.NativeObjectSpec(
    name="DefaultDict",
    object=typing.DefaultDict,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.DefaultDict]"
    "(https://docs.python.org/3/library/typing.html#typing.DefaultDict)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import DefaultDict`",
)

dictObject = types_utils.NativeObjectSpec(
    name="Dict",
    object=typing.Dict,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Dict]"
    "(https://docs.python.org/3/library/typing.html#typing.Dict)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Dict`",
)

iterableObject = types_utils.NativeObjectSpec(
    name="Iterable",
    object=typing.Iterable,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Iterable]"
    "(https://docs.python.org/3/library/typing.html#typing.Iterable)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Iterable`",
)

iteratorObject = types_utils.NativeObjectSpec(
    name="Iterator",
    object=typing.Iterator,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Iterator]"
    "(https://docs.python.org/3/library/typing.html#typing.Iterator)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Iterator`",
)

jsonDumpsObject = types_utils.NativeObjectSpec(
    name="dumps",
    object=json.dumps,
    package=json,
    docs="[https://docs.python.org/3/library/json#json.dumps]"
    "(https://docs.python.org/3/library/json#json.dumps)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from json import dumps`",
)

jsonLoadsObject = types_utils.NativeObjectSpec(
    name="loads",
    object=json.loads,
    package=json,
    docs="[https://docs.python.org/3/library/json#json.loads]"
    "(https://docs.python.org/3/library/json#json.loads)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from json import loads`",
)

listObject = types_utils.NativeObjectSpec(
    name="List",
    object=typing.List,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.List]"
    "(https://docs.python.org/3/library/typing.html#typing.List)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import List`",
)

mappingObject = types_utils.NativeObjectSpec(
    name="Mapping",
    object=typing.Mapping,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Mapping]"
    "(https://docs.python.org/3/library/typing.html#typing.Mapping)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Mapping`",
)

mathObject = types_utils.NativeObjectSpec(
    name="math",
    object=math,
    package=math,
    docs="[https://docs.python.org/3/library/math](https://docs.python.org/3/library/math)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`import math`",
)

namedTupleObject = types_utils.NativeObjectSpec(
    name="NamedTuple",
    object=typing.NamedTuple,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.NamedTuple]"
    "(https://docs.python.org/3/library/typing.html#typing.NamedTuple)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import NamedTuple`",
)

newTypeObject = types_utils.NativeObjectSpec(
    name="NewType",
    object=typing.NewType,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.NewType]"
    "(https://docs.python.org/3/library/typing.html#typing.NewType)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import NewType`",
)

noReturnObject = types_utils.NativeObjectSpec(
    name="NoReturn",
    object=typing.NoReturn,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.NoReturn]"
    "(https://docs.python.org/3/library/typing.html#typing.NoReturn)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import NoReturn`",
)

optionalObject = types_utils.NativeObjectSpec(
    name="Optional",
    object=typing.Optional,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Optional]"
    "(https://docs.python.org/3/library/typing.html#typing.Optional)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Optional`",
)

parseToDatetimeObject = types_utils.NativeObjectSpec(
    name="parse",
    object=parser.parse,
    package=parser,
    docs="[https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse]"
    "(https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse)",
    description="",
    inline_import_example="`from dateutil.parser import parse`",
)

relativedeltaObject = types_utils.NativeObjectSpec(
    name="relativedelta",
    object=relativedelta.relativedelta,
    package=relativedelta,
    docs="[https://dateutil.readthedocs.io/en/stable/relativedelta.html]"
    "(https://dateutil.readthedocs.io/en/stable/relativedelta.html)",
    description="",
    inline_import_example="`from dateutil.relativedelta import relativedelta`",
)

roundFloorObject = types_utils.NativeObjectSpec(
    name="ROUND_FLOOR",
    object=decimal.ROUND_FLOOR,
    package=decimal,
    docs="[https://docs.python.org/3/library/decimal#decimal.ROUND_FLOOR]"
    "(https://docs.python.org/3/library/decimal#decimal.ROUND_FLOOR)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from decimal import ROUND_FLOOR`",
)

roundHalfDownObject = types_utils.NativeObjectSpec(
    name="ROUND_HALF_DOWN",
    object=decimal.ROUND_HALF_DOWN,
    package=decimal,
    docs="[https://docs.python.org/3/library/decimal#decimal.ROUND_HALF_DOWN]"
    "(https://docs.python.org/3/library/decimal#decimal.ROUND_HALF_DOWN)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from decimal import ROUND_HALF_DOWN`",
)

roundHalfUpObject = types_utils.NativeObjectSpec(
    name="ROUND_HALF_UP",
    object=decimal.ROUND_HALF_UP,
    package=decimal,
    docs="[https://docs.python.org/3/library/decimal#decimal.ROUND_HALF_UP]"
    "(https://docs.python.org/3/library/decimal#decimal.ROUND_HALF_UP)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from decimal import ROUND_HALF_UP`",
)

roundCeilingObject = types_utils.NativeObjectSpec(
    name="ROUND_CEILING",
    object=decimal.ROUND_CEILING,
    package=decimal,
    docs="[https://docs.python.org/3/library/decimal#decimal.ROUND_CEILING]"
    "(https://docs.python.org/3/library/decimal#decimal.ROUND_CEILING)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from decimal import ROUND_CEILING`",
)

roundDownObject = types_utils.NativeObjectSpec(
    name="ROUND_DOWN",
    object=decimal.ROUND_DOWN,
    package=decimal,
    docs="[https://docs.python.org/3/library/decimal#decimal.ROUND_DOWN]"
    "(https://docs.python.org/3/library/decimal#decimal.ROUND_DOWN)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from decimal import ROUND_DOWN`",
)

roundHalfEvenObject = types_utils.NativeObjectSpec(
    name="ROUND_HALF_EVEN",
    object=decimal.ROUND_HALF_EVEN,
    package=decimal,
    docs="[https://docs.python.org/3/library/decimal#decimal.ROUND_HALF_EVEN]"
    "(https://docs.python.org/3/library/decimal#decimal.ROUND_HALF_EVEN)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from decimal import ROUND_HALF_EVEN`",
)

round05UpObject = types_utils.NativeObjectSpec(
    name="ROUND_05UP",
    object=decimal.ROUND_05UP,
    package=decimal,
    docs="[https://docs.python.org/3/library/decimal#decimal.ROUND_05UP]"
    "(https://docs.python.org/3/library/decimal#decimal.ROUND_05UP)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from decimal import ROUND_05UP`",
)

setObject = types_utils.NativeObjectSpec(
    name="Set",
    object=typing.Set,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Set]"
    "(https://docs.python.org/3/library/typing.html#typing.Set)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Set`",
)

tupleObject = types_utils.NativeObjectSpec(
    name="Tuple",
    object=typing.Tuple,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Tuple]"
    "(https://docs.python.org/3/library/typing.html#typing.Tuple)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Tuple`",
)

typeObject = types_utils.NativeObjectSpec(
    name="Type",
    object=typing.Type,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Type]"
    "(https://docs.python.org/3/library/typing.html#typing.Type)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Type`",
)

unionObject = types_utils.NativeObjectSpec(
    name="Union",
    object=typing.Union,
    package=typing,
    docs="[https://docs.python.org/3/library/typing.html#typing.Union]"
    "(https://docs.python.org/3/library/typing.html#typing.Union)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from typing import Union`",
)

zoneInfoObject = types_utils.NativeObjectSpec(
    name="ZoneInfo",
    object=zoneinfo.ZoneInfo,
    package=zoneinfo,
    docs="[https://docs.python.org/3/library/zoneinfo.html]"
    "(https://docs.python.org/3/library/zoneinfo.html)",
    description=PYTHON_VERSION_WARNING,
    inline_import_example="`from zoneinfo import ZoneInfo`",
)

# This is a map of packages to methods that are available to be imported. It is used to validate
# imports in sandbox utils.
# If a package has an import of "all_required" it means that the whole package needs to be imported
# e.g. `from math import pow` is not allowed.
ALLOWED_NATIVES = {
    "calendar": {
        "isleap": calendarIsleapFunction,
        "monthrange": calendarMonthrangeFunction,
    },
    "collections": {"defaultdict": defaultDict},
    "datetime": {"datetime": datetimeObject},
    "dateutil.parser": {"parse": parseToDatetimeObject},
    "dateutil.relativedelta": {"relativedelta": relativedeltaObject},
    "decimal": {
        "Decimal": decimalObject,
        "ROUND_05UP": round05UpObject,
        "ROUND_CEILING": roundCeilingObject,
        "ROUND_DOWN": roundDownObject,
        "ROUND_FLOOR": roundFloorObject,
        "ROUND_HALF_DOWN": roundHalfDownObject,
        "ROUND_HALF_EVEN": roundHalfEvenObject,
        "ROUND_HALF_UP": roundHalfUpObject,
    },
    "json": {"dumps": jsonDumpsObject, "loads": jsonLoadsObject},
    "math": {"all_required": mathObject},
    "typing": {
        "Any": anyObject,
        "Callable": callableObject,
        "DefaultDict": defaultDictObject,
        "Dict": dictObject,
        "Iterable": iterableObject,
        "Iterator": iteratorObject,
        "List": listObject,
        "Mapping": mappingObject,
        "NamedTuple": namedTupleObject,
        "NewType": newTypeObject,
        "NoReturn": noReturnObject,
        "Optional": optionalObject,
        "Set": setObject,
        "Type": typeObject,
        "Tuple": tupleObject,
        "Union": unionObject,
    },
    "zoneinfo": {"ZoneInfo": zoneInfoObject},
}
