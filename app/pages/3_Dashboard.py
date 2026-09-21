"""SLA dashboard and management report export — user interaction #4."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import altair as alt
import streamlit as st

from app import db, reporting, ui

ui.page_setup("SLA dashboard", icon="\U0001f4ca")
identity = ui.sidebar_identity()

st.title("SLA dashboard")
st.caption(
    "The view Campus Technology Services takes into its monthly service review: "
    "where volume comes from, where the SLA is slipping, and who is overloaded."
)

frame = ui.load_frame()

if frame.empty:
    st.warning("No tickets yet. Submit one or reseed the sample data from the sidebar.")
    st.stop()

scope_left, scope_right = st.columns([2, 3])
with scope_left:
    lookback = st.selectbox(
        "Reporting window",
        ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
        index=1,
    )
with scope_right:
    category_filter = st.multiselect(
        "Limit to categories", db.CATEGORIES, placeholder="All categories"
    )

DAYS = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90, "All time": None}
window_days = DAYS[lookback]

scoped = frame
if window_days is not None:
    cutoff = datetime.now().timestamp() - window_days * 86400
    scoped = scoped[
        scoped["created_at"].map(lambda moment: moment.timestamp()) >= cutoff
    ]
if category_filter:
    scoped = scoped[scoped["category"].isin(category_filter)]

if scoped.empty:
    st.warning("Nothing in that window. Widen the reporting window.")
    st.stop()

metrics = reporting.kpis(scoped)

st.subheader("Headline numbers")
top = st.columns(4)
top[0].metric("Tickets in window", metrics["total"])
top[1].metric("Still open", metrics["open"], delta=f"{metrics['unassigned']} unowned",
              delta_color="inverse")
top[2].metric("SLA compliance", f"{metrics['sla_compliance_pct']}%",
              help="Share of closed tickets resolved inside the SLA target.")
top[3].metric("Breached", metrics["breached"], delta=f"{metrics['at_risk']} at risk",
              delta_color="inverse")

second = st.columns(4)
second[0].metric("Avg resolution", f"{metrics['avg_resolution_hours']} h")
second[1].metric("Median resolution", f"{metrics['median_resolution_hours']} h")
second[2].metric("Resolved / closed", metrics["resolved"])
second[3].metric("Open over 7 days", metrics["backlog_over_7_days"])

st.divider()

chart_left, chart_right = st.columns(2, gap="large")

with chart_left:
    st.subheader("Volume by category")
    volume = reporting.volume_by_category(scoped)
    volume_chart = (
        alt.Chart(volume)
        .mark_bar()
        .encode(
            y=alt.Y("category:N", title=None, sort="-x"),
            x=alt.X("tickets:Q", title="Tickets"),
            color=alt.Color(
                "state:N",
                title="State",
                scale=alt.Scale(
                    domain=["Open", "Resolved"], range=["#f0803c", "#4c9a6a"]
                ),
            ),
            tooltip=["category", "state", "tickets"],
        )
        .properties(height=290)
    )
    st.altair_chart(volume_chart, use_container_width=True)
    st.caption(
        "Categories at the top are where a self-service article or an automated "
        "fix would remove the most work."
    )

with chart_right:
    st.subheader("SLA outcome by priority")
    sla_frame = reporting.sla_by_priority(scoped)
    sla_chart = (
        alt.Chart(sla_frame)
        .mark_bar()
        .encode(
            x=alt.X("priority:N", title=None, sort=db.PRIORITIES),
            y=alt.Y("tickets:Q", title="Tickets"),
            color=alt.Color(
                "sla_status:N",
                title="SLA",
                scale=alt.Scale(
                    domain=["Met", "On Track", "At Risk", "Breached"],
                    range=["#4c9a6a", "#5a8fc4", "#e0b040", "#c4504b"],
                ),
            ),
            tooltip=["priority", "sla_status", "tickets"],
        )
        .properties(height=290)
    )
    st.altair_chart(sla_chart, use_container_width=True)
    st.caption(
        "Urgent breaches are the ones that reach the Provost's office, so they "
        "are weighted most heavily in the service review."
    )

lower_left, lower_right = st.columns(2, gap="large")

with lower_left:
    st.subheader("Weekly intake")
    intake = reporting.weekly_intake(scoped)
    intake_chart = (
        alt.Chart(intake)
        .mark_line(point=True)
        .encode(
            x=alt.X("week:T", title="Week beginning"),
            y=alt.Y("tickets:Q", title="Tickets created"),
            tooltip=["week:T", "tickets:Q"],
        )
        .properties(height=260)
    )
    st.altair_chart(intake_chart, use_container_width=True)

with lower_right:
    st.subheader("Open load by owner")
    workload = reporting.agent_workload(scoped)
    if workload.empty:
        st.success("No open tickets in this window.")
    else:
        workload_chart = (
            alt.Chart(workload)
            .mark_bar(color="#5a8fc4")
            .encode(
                y=alt.Y("assignee:N", title=None, sort="-x"),
                x=alt.X("open_tickets:Q", title="Open tickets"),
                tooltip=["assignee", "open_tickets", "breached"],
            )
            .properties(height=260)
        )
        st.altair_chart(workload_chart, use_container_width=True)
        st.caption("Hover to see how many of each owner's tickets are already late.")

st.divider()
st.subheader("Tickets past their SLA target")

breached = scoped[scoped["sla_status"] == "Breached"].sort_values("hours_remaining")
if breached.empty:
    st.success("No breaches in this window.")
else:
    display = breached.copy()
    display["priority"] = display["priority"].map(ui.priority_label)
    st.dataframe(
        display[["id", "title", "category", "priority", "status", "assignee",
                 "support_hours_used", "sla_target_hours", "hours_remaining"]],
        hide_index=True,
        use_container_width=True,
        column_config=ui.queue_column_config(),
    )

st.subheader("Export")
export_left, export_right = st.columns([1, 3])
with export_left:
    st.download_button(
        "Download report (CSV)",
        data=reporting.report_csv(scoped),
        file_name=f"helpdesk165_report_{datetime.now():%Y%m%d}.csv",
        mime="text/csv",
        type="primary",
    )
with export_right:
    st.caption(
        f"{len(scoped)} rows covering {lookback.lower()}"
        + (f", limited to {len(category_filter)} categories." if category_filter
           else ", all categories.")
        + " Columns match what is displayed above, including the computed SLA "
        "status, so the numbers in a meeting deck can be traced back to tickets."
    )
