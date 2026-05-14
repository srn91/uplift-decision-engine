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
<style>
body{{margin:0;background:#f8fafc;color:#0f172a;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;line-height:1.5}}
main{{max-width:1080px;margin:0 auto;padding:56px 24px}}.hero{{background:linear-gradient(135deg,#111827,#15803d);color:white;border-radius:22px;padding:38px;box-shadow:0 24px 60px rgba(15,23,42,.18)}}
.eyebrow{{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#bbf7d0;font-weight:700}}h1{{font-size:42px;line-height:1.05;margin:10px 0 14px}}.hero p{{font-size:17px;color:#dcfce7;max-width:780px}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:22px 0}}.card{{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:18px;box-shadow:0 10px 30px rgba(15,23,42,.06)}}
.metric{{font-size:25px;font-weight:800;color:#0f172a}}.label{{font-size:13px;color:#64748b;margin-top:3px}}.links{{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px}}
a.button{{background:#0f172a;color:white;text-decoration:none;padding:11px 14px;border-radius:10px;font-weight:700}}a.secondary{{background:white;color:#0f172a;border:1px solid #cbd5e1}}
@media(max-width:800px){{.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}h1{{font-size:34px}}}}
</style></head>
<body><main>
<section class="hero"><div class="eyebrow">Applied decision system</div><h1>Uplift Decision Engine</h1>
<p>Treatment-effect targeting workflow with segment-level uplift estimates, net-value recommendations, and ranked customer targets.</p>
<div class="links"><a class="button" href="/recommendation">Recommendation report</a><a class="button secondary" href="/docs">API docs</a></div></section>
<section class="grid">
<div class="card"><div class="metric">{customers}</div><div class="label">customers analyzed</div></div>
<div class="card"><div class="metric">{top_segment}</div><div class="label">top segment</div></div>
<div class="card"><div class="metric">{uplift}</div><div class="label">uplift at top quartile</div></div>
<div class="card"><div class="metric">Qini</div><div class="label">evaluation curve</div></div>
</section>
<section class="card"><p>The hosted report shows why a segment is recommended, which customers are targeted, and how the policy compares against a random baseline.</p></section>
</main></body></html>"""


@app.get("/recommendation")
def recommendation() -> dict[str, object]:
    return current_report()
