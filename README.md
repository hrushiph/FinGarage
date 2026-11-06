# FinGarage — Code-Level FinOps & Engineering Contract Room on Switch

> **Flip the Switch Hackathon Submission**
> **Primary Track:** Best Business Workflow (Cross-Role Finance / FinOps $\leftrightarrow$ Backend Engineering)
> **Agent Provider:** Google Antigravity (`provider: antigravity`) via Switch Console (`fingarage.template.yaml`)
> **Repository:** [https://github.com/hrushiph/FinGarage](https://github.com/hrushiph/FinGarage)
> **Interactive Live Showcase:** [https://hrushiph.github.io/FinGarage/](https://hrushiph.github.io/FinGarage/) ([`docs/index.html`](docs/index.html)) | **Visual Receipt Card:** [`finops-hq/receipts/receipt_card.svg`](finops-hq/receipts/receipt_card.svg)

---

## 1. The Problem: The Wall Between FinOps Invoices & Application Code

In every modern cloud & AI engineering organization, **FinOps** and **Application Engineering** live in separate worlds:

1. **Folder A (`./finops-hq` — Finance / FinOps Team):** Sees the November cloud & AI invoice spike (`$14,487.60/month` on `GET /orders/summary` — **9.66x over budget**) and owns the unit-economics budget policy (`<= $0.0050/request`), but has **zero access** to application source code.
2. **Folder B (`./checkout-service` — Backend Engineering Team):** Owns `app.py`, `db.py`, and `llm_engine.py`. Unit tests return `200 OK`, so engineering has **zero visibility** into per-request token bloat, N+1 SQL IOPS queries, or CloudWatch log ingestion volume — and if told to "just cut tokens," takes a naive shortcut (prompt truncation) that silently breaks output accuracy.

---

## 2. The Solution: `FinGarage` (`#fin-garage` Switch Room)

**FinGarage** connects two working-directory-isolated Antigravity agents inside a shared Switch room (`#fin-garage`):

| Agent | Switch Role | Isolated Working Directory | Exclusive Capabilities |Why It Fails If Switch Is Turned Off ("Switch-Off Test") |
| :--- | :--- | :--- | :--- | :--- |
| **`finops-agent`** | `cost-seal-holder` | `./finops-hq` | Parses `invoice_nov_2026.csv`, enforces `budget_policy.yaml`, runs black-box HTTP probes (`probe.py`), mints cryptographic receipts (`receipt_card.png`) | Sees the `$14,487.60/mo` spend breach, but **cannot read or edit** `./checkout-service` source code to fix the N+1 SQL queries or LLM prompt bloat. |
| **`dev-agent`** | Participant | `./checkout-service` | Owns `app.py`, `db.py`, `llm_engine.py`, and `service_config.py` | Sees `200 OK` locally. Without `finops-agent`'s black-box quality & cost probe in `#fin-garage`, ships the **naive prompt-truncation shortcut** that drops accuracy from `100%` to `60%`. |

---

## 3. Five High-Impact Micro-Hooks Built for Judges

1. **Live `X-Unit-Cost-USD` & `X-FinOps-Receipt` HTTP Headers on Every Response:**
   Every response from `GET /orders/summary` emits real-time code-level FinOps telemetry in its HTTP headers:
   ```http
   HTTP/1.1 200 OK
   X-Unit-Cost-USD: 0.003622
   X-Cost-Breakdown: sql=2($0.0002),llm_tokens=340_cached($0.0034),logs_kb=0.4($0.0000)
   X-SQL-Queries: 2
   X-LLM-Tokens: 340
   X-LLM-Cache-Hit: true
   X-Log-Bytes: 381
   X-Latency-Ms: 56
   X-Golden-Accuracy-Pct: 100.0
   X-FinOps-Receipt: VERIFIED-12c36d84 (-92.5%)
   ```
2. **The "Quality-Drop Trap" (Live In-Room Refusal):**
   - **Attempt 1 (`naive` profile):** `dev-agent` cuts cost to `$0.002742/req` by truncating the LLM prompt to 5 rows. `finops-agent` probes the endpoint, detects that `X-Golden-Accuracy-Pct` dropped from `100.0%` to **`60.0%`** (missing `refund_anomaly_detected` and `payment_retry_detected`), and **refuses the fix live in `#fin-garage`**.
   - **Attempt 2 (`optimized` profile):** `dev-agent` replaces the N+1 SQL loop with a 2-query `JOIN`, replaces the 3,820-token raw dump with a 340-token semantic-cached digest, and replaces per-row debug logs with a structured counter — achieving **`$0.003622/req` (`-92.5%`)**, **`56ms` latency (`25.7x` faster)**, and **`100.0%` Golden Accuracy**.
3. **"Don't Trust Chat, Trust the Probe" Guardrail:**
   `finops-hq/probe.py mint-receipt` raises a hard `PermissionError` if called before a cryptographically hashed HTTP probe (`receipts/latest_probe.json`) passes both the Cost Contract (`<= $0.0050/req`) and Golden Accuracy Gate (`>= 95.0%`).
4. **Visual Itemized FinOps Store Receipt Card (`send_attachment`):**
   Once verified, `finops-agent` generates [`finops-hq/receipts/receipt_card.png`](finops-hq/receipts/receipt_card.png) and [`finops-hq/receipts/receipt_card.svg`](finops-hq/receipts/receipt_card.svg) and attaches the receipt card directly into the `#fin-garage` Switch room.
5. **Interactive Judge Showcase (`docs/index.html`):**
   Open [`docs/index.html`](docs/index.html) in any browser to toggle **Switch ON vs. Switch OFF**, step through the **4-Beat Room Simulator**, test the **Guardrail Block**, and adjust the **Monthly Traffic Scale Calculator**.

---

## 4. Verified Before vs. After Results

| Metric | Baseline (`baseline`) | Attempt 1 (`naive` — Refused) | Attempt 2 (`optimized` — Verified) | Net Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **SQL Queries / Request** | `101` (`$0.009090`) | `2` (`$0.000180`) | **`2` (`$0.000180`)** | **-98.0% SQL IOPS** |
| **LLM Context Tokens** | `3,820` uncached (`$0.034380`) | `280` truncated (`$0.002520`) | **`340` cached (`$0.003400`)** | **-90.1% LLM Cost** |
| **CloudWatch Log Volume** | `43.06 KB` (`$0.004822`) | `0.37 KB` (`$0.000042`) | **`0.37 KB` (`$0.000042`)** | **-99.1% Log Volume** |
| **Golden Accuracy SLA (`>=95%`)** | `100.0%` (`5/5` facts) | ❌ **`60.0%` (`3/5` facts — REFUSED)** | ✅ **`100.0%` (`5/5` facts)** | **Zero Quality Loss** |
| **Endpoint Latency** | `1,441 ms` | `76 ms` | **`56 ms`** | **25.7x Faster** |
| **Unit Cost / Request** | **`$0.048292`** | `$0.002742` (Rejected) | **`$0.003622`** | **-92.5% Unit Cost** |
| **Annual Run-Rate (300k req/mo)** | `$173,851.20 / yr` | — | **`$13,039.20 / yr`** | **`$160,812.00 / yr` Saved** |

---

## 5. Quickstart (Zero External Setup — Runs in < 3 Seconds)

Requires only Python 3.9+ (with `pytest`, `PyYAML`, and `Pillow`).

```bash
# 1. Run the automated 4-Beat #fin-garage Switch Room replay
make demo-replay

# 2. Run the full pytest verification suite across both isolated folders
make test
```

### Manual Step-by-Step CLI Commands

```bash
# Start checkout-service (Folder B) on port 8090
python3 checkout-service/app.py --port 8090 --mode baseline

# In a second terminal, run FinOps Audit from Folder A (./finops-hq)
python3 finops-hq/probe.py audit --url http://127.0.0.1:8090

# Test Attempt 1 (Naive shortcut -> Refused with exit code 2!)
python3 checkout-service/service_config.py naive
python3 finops-hq/probe.py verify --url http://127.0.0.1:8090

# Apply Attempt 2 (Smart fix -> Verified Pass + Mint Receipt!)
python3 checkout-service/service_config.py optimized
python3 finops-hq/probe.py verify --url http://127.0.0.1:8090
python3 finops-hq/probe.py mint-receipt --url http://127.0.0.1:8090

# Inspect live HTTP headers with curl
curl -i http://127.0.0.1:8090/orders/summary
```

---

## 6. Running in Switch Console with Google Antigravity

1. Install and sign in to the Switch Antigravity ACP adapter:
   ```bash
   antigravity-acp --login
   ```
2. Import [`fingarage.template.yaml`](fingarage.template.yaml) in **Switch Console**:
   - Spawns `finops-agent` (`provider: antigravity`, `directory: ./finops-hq`, role: `cost-seal-holder`)
   - Spawns `dev-agent` (`provider: antigravity`, `directory: ./checkout-service`)
   - Creates the `#fin-garage` room with the `FinOps Verified Savings Ledger` Room Document and triggers the kickoff audit automatically.

---

## 7. Repository Structure

```text
.
├── fingarage.template.yaml       # Switch Console template (provider: antigravity, 2 isolated folders)
├── Makefile                       # 1-command test & demo replay targets
├── scripts/
│   └── demo_replay.py             # Automated 4-beat end-to-end collaboration replay
├── finops-hq/                     # FOLDER A: FinOps Agent's isolated working directory
│   ├── invoice_nov_2026.csv       # November 2026 Cloud & AI billing invoice ($14,487.60/mo breach)
│   ├── budget_policy.yaml         # Cost contract (<= $0.0050/req) & Golden Accuracy SLA (>= 95%)
│   ├── probe.py                   # Black-box HTTP verifier & guardrail-protected receipt minter
│   ├── render_receipt.py          # Renders itemized FinOps receipt card (.png & .svg)
│   ├── test_finops.py             # Pytest suite for audit, naive refusal, guardrail, and minting
│   └── receipts/                  # Minted receipts (cost-receipt.json, receipt_card.png/svg, room_ledger.md)
├── checkout-service/              # FOLDER B: Backend Engineer Agent's isolated working directory
│   ├── app.py                     # HTTP service emitting live X-Unit-Cost-USD & X-FinOps-Receipt headers
│   ├── db.py                      # Deterministic 100-order SQLite database & SQL query counter
│   ├── llm_engine.py              # Pricing snapshot, prompt strategies & 5-fact Golden Quality Evaluator
│   ├── service_config.py          # Profile switcher (baseline -> naive -> optimized)
│   └── test_service.py            # Pytest suite for checkout-service profiles
└── docs/
    └── index.html                 # Interactive HTML Judge Showcase (Switch-Off Toggle + 4-Beat Simulator)
```

