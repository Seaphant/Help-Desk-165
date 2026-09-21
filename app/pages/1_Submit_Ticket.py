"""Ticket intake form — user interaction #1."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app import db, sla, ui

ui.page_setup("Submit a ticket", icon="\u2795")
identity = ui.sidebar_identity()

st.title("Submit a ticket")
st.caption(
    "Every field below feeds triage. Accurate category and priority are what "
    "let HelpDesk165 route work and measure the SLA."
)

PRIORITY_GUIDANCE = {
    "Urgent": "Teaching or a campus service is stopped right now.",
    "High": "Work is blocked and there is no workaround.",
    "Medium": "Disruptive but there is a workaround.",
    "Low": "Request, question, or minor annoyance.",
}

with st.form("submit_ticket", clear_on_submit=False):
    st.subheader("What is happening?")
    title = st.text_input(
        "Short summary",
        max_chars=120,
        placeholder="Projector in BBC 202 shows no signal from HDMI",
    )
    description = st.text_area(
        "Details",
        height=150,
        placeholder=(
            "What were you doing, what did you expect, what happened instead? "
            "Include room numbers, exact error text, and when it started."
        ),
    )

    field_left, field_right = st.columns(2)
    with field_left:
        category = st.selectbox("Category", db.CATEGORIES)
    with field_right:
        priority = st.selectbox("Priority", db.PRIORITIES, index=2)
        st.caption(PRIORITY_GUIDANCE[priority])

    st.subheader("Who should we contact?")
    contact_left, contact_middle, contact_right = st.columns([2, 2, 1])
    with contact_left:
        requester_name = st.text_input("Full name", value=identity["name"])
    with contact_middle:
        requester_email = st.text_input("Campus email", value=identity["email"])
    with contact_right:
        requester_type = st.selectbox("I am a", db.REQUESTER_TYPES)

    st.caption(
        f"A {priority} ticket carries a "
        f"**{sla.target_hours(priority):.0f} support-hour** response target "
        "(weekdays 08:00-18:00)."
    )

    submitted = st.form_submit_button(
        "Submit ticket", type="primary", use_container_width=False
    )

if submitted:
    problems = []
    if len(title.strip()) < 8:
        problems.append("Give the summary at least 8 characters so triage can scan it.")
    if len(description.strip()) < 15:
        problems.append("Add a bit more detail — at least 15 characters.")
    if not requester_name.strip():
        problems.append("A contact name is required.")
    if "@" not in requester_email or "." not in requester_email.split("@")[-1]:
        problems.append("Enter a valid campus email address.")

    if problems:
        for problem in problems:
            st.error(problem)
    else:
        ticket_id = db.create_ticket(
            title=title,
            description=description,
            category=category,
            priority=priority,
            requester_name=requester_name,
            requester_email=requester_email,
            requester_type=requester_type,
        )
        st.session_state["last_submitted_ticket"] = ticket_id
        st.success(f"Ticket **#{ticket_id}** created and queued for triage.")
        st.balloons()

last_ticket = st.session_state.get("last_submitted_ticket")
if last_ticket:
    ticket = db.get_ticket(last_ticket)
    if ticket:
        st.divider()
        st.subheader(f"Ticket #{ticket['id']}")
        summary_left, summary_right = st.columns([3, 2])
        with summary_left:
            st.markdown(f"**{ticket['title']}**")
            st.write(ticket["description"])
        with summary_right:
            st.metric("Status", ticket["status"])
            st.write(f"**Priority:** {ui.priority_label(ticket['priority'])}")
            st.write(f"**Category:** {ticket['category']}")
            st.write(
                f"**Response target:** {sla.target_hours(ticket['priority']):.0f} "
                "support hours"
            )
        st.page_link(
            "pages/2_Ticket_Queue.py",
            label="Track this ticket in the queue",
            icon="\U0001f4cb",
        )

with st.expander("Not sure which priority to pick?"):
    st.markdown(
        "\n".join(
            f"- **{level}** — {text} Target: "
            f"{sla.target_hours(level):.0f} support hours."
            for level, text in PRIORITY_GUIDANCE.items()
        )
    )
    st.caption(
        "Agents can re-prioritise during triage, so an honest guess is better "
        "than marking everything Urgent."
    )
