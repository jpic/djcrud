from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class HookDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    SKIP = "skip"


@dataclass
class TriggerHookEvent:
    type: str
    action: str
    session_key: str = ""
    thread_id: int | None = None
    job_id: str | None = None
    run_id: int | None = None
    owner_id: int | None = None
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def key(self) -> str:
        return f"{self.type}:{self.action}"


@dataclass
class TriggerHookResult:
    decision: HookDecision = HookDecision.ALLOW
    reason: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def blocks(self) -> bool:
        return self.decision in (HookDecision.DENY, HookDecision.SKIP)
