# Discord handoff message — HelpDesk165

Paste each block below into Discord as its own message. The `--- MESSAGE n of N ---`
lines are cut markers only — do **not** paste them.

--- MESSAGE 1 of 9 (1285 characters) ---

**CMPE 165 Project 1 — what's left and who does what**

Everything is built, tested and pushed. Repo: <https://github.com/Seaphant/Help-Desk-165>
**Due Tuesday, September 22, 2026 at 11:59pm on Canvas.**

There are 5 things blocking us, and none of them are code:
1. **Your names.** 3 placeholder lines in `README.md`, plus 1 red marker on the report cover inside the .docx.
2. **Who speaks on which slide.** All 4 slides have an unfilled `SPEAKER: [member N]` slot in the notes.
3. **The Loom.** Not recorded yet, 4 minute max. Click path is below, one person can do it in 20 minutes.
4. **Loom sharing set to "anyone with the link"** — if the grader hits a permission wall that row scores 0.
5. **Uploading all 5 items to Canvas** before the deadline.

Nice to have, won't cost us points on their own:
- Matching the names in `docs/PROJECT_REPORT.md` line 17. That's only the markdown mirror; the .docx is the graded file.
- Ticking the 4 remaining boxes in `docs/SUBMISSION_CHECKLIST.md`.
- Re-running `python -m pytest -q` before we submit, just to be sure.

The long version of all of this is in the repo at `docs/TEAM_HANDOFF.md`.

Coming in the next 8 messages: exact placeholder text (2), slides + two traps (3), how to run it (4-5), the Loom click path (6-8), Canvas list (9).

--- MESSAGE 2 of 9 (1201 characters) ---

**Exact text you need to replace — part 1**

I grepped the whole repo and also opened the Word and PowerPoint files with python-docx / python-pptx, because Office files are zipped and a normal search can't see inside them. **9 literal placeholders across 4 files.** The Excel workbook is clean, nothing to do there.

**`README.md`, lines 12 to 14** — three bullets:
```
`TEAMMATE 2 — ADD FULL NAME HERE`
`TEAMMATE 3 — ADD FULL NAME HERE`
`TEAMMATE 4 — ADD FULL NAME HERE`
```
Replace each with the same format as the first bullet:
`- **Full Name** — GitHub: [handle](https://github.com/handle)`

Delete line 14 entirely if we're only three people. Then delete the two-line note directly underneath (lines 16-17) that explains the placeholders — it shouldn't survive into the submission.

**`docs/deliverables/CMPE165_Project1_Report.docx`** — cover page, the `Team:` line. It's **bold dark red** so you genuinely can't miss it:
```
ADD REMAINING TEAMMATE NAMES HERE BEFORE SUBMITTING
```
Click it, type our names after "W. Nguyen (github.com/Seaphant) ·", then set the colour back to black and un-bold it.

**`docs/PROJECT_REPORT.md`, line 17** has the identical marker. Lower priority, see message 1.

--- MESSAGE 3 of 9 (1550 characters) ---

**Exact text you need to replace — part 2, the slides**

`docs/deliverables/CMPE165_Project1_Slides.pptx`. Open each slide's **speaker notes**; the placeholder is the first line of each:
```
Slide 1  What Did We Build and Why?  0:00-1:00  SPEAKER: [member 1]
Slide 2  How Did We Execute?         1:00-2:00  SPEAKER: [member 2]
Slide 3  What Could Go Wrong?        2:00-3:00  SPEAKER: [member 3]
Slide 4  Should We Continue?         3:00-4:00  SPEAKER: [member 4]
```
Put your name over `[member N]`. One minute each and the rubric expects all of us to speak. If we're only three, the slide 4 note already says to split that slide between two people.

What each minute has to land:
- **Slide 1** — open with the concrete story (projector dies in BBC 202, nobody owns the request), one sentence on strategy. Don't demo here.
- **Slide 2** — process, not code. The conflict and the AI lesson. Say out loud that we separated SUBMIT from TRIAGE.
- **Slide 3** — don't read the risk register. Six words per risk, then spend the minute on the Monte Carlo chart.
- **Slide 4** — recommendation in the first 3 seconds, then justify it. Hard stop at 4:00.

