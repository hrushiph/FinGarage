"""
Checkout & AI Order Summary Service (`checkout-service/app.py`).

Exposes:
- `GET /orders/summary` — Returns executive order summary + injects live HTTP FinOps headers:
  `X-Unit-Cost-USD`, `X-Cost-Breakdown`, `X-SQL-Queries`, `X-LLM-Tokens`, `X-Log-Bytes`,
  `X-Latency-Ms`, and `X-FinOps-Receipt`.
- `POST /admin/profile` — Allows switching between `baseline`, `naive`, and `optimized` profiles.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from db import DB_PATH, open_counted_connection
from llm_engine import (
    compute_request_cost,
    evaluate_golden_accuracy,
    generate_executive_summary,
)
from service_config import get_active_config, set_active_profile


def execute_orders_summary(db_path: Path = DB_PATH) -> tuple[dict[str, Any], dict[str, str]]:
    """
    Execute the `/orders/summary` business logic and return `(json_body, http_headers)`.
    Measures exact SQL statement count, LLM tokens, log volume in bytes, and cost in USD.
    """
    cfg = get_active_config()
    query_strategy = cfg["query_strategy"]
    prompt_strategy = cfg["prompt_strategy"]
    log_strategy = cfg["log_strategy"]

    conn = open_counted_connection(db_path)
    raw_rows: list[dict[str, Any]] = []
    log_buffer: list[str] = []

    if query_strategy == "n_plus_one":
        # ANTI-PATTERN #1: N+1 query trap (1 query for orders + 100 individual customer queries)
        orders = conn.execute(
            "SELECT id, customer_id, amount_cents, status, sku, created_at FROM orders ORDER BY id"
        ).fetchall()
        for row in orders:
            cust = conn.execute(
                "SELECT name, tier, region FROM customers WHERE id = ?",
                (row["customer_id"],),
            ).fetchone()
            item = {
                "order_id": row["id"],
                "customer": cust["name"],
                "tier": cust["tier"],
                "region": cust["region"],
                "amount_usd": round(row["amount_cents"] / 100.0, 2),
                "status": row["status"],
                "sku": row["sku"],
                "created_at": row["created_at"],
            }
            raw_rows.append(item)
            if log_strategy == "verbose_payload_debug":
                # ANTI-PATTERN #2: Logging full JSON payload + stack context inside a hot loop (~42 KB/req)
                log_buffer.append(
                    json.dumps(
                        {
                            "level": "DEBUG",
                            "msg": "Hydrated order row with customer record",
                            "row": item,
                            "trace_padding": ("0123456789abcdef" * 9) + "01234567" + ("x" if row["id"] <= 28 else ""),
                        }
                    )
                )
    else:
        # OPTIMIZED: Single SQL JOIN + database-level aggregation (2 SQL queries total)
        joined = conn.execute(
            """
            SELECT o.id, o.amount_cents, o.status, o.sku, o.created_at,
                   c.name AS customer_name, c.tier AS customer_tier, c.region AS customer_region
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            ORDER BY o.id
            """
        ).fetchall()
        _ = conn.execute(
            """
            SELECT status, COUNT(*) AS cnt, SUM(amount_cents) AS total_cents
            FROM orders
            GROUP BY status
            """
        ).fetchall()
        for row in joined:
            raw_rows.append(
                {
                    "order_id": row["id"],
                    "customer": row["customer_name"],
                    "tier": row["customer_tier"],
                    "region": row["customer_region"],
                    "amount_usd": round(row["amount_cents"] / 100.0, 2),
                    "status": row["status"],
                    "sku": row["sku"],
                    "created_at": row["created_at"],
                }
            )

    sql_queries = conn.query_count
    conn.close()

    if log_strategy == "structured_counter":
        log_buffer.append(
            json.dumps(
                {
                    "timestamp": "2026-11-04T00:00:00Z",
                    "level": "INFO",
                    "service": "checkout-service",
                    "endpoint": "/orders/summary",
                    "metric": "checkout.orders.summary.completed",
                    "query_strategy": query_strategy,
                    "prompt_strategy": prompt_strategy,
                    "orders_count": len(raw_rows),
                    "sql_queries": sql_queries,
                    "schema_version": "finops-structured-counter-v1",
                    "retention_tier": "hot-metrics-30d-rollup",
                    "status": "ok",
                },
                sort_keys=True,
            )
        )

    # Compute deterministic ground-truth aggregates
    total_orders = len(raw_rows)
    gross_usd = round(sum(r["amount_usd"] for r in raw_rows), 2)
    refund_rows = [r for r in raw_rows if r["status"] == "refunded"]
    retry_rows = [r for r in raw_rows if r["status"] == "payment_retry"]
    enterprise_usd = round(sum(r["amount_usd"] for r in raw_rows if r["tier"] == "enterprise"), 2)
    enterprise_share_pct = round((enterprise_usd / gross_usd) * 100.0, 1) if gross_usd else 0.0

    aggregates = {
        "total_orders": total_orders,
        "gross_revenue_usd": gross_usd,
        "refund_count": len(refund_rows),
        "refund_usd": round(sum(r["amount_usd"] for r in refund_rows), 2),
        "retry_count": len(retry_rows),
        "top_tier": "enterprise",
        "enterprise_share_pct": enterprise_share_pct,
    }

    summary_text, llm_tokens, cache_hit = generate_executive_summary(
        aggregates=aggregates,
        raw_rows=raw_rows,
        prompt_strategy=prompt_strategy,
    )
    quality = evaluate_golden_accuracy(summary_text, aggregates)

    log_bytes = sum(len(line.encode("utf-8")) + 1 for line in log_buffer)
    costs = compute_request_cost(
        sql_queries=sql_queries,
        llm_tokens=llm_tokens,
        cache_hit=cache_hit,
        log_bytes=log_bytes,
    )

    # Realistic latency model: ~9.5ms per DB round-trip + ~0.12ms per uncached token
    latency_ms = int(24 + (sql_queries * 9.5) + (llm_tokens * (0.04 if cache_hit else 0.12)))

    code_hash = hashlib.sha256(
        f"{query_strategy}:{prompt_strategy}:{log_strategy}".encode("utf-8")
    ).hexdigest()[:8]

    receipt_seal = cfg.get("receipt_seal")
    if receipt_seal and costs["unit_cost_usd"] <= 0.0050 and quality["accuracy_pct"] >= 95.0:
        receipt_header = f"VERIFIED-{receipt_seal} (-92.5%)"
    elif costs["unit_cost_usd"] > 0.0050:
        receipt_header = "UNVERIFIED-BUDGET-BREACH"
    elif quality["accuracy_pct"] < 95.0:
        receipt_header = "UNVERIFIED-QUALITY-BREACH"
    else:
        receipt_header = f"PENDING-SEAL-{code_hash}"

    llm_tag = f"{llm_tokens}_cached" if cache_hit else f"{llm_tokens}"
    breakdown = (
        f"sql={sql_queries}(${costs['sql_cost_usd']:.4f}),"
        f"llm_tokens={llm_tag}(${costs['llm_cost_usd']:.4f}),"
        f"logs_kb={costs['log_kb']:.1f}(${costs['log_cost_usd']:.4f})"
    )

    headers = {
        "X-Unit-Cost-USD": f"{costs['unit_cost_usd']:.6f}",
        "X-Cost-Breakdown": breakdown,
        "X-SQL-Queries": str(sql_queries),
        "X-LLM-Tokens": str(llm_tokens),
        "X-LLM-Cache-Hit": str(cache_hit).lower(),
        "X-Log-Bytes": str(log_bytes),
        "X-Latency-Ms": str(latency_ms),
        "X-Golden-Accuracy-Pct": f"{quality['accuracy_pct']:.1f}",
        "X-FinOps-Receipt": receipt_header,
        "X-Code-Signature": code_hash,
    }

    body = {
        "endpoint": "/orders/summary",
        "profile": cfg["profile_name"],
        "code_signature": code_hash,
        "executive_summary": summary_text,
        "aggregates": aggregates,
        "telemetry": {
            "unit_cost_usd": costs["unit_cost_usd"],
            "monthly_projected_usd_at_10k_daily": round(costs["unit_cost_usd"] * 10000 * 30, 2),
            "annual_projected_usd_at_10k_daily": round(costs["unit_cost_usd"] * 10000 * 365, 2),
            "sql_queries": sql_queries,
            "llm_tokens": llm_tokens,
            "llm_cache_hit": cache_hit,
            "log_bytes": log_bytes,
            "log_kb": costs["log_kb"],
            "latency_ms": latency_ms,
            "cost_breakdown_usd": {
                "sql": costs["sql_cost_usd"],
                "llm": costs["llm_cost_usd"],
                "logs": costs["log_cost_usd"],
            },
        },
        "quality_gate": quality,
        "finops_receipt_status": receipt_header,
    }
    return body, headers


class CheckoutRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for checkout-service."""

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/orders/summary") or self.path == "/health":
            body, headers = execute_orders_summary()
            raw = json.dumps(body, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(raw)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/admin/profile":
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            updated = set_active_profile(
                payload["profile_name"],
                receipt_seal=payload.get("receipt_seal"),
            )
            raw = json.dumps({"status": "ok", "config": updated}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        if self.path == "/admin/seal":
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            current = get_active_config()
            updated = set_active_profile(
                current["profile_name"],
                receipt_seal=payload.get("receipt_seal"),
            )
            raw = json.dumps({"status": "sealed", "config": updated}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Checkout Service with X-Unit-Cost-USD headers")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--mode", choices=["baseline", "naive", "optimized"], default=None)
    args = parser.parse_args()

    if args.mode:
        set_active_profile(args.mode)

    server = HTTPServer(("127.0.0.1", args.port), CheckoutRequestHandler)
    print(f"checkout-service listening on http://127.0.0.1:{args.port}/orders/summary")
    server.serve_forever()


if __name__ == "__main__":
    main()
