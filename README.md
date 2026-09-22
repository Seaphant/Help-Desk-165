# HelpDesk165

Campus IT help-desk prototype for **CMPE 165 — Software Engineering Process Management**, Project 1.

One queue for every campus technology request. Built for **SJSU Campus Technology Services (CTS)** as a stand-in for the shared inbox and three spreadsheets that tickets currently live in.

**GitHub:** https://github.com/Seaphant/Help-Desk-165

## Team members

- **William Nguyen** — GitHub: [Seaphant](https://github.com/Seaphant)
- **Amy Wong**
- **Bryce Brewster**
- **Joshua Bemowski** - GitHub: [JoshuaBemowski](https://github.com/JoshuaBemowski)

> The assignment expects every team member's name on the README. Delete the placeholder
> lines that do not apply and fill in the rest.

## Project description

HelpDesk165 is a small, working ticketing product. A requester submits a campus technology problem once and gets a tracking number. An agent searches and filters the queue, assigns an owner, moves status, and leaves a work note. A manager reads SLA performance on a dashboard and exports a CSV.

The prototype is intentionally small. The course asks whether the project should continue, not whether we can build ServiceNow in two weeks. The written report, weighted scoring model, NPV, risk register, decision tree, and Monte Carlo simulation live under [`docs/`](docs/) and [`analysis/`](analysis/).

**What the analysis concluded:** a deterministic four-year NPV of **$179,670** on a **$157,760** build looks like an easy yes, but 10,000 Monte Carlo trials put expected NPV at **$54,286**, with a **27.3%** chance the investment never pays back and a **44.1%** chance the build blows through the $185,000 capital budget. The recommendation is **GO WITH CONDITIONS** — fund an eight-week paid pilot (EMV $98,300) before committing to the full build (EMV $85,000).

## Major features

1. **Submit a ticket** — category, priority, contact, automatic support-hour SLA target, tracking number.
2. **Work the queue** — search, filter, saved views (unassigned, SLA trouble), assign, update status, audit trail.
3. **SLA dashboard** — volume by category, SLA by priority, weekly intake, load by owner, CSV export.
4. **Support-hour clock** — weekday 08:00–18:00, campus holidays excluded. A Friday 5pm ticket is not late on Saturday.
5. **Role-scoped views** — a sidebar Requester / Agent / Manager switch. Requesters see only their own tickets and can comment but not reassign.

## Required packages and dependencies

Python 3.12 is what we developed against (3.11 should also work). From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

[`requirements.txt`](requirements.txt) pins the versions we actually installed:

| Purpose | Packages |
|---|---|
| Prototype | `streamlit`, `pandas`, `altair` |
| Analysis scripts | `numpy`, `matplotlib` |
| Deliverable generation | `python-docx`, `python-pptx`, `openpyxl` |
| Tests | `pytest` |

No database server, no cloud account, and no API keys are needed. The app uses a local SQLite file.

## Instructions for running the software

```bash
streamlit run app/Home.py
```

Then open <http://localhost:43117>. The committed `.streamlit/config.toml` pins that port and runs headless, so no browser opens by itself — the terminal prints the URL. If something else already holds the port, Streamlit exits with `Port 43117 is not available` instead of picking another one, so rerun it as `streamlit run app/Home.py --server.port 8599`.

On first launch the app creates `data/helpdesk.db` and seeds **62 sample tickets** plus six agents. Use the sidebar to switch among Requester, Agent, and Manager views. There is no real login; the role selector is enough to show that those people see different capabilities.

Reseed from **Reset sample data → Reseed database** in the sidebar before recording the Loom so the queue looks the same every take.

Useful extras:

```bash
# Unit tests for the SLA clock, persistence, reporting, and analysis (125 tests)
python -m pytest -q

# Rebuild NPV, scoring, risk, decision-tree, and Monte Carlo artifacts
python -m analysis.run_all

# Rebuild the calculation workbook (live Excel formulas, 9 sheets)
python -m tools.build_workbook docs/deliverables/CMPE165_Project1_Calculations.xlsx

# Re-polish the Word report and the 4-slide deck in place
python -m tools.polish_report
python -m tools.polish_slides

# Regenerate the Markdown copy of the report from the Word file
python -m tools.docx_to_markdown \
    docs/deliverables/CMPE165_Project1_Report.docx docs/PROJECT_REPORT.md

# Check the word / slide limits, and that no document links to a missing file
python -m tools.report_stats
python -m tools.check_doc_links
```

`python -m analysis.run_all` is the one that matters: every number in the report, the slides, and the workbook is read back from [`analysis/outputs/summary.json`](analysis/outputs/summary.json), so they cannot drift apart.

## Sample data

Sample tickets are generated by [`app/seed.py`](app/seed.py) (`random.seed(165)`), so every teammate and every grader gets the same 62 tickets. They cover the eight campus categories the queue uses (Account & Login, Wi-Fi & Network, Hardware, Classroom Technology, Canvas / LMS, Software & Licensing, Printing, Email & Calendar), spread across four priorities (Urgent / High / Medium / Low, with 4 / 8 / 24 / 72-support-hour targets) and six agents, with a realistic mix of open, resolved, on-track, at-risk, and breached tickets so the dashboard has something to show.

You do not need to import a CSV. Reseeding replaces the local database — `data/helpdesk.db` is generated and is deliberately not committed.

## Repository layout

```
app/                  Streamlit prototype
  Home.py             Overview / KPI landing page
  db.py               SQLite schema, ticket CRUD, audit trail
  sla.py              Business-hour SLA clock
  seed.py             Deterministic 62-ticket sample data
  reporting.py        DataFrame shaping and KPI math
  ui.py               Shared chrome, role switcher, column formatting
  pages/              Submit Ticket, Ticket Queue, SLA Dashboard
analysis/             Project-management math (source of truth for all numbers)
  assumptions.py      Every input in one place
  weighted_scoring.py Part C
  npv.py              Part D (NPV, ROI, IRR by bisection, payback)
  risk_register.py    Part H
  decision_tree.py    Part I
  monte_carlo.py      Part J (10,000 trials, seed 165)
  run_all.py          Regenerates every artifact
  outputs/            CSVs, summary.json, 4 PNG charts
tools/                Word / PowerPoint / Excel deliverable builders
tests/                125 pytest tests
docs/                 Report, submission checklist, Loom script, deliverables
data/                 Generated SQLite database (gitignored)
```

## Course deliverables

| Deliverable | Where it is |
|---|---|
| Working prototype | [`app/`](app/) — `streamlit run app/Home.py` |
| Project report (prose) | [`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md) |
| Project report (Word) | [`docs/deliverables/CMPE165_Project1_Report.docx`](docs/deliverables/CMPE165_Project1_Report.docx) |
| Class slides (exactly 4) | [`docs/deliverables/CMPE165_Project1_Slides.pptx`](docs/deliverables/CMPE165_Project1_Slides.pptx) |
| Calculation appendix | [`docs/deliverables/CMPE165_Project1_Calculations.xlsx`](docs/deliverables/CMPE165_Project1_Calculations.xlsx) |
| Analysis source of truth | [`analysis/`](analysis/) and [`analysis/outputs/`](analysis/outputs/) |
| Submission checklist | [`docs/SUBMISSION_CHECKLIST.md`](docs/SUBMISSION_CHECKLIST.md) |
| Loom demo script | [`docs/LOOM_SCRIPT.md`](docs/LOOM_SCRIPT.md) |
| Loom demo recording | Record separately (max 4 minutes). Not in this repository. |

## AI-Assisted Development

**Which AI coding tools the team used.** Cursor (agent-assisted editing and generation) for the Streamlit app, the SLA engine, the analysis scripts, the tests, and the first draft of the written deliverables. Occasional inline completion for boilerplate.

**What the AI helped us build.** Page layout and sidebar chrome; the realistic seed tickets; first-pass pytest cases; the matplotlib charts; the structure of the NPV, weighted-scoring, decision-tree, and Monte Carlo modules; the openpyxl code that writes live Excel formulas into the calculation workbook; and a large share of the report prose, which we then cut and rewrote against the numbers the scripts actually produce.

**Where AI-generated code did not work and we had to modify it.** Four real cases, in the order we hit them:

1. **Imports that could never resolve.** Streamlit puts the running file's own directory (`app/`) on `sys.path`, not the repository root, so generated imports of the form `from app import db` raised `ModuleNotFoundError`. The assistant kept "fixing" this by moving files around and flattening the package. The actual fix was an explicit root insertion at the top of `Home.py` and every file in `app/pages/`:

   ```python
   ROOT = Path(__file__).resolve().parents[1]   # parents[2] inside pages/
   if str(ROOT) not in sys.path:
       sys.path.insert(0, str(ROOT))
   ```

2. **A bug that silently corrupted the SLA metric.** Generated ticket-update logic stamped `resolved_at` when a ticket closed and never cleared it when the ticket was reopened. A reopened ticket therefore kept a frozen SLA clock, and the dashboard **under-counted breaches** — the kind of defect that looks fine on screen and quietly makes a management report wrong. The tests in [`tests/test_db.py`](tests/test_db.py) and [`tests/test_sla.py`](tests/test_sla.py) caught it; the generated code did not. `db.update_ticket` now clears `resolved_at` on any transition back to an open status.

3. **An API that no longer exists.** Generated financial code called `numpy.npv` and `numpy.irr`. NumPy dropped both from its top-level API years ago, so the module crashed on import of its own math. Rather than add a financial-library dependency for one number, we solve IRR by bisection in [`analysis/npv.py`](analysis/npv.py) (200 iterations over a bracketed root, returning `None` when no sign change exists).

4. **Confidently wrong dependency pins.** The first `requirements.txt` was generated with plausible-looking version numbers that did not match anything `pip` actually resolved, so a clean install failed. We regenerated the file from the versions really installed in the virtual environment.

**Important decisions the human team made rather than the AI.**

- **SLA is measured in support hours, not calendar hours.** The generated draft used a plain `timedelta`. That would mark a Low-priority ticket filed Friday at 17:00 "late" on Saturday morning, which is not how CTS staffs the desk. We wrote [`app/sla.py`](app/sla.py) to count only weekdays 08:00–18:00 and to skip campus holidays. This changed the dashboard numbers materially, and it is the difference between a metric the help desk would accept and one it would ignore.
- **The recommendation is GO WITH CONDITIONS, not GO.** Handed only the deterministic NPV of $179,670, generated text defaults to an unqualified GO. The Monte Carlo (27.3% chance of negative NPV, 44.1% chance of a budget overrun) and the decision tree (pilot EMV $98,300 beats build-now EMV $85,000) do not support that. We kept the conditions and the stop gate.

---

The quality of this project is not the complexity of the code. It is whether we can say, with numbers, whether CTS should keep investing. Our answer is yes — after a paid pilot, not before.
