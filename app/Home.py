"""HelpDesk165 overview screen.

Run from the repository root:
    streamlit run app/Home.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit puts this file's directory on sys.path, not the repository root, so
# the `app` package imports below need the root added explicitly.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app import db, reporting, sla, ui

ui.page_setup("Overview")
identity = ui.sidebar_identity()
ui.show_flash()

frame = ui.load_frame()
metrics = reporting.kpis(frame)

st.title("HelpDesk165")
st.markdown(
    "One queue for every campus technology request. Built for **SJSU Campus "
    "Technology Services** to replace the shared inbox and three spreadsheets "
    "that tickets currently live in."
)

if st.session_state.pop("db_was_seeded", False):
    st.info(
        f"First run detected, so the database was seeded with "
        f"{metrics['total']} sample tickets. Reseed any time from the sidebar."
    )

left, right = st.columns([3, 2], gap="large")

with left:
    st.subheader("Where the queue stands")
    row_one = st.columns(3)
    row_one[0].metric("Open tickets", metrics["open"])
    row_one[1].metric(
        "Unassigned",
        metrics["unassigned"],
        help="Open tickets with no owner. These are the ones that go stale.",
    )
    row_one[2].metric(
        "SLA breaches",
        metrics["breached"],
        delta=f"{metrics['at_risk']} at risk",
        delta_color="inverse",
    )

    row_two = st.columns(3)
    row_two[0].metric("SLA compliance", f"{metrics['sla_compliance_pct']}%")
    row_two[1].metric(
        "Avg resolution",
        f"{metrics['avg_resolution_hours']} h",
        help="Support hours, not calendar hours.",
    )
    row_two[2].metric("Backlog over 7 days", metrics["backlog_over_7_days"])

    st.subheader("What you can do")
    action_left, action_right = st.columns(2)
    with action_left:
        st.markdown("**Submit a ticket**")
        st.caption(
            "Describe the problem once. HelpDesk165 assigns an SLA target from "
            "the priority and returns a tracking number."
        )
        st.page_link(
            "pages/1_Submit_Ticket.py", label="Open the intake form", icon="\u2795"
        )

        st.markdown("**Work the queue**")
        st.caption(
            "Search and filter open work, assign an owner, change status, and "
            "leave a timestamped work note that becomes part of the audit trail."
        )
        st.page_link(
            "pages/2_Ticket_Queue.py", label="Open the queue", icon="\U0001f4cb"
        )

    with action_right:
        st.markdown("**Watch SLA performance**")
        st.caption(
            "Breach counts by priority, volume by category, per-agent load, and "
            "a CSV export for the monthly service review."
        )
        st.page_link(
            "pages/3_Dashboard.py", label="Open the dashboard", icon="\U0001f4ca"
        )

        st.markdown("**How SLA targets work**")
        st.caption(
            "Targets are measured in support hours (weekdays 08:00-18:00, campus "
            "holidays excluded), so a Friday evening ticket is not late on Saturday."
        )

with right:
    st.subheader("Hottest open tickets")
    open_frame = frame[frame["is_open"]]
    if open_frame.empty:
        st.success("Nothing open. The queue is clear.")
    else:
        hottest = open_frame.sort_values("hours_remaining").head(6)
        for _, row in hottest.iterrows():
            remaining = row["hours_remaining"]
            timing = (
                f"{abs(remaining):.1f} h over target"
                if remaining < 0
                else f"{remaining:.1f} h left"
            )
            with st.container(border=True):
                st.markdown(
                    f"**#{row['id']} · {row['title']}**  \n"
                    f"{ui.priority_label(row['priority'])} · {row['category']}  \n"
                    f"{ui.sla_label(row['sla_status'])} · {timing} · "
                    f"owner: {row['assignee']}"
                )

    st.subheader("SLA targets")
    st.dataframe(
        {
            "Priority": list(db.PRIORITIES),
            "Target (support hours)": [
                sla.target_hours(priority) for priority in db.PRIORITIES
            ],
        },
        hide_index=True,
        use_container_width=True,
    )

if identity["role"] == "Requester" and identity["email"]:
    st.divider()
    st.subheader("Your requests")
    mine = frame[frame["requester_email"].str.lower() == identity["email"].lower()]
    if mine.empty:
        st.caption(
            f"No tickets on file for {identity['email']}. Submit one and it will "
            "appear here."
        )
    else:
        st.dataframe(
            mine[["id", "title", "category", "priority", "status", "sla_status",
                  "created_at"]],
            hide_index=True,
            use_container_width=True,
            column_config=ui.queue_column_config(),
        )
