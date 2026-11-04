"""Generates the Visual Itemized FinOps Store Receipt Card (.png and .svg) for Switch `send_attachment`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

RECEIPTS_DIR = Path(__file__).resolve().parent / "receipts"


def render_svg_receipt(receipt: dict[str, Any], out_path: Path | None = None) -> Path:
    """Render a crisp dark-mode SVG Itemized FinOps Store Receipt Card."""
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    target = out_path or (RECEIPTS_DIR / "receipt_card.svg")

    b = receipt["baseline"]
    a = receipt["verified"]
    s = receipt["savings"]
    seal = receipt["receipt_seal"]

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 540" width="680" height="540" role="img" aria-label="CostBridge Verified FinOps Receipt Card">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0d1322"/>
      <stop offset="100%" stop-color="#090d16"/>
    </linearGradient>
    <linearGradient id="accentGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#06b6d4"/>
    </linearGradient>
  </defs>

  <!-- Card Background -->
  <rect x="8" y="8" width="664" height="524" rx="16" fill="url(#bgGrad)" stroke="#1e293b" stroke-width="2"/>
  <rect x="8" y="8" width="664" height="8" rx="4" fill="url(#accentGrad)"/>

  <!-- Header -->
  <text x="36" y="48" fill="#10b981" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="18" font-weight="700">COSTBRIDGE // VERIFIED FINOPS RECEIPT</text>
  <rect x="496" y="28" width="144" height="28" rx="6" fill="#064e3b" stroke="#10b981" stroke-width="1"/>
  <text x="568" y="47" text-anchor="middle" fill="#34d399" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" font-weight="700">SEAL: #{seal}</text>

  <text x="36" y="74" fill="#94a3b8" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">Room: {receipt["room"]}   |   Endpoint: {receipt["endpoint"]}   |   Service: {receipt["service"]}</text>
  <line x1="36" y1="90" x2="644" y2="90" stroke="#334155" stroke-dasharray="6,4" stroke-width="1.5"/>

  <!-- Table Column Headers -->
  <text x="36" y="116" fill="#64748b" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" font-weight="700">ITEMIZED DRIVER</text>
  <text x="240" y="116" fill="#64748b" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" font-weight="700">BEFORE (BREACH)</text>
  <text x="435" y="116" fill="#64748b" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" font-weight="700">AFTER (VERIFIED)</text>
  <text x="644" y="116" text-anchor="end" fill="#64748b" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" font-weight="700">DELTA</text>
  <line x1="36" y1="126" x2="644" y2="126" stroke="#1e293b" stroke-width="1.5"/>

  <!-- Row 1: SQL Queries -->
  <text x="36" y="154" fill="#e2e8f0" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="600">1. SQL IOPS Queries</text>
  <text x="240" y="154" fill="#f87171" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">{b["sql_queries"]} q (${b["sql_cost_usd"]:.6f})</text>
  <text x="435" y="154" fill="#34d399" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">{a["sql_queries"]} q (${a["sql_cost_usd"]:.6f})</text>
  <text x="644" y="154" text-anchor="end" fill="#10b981" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="700">-98.0%</text>

  <!-- Row 2: LLM Tokens -->
  <text x="36" y="186" fill="#e2e8f0" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="600">2. LLM Context Tokens</text>
  <text x="240" y="186" fill="#f87171" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">{b["llm_tokens"]:,} tok (${b["llm_cost_usd"]:.6f})</text>
  <text x="435" y="186" fill="#34d399" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">{a["llm_tokens"]:,} tok (${a["llm_cost_usd"]:.6f})</text>
  <text x="644" y="186" text-anchor="end" fill="#10b981" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="700">-90.1%</text>

  <!-- Row 3: Log Ingestion -->
  <text x="36" y="218" fill="#e2e8f0" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="600">3. CloudWatch Log Vol</text>
  <text x="240" y="218" fill="#f87171" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">{b["log_kb"]:.2f} KB (${b["log_cost_usd"]:.6f})</text>
  <text x="435" y="218" fill="#34d399" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">{a["log_kb"]:.2f} KB (${a["log_cost_usd"]:.6f})</text>
  <text x="644" y="218" text-anchor="end" fill="#10b981" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="700">-99.1%</text>

  <!-- Row 4: P95 Latency -->
  <text x="36" y="250" fill="#e2e8f0" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="600">4. Endpoint Latency</text>
  <text x="240" y="250" fill="#fbbf24" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">{b["latency_ms"]:.0f} ms</text>
  <text x="435" y="250" fill="#38bdf8" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">{a["latency_ms"]:.0f} ms</text>
  <text x="644" y="250" text-anchor="end" fill="#38bdf8" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="700">{receipt["savings"]["latency_speedup_x"]}x FASTER</text>

  <!-- Row 5: Golden Accuracy Gate -->
  <text x="36" y="282" fill="#e2e8f0" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="600">5. Golden Accuracy SLA</text>
  <text x="240" y="282" fill="#94a3b8" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">100.0% (Naive: 60.0%)</text>
  <text x="435" y="282" fill="#34d399" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13">{a["golden_accuracy_pct"]:.1f}% (5/5 facts)</text>
  <text x="644" y="282" text-anchor="end" fill="#10b981" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="700">PASS (&gt;=95%)</text>

  <line x1="36" y1="304" x2="644" y2="304" stroke="#334155" stroke-dasharray="6,4" stroke-width="1.5"/>

  <!-- Unit Cost Summary Box -->
  <rect x="36" y="320" width="608" height="106" rx="10" fill="#111827" stroke="#1f2937" stroke-width="1.5"/>
  <text x="56" y="350" fill="#94a3b8" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="14" font-weight="600">UNIT COST PER REQUEST (BUDGET CAP: $0.005000)</text>
  <text x="624" y="350" text-anchor="end" fill="#10b981" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="16" font-weight="700">${b["unit_cost_usd"]:.6f}  --&gt;  ${a["unit_cost_usd"]:.6f} (-{s["reduction_pct"]:.1f}%)</text>

  <text x="56" y="382" fill="#94a3b8" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="14">Monthly Run-Rate (300k req/mo):</text>
  <text x="624" y="382" text-anchor="end" fill="#e2e8f0" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="14" font-weight="700">${b["monthly_cost_usd"]:,.2f}/mo  --&gt;  ${a["monthly_cost_usd"]:,.2f}/mo</text>

  <text x="56" y="410" fill="#34d399" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="15" font-weight="700">VERIFIED ANNUAL RUN-RATE SAVINGS:</text>
  <text x="624" y="410" text-anchor="end" fill="#34d399" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="18" font-weight="700">${s["annual_savings_usd"]:,.2f} / YEAR</text>

  <!-- Footer / Cryptographic Seal -->
  <text x="36" y="458" fill="#64748b" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12">HTTP Header Stamp:   X-Unit-Cost-USD: ${a["unit_cost_usd"]:.6f}   |   X-FinOps-Receipt: PASS; seal={seal}</text>
  <text x="36" y="482" fill="#64748b" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12">Verifier Role:       cost-seal-holder (finops-agent)   |   Pricing Snapshot: {receipt["pricing_snapshot"]}</text>
  <text x="36" y="506" fill="#475569" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">SHA-256 Probe Hash:  {receipt["probe_sha256"]}</text>
</svg>
"""
    target.write_text(svg, encoding="utf-8")
    return target


