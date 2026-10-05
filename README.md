<p align="center"><img src="docs/karbhari-logo.png" width="104" alt="KARBHARI logo"></p>

<h1 align="center">KARBHARI · कारभारी</h1>
<h3 align="center">Working Capital Guardian for Indian MSMEs</h3>

<p align="center"><b>Find what your numbers are hiding.</b> 🔍</p>

<p align="center">
  <a href="https://hub.docker.com/r/yieldnever/karbhari"><img alt="Docker image" src="https://img.shields.io/badge/Docker-yieldnever%2Fkarbhari%3A0.7.0-2496ED?logo=docker&logoColor=white"></a>
  <img alt="API: FastAPI" src="https://img.shields.io/badge/API-FastAPI%200.115-009688?logo=fastapi&logoColor=white">
  <img alt="LLM: Google Gemini" src="https://img.shields.io/badge/LLM-Google%20Gemini-4285F4?logo=googlegemini&logoColor=white">
  <img alt="Frontend: React 19 + TypeScript" src="https://img.shields.io/badge/UI-React%2019%20%2B%20TypeScript-61DAFB?logo=react&logoColor=black">
  <img alt="Tests: 52 passing" src="https://img.shields.io/badge/tests-52%20passing-2EA44F">
  <a href="LICENSE"><img alt="License: Apache 2.0" src="https://img.shields.io/badge/License-Apache%202.0-blue"></a>
</p>

<p align="center">
  🎬 <a href="Karbhari%20Explainer%20Video.mp4">Explainer film</a> &nbsp;·&nbsp;
  📘 <a href="Karbhari-Product-Document.pdf">Product document</a> &nbsp;·&nbsp;
  🧭 <a href="Karbhari-Project-Guide.pdf">Project guide</a> &nbsp;·&nbsp;
  🧪 <a href="ASSETS%20FOR%20TESTING">Test files</a>
</p>

---

## 💡 What is KARBHARI?

Every MSME on a bank cash-credit line can only draw what its **Drawing Power** allows. The bank recalculates it every month from stock, debtors and creditors. When those numbers are stale, mis-aged or duplicated, the business quietly loses capital it is entitled to.

**KARBHARI investigates it for you.** Upload the documents you already have. An AI agent reads them, cross-checks them and rebuilds your Drawing Power from first principles. You get the gap, the reasons, and the evidence behind every rupee.

<p align="center"><img src="docs/screenshot-findings.jpg" width="900" alt="KARBHARI findings view"></p>
<p align="center"><sub>A live run on our test files: ₹2,20,000 of Drawing Power the facility supports but the bank isn't recognising.</sub></p>

## 🎯 Why it matters

- 🏦 **Capital gets stuck.** Small errors in stock statements or debtor ageing shrink the limit an MSME can actually use.
- 🧑‍💼 **Nobody has time to check.** Big companies have treasury teams. A small business has the owner.
- 🤖 **Chatbots don't solve it.** They give advice, do maths in prose and can't show their working.

KARBHARI gives a **defensible answer in minutes, not days**, honest enough to take to your banker or CA.

## 🗺️ How it works

```mermaid
flowchart TB
    owner(["🧑‍💼 MSME owner or CA opens a case"])

    EV["📂 <b>Evidence the business already has</b><br/>📜 Sanction letter · 📦 Stock statements<br/>🧾 Invoices and receipts · 📒 Creditor ledger · 🏦 Bank statement"]

    owner --> EV
    EV --> X["🔍 Text extraction<br/>PDF · Excel · CSV · TXT"]

    subgraph AG["🤖 Investigator agent · Gemini · max 20 steps"]
        direction TB
        t1["list_evidence"] --> t2["read_evidence<br/>on every file"]
        t2 --> t3{"Decides what<br/>to check next"}
    end
    X --> AG

    subgraph EN["🧮 Deterministic engines · pure Python · tested"]
        direction LR
        n1["Debtor reconciliation<br/>tagged, FIFO, unallocated<br/>ageing vs 90-day cut-off"]
        n2["Consistency check<br/>flags swings of 20%+"]
        n3["Drawing Power engine<br/>margins, creditors, limit cap"]
    end
    t3 -->|reconcile_debtors| n1
    t3 -->|check_consistency| n2
    t3 -->|calculate_drawing_power| n3
    n1 -. "reconciled debtors override<br/>the agent's own figure" .-> n3

    G["🛡️ Guardian<br/>builds the headline in code<br/>flags any skipped checks"]
    n1 --> G
    n2 --> G
    n3 --> G

    OUT["✅ <b>What you get</b><br/>💰 Capacity gap · 🏷️ Graded findings<br/>📎 Evidence quotes · 🧭 Full reasoning trace"]
    G --> OUT
```

**The model reasons. Python calculates.** The agent chooses what to read and which checks to run. Every number comes from deterministic, tested code that can't hallucinate.

```mermaid
mindmap
  root((KARBHARI))
    📂 Reads
      Sanction letter
      Stock statements
      Invoices and receipts
      Creditor and bank records
    🔎 Checks
      Debtor ageing
      Duplicate invoices
      Unallocated receipts
      Period-over-period swings
    🧮 Calculates
      Drawing Power
      Capacity gap
    ✅ Proves
      Evidence quotes
      Graded findings
      Reasoning trace
```

