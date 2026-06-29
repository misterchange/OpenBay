# OpenBay — Plan of Action

**A practical plan to build BitTorrent-style peer-to-peer LLM inference, and the falsifiable claims we set out to prove.**

Version 0.1 · Living document · Apache-2.0

---

## Abstract

Running large language models is gated behind expensive accelerators, cloud
accounts, payment rails, and regional restrictions. We propose **OpenBay**, an
open-source peer-to-peer network that pools idle consumer GPUs to serve models no
single participant can run alone — "BitTorrent for AI inference." Prior work
([Petals](https://arxiv.org/abs/2312.08361), 2022 — the first attempt to pool
volunteers' consumer GPUs this way) proved it *possible* but too slow to use:
splitting a model across machines forced a network round-trip for every token,
alongside weak trust guarantees and heavy memory footprints. We argue that a set of 2025–2026 advances
— **speculative / block-diffusion decoding**, **ultra-low-bit quantization-aware
training (QAT)**, and **lightweight verifiable inference** — change the governing
variable (tokens generated per network round-trip) enough to make a usable,
trust-minimized swarm practical. OpenBay runs in two modes — an open, permissionless
swarm, and **private clusters** that friends, a lab, or a team form behind a shared
join code, which dissolves the trust, privacy, and cold-start hurdles and is likely
the easiest path to first adoption. This document states what we will build, in what
order, and the specific, measurable claims by which we should be judged.

## 1. Problem

Inference is the recurring cost of AI, and access to it is unequal. The people
most excluded — those without GPU budgets, corporate cloud accounts, or credit
cards, and those in restricted regions — are exactly those a public good should
serve. Centralized APIs also meter and log every prompt.

A decentralized swarm could fix this *if* it were fast enough to be usable, honest
enough to be trusted, and cheap enough for volunteers to sustain. Petals showed
the concept; three obstacles kept it from mainstream use:

1. **Latency.** Autoregressive decoding requires one pass through the network per
   generated token. Over consumer internet (10–80 ms RTT), this dominates and caps
   throughput at ~1–2 tokens/sec.
2. **Trust.** In a permissionless network, workers can return cheap/garbage output
   and verifiers can free-ride. Petals assumed altruistic, non-malicious peers.
3. **Footprint.** Frontier models in FP16 don't fit consumer VRAM, forcing deep
   sharding and amplifying obstacle (1).

## 2. Key insight

**The bottleneck is tokens-per-WAN-round-trip, not the idea of pooling GPUs.**
Everything hinges on raising how much useful generation happens per network
exchange, and on shrinking models to fit the hardware volunteers actually own.

| Lever | What it changes | Primary sources |
|---|---|---|
| Speculative decoding (block-diffusion drafters) | tokens verified per round-trip: ~1 → 4–8 | [DFlash 2602.06036](https://arxiv.org/abs/2602.06036), [DFlare 2606.02091](https://arxiv.org/abs/2606.02091), DSpark (DeepSeek, 2026) |
| Block diffusion / MTP | tokens generated per forward pass | [BD3-LM 2503.09573](https://arxiv.org/abs/2503.09573), [Fast-dLLM v2 2509.26328](https://arxiv.org/abs/2509.26328) |
| Ultra-low-bit QAT | model VRAM footprint (fits one consumer card) | BitNet; Gemma QAT |
| Verifiable inference | trust at ~1% overhead (no ZK blowup) | [VeriLLM 2509.24257](https://arxiv.org/abs/2509.24257) |
| Decentralized fine-tuning | collaborative adaptation on commodity GPUs | [DECA 2606.03209](https://arxiv.org/abs/2606.03209) |

Honest caveat we carry throughout: speculative decoding still serializes one
*block* per pipeline traversal, and acceptance rates are task-dependent (higher on
code/math, lower on open chat). The gain is real but bounded — roughly 3–8× over a
Petals-style baseline, not orders of magnitude. We will measure it, not assume it.

### The throughput story: why Petals hit ~1 tok/s, and how OpenBay maximizes tokens/sec

The one number a leecher feels is **tokens/sec** — how fast the answer streams back —
and OpenBay runs at the **worker's full GPU speed**. Because each worker holds the
*whole* model, generating a token is just a local GPU pass: the internet is touched
once to send your prompt, then to stream the answer back. On a single consumer card
that's roughly:

- **~80–150 tokens/sec** for a 3B model
- **~40–80 tokens/sec** for a 7–8B model
- **~20–40 tokens/sec** for DiffusionGemma (a 26B model)

A 300-token answer lands in a few **seconds** — and every worker you add lets the
swarm serve more people at the same time.

That speed comes from *not* splitting the model. Petals had to split big models
across many machines, so every token made a full lap across the internet — which is
why it was stuck at ~1 tok/s (the same answer took minutes). OpenBay skips that lap
entirely by keeping each model on one machine.

| Approach | WAN round-trips / token | tokens/sec |
|---|---|---|
| **Petals (2022)** — always shards the model across peers | 1 (a full lap, every token) | ~1 |
| **OpenBay (target)** — whole-model when it fits, block-verified when sharded | 0, or amortized to a fraction | near-native (tens–hundreds); ~10–20 even for giants |

The one trade-off: this speed comes from serving models that fit on a single worker.
Quantization stretches that a long way (7B–30B easily, DiffusionGemma-26B in ~18 GB).
The truly giant models (400B+, 1T MoE) still have to be split across machines — and
making *those* fast is exactly what speculative decoding is for: a whole block of
tokens per lap instead of one, lifting the split case to ~10–20 tok/s.

### Our north star: more tokens/sec, for every model

The whole point of OpenBay is one number: **tokens per second** — how fast your
answer comes back. The goal is to make a pile of ordinary consumer GPUs feel as fast
as one expensive datacenter GPU, for any model, over a normal internet connection.

Four simple ideas get us there:

**1. Keep models on one machine whenever we can.** If a model fits on a single
worker, it runs at full speed — nothing crosses the network while it's answering. So
we shrink models (with QAT compression) to keep *bigger* ones fitting on a single
card. The more models that fit on one machine, the more run fast.

**2. When a model is too big to fit, send more tokens per network trip.** A giant
model has to be split across several machines, and the slow part is the trip between
them. Petals sent *one token per trip* — that's why it crawled at ~1 tok/s. Instead,
we let a worker guess a whole *block* of tokens that the others check in a single
trip (this is what "speculative decoding" does). That's the jump from ~1 to ~10–20
tok/s.

**3. Cut network delay everywhere.** Send each request to a fast, nearby worker.
Reuse work that's already done. And for friends on the same local network (a
cluster), skip the internet entirely.

**4. Be honest about speed.** We always report the real tokens/sec for each model
and task — never a best-case number dressed up as typical.

**The bottom line:** OpenBay is already faster than Petals just by *not* splitting
models that fit on one machine. The only hard part left is making the truly huge
models — the ones that *have* to be split — feel fast too.

## 3. Hypotheses we will prove (or falsify)

This project is judged by these, not by vision. Each is falsifiable with a number.

- **H1 — A whole-model swarm is usable.** A swarm of consumer-class workers, each
  hosting a complete (quantized) model, can serve requests at usable interactive
  latency over LAN, and acceptably over WAN.
  *Metric:* tokens/sec and time-to-first-token (TTFT) vs a single local node;
  target ≥ readable streaming (≈10+ tok/s) on LAN. *(MVP proves this.)*

- **H2 — Speculative/block decoding beats the Petals round-trip wall.** Generating
  and verifying a block per round-trip materially raises throughput over autoregressive
  P2P decoding on the same hardware and network.
  *Metric:* tok/s and tokens-accepted-per-round-trip vs an autoregressive baseline;
  target ≥ 3× on a simulated 40–80 ms WAN link.

- **H3 — A streak economy + spot-checks sustains an honest swarm.** Reciprocity
  (earn-by-seeding, spend-by-requesting) plus randomized output spot-checks resist
  free-riding and detect bad/cheap workers at low overhead.
  *Metric:* free-rider priority decay; spot-check detection rate of injected
  faulty workers; verification overhead target < 5% (path toward VeriLLM's ~1%).

- **H4 — QAT keeps quality while fitting consumer VRAM.** 4-bit (and lower) QAT
  models stay within a small quality delta of FP16 while fitting a single
  consumer card.
  *Metric:* KL-divergence / benchmark delta vs FP16 reference; target within a few %.

## 4. Scope and staging (decouple the hard things)

The cardinal design decision: **do not attempt sharding and ultra-low-bit QAT and
trustless consensus all at once.** Each is independently hard. We stage them so
every version ships and is useful on its own.

- **v1 — Whole-model swarm (this MVP).** Each worker hosts a *complete* model it
  can fit; the coordinator matches requests and runs a streak ledger; clients stream
  tokens. No sharding, no custom quantization, no blockchain. Proves **H1** (and
  sets up H3). This is essentially a productized, accelerated
  [AI Horde](https://aihorde.net/) with a clean client.
- **v2 — Big-model sharding.** Split models too large for one card across peers,
  using block/speculative transport to keep tokens-per-round-trip high. Targets
  **H2**. This is where the best available drafter (the DFlash → DFlare → DSpark line — DSpark is production-proven at DeepSeek scale, open-sourced as DeepSpec) and WAN engineering live, and
  where the drafter/target coupling problem must be solved.
- **v3 — Permissionless trust + economy.** VeriLLM-style verifiable inference,
  reputation, and real settlement. Targets the trustless end of **H3**.

### Cluster mode: private pods (a parallel track)

A **cluster** in OpenBay terms = a **private pod**: one coordinator + a join code +
a private namespace, so only invited machines can register. The "start a 2nd worker
on your LAN" step from the demo is already a baby version of this — add a code and an
access check and you've got cluster mode. The coordinator is lightweight (just
matchmaking), so one friend can host it, or you run a tiny shared one.

**Two flavors (and which is the killer):**

- **Load-balance whole models across friends** — each friend runs models they can
  fit; the cluster spreads requests and pools model variety. Trivial — basically
  works today.
- **Pool GPUs to run one model none of you can alone** — 4 friends × 12 GB = 48 GB →
  run a 70B together (Exo-style sharding). This is the killer feature, and a trusted
  LAN cluster is the best possible place for it: no verification overhead, and on a
  local network the per-token latency that crushed Petals largely disappears. "Us
  four, pooling our laptops to run a model none of us could" is a fantastic demo.

**Honest caveats:**

- **Who hosts the coordinator** — one friend's machine, or a small shared one. Fine
  either way (it's lightweight), but someone has to be the host.
- **NAT traversal** — friends on different home networks still need hole-punching
  (STUN/TURN) to connect directly; same challenge as the open swarm, smaller scale.
- **WAN-distributed friends** — if your cluster is friends across cities (not the
  same LAN), the GPU-pooling flavor still pays the round-trip latency, so it leans
  on speculative decoding to stay fast. Same-room/LAN clusters are where it screams.

## 5. Architecture (v1)

```
[ Leecher/Client ] --prompt--> [ Coordinator ] --match--> [ Worker: whole model ]
        ^                        streak ledger                     | (Ollama/llama.cpp/MLX)
        +<------------------- streamed tokens --------------------+
```

- **Coordinator** — registry of workers and the models each serves; matchmaking;
  streak accounting; (next) randomized spot-check verification.
- **Worker** — registers, hosts a whole model via a local engine (Ollama in v1;
  llama.cpp/MLX/vLLM are drop-in), streams tokens.
- **Client** — submits prompts, renders the stream.

Crucially, **each worker keeps its KV cache local; only prompts and token streams
cross the network.** This sidesteps the datacenter KV-cache-shuffling problems that
afflict disaggregated serving — they don't apply to a whole-model swarm.

## 6. Evaluation plan

We borrow three measurement axes (adapted from distributed-inference literature):

1. **Inference velocity & network efficacy** — TTFT, tokens/sec, tokens-accepted-
   per-round-trip, dropped-shard recovery time (v2), under LAN and simulated WAN
   (e.g. 40/80 ms RTT via `tc netem`).
2. **Generation quality & alignment** — KL-divergence and task benchmarks
   (e.g. GSM8K, HumanEval) of quantized swarm output vs an FP16 reference, to prove
   decentralization/quantization don't degrade results.
3. **Resource efficiency & resilience** — VRAM per worker, MB transferred per
   generated token, free-rider resistance, and spot-check detection rate against
   deliberately faulty workers.

Baselines: a single local node (upper bound on quality/latency) and an
autoregressive P2P relay (the Petals-style lower bound we must beat on WAN).

## 7. Why open-source / public good

The value proposition *is* openness: access that cannot be revoked, metered, or
surveilled, and that runs in regions and budgets the commercial market ignores.
The network only works if anyone can join, audit, and self-host — which a
permissive (Apache-2.0) open-source release guarantees. This also makes the project
fundable as a digital public good (e.g. NLnet/NGI, Mozilla, Emergent Ventures,
research-compute grants) rather than as a closed product.

## 8. Risks & honest limitations

- **Privacy.** A prompt runs on a stranger's GPU in plaintext. v1 targets
  non-sensitive use and **cluster mode** (trusted private pods — see §4), with
  stronger guarantees (confidential compute) coming later. We will not overstate this.
- **Leverage = queues, not magic.** One GPU serves a few concurrent users, not
  thousands. "Free" means cost-shifted to idle hardware and rationed by a streak
  queue — by design, not by accident.
- **Agentic/long-context workloads** stress KV-cache locality and churn; v1 is best
  suited to one-shot and short-context generation.
- **Acceptance-rate variance.** Speculative speedups are strongest on code/math and
  weakest on open-ended chat — the regime that needs them most. We report per-task.
- **The synthesis is unproven.** No prior work combines this full stack end-to-end;
  our headline numbers are targets to be measured, not results to be assumed.

## 9. Milestones (mapped to funding)

See **[ROADMAP.md](ROADMAP.md)** for the engineering breakdown and good-first-issues.
In brief: ship the v1 demo and a public repo → apply to low-friction compute and
individual grants with a working artifact → measure H1/H3 → pursue v2 with a
structured research grant.

## References

Petals (2312.08361) · BD3-LM (2503.09573) · Fast-dLLM v2 (2509.26328) ·
DFlash (2602.06036) · DFlare (2606.02091) · DSpark/DeepSpec (DeepSeek-AI, 2026) · VeriLLM (2509.24257) ·
DECA (2606.03209) · AI Horde (aihorde.net) · Exo (github.com/exo-explore/exo).