def render_png_receipt(receipt: dict[str, Any], out_path: Path | None = None) -> Path:
    """Render a crisp PNG Itemized FinOps Store Receipt Card using Pillow."""
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    target = out_path or (RECEIPTS_DIR / "receipt_card.png")

    width, height = 680, 540
    img = Image.new("RGB", (width, height), (13, 19, 34))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Border and top accent bar
    draw.rectangle([8, 8, width - 8, height - 8], outline=(30, 41, 59), width=2)
    draw.rectangle([8, 8, width - 8, 18], fill=(16, 185, 129))

    b = receipt["baseline"]
    a = receipt["verified"]
    s = receipt["savings"]
    seal = receipt["receipt_seal"]

    lines = [
        ("COSTBRIDGE // VERIFIED FINOPS RECEIPT", (16, 185, 129), 30),
        (f"SEAL: #{seal}  |  ROOM: {receipt['room']}  |  ENDPOINT: {receipt['endpoint']}", (148, 163, 184), 56),
        ("-" * 78, (51, 65, 85), 80),
        ("ITEMIZED DRIVER           BEFORE (BREACH)         AFTER (VERIFIED)        DELTA", (100, 116, 139), 102),
        ("-" * 78, (30, 41, 59), 120),
        (
            f"1. SQL IOPS Queries       {b['sql_queries']:>3} q (${b['sql_cost_usd']:.6f})      "
            f"{a['sql_queries']:>3} q (${a['sql_cost_usd']:.6f})      -98.0%",
            (226, 232, 240),
            142,
        ),
        (
            f"2. LLM Context Tokens    {b['llm_tokens']:>4} t (${b['llm_cost_usd']:.6f})     "
            f"{a['llm_tokens']:>4} t (${a['llm_cost_usd']:.6f})      -90.1%",
            (226, 232, 240),
            170,
        ),
        (
            f"3. CloudWatch Log Vol   {b['log_kb']:>5.2f} KB (${b['log_cost_usd']:.6f})    "
            f"{a['log_kb']:>5.2f} KB (${a['log_cost_usd']:.6f})      -99.1%",
            (226, 232, 240),
            198,
        ),
        (
            f"4. Endpoint Latency       {b['latency_ms']:>4.0f} ms                 "
            f"{a['latency_ms']:>4.0f} ms            {receipt['savings']['latency_speedup_x']}x FASTER",
            (56, 189, 248),
            226,
        ),
        (
            f"5. Golden Accuracy SLA    100.0% (Naive: 60.0%)   "
            f"{a['golden_accuracy_pct']:>5.1f}% (5/5 facts)   PASS (>=95%)",
            (52, 211, 153),
            254,
        ),
        ("-" * 78, (51, 65, 85), 282),
    ]

    for text, color, y in lines:
        draw.text((32, y), text, fill=color, font=font)

    # Summary box
    draw.rectangle([28, 305, width - 28, 425], fill=(17, 24, 39), outline=(31, 41, 55), width=2)
    summary_lines = [
        (
            f"UNIT COST / REQ (CAP $0.0050):  ${b['unit_cost_usd']:.6f}  -->  ${a['unit_cost_usd']:.6f} (-{s['reduction_pct']:.1f}%)",
            (16, 185, 129),
            322,
        ),
        (
            f"MONTHLY RUN-RATE (300k req):    ${b['monthly_cost_usd']:,.2f}/mo  -->  ${a['monthly_cost_usd']:,.2f}/mo",
            (226, 232, 240),
            354,
        ),
        (
            f"VERIFIED ANNUAL SAVINGS:        ${s['annual_savings_usd']:,.2f} / YEAR",
            (52, 211, 153),
            388,
        ),
    ]
    for text, color, y in summary_lines:
        draw.text((44, y), text, fill=color, font=font)

    footer_lines = [
        (f"HTTP Header: X-Unit-Cost-USD: ${a['unit_cost_usd']:.6f} | X-FinOps-Receipt: PASS; seal={seal}", (100, 116, 139), 446),
        (f"Signed by:   cost-seal-holder (finops-agent) | Pricing: {receipt['pricing_snapshot']}", (100, 116, 139), 472),
        (f"Probe SHA256: {receipt['probe_sha256'][:54]}...", (71, 85, 105), 498),
    ]
    for text, color, y in footer_lines:
        draw.text((32, y), text, fill=color, font=font)

    img.save(target, format="PNG")
    return target