Two traps that will silently undo your edits:
1. **Don't run `tools.polish_report` or `tools.polish_slides` after you've typed names in.** Those scripts rewrite the .docx and .pptx in place and put the placeholders straight back. Edit the Office files last.
2. `docs/PROJECT_REPORT.md` is generated from the .docx. Fix the Word file first, or your markdown fix gets thrown away next time it regenerates.

--- MESSAGE 4 of 9 (1078 characters) ---

**How to run it — I tested every command below from a clean clone**

I cloned the public repo anonymously into an empty folder and actually ran all of this, so these are verified, not guessed. You need **Python 3.12** (3.11 should work too; I tested on 3.12.3) and git. Nothing else — no database to install, no API keys, no .env file.

```
git clone https://github.com/Seaphant/Help-Desk-165.git
cd Help-Desk-165
```

**macOS / Linux:**
```
python3 -m venv .venv
source .venv/bin/activate
```
**Windows PowerShell:**
```
python -m venv .venv
.venv\Scripts\Activate.ps1
```
(Windows cmd instead of PowerShell: `.venv\Scripts\activate.bat`)

Then identical on every platform:
```
pip install -r requirements.txt
streamlit run app/Home.py
```

**No database setup at all.** The first page load creates `data/helpdesk.db` by itself and seeds it — you get a banner saying "First run detected, so the database was seeded with 62 sample tickets" and the dashboard fills in with 21 open, 3 unassigned, 19 SLA breaches, 78.0% compliance. `python -m pytest -q` gives 125 passed in 2.35s.

--- MESSAGE 5 of 9 (1247 characters) ---

**Running it — the caveats, all of these actually happened to me**

- **It serves on port 43117, not 8501.** `.streamlit/config.toml` is committed and pins that port, so the default is overridden. The README and the Loom script both still say 8501 — ignore them and trust whatever the terminal prints.
- **The browser won't open by itself.** That same config has headless mode on, so Streamlit just prints the URL and waits. Click or paste it.
- **If the port is busy** Streamlit doesn't fall back, it prints `Port 43117 is not available` and quits. Fix: `streamlit run app/Home.py --server.port 8599`, or any free port.
- **The first install takes a few minutes** on a normal home connection. It's 51 packages and about 560MB of virtualenv, mostly pyarrow, numpy, pandas and matplotlib. It is not frozen, let it finish.
- **PowerShell may refuse to activate** with "running scripts is disabled on this system". Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that same window, then activate again.
- On mac and most Linux there's no bare `python`, only `python3`. Inside the activated venv both work.
- Streamlit logs a `use_container_width` deprecation warning at startup. Cosmetic, ignore it.

Stop the server with `Ctrl+C`.

--- MESSAGE 6 of 9 (1810 characters) ---

**Loom click path — setup and the first 75 seconds**

**4 minute hard cap**, aim to land at 3:50. The assignment says not to spend the recording showing source code, so the only time we touch the repo is ~10 seconds of README near the end. Word-for-word narration is in `docs/LOOM_SCRIPT.md`.

**Before you record:**
1. Start the app, open the URL it prints.
2. **Sidebar → expand `Reset sample data` → click `Reseed database`.** Do this first on *every* take. It rebuilds from a fixed seed so you get the same 62 tickets and the same ticket numbers each time. Skip it and take 2 won't match take 1.
3. Sidebar `Signed in as` = **Agent** (it defaults there). Name/email should read Priya Raman / priya.raman@sjsu.edu.
4. Fullscreen, 100% zoom, close other tabs, notifications off. Record screen + mic, no webcam bubble over the charts.
5. Have two extra tabs ready: the GitHub repo, and the deck on slide 3.

**0:00-0:30 — the problem.** Screen: the **Overview** page. 24,000 campus tech requests a year living in a shared inbox and three spreadsheets; nobody can say who owns a ticket or whether we're hitting SLA. One queue, one clock, one dashboard. Then preview the three things you're about to show. **Don't read the KPI tiles aloud.**

**0:30-1:15 — Action 1, submit a ticket.** Sidebar → **Submit a ticket**.
- Short summary: `Projector in BBC 202 shows no signal from HDMI`
- Details: `Started this morning. Laptop detects a second display but the projector shows No Signal on both HDMI cables. Class of 40 at 10:30.`
- Category → `Classroom Technology`, Priority → `High` (pause half a second on the caption that appears), then **Submit ticket**.
- **Point at the Response target line.** The point: picking High set an 8-support-hour target instantly, and the requester walks away with ticket **#63**.