## 📸 A look inside

A console built like a financial-investigation film: precise numerals, a quiet dot grid, colour that always means something (gold for capacity, red for problems, green for verified), smooth transitions and subtle interface sound effects you can mute.

<table>
  <tr>
    <td width="50%"><img src="docs/screenshot-lobby.jpg" alt="KARBHARI lobby"><br><sub><b>Lobby.</b> Open a case, see the verified benchmark.</sub></td>
    <td width="50%"><img src="docs/screenshot-investigating.jpg" alt="Investigation in progress"><br><sub><b>Investigating.</b> The agent reads, cross-checks and verifies each document.</sub></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/screenshot-investigation.jpg" alt="Investigation detail"><br><sub><b>Every figure.</b> Drawing Power, capacity bars and the debtor book.</sub></td>
    <td width="50%"><img src="docs/screenshot-findings.jpg" alt="Findings"><br><sub><b>Findings.</b> Graded, cited and always backed by tested code.</sub></td>
  </tr>
</table>

## 🇮🇳 Why it works in India

- **Works with what MSMEs already have.** Bank PDFs, Tally and Excel exports, CSVs. No new data entry, no bank integration.
- **Cheap to run.** One container, 1 CPU and 1 GB RAM, Gemini Flash-Lite free tier. Typically 30 seconds to 2 minutes per case.
- **Trusted by the people who matter.** Banks and CAs can audit every figure, because the arithmetic lives in code and every finding cites its source.
- **Honest by design.** It reports what weakens the owner's case as readily as what helps it, so it holds up in front of a credit officer.
- **Big addressable need.** India has over 6 crore MSMEs (Ministry of MSME), and working capital is the most common pain point for the ones with bank credit.

## ⚙️ Project specifications

| | |
|---|---|
| **Agent** | Bounded ReAct loop on Google Gemini, up to 20 tool calls, full trace saved |
| **Tools** | `list_evidence` · `read_evidence` · `reconcile_debtors` · `check_consistency` · `calculate_drawing_power` |
| **Engines** | Pure Python: per-debtor FIFO reconciliation, ageing, duplicates, ±20% variance flags, Drawing Power with sanctioned margins and limit cap |
| **Inputs** | Sanction letter, stock statements, debtor invoices and receipts, creditor ledger, bank statement (PDF, XLSX, CSV, TXT) |
| **Outputs** | Capacity gap, graded findings with evidence quotes, invoice-level reconciliation, step-by-step trace |
| **Console** | Film-style UI: count-up figures, transitions, live investigation overlay, synthesized sound effects (mutable) |
| **Stack** | FastAPI · SQLModel/SQLite · React 19 + TypeScript + Vite · Docker |
| **Quality** | 52 automated tests, including a live end-to-end run against Gemini |
| **Docker** | Public image `docker.io/yieldnever/karbhari:0.7.0` |

## 🚀 How to run

**1. Add your API key.** Copy `backend/.env.example` to `backend/.env` and paste a free key from [Google AI Studio](https://aistudio.google.com/apikey).

**2. Start it with Docker** (recommended):

```bash
docker build -t karbhari:0.7.0 .
run.bat        # or: docker run -p 8000:8000 --env-file backend/.env karbhari:0.7.0
```

Open **http://127.0.0.1:8000** 🎉

<details>
<summary><b>Or run backend and frontend separately (development)</b></summary>

```bash
# backend (Python 3.12+)
cd backend
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000

# frontend (Node 20+), in a second terminal
cd frontend
npm install
npm run dev                     # open http://127.0.0.1:5173
```

Run the tests with `cd backend && python -m pytest -q`.
</details>

## 🧪 What to test it on

Everything you need is in [`ASSETS FOR TESTING/`](ASSETS%20FOR%20TESTING).

1. Create a case and attach the six files, picking a category for each.
2. Click **Run investigation**.
3. You should see:

| Check | Expected result |
|---|---|
| Calculated Drawing Power | **₹25,70,000** vs ₹23,50,000 recognised by the bank |
| Capacity gap | **₹2,20,000** |
| Ineligible debtors | INV-1002 and INV-1005, past 90 days, **₹6,00,000** excluded |
| Period swings | Stock +25%, debtors +29.4%, creditors +33.3% |

## ✅ Verified, not just demoed

We built a tricky 7-document case and worked out the right answer **by hand first**. The live agent then matched it to the rupee: **₹12,10,000** gap, ₹44,10,000 calculated Drawing Power. Along the way it caught a duplicate ₹3,50,000 invoice, a ₹70,000 unallocated receipt, a 105-day-old invoice and a 38% stock swing.

## 🧭 Honest limits and what's next

- The agent can still skip the consistency check. KARBHARI flags the gap in its findings; if it tries to finish before calculating Drawing Power, it is sent back once to do so.
- No OCR yet, so scanned PDFs need a text layer.
- The Actions tab is coming next: an evidence-backed note to your bank.
- Creditors are reconciled as a total, not invoice by invoice.

## 📄 License

[Apache 2.0](LICENSE) · Built for Indian MSMEs
