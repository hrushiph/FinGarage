"""
1-Command End-to-End Replay of the CostBridge (#cost-bridge) Switch Room Workflow.

Executes all 4 demo beats across the isolated `./finops-hq` and `./checkout-service`
directories over real black-box HTTP probes, demonstrating:
  Beat 1: Baseline Invoice Audit & HTTP Header Breach ($0.048292/req | $14,487.60/mo)
  Beat 2: Attempt 1 (Naive Fix) -> Refused by Quality Gate (60% < 95% SLA) + Guardrail Block
  Beat 3: Attempt 2 (Smart Fix) -> Verified (-92.5% cost, 100% accuracy, 25.3x faster)
  Beat 4: Cryptographic Receipt Minted + Live HTTP Header Stamp + PNG/SVG Receipt Cards
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FINOPS_DIR = ROOT_DIR / "finops-hq"
CHECKOUT_DIR = ROOT_DIR / "checkout-service"

sys.path.insert(0, str(FINOPS_DIR))
from probe import (  # noqa: E402
    ensure_live_service,
    http_probe_endpoint,
    mint_receipt,
    run_audit,
    run_verify,
)


def _set_checkout_mode(mode: str) -> None:
    subprocess.run(
        [sys.executable, str(CHECKOUT_DIR / "service_config.py"), mode],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def _print_http_headers(title: str, headers: dict[str, str]) -> None:
    print(f"\n  ┌── {title} (GET /orders/summary) ──")
    keys = [
        "X-Unit-Cost-USD",
        "X-Cost-Breakdown",
        "X-SQL-Queries",
        "X-LLM-Tokens",
        "X-LLM-Cache-Hit",
        "X-Log-Bytes",
        "X-Latency-Ms",
        "X-Golden-Accuracy-Pct",
        "X-FinOps-Receipt",
    ]
    for k in keys:
        if k in headers:
            print(f"  │ {k}: {headers[k]}")
    print("  └" + "─" * 68)


def main() -> None:
    url = "http://127.0.0.1:8094"
    print("=" * 78)
    print("  COSTBRIDGE // #cost-bridge SWITCH ROOM END-TO-END REPLAY")
    print("  Folder A: ./finops-hq (finops-agent)  <-->  Folder B: ./checkout-service (dev-agent)")
    print("=" * 78)

    with ensure_live_service(url):
        # ------------------------------------------------------------------
        # BEAT 1: Baseline Invoice Audit & Breach Detection
        # ------------------------------------------------------------------
        print("\n[BEAT 1/4] finops-agent (./finops-hq) audits invoice_nov_2026.csv & probes baseline...")
        _set_checkout_mode("baseline")
        audit = run_audit(url)
        _print_http_headers("LIVE HTTP HEADERS — BASELINE BREACH", audit["http_headers"])
        print("\n" + audit["room_alert_markdown"])

        # ------------------------------------------------------------------
        # BEAT 2: Attempt 1 (Naive Fix) -> Refused Live + Guardrail Test
        # ------------------------------------------------------------------
        print("\n" + "-" * 78)
        print("[BEAT 2/4] dev-agent (./checkout-service) applies Attempt 1 ('naive' prompt truncation)...")
        _set_checkout_mode("naive")
        refusal = run_verify(url)
        _print_http_headers("LIVE HTTP HEADERS — ATTEMPT 1 (NAIVE SHORTCUT)", refusal["http_headers"])
        print("\n" + refusal["room_message_markdown"])

        print("\n  [GUARDRAIL CHECK] What if an agent tries to mint a receipt without a passing probe?")
        try:
            mint_receipt(url)
        except PermissionError as exc:
            print(f"  🛡️  {exc}")

        # ------------------------------------------------------------------
        # BEAT 3: Attempt 2 (Smart Architectural Fix) -> Verified Pass
        # ------------------------------------------------------------------
        print("\n" + "-" * 78)
        print("[BEAT 3/4] dev-agent (./checkout-service) applies Attempt 2 ('optimized' JOIN + cached digest)...")
        _set_checkout_mode("optimized")
        verified = run_verify(url)
        print("\n" + verified["room_message_markdown"])

        # ------------------------------------------------------------------
        # BEAT 4: Mint Cryptographic FinOps Receipt & Stamp Live HTTP Header
        # ------------------------------------------------------------------
        print("\n" + "-" * 78)
        print("[BEAT 4/4] finops-agent (cost-seal-holder) mints FinOps Receipt & stamps HTTP header...")
        receipt = mint_receipt(url)
        sealed_headers, _ = http_probe_endpoint(url, "/orders/summary")
        _print_http_headers("LIVE HTTP HEADERS — VERIFIED & SEALED", sealed_headers)

        print(f"\n🏆 Minted Receipt ID:       {receipt['receipt_id']}")
        print(f"   Unit Cost Reduction:     ${receipt['baseline']['unit_cost_usd']:.6f} -> ${receipt['verified']['unit_cost_usd']:.6f} (-{receipt['savings']['reduction_pct']}%)")
        print(f"   Monthly Run-Rate Saved:  ${receipt['savings']['monthly_savings_usd']:,.2f}/mo")
        print(f"   Annual Run-Rate Saved:   ${receipt['savings']['annual_savings_usd']:,.2f}/yr")
        print(f"   Latency Improvement:     {receipt['baseline']['latency_ms']:.0f}ms -> {receipt['verified']['latency_ms']:.0f}ms ({receipt['savings']['latency_speedup_x']}x faster)")
        print(f"   PNG Card (Switch Room):  {receipt['artifacts']['png']}")
        print(f"   SVG Card (Web/Docs):     {receipt['artifacts']['svg']}")
        print(f"   Room Document Ledger:    {receipt['artifacts']['ledger_md']}")
        print("=" * 78)


if __name__ == "__main__":
    main()

