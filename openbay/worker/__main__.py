"""Run a worker:

    python -m openbay.worker --model llama3.2 --coordinator http://localhost:8000

Registers with the coordinator on startup, then serves its model.
"""
from __future__ import annotations

import argparse
import socket

import httpx
import uvicorn

from .worker import build_app


def _register(coordinator: str, node_id: str, url: str, model: str) -> None:
    try:
        httpx.post(
            f"{coordinator}/register",
            json={"node_id": node_id, "url": url, "models": [model]},
            timeout=10,
        )
        print(f"[worker] registered '{node_id}' with {coordinator}")
    except Exception as exc:  # noqa: BLE001 - best-effort, keep serving regardless
        print(f"[worker] registration failed ({exc}); will keep serving locally")


def main() -> None:
    p = argparse.ArgumentParser(description="OpenBay worker")
    p.add_argument("--model", required=True, help="model name to serve (e.g. llama3.2)")
    p.add_argument("--coordinator", default="http://localhost:8000")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=9000)
    p.add_argument("--advertise", default=None,
                   help="URL other nodes use to reach this worker "
                        "(default http://localhost:<port>)")
    args = p.parse_args()

    node_id = f"{socket.gethostname()}-{args.port}"
    advertise = args.advertise or f"http://localhost:{args.port}"
    app = build_app(args.model)

    @app.on_event("startup")
    def _on_startup() -> None:
        _register(args.coordinator, node_id, advertise, args.model)

    print(f"[worker] serving '{args.model}' at {advertise} (engine: Ollama)")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
