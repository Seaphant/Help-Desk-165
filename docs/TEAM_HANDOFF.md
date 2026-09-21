# Team handoff — CMPE 165 Project 1 (HelpDesk165)

Everything a teammate needs to finish this submission, written for someone who
has never opened the repository. Nothing here changes the report, the analysis,
or any number — it only tells you what is still blank and how to run the thing.

**Hard deadline: Tuesday, September 22, 2026, 11:59 pm, submitted on Canvas.**

- Repository: <https://github.com/Seaphant/Help-Desk-165>
- Instructor: Dhruba Borthakur
- Recommendation the whole submission defends: **GO WITH CONDITIONS**

---

## 1. Every placeholder that a human still has to fill in

This list was produced by grepping the whole working tree case-insensitively for
`TODO`, `TBD`, `ADD `, `PLACEHOLDER`, `TEAMMATE`, `[member`, `XXX`, `FILL`,
`YOUR NAME`, and angle brackets, and by reading the `.docx`, `.pptx`, and
`.xlsx` with `python-docx` / `python-pptx` / `openpyxl` (Office XML is zipped, so
a plain grep cannot see inside it). **Nine literal placeholders in four files,
plus four unchecked human tasks.**

### 1a. Literal placeholder text

| # | File | Line / location | Exact literal text | Instances | What to change | Who |
|---|---|---|---|---|---|---|
| 1 | `README.md` | line 12 | `` `TEAMMATE 2 — ADD FULL NAME HERE` *(placeholder — replace before Canvas submission)* `` | 1 | Replace the whole bullet with `- **Full Name** — GitHub: [handle](https://github.com/handle)` | Teammate 2 |
| 2 | `README.md` | line 13 | `` `TEAMMATE 3 — ADD FULL NAME HERE` *(placeholder — replace before Canvas submission)* `` | 1 | Same | Teammate 3 |
| 3 | `README.md` | line 14 | `` `TEAMMATE 4 — ADD FULL NAME HERE` *(placeholder — delete this line if the team is smaller)* `` | 1 | Same, **or delete the line** if there is no fourth member | Teammate 4 |
| 4 | `README.md` | lines 16–17 | `> The assignment expects every team member's name on the README. Delete the placeholder` / `> lines that do not apply and fill in the rest.` | 1 block | Delete the whole two-line blockquote once names are in | Whoever edits the README |
| 5 | `docs/PROJECT_REPORT.md` | line 17 | `**Team:** W. Nguyen (github.com/Seaphant) · **ADD REMAINING TEAMMATE NAMES HERE BEFORE SUBMITTING**` | 1 | Replace the bold marker with the remaining names, comma separated | One person, then tell the rest |
| 6 | `docs/deliverables/CMPE165_Project1_Report.docx` | cover page, paragraph 8 (the `Team:` line) | `ADD REMAINING TEAMMATE NAMES HERE BEFORE SUBMITTING` — a **bold, dark-red** run so you cannot miss it | 1 | Open in Word, click the red text, type the names, set the colour back to black and un-bold | Same person as #5 |
| 7 | `docs/deliverables/CMPE165_Project1_Slides.pptx` | slide 1 speaker notes, first line | `TIME: 0:00-1:00 (60 seconds). SPEAKER: [member 1].` | 1 | Replace `[member 1]` with a real name | Slide 1 speaker |
| 8 | `docs/deliverables/CMPE165_Project1_Slides.pptx` | slide 2 speaker notes, first line | `TIME: 1:00-2:00 (60 seconds). SPEAKER: [member 2].` | 1 | Replace `[member 2]` with a real name | Slide 2 speaker |
| 9 | `docs/deliverables/CMPE165_Project1_Slides.pptx` | slide 3 speaker notes, first line | `TIME: 2:00-3:00 (60 seconds). SPEAKER: [member 3].` | 1 | Replace `[member 3]` with a real name | Slide 3 speaker |
| 10 | `docs/deliverables/CMPE165_Project1_Slides.pptx` | slide 4 speaker notes, first line | `TIME: 3:00-4:00 (60 seconds). SPEAKER: [member 4]. If the team has fewer than four members, split this slide between two speakers so everyone presents.` | 1 | Replace `[member 4]`; if the team is smaller, name the two people who split it | Slide 4 speaker |

