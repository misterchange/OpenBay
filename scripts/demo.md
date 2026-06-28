# Local demo — run the swarm in 5 minutes

This shows a leecher running a model served by a worker's GPU, through the
coordinator, with a live streak ledger.

## 0. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A model pulled:
  ```bash
  ollama pull llama3.2
  ```

## 1. Install OpenBay

```bash
cd openbay
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

## 2. Start the swarm (three terminals)

**Terminal 1 — coordinator:**
```bash
python -m openbay.coordinator
# -> listening on http://0.0.0.0:8000
```

**Terminal 2 — a worker (hosts the whole model):**
```bash
python -m openbay.worker --model llama3.2
# -> registered with coordinator; serving on http://localhost:9000
```

**Terminal 3 — a leecher (asks a question):**
```bash
python -m openbay.client "Explain black holes to a 10-year-old" --model llama3.2
```
Tokens stream back from the worker via the coordinator.

## 3. See the economy

```bash
curl http://localhost:8000/nodes     # who is in the swarm
curl http://localhost:8000/ledger    # streak: worker earned, client spent
```

## 4. Make it a real swarm

Start a second worker on another port — or another machine on your LAN:

```bash
# same machine, second instance
python -m openbay.worker --model llama3.2 --port 9001

# another LAN machine (tell the coordinator how to reach it)
python -m openbay.worker --model llama3.2 --port 9001 \
    --coordinator http://<coordinator-ip>:8000 \
    --advertise http://<this-machine-ip>:9001
```

Re-run the client a few times: requests now load-balance across workers, and both
earn streak. That's the core idea — demonstrated end to end.

> This is the **v1 whole-model** path: each worker hosts a complete model, only
> prompts and tokens cross the network (never a KV cache). Sharding huge models
> across peers is v2 — see [../docs/ROADMAP.md](../docs/ROADMAP.md).
