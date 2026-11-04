"""Tests for finops-hq black-box HTTP probe, quality-drop refusal, guardrail, and receipt minting."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

FINOPS_DIR = Path(__file__).resolve().parent
CHECKOUT_DIR = FINOPS_DIR.parent / "checkout-service"
sys.path.insert(0, str(FINOPS_DIR))

from probe import RECEIPTS_DIR, mint_receipt, run_audit, run_verify  # noqa: E402


def _set_checkout_mode(mode: str) -> None:
    """Switch checkout-service mode via CLI (preserving folder boundary)."""
    subprocess.run(
        [sys.executable, str(CHECKOUT_DIR / "service_config.py"), mode],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def test_audit_detects_baseline_budget_breach() -> None:
    _set_checkout_mode("baseline")
    audit = run_audit("http://127.0.0.1:8092")

    assert audit["invoice"]["invoice_monthly_cost_usd"] == 14487.60
    assert audit["measured"]["unit_cost_usd"] == 0.048292
    assert audit["measured"]["sql_queries"] == 101
    assert audit["http_headers"]["X-FinOps-Receipt"] == "UNVERIFIED-BUDGET-BREACH"


def test_verify_refuses_naive_fix_and_guardrail_blocks_minting() -> None:
    _set_checkout_mode("naive")
    res = run_verify("http://127.0.0.1:8092")

    assert res["verified"] is False
    assert res["verdict"] == "REFUSED_QUALITY_REGRESSION"
    assert all(res["cost_checks"].values()) is True
    assert res["measured"]["golden_accuracy_pct"] == 60.0
    assert "refund_anomaly_detected" in res["missing_facts"]
    assert "payment_retry_detected" in res["missing_facts"]

    # Guardrail: attempting to mint a receipt after a refused probe MUST raise PermissionError
    with pytest.raises(PermissionError, match="GUARDRAIL BLOCKED"):
        mint_receipt("http://127.0.0.1:8092")


def test_verify_and_mint_receipt_on_optimized_profile() -> None:
    _set_checkout_mode("optimized")
    res = run_verify("http://127.0.0.1:8092")

    assert res["verified"] is True
    assert res["verdict"] == "VERIFIED_PASS"
    assert res["measured"]["unit_cost_usd"] == 0.003622
    assert res["measured"]["golden_accuracy_pct"] == 100.0

    receipt = mint_receipt("http://127.0.0.1:8092")
    seal = receipt["receipt_seal"]

    assert receipt["live_http_headers"]["X-FinOps-Receipt"] == f"VERIFIED-{seal} (-92.5%)"
    assert receipt["savings"]["reduction_pct"] == 92.5
    assert receipt["savings"]["annual_savings_usd"] == 160812.00

    assert (RECEIPTS_DIR / "cost-receipt.json").exists()
    assert (RECEIPTS_DIR / "receipt_card.svg").exists()
    assert (RECEIPTS_DIR / "receipt_card.png").exists()
    assert (RECEIPTS_DIR / "room_ledger.md").exists()

    # Reset back to baseline after test suite
    _set_checkout_mode("baseline")


def test_guardrail_blocks_stale_probe_after_code_change() -> None:
    """Verify mint_receipt blocks if live code signature changed after latest_probe.json was written."""
    _set_checkout_mode("optimized")
    assert run_verify("http://127.0.0.1:8092")["verified"] is True

    # Simulate code regression back to baseline after verification passed
    _set_checkout_mode("baseline")
    with pytest.raises(PermissionError, match="Live service code signature"):
        mint_receipt("http://127.0.0.1:8092")