The `.xlsx` calculation workbook has **zero** placeholders. Nothing to fill in
there. The only `<` / `>` occurrences anywhere in the Markdown are autolinks like
`<https://github.com/Seaphant/Help-Desk-165>`, not fill-in slots.

### 1b. Unchecked human tasks in `docs/SUBMISSION_CHECKLIST.md`

Four `- [ ]` boxes remain. Tick them as you go.

| Line | Task | Blocking? |
|---|---|---|
| 80 | Fill in teammate names in `README.md` | **Yes** — rubric row 11 |
| 94 | Record the Loom, max 4 minutes, sharing set to "anyone with the link" | **Yes** — rubric row 12, and it is a Canvas field |
| 97 | Decide who speaks on each slide and write the names into the speaker notes | **Yes** — rubric row 13 expects everyone to talk |
| 100 | Submit on Canvas: `.docx`, `.pptx`, `.xlsx`, GitHub URL, Loom URL | **Yes** |

`docs/LOOM_SCRIPT.md` has no literal placeholder, but step 6 of *Before you hit
record* ("decide the handoffs now and write them in the margin") is a decision
someone has to make before recording.

### 1c. Two traps that will silently undo your edits

1. **Do not re-run `python -m tools.polish_report` or `python -m tools.polish_slides`
   after you type the names in.** Those scripts rewrite the `.docx` and `.pptx`
   in place and re-insert the placeholders verbatim — the red `ADD REMAINING
   TEAMMATE NAMES HERE BEFORE SUBMITTING` run is written by `annotate_cover()` in
   `tools/polish_report.py`, and the `SPEAKER: [member N]` lines are written by
   `tools/polish_slides.py`. Edit the Office files last, or edit the strings in
   those two scripts instead of the documents.
2. **`docs/PROJECT_REPORT.md` is generated from the `.docx`**, via
   `python -m tools.docx_to_markdown`. If you fix the Markdown but not the Word
   file, the next regeneration throws your fix away. Fix the `.docx` first, then
   regenerate the Markdown if you want them identical.

---

## 2. Setup runbook (verified end to end, not guessed)

Verified on 2026-09-21 by cloning the public repo into an empty temp directory as
an anonymous user and running every command below. Results are in section 2d.

### 2a. What you need first

- **Python 3.12** is what the project was developed against; the verification run
  used **Python 3.12.3**. Python 3.11 should also work. Anything older than 3.10
  will not — the code uses `from __future__ import annotations` with modern
  built-in generics.
- **Git**.
- Nothing else. No database server, no cloud account, no API keys, no `.env`
  file. The app uses a local SQLite file it creates for itself.

### 2b. The commands

```bash
git clone https://github.com/Seaphant/Help-Desk-165.git
cd Help-Desk-165
```

Create and activate the virtual environment. **The activation line differs by
operating system — this is the step people get wrong:**

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

```powershell
# Windows, PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

```bat
:: Windows, Command Prompt
python -m venv .venv
.venv\Scripts\activate.bat
```

Then, identically on every platform:

```bash
pip install -r requirements.txt
streamlit run app/Home.py
```

Open the URL Streamlit prints. Stop the server with `Ctrl+C`.

### 2c. Caveats, all of them real

- **The app serves on port 43117, not 8501.** `.streamlit/config.toml` is
  committed and pins `port = 43117`, so the verbatim command prints
  `Local URL: http://localhost:43117`. The README and `LOOM_SCRIPT.md` both still
  say 8501 — they are describing the Streamlit default, which the committed
  config overrides. Trust whatever the terminal prints.
- **The browser will not open by itself.** That same config sets
  `headless = true`, so Streamlit prints the URL and waits. Click or paste it.
- **Port already in use.** If something else holds 43117, Streamlit refuses to
  start and prints exactly `Port 43117 is not available`. Fix it with
  `streamlit run app/Home.py --server.port 8599` (any free port).
