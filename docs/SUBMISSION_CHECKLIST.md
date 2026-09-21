# CMPE 165 Project 1 — Submission Checklist

HelpDesk165. Use this page as the last pass before submitting on Canvas. Every
row points at a file that exists in this repository, or at a thing only a human
can do (marked **YOU**).

Re-verify the countable limits at any time:

```bash
python -m tools.report_stats     # word count, slide count, workbook sheets
python -m pytest -q              # 125 tests
python -m analysis.run_all       # regenerates every number the documents quote
```

---

## Part 1 — The five required deliverables

| # | Required deliverable | Requirement | Status | File / action |
|---|---|---|---|---|
| 1 | **Project report** | Under 5,000 words | Ready — 4,634 words of prose, headings, and captions (4,312 body prose). Table cells add 903 more; word limits conventionally exclude tables. | [`deliverables/CMPE165_Project1_Report.docx`](deliverables/CMPE165_Project1_Report.docx) — submit this one. Markdown mirror: [`PROJECT_REPORT.md`](PROJECT_REPORT.md) |
| 2 | **GitHub repository URL** | Public, with README and AI reflection | Repo content ready; **push still required** | Paste `https://github.com/Seaphant/Help-Desk-165` into Canvas. See "What you still have to do" below. |
| 3 | **Loom demo URL** | Max 4 minutes, shows working software | Script ready; **recording still required** | [`LOOM_SCRIPT.md`](LOOM_SCRIPT.md) — timed, with the exact click path |
| 4 | **Calculation appendix** | Shows the arithmetic, not just answers | Ready — 9 sheets, live Excel formulas | [`deliverables/CMPE165_Project1_Calculations.xlsx`](deliverables/CMPE165_Project1_Calculations.xlsx) |
| 5 | **Class slides** | Maximum 4 slides | Ready — exactly 4, with speaker notes and per-slide time budgets | [`deliverables/CMPE165_Project1_Slides.pptx`](deliverables/CMPE165_Project1_Slides.pptx) |

The workbook is the one graders poke at. Click any weighted score, discount
factor, present value, or EMV cell and the formula bar shows the arithmetic;
change an assumption and the totals move.

---

## Part 2 — The 13 rubric rows (100 points)

| Rubric row | Pts | Answered in | Backed by code / data |
|---|---|---|---|
| 1. Problem, mission, strategy, stakeholders | 8 | Report Part A, Part B1 | — |
| 2. Organizational structure and culture | 7 | Report Part B2, B3 | — |
| 3. Project selection and weighted scoring | 8 | Report Part C, Table 3 | [`analysis/weighted_scoring.py`](../analysis/weighted_scoring.py) → [`part_c_weighted_scoring.csv`](../analysis/outputs/part_c_weighted_scoring.csv); workbook sheet *Part C Scoring* |
| 4. Financial analysis / NPV | 8 | Report Part D, Table 4 | [`analysis/npv.py`](../analysis/npv.py) → [`part_d_npv.csv`](../analysis/outputs/part_d_npv.csv); workbook sheet *Part D NPV* |
| 5. Leadership and ethics | 8 | Report Part E | — |
| 6. Team structure, conflict, negotiation | 8 | Report Part F, Part G, Table 5 | — |
| 7. Risk identification and risk register | 8 | Report Part H, Table 6 | [`analysis/risk_register.py`](../analysis/risk_register.py) → [`part_h_risk_register.csv`](../analysis/outputs/part_h_risk_register.csv); workbook sheet *Part H Risks* |
| 8. Decision-tree analysis | 8 | Report Part I | [`analysis/decision_tree.py`](../analysis/decision_tree.py) → [`part_i_decision_tree.csv`](../analysis/outputs/part_i_decision_tree.csv); workbook sheet *Part I Decision Tree* |
| 9. Monte Carlo analysis | 8 | Report Part J, Tables 7–9, Figures 1–3 | [`analysis/monte_carlo.py`](../analysis/monte_carlo.py) → three `part_j_*.csv` files + 4 PNG charts; workbook sheets *Part J Inputs / Results / Sensitivity* |
| 10. Working software prototype | 10 | Repository [`app/`](../app/) — `streamlit run app/Home.py` | 4 user interactions; 125 tests in [`tests/`](../tests/) |
| 11. GitHub repo and AI-development reflection | 5 | [`README.md`](../README.md) → section **AI-Assisted Development** | 4 concrete AI failures + 2 human decisions |
| 12. Loom demo | 5 | Recorded separately, max 4 min | [`LOOM_SCRIPT.md`](LOOM_SCRIPT.md) |
| 13. Final recommendation and classroom presentation | 7 | Report *Final recommendation*; 4-slide deck | Recommendation: **GO WITH CONDITIONS** |

