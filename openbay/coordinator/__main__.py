"""Run the coordinator:  python -m openbay.coordinator"""
from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    host = os.environ.get("OPENBAY_HOST", "0.0.0.0")
    port = int(os.environ.get("OPENBAY_PORT", "8000"))
    print(f"[coordinator] listening on http://{host}:{port}")
    uvicorn.run("openbay.coordinator.app:app", host=host, port=port)


if __name__ == "__main__":
    main()
