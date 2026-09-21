# Loom demo script — HelpDesk165

**Hard limit: 4 minutes.** Loom's free tier cuts at 5, and the rubric caps at 4.
Aim to land at **3:50** so you have margin.

---

## Before you hit record

1. **Start the app** from the repository root:

   ```bash
   streamlit run app/Home.py
   ```

   Open the URL Streamlit prints (normally <http://localhost:8501>).

2. **Reseed the sample data.** In the sidebar, expand **Reset sample data** and
   click **Reseed database**. This is the single most important setup step — it
   rebuilds the database from `random.seed(165)` so you get exactly 62 tickets
   and the same ticket numbers every take. If you re-record, reseed again.

3. **Set the sidebar role to `Agent`** (it defaults there). The name and email
   fields should read *Priya Raman / priya.raman@sjsu.edu*.

4. **Browser housekeeping:** full-screen the window, zoom to 100%, close other
   tabs, hide your bookmarks bar, and silence notifications. Record **screen +
   microphone**, no webcam bubble over the dashboard charts.

5. **Have these two tabs ready** so segment 3 is a click, not a hunt:
   - the GitHub repo: <https://github.com/Seaphant/Help-Desk-165>
   - `docs/deliverables/CMPE165_Project1_Slides.pptx` on slide 3 (the Monte
     Carlo chart), or the PDF preview

6. **One take, one voice per segment.** If more than one teammate speaks, decide
   the handoffs now and write them in the margin.

> Ticket **numbers** below are stable after a reseed. The "hours late" figures
> drift with the wall clock, so read whatever is on screen rather than the
> numbers printed here.

---

## 0:00 – 0:30 · The problem *(30 s)*

**Screen:** the HelpDesk165 **Overview** page, already loaded.

> "SJSU Campus Technology Services takes about twenty-four thousand technology
> requests a year — Wi-Fi, classroom projectors, Canvas, accounts — and today
> they live in
> a shared inbox and three spreadsheets. Nobody can answer two basic questions:
> who owns this ticket right now, and are we hitting our service-level target?
> This is HelpDesk165. One queue, one clock, one dashboard. I'll show you a
> request going in, an agent working it, and the management view that comes out —
> then what our numbers say about funding it."

**Do not** read the KPI tiles aloud. Let them sit on screen while you talk.

---

## 0:30 – 2:45 · Product demo *(2 min 15 s — the biggest block, and the rubric's)*

### Action 1 — Submit a ticket *(0:30 – 1:15, about 45 s)*

**Click path:**

1. Sidebar → **Submit a ticket**
2. **Short summary:** `Projector in BBC 202 shows no signal from HDMI`
3. **Details:** `Started this morning. Laptop detects a second display but the
   projector shows No Signal on both HDMI cables. Class of 40 at 10:30.`
4. **Category** → `Classroom Technology`
5. **Priority** → `High` — pause half a second on the caption that appears
6. **Submit ticket**

> "A requester describes the problem once. The category and priority aren't
> decoration — as soon as I pick High, the form tells me the response target is
> eight support hours. Submit, and it comes back with ticket number
> sixty-three and a status of New. That tracking number is the thing the shared
> inbox could never give anyone."

The confirmation panel below the form shows the ticket, its priority, and the
response target. Point at the **Response target** line.

### Action 2 — Work the queue *(1:15 – 2:10, about 55 s)*

**Click path:**

1. Sidebar → **Ticket queue**
2. In the **View** dropdown (top right of the filter card) choose **SLA
   trouble** — the table collapses to breached and at-risk tickets and the
   **Breached** metric jumps
3. Switch **View** back to **Open work**, then choose **Needs an owner** — three
   unassigned tickets remain
4. In the **Search** box type `projector` to show keyword search finding your new
   ticket, then clear it
5. Scroll to **Open a ticket** and pick **#47 · Document camera not detected by
   podium PC**
6. In the **Update** panel on the right: **Status** → `In Progress`, **Owner** →
   `Priya Raman`
7. **Work note:** `Swapped the USB cable and confirmed the camera enumerates.
   Driver reinstall scheduled with the instructor for 3pm.`
8. **Save update**

> "This is the agent's day. Saved views answer 'what's late' and 'what has no
> owner' without writing a filter. I'll take this document-camera ticket, move
> it to In Progress, assign it to myself, and log what I actually did. Notice
> the SLA panel — it counts *support hours*, weekdays eight to six, not calendar
> hours. And every change I just made is written to the activity trail
> underneath, so there's an audit history instead of a forwarded email chain."

After saving, scroll to the **Activity** list and point at the two new
field-change lines and your note. **This is the moment that sells the product —
let it breathe for two seconds.**

### Action 3 — The management view *(2:10 – 2:45, about 35 s)*

**Click path:**

1. Sidebar → **SLA dashboard**
2. Leave the window at **Last 30 days**
3. Hover one bar in **Open load by owner** so the tooltip shows the breached
   count
4. Scroll to **Tickets past their SLA target**
5. Click **Download report (CSV)** — the browser's download chip is the proof

> "Same data, manager's question. Where volume comes from, where the SLA is
> slipping by priority, who's overloaded — and hovering shows how many of each
> person's tickets are already late. The breach table is the monthly service
> review agenda, and the CSV export has the same columns as the screen, so a
> number in a meeting deck traces back to a ticket."

---

## 2:45 – 3:30 · How we built it, and one thing that went wrong *(45 s)*

**Screen:** switch to the GitHub tab, scroll the README to
**AI-Assisted Development**.

> "Python, Streamlit, SQLite, pandas, and Altair, with a hundred and twenty-five
> tests. We built it with AI assistance and the README documents where that
> helped and where it didn't.
>
> The failure worth your time: the generated ticket-update code stamped a
> resolved timestamp when a ticket closed, and never cleared it when a ticket
> was reopened. So a reopened ticket had a frozen SLA clock, and the dashboard
> you just saw **under-counted breaches**. It looked completely fine on screen.
> A unit test caught it, not a human reading the code — and that's the lesson:
> AI-generated code fails quietly in the business logic, not loudly at the
> syntax level.
>
> The call we made against the AI's default was the SLA clock itself. The
> generated version used a plain timedelta, which would mark a low-priority
> ticket filed Friday at five 'late' on Saturday morning. Nobody staffs the desk
> on Saturday, so we wrote a support-hour calendar instead."

---

## 3:30 – 4:00 · What comes next *(30 s)*

**Screen:** switch to slide 3 of the deck — the Monte Carlo cost chart.

> "Should the campus fund this? A straight net-present-value calculation says an
> easy yes — a hundred and eighty thousand dollars over four years on a hundred
> fifty-eight thousand dollar build. But ten thousand Monte Carlo trials say
> expected NPV is about fifty-four thousand, there's a twenty-seven percent
> chance it never pays back, and a forty-four percent chance we blow through the
> budget. Adoption is the swing variable, not code.
>
> So our recommendation is **go, with conditions**: fund an eight-week paid
> pilot, which the decision tree prices at ninety-eight thousand expected value
> against eighty-five for building everything now. Next up is real
> authentication, Banner integration, and the two risks the register prices
> highest. Thanks for watching."

---

## Timing card — tape this next to your monitor

| Clock | Segment | Screen |
|---|---|---|
| 0:00 | Problem | Overview page |
| 0:30 | Submit a ticket | Submit a ticket |
| 1:15 | Work the queue (filter → assign → note) | Ticket queue |
| 2:10 | Management view + CSV export | SLA dashboard |
| 2:45 | Stack, AI reflection, the reopened-ticket bug | GitHub README |
| 3:30 | Monte Carlo, GO WITH CONDITIONS, next steps | Slide 3 |
| 3:50 | Stop talking | — |

## If you are running long

Cut in this order — the first two cost you nothing on the rubric:

1. The keyword search in step 4 of Action 2 (saves ~8 s).
2. The tooltip hover on the dashboard (saves ~6 s).
3. The "Needs an owner" view; keep "SLA trouble", which is the better story.

**Never cut:** submitting the ticket, assigning it with a work note, the CSV
export, or the AI-failure story. Those are the graded parts — two user actions
minimum, and the AI reflection.
