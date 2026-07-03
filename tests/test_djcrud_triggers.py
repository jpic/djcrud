import pytest

from djcrud_triggers.apps import DjcrudTriggersConfig
from djcrud_triggers.hooks import (
    HookDecision,
    TriggerHookEvent,
    TriggerHookResult,
    clear_hooks,
    register_hook,
    trigger_hooks,
)


@pytest.fixture(autouse=True)
def _reset_hooks():
    clear_hooks()
    yield
    clear_hooks()


def test_register_requires_installed_app():
    with pytest.raises(ValueError, match="INSTALLED_APPS"):
        register_hook(
            "run:complete",
            DjcrudTriggersConfig._noop_hook,
            app="not_an_app",
        )


def test_register_from_trusted_module():
    register_hook(
        "run:complete",
        DjcrudTriggersConfig._noop_hook,
        app="djcrud_triggers",
    )
    result = trigger_hooks(TriggerHookEvent(type="run", action="complete"))
    assert result.decision == HookDecision.ALLOW


def test_decision_hook_can_skip():
    register_hook("job:fire", DjcrudTriggersConfig._skip_hook, app="djcrud_triggers")
    result = trigger_hooks(TriggerHookEvent(type="job", action="fire", job_id="abc"))
    assert result.decision == HookDecision.SKIP
    assert result.reason == "busy"


def test_handler_module_must_be_installed():
    def outside_handler(event):
        return None

    outside_handler.__module__ = "totally_fake_module"
    with pytest.raises(ValueError, match="not in an INSTALLED_APPS"):
        register_hook("run:complete", outside_handler, app="djcrud_triggers")