The report's own reading guide ("Where each graded requirement is answered")
repeats this mapping, so a grader hits it on page one without hunting.

---

## Part 3 — Consistency spot-check

These numbers appear in the report, the slides, and the workbook. They all come
from `analysis/outputs/summary.json`, so they cannot disagree — but if you edit
any document by hand, re-check these five:

| Number | Value |
|---|---|
| Initial build cost | **$157,760** |
| Deterministic 4-year NPV | **$179,670** (ROI 113.9%, IRR 44.9%, payback in year 3) |
| Weighted scoring | Project **A 8.40** vs Project B 5.95 |
| Risk exposure | **$108,800** total; top three R3 $28,500 / R2 $18,900 / R5 $15,000 |
| Decision tree EMV | Pilot **$98,300** > build now $85,000 > license $72,750 |
| Monte Carlo (10,000 trials, seed 165) | Mean cost **$183,414**, P80 $208,011, **44.1%** over the $185,000 budget, mean NPV **$54,286**, **27.3%** chance NPV < 0 |

If you change an assumption, change it in [`analysis/assumptions.py`](../analysis/assumptions.py)
only, then re-run `python -m analysis.run_all` and rebuild the workbook. Do not
retype numbers into the documents.

---

## What you still have to do (**YOU** — cannot be automated)

- [ ] **Fill in teammate names in [`README.md`](../README.md).** There are
      placeholder lines reading `TEAMMATE 2 — ADD FULL NAME HERE`. Replace them
      with real names and delete any extras. The rubric expects every team
      member listed.
- [ ] **Push the repository to GitHub.** No GitHub credentials exist in the
      build environment, so this has to happen from your own machine. Use the
      prepared bundle: open `HelpDesk165-github-upload`, double-click
      **`PUSH_TO_GITHUB.bat`** (Windows) or run **`./push_to_github.sh`**
      (WSL / macOS / Linux), and sign in to GitHub when the browser opens. See
      `README_UPLOAD.md` in that folder.
- [ ] **Confirm the repository is public** at
      <https://github.com/Seaphant/Help-Desk-165> — open it in a private
      browser window. A private repo scores zero on rubric row 11.
- [ ] **Record the Loom**, max 4 minutes, following
      [`LOOM_SCRIPT.md`](LOOM_SCRIPT.md). Reseed the sample data from the
      sidebar first. Set the Loom link sharing to "anyone with the link".
- [ ] **Decide who speaks on each slide.** The speaker notes in the deck carry
      per-slide time budgets; the assignment expects every team member to talk.
      Write the names into the notes.
- [ ] **Submit on Canvas**: the `.docx`, the `.pptx`, the `.xlsx`, the GitHub
      URL, and the Loom URL. Five items.

## Ready-to-submit file paths

Copies of the three editable deliverables, plus a PDF preview of the deck, are in
`~/Downloads`:

```
CMPE165_Project1_Report.docx
CMPE165_Project1_Slides.pptx
CMPE165_Project1_Slides_preview.pdf     (preview only — do not submit)
CMPE165_Project1_Calculations.xlsx
HelpDesk165-github-upload/              (the one-click GitHub push)
HelpDesk165-github-upload.zip           (same thing, zipped, as a fallback)
```
