# How We Built FinGarage: Turning Cloud FinOps Invoices into Verified Code Refactors with Switch & Google Antigravity

*Published for the Flip the Switch Hackathon (WeMakeDevs)*

---

## The $14,487/Month Question Nobody Can Answer Alone

Every month, FinOps teams open their cloud and LLM billing dashboard and see a horror story: a single internal endpoint—`GET /orders/summary`—just burned **$14,487.60 in 30 days** (`$0.048292 per request`, nearly **10x over budget**).

FinOps files a Jira ticket. Three weeks later, a backend engineer looks at `/orders/summary`, sees that all unit tests pass with `200 OK`, and has no idea whether the cost spike comes from RDS Provisioned IOPS, LLM tokens, or CloudWatch log ingestion. Worse: if told to *"just cut LLM tokens,"* the engineer truncates the prompt to the first 5 rows—cutting the bill by 94%, but **silently breaking refund anomaly detection in production**.

We asked a simple question: **What if Finance and Engineering didn't coordinate through stale tickets, but collaborated live inside a Switch Room with deterministic HTTP cost and quality probes?**

---

## Enter FinGarage (`#fin-garage`)

Using **Switch** and **Google Antigravity (`provider: antigravity`)**, we built **FinGarage** around Switch's core architectural strength: **Working Directory Isolation + Shared Room Contracts**.

- **`finops-agent` (`./finops-hq`, role: `cost-seal-holder`):** Has exclusive access to `invoice_nov_2026.csv`, `budget_policy.yaml`, and the black-box verifier `probe.py`. It **cannot** read or modify `./checkout-service` code.
- **`dev-agent` (`./checkout-service`):** Has exclusive access to `app.py`, `db.py`, and `llm_engine.py`. It **cannot** read the invoice or self-certify cost compliance.

Neither agent can solve the problem if you turn Switch off.

---

## Making Every HTTP Request Carry Its Own Price Tag

First, we instrumented `checkout-service` so every response from `GET /orders/summary` emits itemized unit-cost telemetry directly in its HTTP headers:

```http
X-Unit-Cost-USD: 0.048292
X-Cost-Breakdown: sql=101($0.0091),llm_tokens=3820($0.0344),logs_kb=43.1($0.0048)
X-Golden-Accuracy-Pct: 100.0
X-FinOps-Receipt: UNVERIFIED-BUDGET-BREACH
```

When `finops-agent` runs `python3 probe.py audit` from `./finops-hq`, it correlates the November invoice spike with the exact three code-level anti-patterns in a single `#fin-garage` room alert:
1. **101 SQL queries/request** (an N+1 customer hydration loop)
2. **3,820 uncached LLM tokens/request** (re-sending raw JSON rows on every call)
3. **43.06 KB of logs/request** (a `DEBUG` payload dump inside the hot loop)

---

## Catching the "Cheap But Wrong" Shortcut Live in `#fin-garage`

The most realistic moment in our Switch room happens on **Attempt 1**:
1. `dev-agent` takes a shortcut (`naive` mode): it fixes the SQL query and truncates the LLM prompt to 5 rows. Unit cost drops to `$0.002742/req`.
2. `dev-agent` messages `#fin-garage`: *"@finops-agent Unit cost is now under $0.0050, please verify!"*
3. Instead of trusting chat claims (**"Don't Trust Chat, Trust the Probe"**), `finops-agent` runs `python3 probe.py verify`.
4. The probe catches that `X-Golden-Accuracy-Pct` dropped from `100.0%` to **`60.0%`** because truncating tail rows missed `refund_anomaly_detected` and `payment_retry_detected`.
5. `finops-agent` **refuses the fix in-room** and blocks receipt minting (`PermissionError: GUARDRAIL BLOCKED`).

On **Attempt 2**, `dev-agent` implements the true architectural fix (`optimized` mode): a 2-query SQL `JOIN` + database-level aggregation, a 340-token semantic-cached digest that preserves all 5 ground-truth facts, and a structured metric counter log.

---

## The Payoff: -92.5% Unit Cost, 25.7x Faster, and a Minted Receipt Card

When `finops-agent` re-runs `probe.py verify` and `probe.py mint-receipt`:
- **Unit Cost:** `$0.048292` $\rightarrow$ **`$0.003622` (`-92.5%`)**
- **Annual Run-Rate Savings:** **`$160,812.00 / year`** (at 300k requests/month)
- **Latency:** `1,441 ms` $\rightarrow$ **`56 ms` (`25.7x` faster)**
- **Golden Accuracy:** **`100.0%` (`5/5` facts)**
- **Live HTTP Stamp:** `X-FinOps-Receipt: VERIFIED-12c36d84 (-92.5%)`

Finally, `finops-agent` updates the Switch Room Document (`FinOps Verified Savings Ledger`) and attaches a visual **Itemized FinOps Store Receipt Card** (`receipt_card.png`) directly into `#fin-garage` via `send_attachment`.

