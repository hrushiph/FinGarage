"""
Code-level configuration for checkout-service.

When `dev-agent` optimizes the repository inside `./checkout-service`, it updates
`ACTIVE_PROFILE` (or individual strategies) from "baseline" to "optimized".
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

STATE_FILE = Path(__file__).resolve().parent / ".runtime_mode.json"

PROFILES: dict[str, dict[str, str]] = {
    # Initial unoptimized state ($0.0482/req | 101 SQL queries | 3,820 tokens | 42 KB logs | 100% quality)
    "baseline": {
        "profile_name": "baseline",
        "query_strategy": "n_plus_one",          # 1 query for orders + 100 queries in a loop for customers
        "prompt_strategy": "bloated_uncached",   # 3,820 uncached tokens on frontier model
        "log_strategy": "verbose_payload_debug", # Logs full JSON payload on every row (43 KB/req)
    },
    # Naive shortcut that breaks the Golden Quality Gate ($0.0029/req | 2 SQL queries | 60% quality -> REFUSED!)
    "naive": {
        "profile_name": "naive",
        "query_strategy": "eager_join",
        "prompt_strategy": "naive_truncated",    # Truncates prompt and drops refund/retry anomalies!
        "log_strategy": "structured_counter",
    },
    # Verified FinOps fix ($0.0038/req | 2 SQL queries | 340 cached tokens | 0.4 KB logs | 100% quality -> PASS!)
    "optimized": {
        "profile_name": "optimized",
        "query_strategy": "eager_join",          # Single SQL JOIN + aggregate summary query (2 queries total)
        "prompt_strategy": "cached_digest",      # Semantic cached prefix + compact digest (340 tokens)
        "log_strategy": "structured_counter",    # Lightweight metric counter (0.38 KB/req)
    },
}


def get_active_config() -> dict[str, Any]:
    """Return the active code-level strategy configuration."""
    env_mode = os.environ.get("FINGARAGE_MODE")
    if env_mode and env_mode in PROFILES:
        return dict(PROFILES[env_mode])

    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            mode = data.get("profile_name", "baseline")
            if mode in PROFILES:
                merged = dict(PROFILES[mode])
                merged.update(data)
                return merged
        except Exception:
            pass

    return dict(PROFILES["baseline"])


def set_active_profile(profile_name: str, receipt_seal: str | None = None) -> dict[str, Any]:
    """Switch the service profile (baseline, naive, optimized) and optionally attach a receipt seal."""
    if profile_name not in PROFILES:
        raise ValueError(f"Unknown profile {profile_name!r}. Choose from {list(PROFILES)}")
    payload: dict[str, Any] = dict(PROFILES[profile_name])
    if receipt_seal:
        payload["receipt_seal"] = receipt_seal
    STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    import sys

    mode_arg = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    seal_arg = sys.argv[2] if len(sys.argv) > 2 else None
    updated_cfg = set_active_profile(mode_arg, receipt_seal=seal_arg)
    print(json.dumps(updated_cfg))
