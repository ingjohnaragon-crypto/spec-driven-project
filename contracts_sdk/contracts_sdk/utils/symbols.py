# IF UPDATING THESE CLASSES, YOU MUST ALSO UPDATE THE CORRESPONDING ENUM CLASSES FOR LANGUAGE V4

# Client ID used for PostingInstructions instructed by Smart Contracts.
POSTINGS_V3_KAFKA_CLIENT_ID = "CoreContracts"
# The default asset used when instructing PostingInstructions in Smart Contracts.
DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"
# The default account address used when instructing PostingInstructions in Smart Contracts.
DEFAULT_ADDRESS = "DEFAULT"
# Used by the Experience Layer to describe PostingInstructions.
TRANSACTION_REFERENCE_FIELD_NAME = "description"
# Internal PostingInstruction attribute used to identify Smart Contract instructed postings.
ORIGINATING_ACCOUNT_ID_TAG = "originating_account_id"


class VaultRejectionReasonCode:
    UNKNOWN_REASON = 0
    INSUFFICIENT_FUNDS = 1
    WRONG_DENOMINATION = 2
    AGAINST_TNC = 3
    CLIENT_CUSTOM_REASON = 4


class Tside:
    ASSET = 1
    LIABILITY = 2


TSIDE_NET_BALANCE_MAP = {Tside.LIABILITY: 1, Tside.ASSET: -1}


class ContractParameterLevel:
    GLOBAL = 1
    TEMPLATE = 2
    INSTANCE = 3


class ContractParameterUpdatePermission:
    PERMISSION_UNKNOWN = 0
    FIXED = 1
    OPS_EDITABLE = 2
    USER_EDITABLE = 3
    USER_EDITABLE_WITH_OPS_PERMISSION = 4


class Features:
    UNKNOWN_FEATURE = 0
    MANDATES = 1
    MULTIPLE_OWNERS = 3
    CARD = 4
    SUB_ACCOUNTS = 5
    JOINT_ACCOUNT = 6
    INVESTMENT = 7


class NoteType:
    UNKNOWN = 0
    RAW_TEXT = 1
    REASON_CODE = 2


class NumberKind:
    PLAIN = "plain"
    PERCENTAGE = "percentage"
    MONEY = "money"
    MONTHS = "months"


class Languages:
    ENGLISH = 0


class Phase:
    COMMITTED = "committed"
    PENDING_IN = "pending_in"
    PENDING_OUT = "pending_out"


class PostingInstructionType:
    OUTBOUND_AUTHORISATION = "OutboundAuthorisation"
    INBOUND_AUTHORISATION = "InboundAuthorisation"
    AUTHORISATION = "Authorisation"
    AUTHORISATION_ADJUSTMENT = "AuthorisationAdjustment"
    CUSTOM_INSTRUCTION = "CustomInstruction"
    OUTBOUND_HARD_SETTLEMENT = "OutboundHardSettlement"
    INBOUND_HARD_SETTLEMENT = "InboundHardSettlement"
    HARD_SETTLEMENT = "HardSettlement"
    RELEASE = "Release"
    SETTLEMENT = "Settlement"
    TRANSFER = "Transfer"


class DefinedDateTime:
    LIVE = -1
    EFFECTIVE_TIME = 1
    INTERVAL_START = 2
    EFFECTIVE_DATETIME = 3


class ScheduleFailover:
    FIRST_VALID_DAY_BEFORE = 1
    FIRST_VALID_DAY_AFTER = 2


class SupervisionExecutionMode:
    OVERRIDE = 1
    INVOKED = 2


class DateTimePrecision:
    MINUTE = 0
    DAY = 1


class Timeline:
    PRESENT = 1
    FUTURE = 2


class AdjustmentStrategy:
    SCHEDULE_TRIGGERED = 1


class DateTimeView:
    """Used in a data fetcher to specify by which datetime view to fetch results"""

    # INSERTION_DATETIME = 1 was previously defined in vault/kernel/contracts/proto/data_fetchers/data_fetchers.proto
    VALUE_DATETIME = 2
    BOOKING_DATETIME = 3


class DateFailover:
    UNKNOWN = 0
    FIRST_VALID_DAY_BEFORE = 1
    FIRST_VALID_DAY_AFTER = 2


class PostingInstructionRejectionReason:
    REJECTION_REASON_UNKNOWN = 0
    RESTRICTION_PREVENT_DEBITS = 1
    RESTRICTION_PREVENT_CREDITS = 2
    RESTRICTION_LIMIT_DEBITS = 3
    RESTRICTION_LIMIT_CREDITS = 4
    RESTRICTION_REVIEW_DEBITS = 5
    RESTRICTION_REVIEW_CREDITS = 6
    INSUFFICIENT_FUNDS = 7
    AGAINST_TERMS_AND_CONDITIONS = 8
    CLIENT_CUSTOM_REASON = 9
    ACCOUNT_STATUS_INVALID = 10
    WRONG_DENOMINATION = 11


# These match up to the hook function names in the Contracts Language 4 API.
class HookName:
    UNKNOWN_HOOK = 0
    ACTIVATION_HOOK = 1
    SCHEDULED_EVENT_HOOK = 2
    DEACTIVATION_HOOK = 3
    CONVERSION_HOOK = 4
    POST_PARAMETER_CHANGE_HOOK = 5
    PRE_PARAMETER_CHANGE_HOOK = 6
    PRE_POSTING_HOOK = 7
    POST_POSTING_HOOK = 8
    DERIVED_PARAMETERS_HOOK = 9
    ATTRIBUTE_HOOK = 10
    SCHEDULED_EVENT_ADJUSTMENT_HOOK = 11
    POST_POSTING_ADJUSTMENT_HOOK = 12
    POST_PARAMETER_CHANGE_ADJUSTMENT_HOOK = 13
