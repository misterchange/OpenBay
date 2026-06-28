"""Run the coordinator:  python -m openbay.coordinator"""
from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    host = os.environ.get("OPENBAY_HOST", "0.0.0.0")
    port = int(os.environ.get("OPENBAY_PORT", "8000"))
    shown = "localhost" if host in ("0.0.0.0", "") else host
    print(f"[coordinator] up — open http://{shown}:{port} in a browser, or use the client CLI")
    uvicorn.run("openbay.coordinator.app:app", host=host, port=port)


if __name__ == "__main__":
    main()
