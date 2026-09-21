"""Shared Streamlit chrome: page setup, the role switcher, and small badges.

The prototype deliberately has no authentication. Role is a sidebar selector,
which is enough to demonstrate that requesters and agents see different
capabilities without building an identity system the assignment does not ask
for.
"""

from __future__ import annotations

import streamlit as st

from app import db, reporting, seed

ROLES = ["Requester", "Agent", "Manager"]

ROLE_HELP = {
    "Requester": "Submit tickets and follow your own requests.",
    "Agent": "Triage the queue, assign owners, and log work.",
    "Manager": "Watch SLA performance and export reports.",
}

DEFAULT_IDENTITY = {
    "Requester": ("Jordan Nguyen", "jordan.nguyen@sjsu.edu"),
    "Agent": ("Priya Raman", "priya.raman@sjsu.edu"),
    "Manager": ("Dana Whitfield", "dana.whitfield@sjsu.edu"),
}

PRIORITY_ICON = {
    "Urgent": "\U0001f534",
    "High": "\U0001f7e0",
    "Medium": "\U0001f7e1",
    "Low": "\U0001f7e2",
}

SLA_ICON = {
    "Met": "\u2705",
    "On Track": "\U0001f7e2",
    "At Risk": "\U0001f7e1",
    "Breached": "\U0001f534",
}

BASE_CSS = """
<style>
  div[data-testid="stMetricValue"] { font-size: 1.75rem; }
  div[data-testid="stMetric"] {
      background: rgba(128, 128, 128, 0.07);
      border: 1px solid rgba(128, 128, 128, 0.18);
      border-radius: 10px;
      padding: 0.75rem 0.9rem;
  }
  section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] p {
      font-size: 0.78rem;
  }
</style>
"""


def page_setup(title: str, icon: str = "\U0001f3eb") -> None:
    """Standard page config plus first-run database seeding."""
    st.set_page_config(
        page_title=f"{title} | HelpDesk165",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(BASE_CSS, unsafe_allow_html=True)

    if not st.session_state.get("db_ready"):
        seeded = seed.ensure_seeded()
        st.session_state["db_ready"] = True
        st.session_state["db_was_seeded"] = seeded


def sidebar_identity() -> dict[str, str]:
    """Render the role switcher and return the active identity."""
    with st.sidebar:
        st.markdown("### HelpDesk165")
        st.caption("SJSU Campus Technology Services")

        role = st.selectbox(
            "Signed in as",
            ROLES,
            index=ROLES.index(st.session_state.get("role", "Agent")),
            help="No real authentication in the prototype; this switches the view.",
        )
        st.session_state["role"] = role

        default_name, default_email = DEFAULT_IDENTITY[role]
        name = st.text_input("Your name", value=st.session_state.get(
            f"name_{role}", default_name
        ))
        st.session_state[f"name_{role}"] = name

        email = st.text_input("Your email", value=st.session_state.get(
            f"email_{role}", default_email
        ))
        st.session_state[f"email_{role}"] = email

        st.caption(ROLE_HELP[role])
        st.divider()

        st.page_link("Home.py", label="Overview", icon="\U0001f3e0")
        st.page_link(
            "pages/1_Submit_Ticket.py", label="Submit a ticket", icon="\u2795"
        )
        st.page_link("pages/2_Ticket_Queue.py", label="Ticket queue", icon="\U0001f4cb")
        st.page_link("pages/3_Dashboard.py", label="SLA dashboard", icon="\U0001f4ca")

        st.divider()
        st.caption(f"Database: `{db.db_path().name}` \u00b7 {db.count_tickets()} tickets")

        with st.expander("Reset sample data"):
            st.caption(
                "Rebuilds the database from the deterministic seed. Useful before "
                "recording a demo."
            )
            if st.button("Reseed database", use_container_width=True):
                seed.seed_database()
                st.session_state["flash"] = "Sample data reloaded."
                st.rerun()

    return {"role": role, "name": name.strip(), "email": email.strip()}


def show_flash() -> None:
    """Display and clear a one-shot message set before a rerun."""
    message = st.session_state.pop("flash", None)
    if message:
        st.success(message)


def load_frame():
    """All tickets as a metrics-enriched DataFrame."""
    return reporting.tickets_dataframe(db.list_tickets())


def priority_label(priority: str) -> str:
    return f"{PRIORITY_ICON.get(priority, '')} {priority}".strip()


def sla_label(status: str) -> str:
    return f"{SLA_ICON.get(status, '')} {status}".strip()


def ticket_option_label(row) -> str:
    return (
        f"#{row['id']} \u00b7 {PRIORITY_ICON.get(row['priority'], '')} "
        f"{row['title'][:58]}"
    )


def queue_column_config():
    """Column formatting shared by the queue and dashboard tables."""
    import streamlit as st  # local import keeps this helper self-contained

    return {
        "id": st.column_config.NumberColumn("Ticket", format="%d", width="small"),
        "title": st.column_config.TextColumn("Summary", width="large"),
        "category": st.column_config.TextColumn("Category"),
        "priority": st.column_config.TextColumn("Priority", width="small"),
        "status": st.column_config.TextColumn("Status"),
        "assignee": st.column_config.TextColumn("Owner"),
        "sla_status": st.column_config.TextColumn("SLA", width="small"),
        "hours_remaining": st.column_config.NumberColumn(
            "Hrs left", format="%.1f", width="small",
            help="Support hours remaining before the SLA target is missed.",
        ),
        "support_hours_used": st.column_config.NumberColumn(
            "Hrs used", format="%.1f", width="small"
        ),
        "created_at": st.column_config.DatetimeColumn(
            "Created", format="MMM D, HH:mm"
        ),
        "resolved_at": st.column_config.DatetimeColumn(
            "Resolved", format="MMM D, HH:mm"
        ),
        "age_bucket": st.column_config.TextColumn("Age"),
    }
