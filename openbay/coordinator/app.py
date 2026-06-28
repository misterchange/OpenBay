"""OpenBay coordinator (the "tracker").

Responsibilities in v1:
  - keep a registry of workers and which whole models each can serve
  - match an incoming client request to a capable worker
  - relay the token stream back to the client
  - update the streak ledger (worker earns, client spends)

NOT yet implemented (see docs/ROADMAP.md): spot-check verification,
NAT traversal, persistence, latency-aware routing, sharding (v2).
"""
from __future__ import annotations

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from ..common.models import InferRequest, RegisterRequest
from .ledger import Registry

app = FastAPI(title="OpenBay Coordinator", version="0.1.0")
registry = Registry()


@app.get("/")
def root() -> dict:
    return {
        "service": "openbay-coordinator",
        "status": "ok",
        "workers": len(registry.nodes()),
    }


@app.post("/register")
def register(req: RegisterRequest) -> dict:
    registry.register(req.node_id, req.url, req.models, req.gpu)
    return {"ok": True}


@app.post("/heartbeat")
def heartbeat(node_id: str) -> dict:
    registry.heartbeat(node_id)
    return {"ok": True}


@app.get("/nodes")
def nodes() -> list[dict]:
    return registry.nodes()


@app.get("/ledger")
def ledger() -> dict:
    return registry.balances()


@app.post("/v1/infer")
async def infer(req: InferRequest) -> StreamingResponse:
    worker = registry.pick(req.model)
    if worker is None:
        raise HTTPException(
            status_code=503,
            detail=f"no worker currently serving model '{req.model}'",
        )

    async def stream():
        tokens = 0
        payload = {
            "model": req.model,
            "prompt": req.prompt,
            "max_tokens": req.max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=None) as cx:
                async with cx.stream(
                    "POST", f"{worker.url}/generate", json=payload
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            tokens += 1
                            yield line + "\n"
        finally:
            # Settle streak even if the client disconnects mid-stream.
            registry.settle(req.client_id, worker.node_id, tokens)

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={"X-Worker": worker.node_id},
    )
