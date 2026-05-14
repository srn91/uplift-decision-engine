from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

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


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    report = current_report()
    top_segment = report["top_recommended_segment"]
    customers = report["customers_analyzed"]
    uplift = report["uplift_at_top_quartile"]
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Uplift Decision Engine</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;max-width:860px;margin:48px auto;padding:0 24px;line-height:1.5;color:#111}}a{{color:#0645ad}}</style></head>
<body>
<h1>Uplift Decision Engine</h1>
<p>Treatment-effect targeting workflow with segment-level uplift estimates, net-value recommendations, and ranked targets.</p>
<ul><li>Customers analyzed: {customers}</li><li>Top segment: {top_segment}</li><li>Uplift at top quartile: {uplift}</li></ul>
<h2>Open endpoints</h2>
<ul>
<li><a href="/recommendation">Recommendation report</a></li>
<li><a href="/health">Health check</a></li>
<li><a href="/docs">API docs</a></li>
</ul>
</body></html>"""


@app.get("/recommendation")
def recommendation() -> dict[str, object]:
    return current_report()
