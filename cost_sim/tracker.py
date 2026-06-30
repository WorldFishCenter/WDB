"""Thin Anthropic client wrapper that intercepts messages.create() and records
real token usage for cost accounting.

Inject a TrackingClient wherever a Live backend accepts client=:

    log = CostLog()
    client = anthropic.Anthropic()
    reasoner = LiveReasoner(client=TrackingClient(client, log, slot="mode_a"))
    synth    = LiveSynthesizer(client=TrackingClient(client, log, slot="mode_b"))
    resolver = LiveResolver(catalog, client=TrackingClient(client, log, slot="mode_c"))

The wrapper is transparent: it passes every argument through unchanged and returns
the original response object, so the Live backends never need to know it is there.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .rates import cost_usd


@dataclass
class CallRecord:
    slot: str       # "mode_a" / "mode_b" / "mode_c"
    model: str      # exact model ID passed to messages.create()
    in_tok: int
    out_tok: int
    cost_usd: float
    ts: float = field(default_factory=time.time)


class CostLog:
    """Accumulates CallRecord entries across an entire simulation run."""

    def __init__(self) -> None:
        self.records: list[CallRecord] = []

    def record(self, *, slot: str, model: str, in_tok: int, out_tok: int) -> None:
        c = cost_usd(model, in_tok, out_tok)
        self.records.append(CallRecord(slot=slot, model=model, in_tok=in_tok, out_tok=out_tok, cost_usd=c))

    def total_usd(self) -> float:
        return sum(r.cost_usd for r in self.records)

    def since(self, ts: float) -> list[CallRecord]:
        """Records added after timestamp ts — used to isolate one question's cost."""
        return [r for r in self.records if r.ts >= ts]

    def by_slot(self) -> dict[str, list[CallRecord]]:
        result: dict[str, list[CallRecord]] = {}
        for r in self.records:
            result.setdefault(r.slot, []).append(r)
        return result


class _TrackingMessages:
    """Proxies .messages.create() and records usage on every response."""

    def __init__(self, real_messages: Any, log: CostLog, slot: str) -> None:
        self._real = real_messages
        self._log = log
        self._slot = slot

    def create(self, *args: Any, **kwargs: Any) -> Any:
        resp = self._real.create(*args, **kwargs)
        model = kwargs.get("model", args[0] if args else "unknown")
        self._log.record(
            slot=self._slot,
            model=model,
            in_tok=resp.usage.input_tokens,
            out_tok=resp.usage.output_tokens,
        )
        return resp


class TrackingClient:
    """Wraps anthropic.Anthropic() transparently, intercepting messages.create()."""

    def __init__(self, real_client: Any, log: CostLog, slot: str) -> None:
        self._real = real_client
        self.messages = _TrackingMessages(real_client.messages, log, slot)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)
