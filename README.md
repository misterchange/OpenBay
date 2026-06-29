# OpenBay

**Open, shared AI for everyone's hardware.**

*Run frontier-scale models on pooled consumer GPUs. BitTorrent-style peer-to-peer inference.*

Large models are gated behind expensive GPUs, cloud accounts, credit cards, and
region locks. OpenBay lets anyone run a model their own hardware can't, by
pooling idle consumer GPUs into a verifiable swarm. A **leecher** sends a prompt;
**workers** with spare GPU time serve it and earn **streak**; the more you contribute,
the higher your priority. It's open-source infrastructure for AI access that no
single company can revoke, meter, or surveil.

> **Status: v0.1 — working MVP skeleton.** This repo runs an end-to-end
> *whole-model swarm* on your machine/LAN today: a coordinator, one or more
> workers (each serving a complete model via [Ollama](https://ollama.com)), and a
> streaming client with a streak ledger. Sharding huge models across peers (v2) and
> trustless verification (v3) are on the [roadmap](docs/ROADMAP.md).

See **[docs/PLAN.md](docs/PLAN.md)** for the full plan of action and the
falsifiable hypotheses this project sets out to prove.

## Roles

OpenBay has three roles — you can be any or several of them:

- **Worker** — has a GPU (or a capable CPU). *Runs* the model and serves
  inference. The scarce, valuable job; earns the most **streak**.
- **Seeder** — no GPU needed, just disk + bandwidth. *Holds and distributes* the
  model weights (BitTorrent-style) so workers can fetch them. Earns modest
  **streak**. *(Planned — the weight-distribution layer; not in the v0.1 MVP yet.)*
- **Leecher** — the end user. Sends a prompt, gets tokens back, **downloads
  nothing**. Free to use; **streak** only sets queue priority, never gates access.

> Naming note: faithful to BitTorrent, a *seeder* holds the file (the weights);
> the GPU compute role is new, so we call it a *worker*. A *streak* (green ⚡) is
> your contribution energy — earn it by working or seeding, spend it by leeching.

---

## Why this works now

Pooling volunteers' GPUs to run big models isn't a new idea — a 2022 research
project called **[Petals](https://arxiv.org/abs/2312.08361)** first proved it's
possible. But it was too slow to use, and *why* is the whole point of OpenBay.

To run a model too big for one machine, Petals chopped it into pieces spread across
many computers. The problem: generating text is sequential — each word depends on the
one before — so producing *every single word* meant a full round-trip across the
internet, machine to machine. That capped it at about **1 word per second.**

OpenBay's core move is the opposite: **keep each model whole, on one machine.** No
per-word internet trip, so you get that machine's full speed (tens to hundreds of
words per second). And for models too big to keep whole, three 2026 advances finally
make the split-up case fast too:

- **Speculative decoding** ([DFlash](https://arxiv.org/abs/2602.06036) /
  [DFlare](https://arxiv.org/abs/2606.02091)) — a machine guesses a whole *block* of
  words that the others check in one internet trip, instead of one word per trip.
- **Quantization** (BitNet, Gemma QAT) — shrinks models so *bigger* ones still fit on
  one card, keeping them in the fast whole-model lane.
- **Open diffusion / MoE models** (DiffusionGemma) — generate many words per step and
  run on consumer hardware.

The bottleneck was never "pooling GPUs." It was **how many words you generate per
internet trip** — and that's exactly what these techniques move.

## Quickstart (local demo, ~5 min)

**Prerequisites:** Python 3.10+, and [Ollama](https://ollama.com) running with a
small model pulled:

```bash
ollama pull llama3.2        # ~2 GB; any Ollama model works
```

**Install:**

```bash
git clone https://github.com/<you>/openbay.git
cd openbay
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

**Run the swarm (3 terminals):**

```bash
# 1) Coordinator (the tracker)
python -m openbay.coordinator

# 2) A worker serving a whole model
python -m openbay.worker --model llama3.2

# 3) A leecher asking a question
python -m openbay.client "Explain black holes to a 10-year-old" --model llama3.2
```

Tokens stream back from the worker, through the coordinator, to you. Check the
economy at any time:

```bash
curl http://localhost:8000/ledger   # streak: workers earn, clients spend
curl http://localhost:8000/nodes    # who's in the swarm
```

Start a **second** worker on another port (or another machine on your LAN, using
`--advertise http://<lan-ip>:9001`) and requests load-balance across the swarm —
the core idea, demonstrated.

## How v1 works

```
[ Leecher ] --prompt--> [ Coordinator ] --picks a worker--> [ Worker (whole model, Ollama) ]
     ^                       (streak ledger)                          |
     +<----------------- streamed tokens ----------------------------+
```

- **Coordinator** (`openbay/coordinator/`) — registry + matchmaking + streak.
- **Worker** (`openbay/worker/`) — registers, serves a whole model, streams tokens.
- **Client** (`openbay/client/`) — sends a prompt, prints the stream.

Each worker hosts a **whole** model (no per-token network hops, no pipeline
stalls). What crosses the network is a prompt and a token stream — never a KV
cache. This is the design that works today; sharding huge models is v2.

## Performance — what to expect, and the goal

Because each **worker** runs a *whole* model, the speed a leecher sees is
essentially the worker's **native** tokens/sec — OpenBay adds almost nothing (only
the prompt and the text stream cross the wire). There's **no per-token network
round-trip**, which is exactly why Petals was stuck at ~1 tok/s and OpenBay isn't:

| Approach | Internet trips per token | tokens/sec |
|---|---|---|
| **Petals (2022)** — splits each model across machines | 1 (a full trip, every token) | ~1 |
| **OpenBay** — keeps each model whole when it fits | 0 (whole); a fraction when it must split | near-native (tens–hundreds); ~10–20 even for giants |

Rough native worker speeds on a single consumer GPU: **~80–150 tok/s** for a 3B,
**~40–80** for a 7–8B, **~20–40** for DiffusionGemma-26B. (Mac/CPU are slower; check
yours with `ollama ps`.)

**North-star goal:** push pooled consumer GPUs toward *datacenter-GPU* tokens/sec
for **any** model — keep models in the fast whole-model regime with QAT, and
amortize round-trips with speculative/block decoding (DFlash/DFlare) when a model is
too big to fit one worker. The full throughput argument is in
[docs/PLAN.md](docs/PLAN.md).

## Cluster mode (private pods) — *planned*

OpenBay also runs **private**: friends, a lab, or a team form a **cluster** with a
shared join code and pool their machines into a trusted pod. Because everyone's
invited, the hardest parts of the open swarm simply vanish — **no privacy worries,
no verification, no cold-start.** Two flavors:

- **Share the load** — each member runs whole models they can fit; the cluster
  spreads requests across them.
- **Pool the VRAM** — combine cards to run one model none of you could host alone
  (four 12 GB → 48 GB → a 70B), Exo-style. Best on a LAN, where pooling is fast.

It's the same codebase as the open swarm, plus a join code and a private namespace —
and likely the easiest, most viral way to get started. Full rationale in
[docs/PLAN.md](docs/PLAN.md).

## Roadmap (short)

- **v1 — whole-model swarm** *(this MVP)*: matchmaking, streak, streaming. Next:
  spot-check verification, persistence, NAT traversal, a desktop worker.
- **v2 — big-model sharding**: split models too big for one card across peers,
  with speculative/block transport to keep tokens-per-round-trip high.
- **v3 — permissionless trust + economy**: verifiable inference
  ([VeriLLM](https://arxiv.org/abs/2509.24257)-style), reputation, settlement.

Full detail and "good first issues" in **[docs/ROADMAP.md](docs/ROADMAP.md)**.

## Contributing

Early and open. Pick a "good first issue" in the roadmap, or open an issue to
discuss. Licensed under **Apache-2.0** — free to use, study, share, and build on.

## Tests

```bash
pip install -e ".[dev]"
pytest          # smoke tests; no Ollama or GPU required
```
