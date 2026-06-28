"""OpenBay client CLI:

    python -m openbay.client "Explain black holes simply" --model llama3.2

Sends a prompt to the coordinator and prints tokens as the swarm streams them.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid

import httpx


def run(prompt: str, model: str, coordinator: str, client_id: str) -> int:
    payload = {"model": model, "prompt": prompt, "client_id": client_id}
    seeder = None
    with httpx.Client(timeout=None) as cx:
        with cx.stream("POST", f"{coordinator}/v1/infer", json=payload) as r:
            if r.status_code != 200:
                body = r.read().decode(errors="replace")
                print(f"error {r.status_code}: {body}", file=sys.stderr)
                return 1
            seeder = r.headers.get("X-Seeder")
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sys.stdout.write(obj.get("token", ""))
                sys.stdout.flush()
                if obj.get("done"):
                    break
    print()
    if seeder:
        print(f"[served by seeder: {seeder}]", file=sys.stderr)
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="OpenBay client")
    p.add_argument("prompt")
    p.add_argument("--model", default="llama3.2")
    p.add_argument("--coordinator", default="http://localhost:8000")
    p.add_argument("--client-id", default=None)
    a = p.parse_args()
    cid = a.client_id or f"client-{uuid.uuid4().hex[:6]}"
    raise SystemExit(run(a.prompt, a.model, a.coordinator, cid))


if __name__ == "__main__":
    main()
