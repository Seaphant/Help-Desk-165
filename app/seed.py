"""Generate realistic sample data for HelpDesk165.

The seed is deterministic (``random.seed(165)``) so screenshots, the dashboard
numbers, and the tests stay reproducible, but ticket timestamps are anchored to
the current date so a freshly cloned repo shows a live-looking queue instead of
a wall of stale tickets.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from app import db, sla

RANDOM_SEED = 165
DEFAULT_TICKET_COUNT = 62
HISTORY_DAYS = 45

AGENTS = [
    ("Priya Raman", "Tier 1 Support"),
    ("Marcus Webb", "Tier 1 Support"),
    ("Lena Ortiz", "Tier 2 Support"),
    ("Daniel Cho", "Tier 2 Support"),
    ("Aisha Bello", "Classroom Technology"),
    ("Tom Fitzgerald", "Identity & Access"),
]

# Realistic ticket templates per category: (title, description)
TICKET_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "Account & Login": [
        (
            "Cannot log in to MySJSU after password reset",
            "I reset my password last night and now MySJSU says my credentials are "
            "invalid. Duo still sends a push, but the portal rejects the login.",
        ),
        (
            "Duo push notifications never arrive",
            "My phone stopped receiving Duo prompts this morning. I reinstalled the "
            "app and re-scanned the QR code with no change.",
        ),
        (
            "Account locked after too many attempts",
            "I was locked out after mistyping my password. The self-service unlock "
            "page returns an internal error.",
        ),
        (
            "Need access to the shared department drive",
            "I transferred into the Mechanical Engineering department and still "
            "cannot open the shared ME-Faculty folder.",
        ),
    ],
    "Wi-Fi & Network": [
        (
            "eduroam drops every few minutes in Engineering 285",
            "My laptop disconnects from eduroam roughly every five minutes in "
            "ENGR 285. Other buildings are fine.",
        ),
        (
            "Cannot reach the VPN from off campus",
            "The GlobalProtect client connects and then immediately disconnects "
            "with a gateway timeout when I work from home.",
        ),
        (
            "Slow network in the library basement study rooms",
            "Download speeds in the lower-level study rooms are under 1 Mbps during "
            "afternoon hours.",
        ),
        (
            "Guest Wi-Fi registration page will not load",
            "Visitors for the industry advisory board meeting cannot reach the guest "
            "network sign-up page.",
        ),
    ],
    "Hardware": [
        (
            "Loaner laptop will not power on",
            "The loaner ThinkPad from the library checkout desk shows no lights when "
            "plugged in. I have tried two different chargers.",
        ),
        (
            "Office monitor flickers and loses signal",
            "My second monitor flickers roughly once a minute and occasionally drops "
            "to a no-signal message.",
        ),
        (
            "Lab workstation fails POST with three beeps",
            "Workstation 12 in the CMPE lab beeps three times on startup and never "
            "reaches the login screen.",
        ),
        (
            "Docking station no longer charges laptop",
            "The dock passes video through but stopped charging after the last "
            "firmware update.",
        ),
    ],
    "Classroom Technology": [
        (
            "Projector in BBC 202 shows no signal from HDMI",
            "The ceiling projector will not pick up HDMI from the podium PC or from "
            "my laptop. Class starts at 10:30.",
        ),
        (
            "Lecture capture did not record Tuesday session",
            "My Tuesday CMPE 165 lecture is missing from the capture archive even "
            "though the recording light was on.",
        ),
        (
            "Podium microphone cuts out mid-lecture",
            "The lapel microphone in SCI 142 cuts out for a few seconds at a time, "
            "which breaks the lecture recording audio.",
        ),
        (
            "Document camera not detected by podium PC",
            "The document camera in ENGR 337 does not appear as a source in Zoom or "
            "in the podium software.",
        ),
    ],
    "Canvas / LMS": [
        (
            "Students missing from Canvas roster",
            "Six students who added my section during late registration are not in "
            "the Canvas course shell.",
        ),
        (
            "Quiz submissions not recording scores",
            "Quiz 3 shows submitted but ungraded for the whole class even though it "
            "is an auto-graded multiple-choice quiz.",
        ),
        (
            "Cannot upload a file larger than 200 MB",
            "My recorded project demo fails to upload to the assignment with a "
            "generic error.",
        ),
        (
            "Gradebook export is missing a column",
            "The CSV export from the gradebook drops the midterm column entirely.",
        ),
    ],
    "Software & Licensing": [
        (
            "MATLAB license checkout fails on lab machines",
            "MATLAB reports that all licenses are in use even at 7am when the lab is "
            "empty.",
        ),
        (
            "Need SolidWorks installed for senior project",
            "My capstone team needs SolidWorks on the team workstation before the "
            "design review.",
        ),
        (
            "Adobe Creative Cloud sign-in loops",
            "Creative Cloud asks me to sign in, accepts my credentials, and then "
            "immediately asks again.",
        ),
        (
            "Request Python environment for CMPE 165 lab",
            "The lab image ships Python 3.9 and the course materials assume 3.12.",
        ),
    ],
    "Printing": [
        (
            "Printing quota not updating after payment",
            "I added $20 to my print account two days ago and the balance still "
            "reads zero.",
        ),
        (
            "Library printer jams on every duplex job",
            "The printer near the reference desk jams whenever double-sided printing "
            "is selected.",
        ),
        (
            "Cannot find department printer on new laptop",
            "The ME department printer does not appear in the print dialog on my "
            "replacement laptop.",
        ),
    ],
    "Email & Calendar": [
        (
            "Shared department calendar invites not syncing",
            "Invites sent to the department calendar do not appear for half the "
            "staff who are subscribed to it.",
        ),
        (
            "Legitimate email quarantined as phishing",
            "Messages from our industry partner are being quarantined and the "
            "senders are not getting bounce notices.",
        ),
        (
            "Mailbox full warning at 2 GB",
            "I am getting mailbox-full warnings well below the quota published on "
            "the CTS site.",
        ),
        (
            "Distribution list missing new hires",
            "Three staff members hired this month are not receiving messages sent to "
            "the ME-Staff list.",
        ),
    ],
}

FIRST_NAMES = [
    "Jordan", "Emily", "Raj", "Sofia", "Kevin", "Hannah", "Diego", "Mei",
    "Andre", "Fatima", "Chris", "Nina", "Omar", "Grace", "Liam", "Yuki",
    "Carlos", "Alice", "Devin", "Noor", "Tanya", "Peter", "Sana", "Miguel",
]

LAST_NAMES = [
    "Nguyen", "Patel", "Garcia", "Kim", "Johnson", "Silva", "Okafor", "Rossi",
    "Hansen", "Ahmed", "Tran", "Brooks", "Mendoza", "Lee", "Wagner", "Dubois",
]

# Weighted so the queue looks like a real help desk: mostly Medium, a few Urgent.
PRIORITY_WEIGHTS = {"Urgent": 8, "High": 22, "Medium": 48, "Low": 22}

# Weighted toward resolved work, with a healthy live queue left over.
STATUS_WEIGHTS = {
    "New": 8,
    "Open": 12,
    "In Progress": 14,
    "Waiting on Requester": 8,
    "Resolved": 22,
    "Closed": 36,
}

RESOLUTION_NOTES = [
    "Verified the fix with the requester over the phone and closed the ticket.",
    "Replaced the failing component and confirmed normal operation.",
    "Reset the account and walked the requester through re-enrolling in Duo.",
    "Pushed the corrected configuration and confirmed the issue cleared.",
    "Escalated to Tier 2, who applied the vendor patch.",
    "Provided a documented workaround and logged a follow-up change request.",
]

TRIAGE_NOTES = [
    "Triaged and assigned to the owning team.",
    "Reproduced the issue on a test account.",
    "Requested a screenshot and the exact error text from the requester.",
    "Checked the building switch logs for related errors.",
    "Confirmed this matches two other tickets opened this week.",
]


def _weighted_choice(rng: random.Random, weights: dict[str, int]) -> str:
    return rng.choices(list(weights), weights=list(weights.values()), k=1)[0]


def _requester(rng: random.Random) -> tuple[str, str, str]:
    name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    requester_type = rng.choices(
        db.REQUESTER_TYPES, weights=[70, 18, 12], k=1
    )[0]
    handle = name.lower().replace(" ", ".")
    domain = "sjsu.edu"
    return name, f"{handle}@{domain}", requester_type


def _business_moment(rng: random.Random, anchor: datetime, days_back: int) -> datetime:
    """A timestamp on a support day, inside or near the support window."""
    day = (anchor - timedelta(days=days_back)).date()
    while not sla.is_support_day(day):
        day -= timedelta(days=1)
    hour = rng.randint(7, 18)
    minute = rng.choice([0, 7, 13, 22, 31, 38, 44, 51, 58])
    return datetime.combine(day, datetime.min.time()).replace(
        hour=hour, minute=minute
    )


def seed_database(
    ticket_count: int = DEFAULT_TICKET_COUNT,
    reset: bool = True,
    now: datetime | None = None,
) -> int:
    """Populate the database with agents and sample tickets.

    Returns the number of tickets created.
    """
    if reset:
        db.reset_database()
    else:
        db.init_db()

    for name, team in AGENTS:
        db.add_agent(name, team)

    rng = random.Random(RANDOM_SEED)
    anchor = now or datetime.now()
    agent_pool = [name for name, _ in AGENTS]

    flat_templates = [
        (category, title, description)
        for category, templates in TICKET_TEMPLATES.items()
        for title, description in templates
    ]

    created = 0
    for index in range(ticket_count):
        category, title, description = flat_templates[index % len(flat_templates)]
        priority = _weighted_choice(rng, PRIORITY_WEIGHTS)
        status = _weighted_choice(rng, STATUS_WEIGHTS)
        requester_name, requester_email, requester_type = _requester(rng)

        # Newer tickets are more likely to still be open, which is what makes
        # the dashboard's aging buckets look plausible.
        if status in db.CLOSED_STATUSES:
            days_back = rng.randint(4, HISTORY_DAYS)
        else:
            days_back = rng.randint(0, 9)

        created_at = _business_moment(rng, anchor, days_back)
        assignee = None if status == "New" else rng.choice(agent_pool)

        resolved_at = None
        if status in db.CLOSED_STATUSES:
            target = sla.target_hours(priority)
            # Most tickets land inside the SLA; a minority blow through it so the
            # breach reporting has something real to show.
            if rng.random() < 0.78:
                support_hours = rng.uniform(0.3, target * 0.9)
            else:
                support_hours = rng.uniform(target * 1.1, target * 2.4)
            resolved_at = _advance_business_hours(created_at, support_hours)
            if resolved_at > anchor:
                resolved_at = anchor

        ticket_id = db.create_ticket(
            title=title,
            description=description,
            category=category,
            priority=priority,
            requester_name=requester_name,
            requester_email=requester_email,
            requester_type=requester_type,
            assignee=assignee,
            status=status,
            created_at=created_at,
            resolved_at=resolved_at,
        )
        created += 1

        _seed_history(rng, ticket_id, status, assignee, created_at, resolved_at)

    return created


def _advance_business_hours(start: datetime, support_hours: float) -> datetime:
    """Walk forward from ``start`` until ``support_hours`` have accrued."""
    remaining = support_hours
    cursor = start
    guard = 0
    while remaining > 0 and guard < 5000:
        guard += 1
        step = timedelta(minutes=15)
        nxt = cursor + step
        remaining -= sla.business_hours_between(cursor, nxt)
        cursor = nxt
    return cursor


def _seed_history(
    rng: random.Random,
    ticket_id: int,
    status: str,
    assignee: str | None,
    created_at: datetime,
    resolved_at: datetime | None,
) -> None:
    """Write a plausible audit trail so ticket detail views are not empty."""
    events: list[tuple[str, str]] = []
    if assignee:
        events.append(("assignment", f"Assigned to {assignee}."))
    if status != "New":
        events.append(("triage", rng.choice(TRIAGE_NOTES)))
    if resolved_at is not None:
        events.append(("resolution", rng.choice(RESOLUTION_NOTES)))

    span_end = resolved_at or created_at + timedelta(hours=2)
    total_span = max((span_end - created_at).total_seconds(), 600)

    for position, (_, note) in enumerate(events, start=1):
        offset = total_span * position / (len(events) + 1)
        moment = created_at + timedelta(seconds=offset)
        db.add_comment(
            ticket_id,
            actor=assignee or "CTS Triage Bot",
            note=note,
            now=moment,
        )


def ensure_seeded() -> bool:
    """Seed only when the database has no tickets. Returns True if it seeded."""
    db.init_db()
    if db.count_tickets() > 0:
        return False
    seed_database()
    return True


if __name__ == "__main__":
    count = seed_database()
    print(f"Seeded {count} tickets into {db.db_path()}")