- **First install is the slow part.** `pip install -r requirements.txt` pulls 51
  packages and produces a ~560 MB virtual environment; `pyarrow`, `numpy`,
  `pandas`, and `matplotlib` are most of it. With a warm pip cache the
  verification run took 17 seconds, but on a clean machine over normal home
  internet expect a few minutes of downloading. It is not hung.
- **PowerShell may block activation** with "running scripts is disabled on this
  system." Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in
  that same window, then activate again.
- **On macOS and most Linux boxes there is no bare `python`, only `python3`.**
  Inside the activated venv both names work; outside it, use `python3`.
- Streamlit logs a `use_container_width` deprecation notice on startup. It is
  cosmetic. Ignore it.

### 2d. Verification results

| Step | Result |
|---|---|
| `git clone` of the public repo, anonymous | Succeeded; `HEAD` = `49f2578`, identical to the working copy |
| `python3 -m venv .venv` | Succeeded, Python 3.12.3 |
| `pip install -r requirements.txt` | Succeeded, 51 packages, no build errors, no pin conflicts |
| `streamlit run app/Home.py` | Served on `http://localhost:43117`, HTTP 200 |
| Database bootstrap | `data/helpdesk.db` **did not exist** before first load and was created automatically on it. No migration, no import, no manual step. |
| Seed data | Banner: *"First run detected, so the database was seeded with 62 sample tickets."* Landing KPIs: 21 open, 3 unassigned, 19 SLA breaches, 78.0% compliance |
| `python -m pytest -q` | **125 passed in 2.35s** |
| The three deliverable download links | All HTTP 200 (see section 5) |

---

## 3. Loom runbook — the click-by-click path

**Cap is 4 minutes.** Aim to stop at 3:50. The assignment explicitly says not to
spend the recording walking through source code, so the only time you show the
repository is the ten seconds of README in segment 3. Full narration, including
the exact wording for each segment, is in `docs/LOOM_SCRIPT.md`; this is the
condensed click path to keep on a second monitor.

### Before you press record

1. Start the app: `streamlit run app/Home.py`, open `http://localhost:43117`.
2. **Sidebar → expand `Reset sample data` → click `Reseed database`.** Do this
   first, every single take. It rebuilds the database from `random.seed(165)`,
   so you get exactly 62 tickets with the same ticket numbers each time — which
   is why the ticket numbers below are safe to rely on. Skip it and your
   second take will not match your first.
3. Sidebar → `Signed in as` = **Agent** (it defaults there). The name and email
   fields should read *Priya Raman / priya.raman@sjsu.edu*.
4. Full-screen the browser, zoom 100%, close other tabs, hide bookmarks, silence
   notifications. Record **screen + microphone**, no webcam bubble over the charts.
5. Open two extra tabs so segment 3 is a click and not a hunt: the GitHub repo,
   and the deck on slide 3 (the Monte Carlo chart).
6. Ticket *numbers* are stable after a reseed. The "hours late" figures move with
   the wall clock — read whatever is on screen, do not memorise a number.

### 0:00–0:30 · The problem

- **Screen:** the **Overview** page, already loaded.
- Say: 24,000 campus tech requests a year, living in a shared inbox and three
  spreadsheets; nobody can say who owns a ticket or whether the SLA is being hit.
  HelpDesk165 is one queue, one clock, one dashboard.
- Preview what is coming: a request going in, an agent working it, the management
  view, then what the numbers say about funding it.
- **Do not** read the KPI tiles aloud. Let them sit on screen.

### 0:30–1:15 · Action 1, submit a ticket

- Sidebar → **Submit a ticket**
- **Short summary:** `Projector in BBC 202 shows no signal from HDMI`
- **Details:** `Started this morning. Laptop detects a second display but the projector shows No Signal on both HDMI cables. Class of 40 at 10:30.`
- **Category** → `Classroom Technology`
- **Priority** → `High` — pause half a second on the caption that appears
- Click **Submit ticket**
- **Point at** the **Response target** line in the confirmation panel. The point
  to make out loud: picking High immediately set an eight-support-hour target,
  and the requester walks away with ticket **#63**, a tracking number the shared
  inbox could never give them.

