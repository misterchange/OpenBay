"""Shared request/response schemas (pydantic v2)."""
from __future__ import annotations

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    node_id: str
    url: str               # URL other nodes use to reach this worker
    models: list[str]      # model names this worker can serve (whole-model, v1)
    gpu: str | None = None


class InferRequest(BaseModel):
    """Client -> coordinator."""
    model: str
    prompt: str
    client_id: str = "anon"
    max_tokens: int = 256


class GenerateRequest(BaseModel):
    """Coordinator -> worker."""
    model: str
    prompt: str
    max_tokens: int = 256
