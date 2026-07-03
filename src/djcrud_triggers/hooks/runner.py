from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .events import HookDecision, TriggerHookEvent, TriggerHookResult

if TYPE_CHECKING:
    from .registry import _HandlerEntry

logger = logging.getLogger(__name__)


def _normalize_result(value) -> TriggerHookResult | None:
    if value is None:
        return None
    if isinstance(value, TriggerHookResult):
        return value
    if isinstance(value, HookDecision):
        return TriggerHookResult(decision=value)
    return None


def run_handlers(
    entries: list[_HandlerEntry],
    event: TriggerHookEvent,
    *,
    is_decision: bool,
) -> TriggerHookResult:
    aggregate = TriggerHookResult()
    for entry in entries:
        try:
            raw = entry.handler(event)
        except Exception:
            logger.exception(
                "hook handler failed event=%s app=%s",
                event.key,
                entry.app,
            )
            if is_decision:
                continue
            continue
        result = _normalize_result(raw)
        if result is None:
            continue
        if result.context:
            aggregate.context.update(result.context)
        if not is_decision:
            continue
        if result.blocks:
            return result
    return aggregate
