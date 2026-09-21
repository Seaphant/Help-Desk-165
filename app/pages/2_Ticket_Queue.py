"""Ticket queue: search and filter (interaction #2), triage and update (#3)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app import db, reporting, sla, ui

ui.page_setup("Ticket queue", icon="\U0001f4cb")
identity = ui.sidebar_identity()
ui.show_flash()

is_agent = identity["role"] in ("Agent", "Manager")

st.title("Ticket queue")
st.caption(
    "Search and filter the queue, then open a ticket to assign it, move it "
    "through the workflow, and log what you did."
)

QUEUE_VIEWS = {
    "Open work": db.OPEN_STATUSES,
    "Needs an owner": db.OPEN_STATUSES,
    "SLA trouble": db.OPEN_STATUSES,
    "Everything": db.STATUSES,
    "Closed": db.CLOSED_STATUSES,
}

with st.container(border=True):
    top_left, top_right = st.columns([3, 2])
    with top_left:
        search = st.text_input(
            "Search",
            placeholder="Keyword, requester name, or ticket number",
            label_visibility="collapsed",
        )
    with top_right:
        view = st.selectbox(
            "View", list(QUEUE_VIEWS), label_visibility="collapsed"
        )

    filter_columns = st.columns(4)
    with filter_columns[0]:
        statuses = st.multiselect("Status", db.STATUSES, default=QUEUE_VIEWS[view])
    with filter_columns[1]:
        priorities = st.multiselect("Priority", db.PRIORITIES)
    with filter_columns[2]:
        categories = st.multiselect("Category", db.CATEGORIES)
    with filter_columns[3]:
        assignee_options = ["Unassigned"] + db.agent_names()
        assignees = st.multiselect("Owner", assignee_options)

tickets = db.list_tickets(
    statuses=statuses,
    priorities=priorities,
    categories=categories,
    assignees=assignees,
    search=search,
    requester_email=None if is_agent else identity["email"],
)
frame = reporting.tickets_dataframe(tickets)

# The two saved views that cannot be expressed as plain column filters.
if not frame.empty:
    if view == "Needs an owner":
        frame = frame[frame["assignee"] == "Unassigned"]
    elif view == "SLA trouble":
        frame = frame[frame["sla_status"].isin(["Breached", "At Risk"])]

if not is_agent:
    st.info(
        f"Requester view: showing only tickets submitted from "
        f"**{identity['email'] or 'your email'}**. Switch the sidebar role to "
        "Agent to work the full queue."
    )

count_left, count_middle, count_right = st.columns(3)
count_left.metric("Matching tickets", len(frame))
count_middle.metric(
    "Breached", int((frame["sla_status"] == "Breached").sum()) if not frame.empty else 0
)
count_right.metric(
    "At risk", int((frame["sla_status"] == "At Risk").sum()) if not frame.empty else 0
)

if frame.empty:
    st.warning(
        "No tickets match these filters. Clear the search box or widen the "
        "status filter."
    )
    st.stop()

display = frame.copy()
display["priority"] = display["priority"].map(ui.priority_label)
display["sla_status"] = display["sla_status"].map(ui.sla_label)

st.dataframe(
    display[
        ["id", "title", "category", "priority", "status", "assignee",
         "sla_status", "hours_remaining", "created_at"]
    ],
    hide_index=True,
    use_container_width=True,
    height=340,
    column_config=ui.queue_column_config(),
)

st.divider()
st.subheader("Open a ticket")

ordered = frame.sort_values("hours_remaining")
options = ordered["id"].tolist()
labels = {row["id"]: ui.ticket_option_label(row) for _, row in ordered.iterrows()}

selected_id = st.selectbox(
    "Ticket",
    options,
    format_func=lambda ticket_id: labels[ticket_id],
    label_visibility="collapsed",
)

ticket = db.get_ticket(int(selected_id))
if ticket is None:
    st.error("That ticket no longer exists. Refresh the queue.")
    st.stop()

created_at = db.parse_timestamp(ticket["created_at"])
resolved_at = db.parse_timestamp(ticket["resolved_at"])
status_text = sla.sla_status(ticket["priority"], created_at, resolved_at)
remaining = sla.hours_remaining(ticket["priority"], created_at, resolved_at)

detail_left, detail_right = st.columns([3, 2], gap="large")

with detail_left:
    st.markdown(f"### #{ticket['id']} · {ticket['title']}")
    st.caption(
        f"{ticket['requester_name']} ({ticket['requester_type']}) · "
        f"{ticket['requester_email']} · opened {ticket['created_at']}"
    )
    with st.container(border=True):
        st.write(ticket["description"])

    st.markdown("#### Activity")
    events = db.list_events(ticket["id"])
    for event in reversed(events):
        if event["event_type"] == "comment":
            body = event["note"]
        elif event["event_type"] == "created":
            body = event["note"]
        else:
            field = (event["field"] or "").replace("_", " ")
            body = (
                f"Changed **{field}** from "
                f"`{event['old_value'] or 'none'}` to `{event['new_value']}`."
            )
        st.markdown(f"- `{event['created_at']}` **{event['actor']}** — {body}")

with detail_right:
    st.markdown("#### SLA")
    st.metric(
        ui.sla_label(status_text),
        f"{abs(remaining):.1f} h {'over' if remaining < 0 else 'left'}",
        help=(
            f"{ticket['priority']} target is "
            f"{sla.target_hours(ticket['priority']):.0f} support hours."
        ),
    )
    consumed = sla.elapsed_hours(created_at, resolved_at)
    target = sla.target_hours(ticket["priority"])
    st.progress(min(consumed / target, 1.0))
    st.caption(f"{consumed:.1f} of {target:.0f} support hours used.")

    st.markdown("#### Update")
    if is_agent:
        with st.form(f"update_{ticket['id']}"):
            new_status = st.selectbox(
                "Status", db.STATUSES, index=db.STATUSES.index(ticket["status"])
            )
            new_priority = st.selectbox(
                "Priority",
                db.PRIORITIES,
                index=db.PRIORITIES.index(ticket["priority"]),
            )
            owner_options = ["Unassigned"] + db.agent_names()
            current_owner = ticket["assignee"] or "Unassigned"
            if current_owner not in owner_options:
                owner_options.append(current_owner)
            new_owner = st.selectbox(
                "Owner", owner_options, index=owner_options.index(current_owner)
            )
            new_category = st.selectbox(
                "Category",
                db.CATEGORIES,
                index=db.CATEGORIES.index(ticket["category"]),
            )
            note = st.text_area(
                "Work note",
                placeholder="What did you check, change, or ask for?",
                height=90,
            )
            saved = st.form_submit_button("Save update", type="primary")

        if saved:
            changed = db.update_ticket(
                ticket["id"],
                actor=identity["name"] or identity["role"],
                changes={
                    "status": new_status,
                    "priority": new_priority,
                    "assignee": None if new_owner == "Unassigned" else new_owner,
                    "category": new_category,
                },
                note=note,
            )
            if changed:
                st.session_state["flash"] = (
                    f"Ticket #{ticket['id']} updated ({', '.join(changed)})."
                )
                st.rerun()
            else:
                st.info("Nothing changed — pick a different value or add a note.")
    else:
        with st.form(f"comment_{ticket['id']}"):
            note = st.text_area(
                "Add a comment",
                placeholder="Extra detail, or a reply to the agent's question.",
                height=110,
            )
            posted = st.form_submit_button("Post comment", type="primary")
        if posted:
            if note.strip():
                db.add_comment(
                    ticket["id"], actor=identity["name"] or "Requester", note=note
                )
                st.session_state["flash"] = "Comment added to the ticket."
                st.rerun()
            else:
                st.warning("Write something before posting.")
        st.caption("Only agents can reassign or change status.")
