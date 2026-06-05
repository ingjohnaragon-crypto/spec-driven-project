import re
from functools import lru_cache

#  Regex Description
#  All fields support the modifiers: '*' '/' '?' ',' '-'
#  ┌──────────── second (0-59)
#  │ ┌────────── minute (0-59)
#  │ │ ┌──────── hour (0-23)
#  │ │ │ ┌────── day of the month (1-31), Additional Modifiers (L,W,LW,LAST)
#  │ │ │ │ ┌──── month (1-12)
#  │ │ │ │ │ ┌── day of the week (0-6 or MON-SUN), Additional Modifiers (L,#)
#  │ │ │ │ │ │ ┌ year (1970-2099)
#  * * * * * * *


@lru_cache(maxsize=1)
def initialise_cron():
    def make_subpatterns(modifier, patterns, alt_modifier=""):
        subpatterns = {
            "Wildcard": "\\*|\\?",
            "Value": f"{modifier}",
            "Range": f"({modifier})-({modifier})",
            "WildcardAndInterval": "\\*/(\\d+)",
            "ValueAndInterval": f"({modifier})/(\\d+)",
            "RangeAndInterval": f"({modifier})-({modifier})/(\\d+)",
            "LastDom": "l",
            "Workdom": f"({modifier})w",
            "LastWorkdom": "lw",
            "DowOfLastWeek": f"({modifier})l",
            "DowOfSpecificWeek": f"({modifier})#([1-5])",
            # Alternate Modifiers is used for text (Month / Days)
            "AltValue": f"{alt_modifier}",
            "AltRange": f"({alt_modifier})-({alt_modifier})",
            "AltValueAndInterval": f"({alt_modifier})/(\\d+)",
            "AltRangeAndInterval": f"({alt_modifier})-({alt_modifier})/(\\d+)",
            "AltDowOfSpecificWeek": f"({alt_modifier})#([1-5])",
        }
        base_pattern = "("
        for pattern in patterns:
            base_pattern += subpatterns[pattern] + "|"
        base_pattern = base_pattern.rstrip("|") + ")"

        return f"({base_pattern}(,{base_pattern})*\\s*)"

    default_subpatterns = [
        "Wildcard",
        "Value",
        "Range",
        "WildcardAndInterval",
        "ValueAndInterval",
        "RangeAndInterval",
    ]

    # Start of string
    pattern = "^"
    # All patterns below allow for the symbols: '*', '?', '/', ',', '-'

    # 60 Seconds, Minutes (0-59)
    pattern += make_subpatterns(r"(0?[0-9]|[1-4][0-9]|5[0-9])", default_subpatterns) * 2

    # 24 Hours (0-23)
    pattern += make_subpatterns(r"(0?[0-9]|1[0-9]|2[0-3])", default_subpatterns)

    # 31 Days (1-31)
    day_of_month_subpatterns = ["LastDom", "Workdom", "LastWorkdom", "AltValue"]
    pattern += make_subpatterns(
        r"(0?[1-9]|[12][0-9]|3[01])", default_subpatterns + day_of_month_subpatterns, r"LAST"
    )

    # 12 Months (1-12)
    month_str = r"JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC"
    month_subpatterns = ["AltValue", "AltRange", "AltValueAndInterval", "AltRangeAndInterval"]
    pattern += make_subpatterns(
        r"(0?[1-9]|1[0-2])", default_subpatterns + month_subpatterns, month_str
    )

    # 0-6 or MON/TUE/WED/THU/FRI/SAT/SUN
    day_of_week_subpatterns = [
        "DowOfLastWeek",
        "DowOfSpecificWeek",
        "AltValue",
        "AltRange",
        "AltValueAndInterval",
        "AltRangeAndInterval",
        "AltDowOfSpecificWeek",
    ]
    dow_str = r"MON|TUE|WED|THU|FRI|SAT|SUN"
    pattern += make_subpatterns(
        r"(0?[0-6])", default_subpatterns + day_of_week_subpatterns, dow_str
    )

    # Year (1970-2099)
    pattern += make_subpatterns(r"(19[7-9][0-9]|20[0-9][0-9])", default_subpatterns)

    # End of string
    pattern += r"$"
    return re.compile(pattern, re.IGNORECASE)


# initialise_cron() is called once on import to compile the regex and cache the result.
initialise_cron()


def validate_cron(expression: str) -> bool:
    """
    Performs regex-based validation to filter out expressions that are not supported by the Vault
    Scheduler. This util alone does not check whether a ScheduleExpression is valid, as it is
    designed as a first line of defence to help a client catch invalid expressions during their unit
    testing stage. This util technically allows a wider set of cron expressions than we document in
    the ScheduleExpression class of the Contracts Language API. The Thought Machine documentation
    site is the ultimate reference to supported cron expressions: do not make use of values outside
    of this accepted range.
    Also, this util doesn't check the validity of chained complex expressions, nor does it check
    whether the represented dates are well defined, such as 30th Feb. The util leaves validity
    checks for those use cases to the downstream services within Vault Core where the schedules are
    actually being created.
    """

    num_fields = len(expression.split(" "))
    if num_fields != 7:
        return False

    cron_regex = initialise_cron()
    return cron_regex.match(expression) is not None
