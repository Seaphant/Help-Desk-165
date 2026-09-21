"""Derived metrics that sit between the database and the Streamlit pages.

Keeping the SLA joins and KPI math here means the dashboard and the queue agree
on every number, and the whole thing is testable without launching Streamlit.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from app import db, sla

AGE_BUCKETS = ["< 1 day", "1-3 days", "4-7 days", "> 7 days"]


def _age_bucket(created_at: datetime, now: datetime) -> str:
    days = (now - created_at).total_seconds() / 86400.0
    if days < 1:
        return AGE_BUCKETS[0]
    if days <= 3:
        return AGE_BUCKETS[1]
    if days <= 7:
        return AGE_BUCKETS[2]
    return AGE_BUCKETS[3]


def tickets_dataframe(
    tickets: list[dict[str, Any]], now: datetime | None = None
) -> pd.DataFrame:
    """Turn ticket rows into a frame with SLA and aging columns attached."""
    moment = now or datetime.now()
    columns = [
        "id", "title", "category", "priority", "status", "assignee",
        "requester_name", "requester_email", "requester_type",
        "created_at", "updated_at", "resolved_at", "is_open",
        "sla_target_hours", "support_hours_used", "hours_remaining",
        "sla_status", "age_bucket",
    ]

    if not tickets:
        return pd.DataFrame(columns=columns)

    rows = []
    for ticket in tickets:
        created_at = db.parse_timestamp(ticket["created_at"])
        resolved_at = db.parse_timestamp(ticket["resolved_at"])
        rows.append(
            {
                "id": ticket["id"],
                "title": ticket["title"],
                "category": ticket["category"],
                "priority": ticket["priority"],
                "status": ticket["status"],
                "assignee": ticket["assignee"] or "Unassigned",
                "requester_name": ticket["requester_name"],
                "requester_email": ticket["requester_email"],
                "requester_type": ticket["requester_type"],
                "created_at": created_at,
                "updated_at": db.parse_timestamp(ticket["updated_at"]),
                "resolved_at": resolved_at,
                "is_open": ticket["status"] in db.OPEN_STATUSES,
                "sla_target_hours": sla.target_hours(ticket["priority"]),
                "support_hours_used": sla.elapsed_hours(
                    created_at, resolved_at, moment
                ),
                "hours_remaining": sla.hours_remaining(
                    ticket["priority"], created_at, resolved_at, moment
                ),
                "sla_status": sla.sla_status(
                    ticket["priority"], created_at, resolved_at, moment
                ),
                "age_bucket": _age_bucket(created_at, moment),
            }
        )

    return pd.DataFrame(rows, columns=columns)


def kpis(frame: pd.DataFrame) -> dict[str, Any]:
    """Headline numbers for the dashboard and the home screen."""
    total = int(len(frame))
    if total == 0:
        return {
            "total": 0,
            "open": 0,
            "unassigned": 0,
            "resolved": 0,
            "breached": 0,
            "at_risk": 0,
            "sla_compliance_pct": 0.0,
            "avg_resolution_hours": 0.0,
            "median_resolution_hours": 0.0,
            "backlog_over_7_days": 0,
        }

    open_frame = frame[frame["is_open"]]
    closed_frame = frame[~frame["is_open"]]

    # Compliance is judged on finished work only; an open ticket that still has
    # SLA time left has not passed or failed anything yet.
    judged = closed_frame
    met = int((judged["sla_status"] == "Met").sum())
    compliance = (met / len(judged) * 100.0) if len(judged) else 0.0

    resolution_hours = closed_frame["support_hours_used"]

    return {
        "total": total,
        "open": int(len(open_frame)),
        "unassigned": int((open_frame["assignee"] == "Unassigned").sum()),
        "resolved": int(len(closed_frame)),
        "breached": int((frame["sla_status"] == "Breached").sum()),
        "at_risk": int((frame["sla_status"] == "At Risk").sum()),
        "sla_compliance_pct": round(compliance, 1),
        "avg_resolution_hours": round(float(resolution_hours.mean()), 1)
        if len(resolution_hours)
        else 0.0,
        "median_resolution_hours": round(float(resolution_hours.median()), 1)
        if len(resolution_hours)
        else 0.0,
        "backlog_over_7_days": int(
            (open_frame["age_bucket"] == "> 7 days").sum()
        ),
    }


def volume_by_category(frame: pd.DataFrame) -> pd.DataFrame:
    """Open vs. resolved counts per category, sorted by total volume."""
    if frame.empty:
        return pd.DataFrame(columns=["category", "state", "tickets"])

    working = frame.copy()
    working["state"] = working["is_open"].map({True: "Open", False: "Resolved"})
    grouped = (
        working.groupby(["category", "state"], as_index=False)
        .size()
        .rename(columns={"size": "tickets"})
    )
    order = (
        working.groupby("category", as_index=False)
        .size()
        .sort_values("size", ascending=False)["category"]
        .tolist()
    )
    grouped["category"] = pd.Categorical(
        grouped["category"], categories=order, ordered=True
    )
    return grouped.sort_values(["category", "state"])


def sla_by_priority(frame: pd.DataFrame) -> pd.DataFrame:
    """SLA outcome counts per priority, in escalating priority order."""
    if frame.empty:
        return pd.DataFrame(columns=["priority", "sla_status", "tickets"])

    grouped = (
        frame.groupby(["priority", "sla_status"], as_index=False)
        .size()
        .rename(columns={"size": "tickets"})
    )
    grouped["priority"] = pd.Categorical(
        grouped["priority"], categories=db.PRIORITIES, ordered=True
    )
    return grouped.sort_values(["priority", "sla_status"])


def agent_workload(frame: pd.DataFrame) -> pd.DataFrame:
    """Open ticket load per assignee, including breach counts."""
    if frame.empty:
        return pd.DataFrame(columns=["assignee", "open_tickets", "breached"])

    open_frame = frame[frame["is_open"]]
    if open_frame.empty:
        return pd.DataFrame(columns=["assignee", "open_tickets", "breached"])

    grouped = (
        open_frame.assign(breached=open_frame["sla_status"] == "Breached")
        .groupby("assignee", as_index=False)
        .agg(open_tickets=("id", "count"), breached=("breached", "sum"))
        .sort_values("open_tickets", ascending=False)
    )
    grouped["breached"] = grouped["breached"].astype(int)
    return grouped


def weekly_intake(frame: pd.DataFrame) -> pd.DataFrame:
    """Tickets created per calendar week, oldest first."""
    if frame.empty:
        return pd.DataFrame(columns=["week", "tickets"])

    working = frame.copy()
    working["week"] = (
        pd.to_datetime(working["created_at"]).dt.to_period("W").dt.start_time
    )
    return (
        working.groupby("week", as_index=False)
        .size()
        .rename(columns={"size": "tickets"})
        .sort_values("week")
    )


REPORT_COLUMNS = [
    "id", "title", "category", "priority", "status", "assignee",
    "requester_name", "requester_email", "requester_type",
    "created_at", "resolved_at", "sla_target_hours",
    "support_hours_used", "hours_remaining", "sla_status", "age_bucket",
]


def report_csv(frame: pd.DataFrame) -> bytes:
    """Management report export, matching what the dashboard displays."""
    if frame.empty:
        return pd.DataFrame(columns=REPORT_COLUMNS).to_csv(index=False).encode()
    return frame[REPORT_COLUMNS].to_csv(index=False).encode()
