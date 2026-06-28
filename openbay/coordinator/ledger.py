"""In-memory node registry + kudos ledger.

This is the MVP's coordination brain. It deliberately keeps everything in
process memory so the demo runs with zero external dependencies. Persistence
(SQLite/Redis), churn eviction, and on-chain settlement are later milestones
(see docs/ROADMAP.md).
"""
from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field


@dataclass
class Seeder:
    node_id: str
    url: str
    models: list[str]
    gpu: str | None = None
    last_seen: float = field(default_factory=time.time)


class Registry:
    def __init__(self) -> None:
        self._seeders: dict[str, Seeder] = {}
        self._kudos: dict[str, float] = {}
        self._lock = threading.Lock()

    # --- node lifecycle ---
    def register(self, node_id: str, url: str, models: list[str],
                 gpu: str | None = None) -> None:
        with self._lock:
            self._seeders[node_id] = Seeder(node_id, url, list(models), gpu)
            self._kudos.setdefault(node_id, 0.0)

    def heartbeat(self, node_id: str) -> None:
        with self._lock:
            s = self._seeders.get(node_id)
            if s:
                s.last_seen = time.time()

    def seeders_for(self, model: str) -> list[Seeder]:
        with self._lock:
            return [s for s in self._seeders.values() if model in s.models]

    def pick(self, model: str) -> Seeder | None:
        # v1: random among capable seeders. v2: load/latency-aware + KV-cache reuse.
        candidates = self.seeders_for(model)
        return random.choice(candidates) if candidates else None

    # --- kudos economy ---
    def settle(self, client_id: str, node_id: str, tokens: float) -> None:
        """Credit the seeder for work done, debit the client who consumed it."""
        with self._lock:
            self._kudos[node_id] = self._kudos.get(node_id, 0.0) + tokens
            self._kudos[client_id] = self._kudos.get(client_id, 0.0) - tokens

    def balances(self) -> dict[str, float]:
        with self._lock:
            return dict(self._kudos)

    def nodes(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "node_id": s.node_id,
                    "url": s.url,
                    "models": s.models,
                    "gpu": s.gpu,
                    "last_seen": s.last_seen,
                }
                for s in self._seeders.values()
            ]
