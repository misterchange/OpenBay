# OpenBay

**Open, shared AI for everyone's hardware.**

*Run frontier-scale models on pooled consumer GPUs. BitTorrent-style peer-to-peer inference.*

Large models are gated behind expensive GPUs, cloud accounts, credit cards, and
region locks. OpenBay lets anyone run a model their own hardware can't, by
pooling idle consumer GPUs into a verifiable swarm. A **leecher** sends a prompt;
**seeders** with spare GPU time serve it and earn **streak**; the more you seed,
the higher your priority. It's open-source infrastructure for AI access that no
single company can revoke, meter, or surveil.

> **Status: v0.1 — working MVP skeleton.** This repo runs an end-to-end
> *whole-model swarm* on your machine/LAN today: a coordinator, one or more
> seeders (each serving a complete model via [Ollama](https://ollama.com)), and a
> streaming client with a streak ledger. Sharding huge models across peers (v2) and
> trustless verification (v3) are on the [roadmap](docs/ROADMAP.md).

See **[docs/PLAN.md](docs/PLAN.md)** for the full plan of action and the
falsifiable hypotheses this project sets out to prove.

---

## Why this can work now (when Petals couldn't)

[Petals](https://arxiv.org/abs/2312.08361) proved you *can* pool consumer GPUs,
but autoregressive decoding forced **one network round-trip per token** — over home
internet that caps you at ~1–2 tokens/sec. The 2026 advances that change the math:

- **Speculative decoding** (incl. block-diffusion drafters like
  [DFlash](https://arxiv.org/abs/2602.06036) /
  [DFlare](https://arxiv.org/abs/2606.02091)) — verify a *block* of tokens per
  round-trip, lifting tokens-per-round-trip from ~1 to 4–8.
- **Quantization-Aware Training** (BitNet, Gemma QAT) — near-lossless 4-bit (and
  lower) models that fit a single consumer card.
- **Open diffusion/MoE models** (DiffusionGemma, Apache-2.0) — more tokens per
  forward pass, runnable locally.

The bottleneck was never "pooling GPUs." It was *tokens-per-round-trip*. That's
the variable these techniques move.

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

# 2) A seeder serving a whole model
python -m openbay.seeder --model llama3.2

# 3) A leecher asking a question
python -m openbay.client "Explain black holes to a 10-year-old" --model llama3.2
```

Tokens stream back from the seeder, through the coordinator, to you. Check the
economy at any time:

```bash
curl http://localhost:8000/ledger   # streak: seeders earn, clients spend
curl http://localhost:8000/nodes    # who's in the swarm
```

Start a **second** seeder on another port (or another machine on your LAN, using
`--advertise http://<lan-ip>:9001`) and requests load-balance across the swarm —
the core idea, demonstrated.

## How v1 works

```
[ Leecher ] --prompt--> [ Coordinator ] --picks a seeder--> [ Seeder (whole model, Ollama) ]
     ^                       (streak ledger)                          |
     +<----------------- streamed tokens ----------------------------+
```

- **Coordinator** (`openbay/coordinator/`) — registry + matchmaking + streak.
- **Seeder** (`openbay/seeder/`) — registers, serves a whole model, streams tokens.
- **Client** (`openbay/client/`) — sends a prompt, prints the stream.

Each seeder hosts a **whole** model (no per-token network hops, no pipeline
stalls). What crosses the network is a prompt and a token stream — never a KV
cache. This is the design that works today; sharding huge models is v2.

## Roadmap (short)

- **v1 — whole-model swarm** *(this MVP)*: matchmaking, streak, streaming. Next:
  spot-check verification, persistence, NAT traversal, a desktop seeder.
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
