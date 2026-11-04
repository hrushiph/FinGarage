"""Automated unit & FinOps contract tests for checkout-service."""

from __future__ import annotations

import sys
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from app import execute_orders_summary  # noqa: E402
from service_config import set_active_profile  # noqa: E402


def test_baseline_exhibits_three_cost_traps() -> None:
    set_active_profile("baseline")
    body, headers = execute_orders_summary()

    assert body["telemetry"]["sql_queries"] == 101
    assert body["telemetry"]["llm_tokens"] >= 3820
    assert body["telemetry"]["log_bytes"] > 40000
    assert body["telemetry"]["unit_cost_usd"] > 0.045
    assert body["quality_gate"]["accuracy_pct"] == 100.0
    assert headers["X-FinOps-Receipt"] == "UNVERIFIED-BUDGET-BREACH"


def test_naive_fix_fails_golden_quality_gate() -> None:
    set_active_profile("naive")
    body, headers = execute_orders_summary()

    # Cuts SQL queries and cost, but breaks accuracy (60% < 95% SLA)
    assert body["telemetry"]["sql_queries"] == 2
    assert body["telemetry"]["unit_cost_usd"] < 0.0050
    assert body["quality_gate"]["accuracy_pct"] == 60.0
    assert "refund_anomaly_detected" in body["quality_gate"]["missing_facts"]
    assert headers["X-FinOps-Receipt"] == "UNVERIFIED-QUALITY-BREACH"


def test_optimized_profile_passes_cost_and_quality_gates() -> None:
    set_active_profile("optimized", receipt_seal="cb9f2a81")
    body, headers = execute_orders_summary()

    assert body["telemetry"]["sql_queries"] == 2
    assert body["telemetry"]["llm_tokens"] == 340
    assert body["telemetry"]["llm_cache_hit"] is True
    assert body["telemetry"]["log_bytes"] < 500
    assert body["telemetry"]["unit_cost_usd"] == 0.003622
    assert body["quality_gate"]["accuracy_pct"] == 100.0
    assert headers["X-FinOps-Receipt"].startswith("VERIFIED-cb9f2a81")