### 1:15–2:10 · Action 2, work the queue

- Sidebar → **Ticket queue**
- **View** dropdown (top right of the filter card) → **SLA trouble**. The table
  collapses to breached and at-risk tickets and the **Breached** metric jumps.
- **View** → back to **Open work**, then → **Needs an owner**. Three unassigned
  tickets remain.
- **Search** box → type `projector`, show it finding your new ticket, then clear it.
- Scroll to **Open a ticket** → select **#47 · Document camera not detected by
  podium PC**
- In the **Update** panel: **Status** → `In Progress`, **Owner** → `Priya Raman`
- **Work note:** `Swapped the USB cable and confirmed the camera enumerates. Driver reinstall scheduled with the instructor for 3pm.`
- Click **Save update**
- Scroll to **Activity** and **point at** the two new field-change lines and your
  note. **Let this breathe for two seconds — it is the moment that sells the
  product.** Mention that the SLA panel counts *support hours*, weekdays 08:00 to
  18:00, not calendar hours.

### 2:10–2:45 · Action 3, the management view

- Sidebar → **SLA dashboard**
- Leave **Reporting window** on **Last 30 days**
- Hover one bar in **Open load by owner** so the tooltip shows the breached count
- Scroll to **Tickets past their SLA target**
- Click **Download report (CSV)** — the browser's download chip is the proof
- Point out that the CSV has the same columns as the screen, so a number in a
  meeting deck traces back to a ticket.

### 2:45–3:30 · How we built it, and one thing that went wrong

- **Screen:** switch to the GitHub tab, scroll the README to
  **AI-Assisted Development**. Do not scroll through source files.
- Stack in one breath: Python, Streamlit, SQLite, pandas, Altair, 125 tests.
- The one challenge, told as a story: AI-generated update logic stamped
  `resolved_at` when a ticket closed and never cleared it on reopen, so a
  reopened ticket had a frozen SLA clock and the dashboard **under-counted
  breaches**. It looked completely fine on screen. A unit test caught it, not a
  human reading the code. The lesson: AI-generated code fails quietly in the
  business logic, not loudly at the syntax level.
- The call made against the AI's default: the support-hour SLA clock, because a
  plain `timedelta` would mark a Friday-5pm Low ticket late on Saturday morning
  and nobody staffs the desk on Saturday.

### 3:30–4:00 · What comes next

- **Screen:** slide 3 of the deck, the Monte Carlo cost chart.
- Deterministic NPV looks like an easy yes: ~$180K over four years on a ~$158K
  build. 10,000 trials say expected NPV is ~$54K, with a 27% chance it never pays
  back and a 44% chance of blowing the budget. Adoption is the swing variable,
  not code.
- Recommendation: **go, with conditions** — fund an eight-week paid pilot, which
  the decision tree prices at $98K expected value against $85K for building
  everything now. Next up: real authentication, Banner integration, and the two
  highest-priced risks.
- Thank them and stop.

### If you are running long

Cut in this order; the first two cost nothing on the rubric.

1. The keyword search in Action 2 (~8 s)
2. The dashboard tooltip hover (~6 s)
3. The "Needs an owner" view — keep "SLA trouble", it is the better story

**Never cut:** submitting the ticket, assigning it with a work note, the CSV
export, or the AI-failure story. Those are the graded parts — two user actions
minimum, plus the AI reflection.

Finally: set the Loom's sharing to **anyone with the link**, or the grader sees a
permission wall and rubric row 12 scores zero.

---

## 4. Slide speaker grid

Four slides, one minute each, and the assignment expects every member to talk.
Write the chosen name over `[member N]` in that slide's speaker notes.

