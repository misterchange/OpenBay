"""Worker node: serves a whole model and streams tokens.

v1 wraps a local Ollama server (https://ollama.com) as the inference engine,
because it's the easiest way for a volunteer to host a real model on consumer
hardware. Swapping in llama.cpp / MLX / vLLM is a drop-in change to
``stream_tokens`` and a later milestone.
"""
from __future__ import annotations

import json

import httpx
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from ..common.models import GenerateRequest

OLLAMA_URL = "http://localhost:11434/api/generate"


def build_app(default_model: str) -> FastAPI:
    app = FastAPI(title="OpenBay Worker", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True, "model": default_model}

    @app.post("/generate")
    async def generate(req: GenerateRequest) -> StreamingResponse:
        async def stream():
            payload = {
                "model": req.model or default_model,
                "prompt": req.prompt,
                "stream": True,
            }
            async with httpx.AsyncClient(timeout=None) as cx:
                async with cx.stream("POST", OLLAMA_URL, json=payload) as r:
                    async for line in r.aiter_lines():
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        # Normalise Ollama's format into our wire format so the
                        # client never has to know which engine produced it.
                        out = {"token": obj.get("response", ""),
                               "done": bool(obj.get("done", False))}
                        yield json.dumps(out) + "\n"

        return StreamingResponse(stream(), media_type="application/x-ndjson")

    return app
