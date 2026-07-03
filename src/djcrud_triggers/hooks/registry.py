from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from django.apps import apps
from django.conf import settings

from .events import HookDecision, TriggerHookEvent, TriggerHookResult
from .runner import run_handlers

logger = logging.getLogger(__name__)

TriggerHookHandler = Callable[
    [TriggerHookEvent], TriggerHookResult | None | HookDecision | None
]


@dataclass(order=True)
class _HandlerEntry:
    priority: int
    app: str
    event_key: str
    handler: TriggerHookHandler = field(compare=False)
    handler_id: int = field(compare=False, default=0)

    def __post_init__(self) -> None:
        if self.handler_id == 0:
            object.__setattr__(self, "handler_id", id(self.handler))


_HANDLERS: dict[str, list[_HandlerEntry]] = {}
_DECISION_EVENTS = frozenset(
    {
        "job:fire",
        "run:start",
        "heartbeat:tick",
    }
)


def _validate_handler(handler: TriggerHookHandler, *, app: str) -> None:
    if not callable(handler):
        raise TypeError("handler must be callable")
    module = getattr(handler, "__module__", "") or ""
    if module.startswith("_"):
        raise ValueError(f"handler module {module!r} is not allowed")
    installed_roots = _installed_app_roots()
    if not any(
        module == root or module.startswith(f"{root}.") for root in installed_roots
    ):
        raise ValueError(
            f"handler {handler!r} from {module!r} is not in an INSTALLED_APPS package "
            f"(registered by {app!r})"
        )


def _installed_app_roots() -> set[str]:
    roots: set[str] = set()
    for app_config in apps.get_app_configs():
        name = app_config.name
        roots.add(name)
        module = getattr(app_config, "module", None)
        if module is not None:
            roots.add(module.__name__)
    return roots


def register_hook(
    event_key: str,
    handler: TriggerHookHandler,
    *,
    priority: int = 0,
    app: str | None = None,
) -> None:
    """Register a typed hook handler from a trusted installed app."""
    if ":" not in event_key:
        raise ValueError(f"event_key must be type:action, got {event_key!r}")
    if app is None:
        module = getattr(handler, "__module__", "")
        for app_config in apps.get_app_configs():
            mod = getattr(app_config, "module", None)
            if mod is not None and (
                module == mod.__name__ or module.startswith(f"{mod.__name__}.")
            ):
                app = app_config.name
                break
        if app is None:
            raise ValueError("could not infer app for handler; pass app=")
    if app not in {cfg.name for cfg in apps.get_app_configs()}:
        raise ValueError(f"app {app!r} is not in INSTALLED_APPS")
    _validate_handler(handler, app=app)
    entry = _HandlerEntry(
        priority=-priority, app=app, event_key=event_key, handler=handler
    )
    _HANDLERS.setdefault(event_key, []).append(entry)
    _HANDLERS[event_key].sort()
    logger.debug("registered hook %s from %s priority=%s", event_key, app, priority)


def unregister_hook(event_key: str, handler: TriggerHookHandler) -> bool:
    entries = _HANDLERS.get(event_key)
    if not entries:
        return False
    handler_id = id(handler)
    _HANDLERS[event_key] = [e for e in entries if e.handler_id != handler_id]
    if not _HANDLERS[event_key]:
        _HANDLERS.pop(event_key, None)
    return True


def _handlers_for(event: TriggerHookEvent) -> list[_HandlerEntry]:
    specific = list(_HANDLERS.get(event.key, []))
    general = list(_HANDLERS.get(event.type, []))
    combined = specific + general
    combined.sort()
    return combined


def trigger_hooks(event: TriggerHookEvent) -> TriggerHookResult:
    """Dispatch hooks for an event. Decision hooks can deny or skip."""
    if not getattr(settings, "DJACP_HOOKS_ENABLED", True):
        return TriggerHookResult()
    entries = _handlers_for(event)
    if not entries:
        return TriggerHookResult()
    is_decision = event.key in _DECISION_EVENTS
    return run_handlers(entries, event, is_decision=is_decision)


def clear_hooks() -> None:
    """Test helper: remove all registered handlers."""
    _HANDLERS.clear()