--- MESSAGE 7 of 9 (1387 characters) ---

**Loom click path — 1:15 to 2:45, the two required user actions**

**1:15-2:10 — Action 2, work the queue.** Sidebar → **Ticket queue**.
- **View** dropdown (top right of the filter card) → **SLA trouble**. The table collapses and the Breached metric jumps.
- **View** → back to **Open work**, then → **Needs an owner**. Three unassigned tickets left.
- **Search** box → type `projector`, show it finding your new ticket, then clear it.
- Scroll to **Open a ticket** → pick **#47 · Document camera not detected by podium PC**.
- In the **Update** panel: Status → `In Progress`, Owner → `Priya Raman`.
- Work note: `Swapped the USB cable and confirmed the camera enumerates. Driver reinstall scheduled with the instructor for 3pm.` → **Save update**.
- Scroll to **Activity**, point at the two new field-change lines and your note, **let it breathe two seconds** — this is the bit that sells it. Mention the SLA panel counts support hours, weekdays 8-6, not calendar hours.

**2:10-2:45 — Action 3, the manager view.** Sidebar → **SLA dashboard**. Leave the window on **Last 30 days**. Hover a bar in **Open load by owner** so the tooltip shows the breached count. Scroll to **Tickets past their SLA target**. Click **Download report (CSV)** — the download chip is the proof. Worth saying: the CSV has the same columns as the screen, so a number in a meeting deck traces back to a ticket.

--- MESSAGE 8 of 9 (1279 characters) ---

**Loom click path — 2:45 to 4:00, and what to cut if you run long**

**2:45-3:30 — how we built it + one thing that went wrong.** Switch to the GitHub tab, scroll the README to **AI-Assisted Development**. Stack in one breath: Python, Streamlit, SQLite, pandas, Altair, 125 tests. Then the story: AI-generated code stamped `resolved_at` on close and never cleared it on reopen, so reopened tickets had a frozen SLA clock and the dashboard **under-counted breaches**. Looked completely fine on screen. A unit test caught it, not a human. Lesson: AI code fails quietly in business logic, not loudly at the syntax level.

**3:30-4:00 — what's next.** Switch to slide 3, the Monte Carlo chart. Straight NPV says easy yes, ~$180K over four years on a ~$158K build. 10,000 trials say expected NPV ~$54K, 27% chance it never pays back, 44% chance we blow the budget. Adoption is the swing variable, not code. So: **go, with conditions** — an 8-week paid pilot at $98K expected value vs $85K for building everything now. Thanks, stop.

**If you're long, cut in this order:** the keyword search (~8s), the dashboard tooltip (~6s), the "Needs an owner" view. **Never cut** submitting the ticket, the assign + work note, the CSV export, or the AI failure story — those are the graded parts.

--- MESSAGE 9 of 9 (1369 characters) ---

**Canvas submission — 5 items, due Tue Sep 22 2026 11:59pm**

All five go in the same submission:
1. **Project report** — `CMPE165_Project1_Report.docx` (216KB, 4,634 words, limit is 5,000)
2. **GitHub URL** — paste `https://github.com/Seaphant/Help-Desk-165`
3. **Loom URL** — from the recording, max 4 min, sharing open
4. **Calculation appendix** — `CMPE165_Project1_Calculations.xlsx` (26KB, 9 sheets of live Excel formulas)
5. **Class slides** — `CMPE165_Project1_Slides.pptx` (122KB, exactly 4 slides)

Direct downloads if you don't want to clone the repo (I checked all three, they work):
<https://github.com/Seaphant/Help-Desk-165/raw/main/docs/deliverables/CMPE165_Project1_Report.docx>
<https://github.com/Seaphant/Help-Desk-165/raw/main/docs/deliverables/CMPE165_Project1_Slides.pptx>
<https://github.com/Seaphant/Help-Desk-165/raw/main/docs/deliverables/CMPE165_Project1_Calculations.xlsx>

**One rule before you edit anything:** every number in the report, the slides and the workbook is read back from `analysis/outputs/summary.json`, which is why they can't contradict each other. If you retype a number by hand you break that. **Names only.** If an assumption genuinely needs to change it goes in `analysis/assumptions.py` and then `python -m analysis.run_all`.

Grab a slide, put your name in the README and the .docx, and shout if the app won't start.

