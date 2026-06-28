# Roadmap

Staged so every version ships something usable. See [PLAN.md](PLAN.md) for the
hypotheses each milestone proves.

## v1 — Whole-model swarm (in progress)

**Goal:** prove H1 (a whole-model consumer-GPU swarm is usable) and set up H3.

Done (v0.1 skeleton):
- [x] Coordinator: registry + matchmaking + kudos ledger
- [x] Seeder: registers, serves a whole model via Ollama, streams tokens
- [x] Client: streams tokens from the swarm
- [x] Smoke tests (no GPU/Ollama needed)

Next (good first issues 👇):
- [ ] **Spot-check verification** — coordinator re-sends a small % of jobs to a
      second seeder and compares first-N tokens; flag mismatches. *(core to H3)*
- [ ] **Persistence** — back the registry + kudos ledger with SQLite so state
      survives restarts.
- [ ] **Heartbeat + eviction** — drop seeders that stop sending heartbeats; reroute.
- [ ] **`/metrics`** — expose TTFT and tokens/sec per request (Prometheus-style).
- [ ] **WAN simulation harness** — scripted `tc netem` latency to benchmark H2 honestly.
- [ ] **Desktop seeder** — one-click "share my GPU while idle" wrapper (Tauri/Electron).
- [ ] **Engine adapters** — llama.cpp and MLX seeders alongside Ollama.
- [ ] **A tiny web dashboard** — live swarm + kudos view.

## v2 — Big-model sharding

**Goal:** prove H2 (beat the Petals round-trip wall) and serve models too big for
one card.

- [ ] Layer-wise sharding across peers (Exo/HyperCluster-style), VRAM-aware.
- [ ] Block/speculative transport: draft K tokens, verify a block per round-trip.
- [ ] Resolve the drafter↔target coupling (KV-injection) for a distributed target.
- [ ] Churn handling: re-prefill or replicate KV on shard drop; measure recovery.
- [ ] NAT traversal (STUN/TURN), DHT-based shard discovery.

## v3 — Permissionless trust + economy

**Goal:** trustless end of H3.

- [ ] Verifiable inference (VeriLLM-style commit-sample-check, ~1% overhead).
- [ ] Reputation + stake/slashing; persistent identity.
- [ ] Real settlement (optional; only if going fully permissionless).
- [ ] Collaborative fine-tuning (DECA-style) on the swarm.

## Good first issues — start here

If you're new, these are self-contained and high-value:
1. SQLite persistence for the ledger (`coordinator/ledger.py`).
2. Spot-check verification endpoint + comparison logic.
3. `/metrics` timing on `/v1/infer`.
4. A llama.cpp seeder adapter mirroring `seeder/worker.py`.
5. A 30-line web page hitting `/nodes` and `/ledger` for a live dashboard.

Open an issue describing your approach before large changes. Apache-2.0; be kind.
