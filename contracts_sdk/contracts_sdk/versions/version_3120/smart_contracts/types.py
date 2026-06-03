from ...version_3110.smart_contracts.types import *  # noqa: F401, F403
from ...version_3110.smart_contracts import types as types3110
from ..common.types import (
    SupervisedHooks,
    SupervisionExecutionMode,
    HookDirectives,
    InstructAccountNotificationDirective,
)


def types_registry():  # type: ignore
    TYPES = types3110.types_registry()
    TYPES["SupervisedHooks"] = SupervisedHooks
    TYPES["SupervisionExecutionMode"] = SupervisionExecutionMode
    TYPES["InstructAccountNotificationDirective"] = InstructAccountNotificationDirective
    TYPES["HookDirectives"] = HookDirectives
    return TYPES