| Slide | Title | Time budget | Notes slot to replace | Speaker | What this minute has to land |
|---|---|---|---|---|---|
| 1 | What Did We Build and Why? | 0:00–1:00 | `SPEAKER: [member 1]` | _____ | Open with the concrete story — a projector dies in BBC 202 and nobody owns the request. One sentence on strategy: CTS is funded on service quality, so a defensible SLA number *is* the strategy. **Do not demo here.** |
| 2 | How Did We Execute? | 1:00–2:00 | `SPEAKER: [member 2]` | _____ | Process, not code. Spend the words on the conflict and the vibe-coding lesson. Say explicitly that SUBMIT was separated from TRIAGE — a negotiation outcome, not a split-the-difference compromise. |
| 3 | What Could Go Wrong? | 2:00–3:00 | `SPEAKER: [member 3]` | _____ | Do not read the risk register; six words per risk, then spend the minute on the chart. Green dashed = estimate $157,760, red = 10,000-trial expectation $183,414, dotted = approved $185,000. The decision that changes: budget to the P80, ~$208,000. |
| 4 | Should We Continue? | 3:00–4:00 | `SPEAKER: [member 4]` | _____ | Recommendation in the first three seconds, then justify. Close on the stop gate: stopping at week eight is a *successful* use of this analysis. **HARD STOP at 4:00.** |

The slide 4 note already says it: if the team has fewer than four people, split
slide 4 between two speakers so everyone presents. Likely questions the deck
anticipates — "why not just buy ServiceNow?" (that is the slide 3 decision tree,
and it loses on EMV) and "did AI write the analysis?" (it wrote structure; the
team chose every assumption and the recommendation).

---

## 5. Canvas submission — five items

All five go in the same Canvas submission, due **Tuesday, September 22, 2026,
11:59 pm**.

| # | Deliverable | What to upload / paste | Requirement it satisfies |
|---|---|---|---|
| 1 | Project report | `docs/deliverables/CMPE165_Project1_Report.docx` (216 KB) | Under 5,000 words — currently 4,634 including headings and captions |
| 2 | GitHub repository URL | `https://github.com/Seaphant/Help-Desk-165` | Public, README present, AI reflection present |
| 3 | Loom demo URL | The link from your recording | Max 4 minutes, shows working software, link sharing open |
| 4 | Calculation appendix | `docs/deliverables/CMPE165_Project1_Calculations.xlsx` (26 KB) | 9 sheets of live Excel formulas, not pasted answers |
| 5 | Class slides | `docs/deliverables/CMPE165_Project1_Slides.pptx` (122 KB) | Exactly 4 slides |

Direct downloads, each verified HTTP 200:

- <https://github.com/Seaphant/Help-Desk-165/raw/main/docs/deliverables/CMPE165_Project1_Report.docx>
- <https://github.com/Seaphant/Help-Desk-165/raw/main/docs/deliverables/CMPE165_Project1_Slides.pptx>
- <https://github.com/Seaphant/Help-Desk-165/raw/main/docs/deliverables/CMPE165_Project1_Calculations.xlsx>

### Blocking vs nice-to-have

**Blocking — the submission is incomplete without these:**

1. Teammate names in `README.md` (3 placeholder lines)
2. Teammate names on the report cover, in the `.docx` (1 red marker)
3. Speaker names in all four slides' notes (4 `[member N]` slots)
4. The Loom recorded, under 4 minutes, sharing open
5. All five items actually attached in Canvas before 11:59 pm

**Nice-to-have — improves consistency, will not cost points on its own:**

- Matching the teammate names in `docs/PROJECT_REPORT.md` line 17 (the Markdown
  mirror; the graded artifact is the `.docx`)
- Ticking the four boxes in `docs/SUBMISSION_CHECKLIST.md`
- Re-running `python -m pytest -q` and `python -m analysis.run_all` before
  submitting, to confirm nothing drifted

### Do not touch

Every figure in the report, the slides, and the workbook is read back from
`analysis/outputs/summary.json`, so the documents cannot disagree with each
other. If you retype a number by hand you break that guarantee. If an assumption
genuinely needs to change, change it in `analysis/assumptions.py` and re-run
`python -m analysis.run_all`. Otherwise: names only.
