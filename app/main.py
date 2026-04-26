from __future__ import annotations

from fastapi import FastAPI

from app.dataset import generate_rows
from app.uplift import estimate_uplift


app = FastAPI(
    title="Uplift Decision Engine",
    description="A local-first uplift workflow for intervention targeting decisions.",
    version="0.1.0",
)


def current_report() -> dict[str, object]:
    return estimate_uplift(generate_rows())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/recommendation")
def recommendation() -> dict[str, object]:
    return current_report()
