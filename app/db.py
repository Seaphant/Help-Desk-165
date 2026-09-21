"""SQLite persistence for HelpDesk165.

A connection is opened per operation instead of being cached on the module.
Streamlit reruns the script on every widget interaction and serves sessions
from a thread pool, so a long-lived connection would eventually be touched
from the wrong thread.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "helpdesk.db"

CATEGORIES = [
    "Account & Login",
    "Wi-Fi & Network",
    "Hardware",
    "Classroom Technology",
    "Canvas / LMS",
    "Software & Licensing",
    "Printing",
    "Email & Calendar",
]

PRIORITIES = ["Urgent", "High", "Medium", "Low"]

STATUSES = [
    "New",
    "Open",
    "In Progress",
    "Waiting on Requester",
    "Resolved",
    "Closed",
]

OPEN_STATUSES = ["New", "Open", "In Progress", "Waiting on Requester"]
CLOSED_STATUSES = ["Resolved", "Closed"]

REQUESTER_TYPES = ["Student", "Faculty", "Staff"]

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    team        TEXT NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tickets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    category        TEXT NOT NULL,
    priority        TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'New',
    requester_name  TEXT NOT NULL,
    requester_email TEXT NOT NULL,
    requester_type  TEXT NOT NULL DEFAULT 'Student',
    assignee        TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    resolved_at     TEXT
);

CREATE TABLE IF NOT EXISTS ticket_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    event_type  TEXT NOT NULL,
    field       TEXT,
    old_value   TEXT,
    new_value   TEXT,
    note        TEXT,
    actor       TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON tickets(assignee);
CREATE INDEX IF NOT EXISTS idx_events_ticket ON ticket_events(ticket_id);
"""

# Fields an agent is allowed to change from the queue screen.
EDITABLE_FIELDS = ("status", "priority", "assignee", "category")


def db_path() -> Path:
    """Database location, overridable with HELPDESK_DB (used by the tests)."""
    return Path(os.environ.get("HELPDESK_DB", DEFAULT_DB_PATH))


def format_timestamp(moment: datetime) -> str:
    return moment.strftime(TIMESTAMP_FORMAT)


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, TIMESTAMP_FORMAT)


def get_connection() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA)


def count_tickets() -> int:
    with get_connection() as connection:
        return connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]


def add_agent(name: str, team: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO agents (name, team) VALUES (?, ?)", (name, team)
        )


def list_agents(include_inactive: bool = False) -> list[dict[str, Any]]:
    query = "SELECT * FROM agents"
    if not include_inactive:
        query += " WHERE active = 1"
    query += " ORDER BY name"
    with get_connection() as connection:
        return [dict(row) for row in connection.execute(query)]


def agent_names() -> list[str]:
    return [agent["name"] for agent in list_agents()]


def create_ticket(
    title: str,
    description: str,
    category: str,
    priority: str,
    requester_name: str,
    requester_email: str,
    requester_type: str = "Student",
    assignee: str | None = None,
    status: str = "New",
    created_at: datetime | None = None,
    resolved_at: datetime | None = None,
) -> int:
    """Insert a ticket and its opening audit event. Returns the new ticket id."""
    if not title.strip():
        raise ValueError("Ticket title is required")
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category: {category}")
    if priority not in PRIORITIES:
        raise ValueError(f"Unknown priority: {priority}")
    if status not in STATUSES:
        raise ValueError(f"Unknown status: {status}")

    created = created_at or datetime.now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO tickets (
                title, description, category, priority, status,
                requester_name, requester_email, requester_type,
                assignee, created_at, updated_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title.strip(),
                description.strip(),
                category,
                priority,
                status,
                requester_name.strip(),
                requester_email.strip(),
                requester_type,
                assignee,
                format_timestamp(created),
                format_timestamp(created),
                format_timestamp(resolved_at) if resolved_at else None,
            ),
        )
        ticket_id = int(cursor.lastrowid)
        connection.execute(
            """
            INSERT INTO ticket_events (
                ticket_id, event_type, note, actor, created_at
            ) VALUES (?, 'created', ?, ?, ?)
            """,
            (
                ticket_id,
                f"Ticket submitted with {priority} priority.",
                requester_name.strip(),
                format_timestamp(created),
            ),
        )
    return ticket_id


def get_ticket(ticket_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
    return dict(row) if row else None


def list_tickets(
    statuses: Iterable[str] | None = None,
    priorities: Iterable[str] | None = None,
    categories: Iterable[str] | None = None,
    assignees: Iterable[str] | None = None,
    search: str | None = None,
    requester_email: str | None = None,
) -> list[dict[str, Any]]:
    """Filtered ticket list, newest first.

    ``assignees`` accepts the sentinel "Unassigned" to match a NULL assignee,
    which is the filter agents reach for most often.
    """
    clauses: list[str] = []
    params: list[Any] = []

    def add_in_clause(column: str, values: Iterable[str] | None) -> None:
        values = list(values or [])
        if not values:
            return
        placeholders = ", ".join("?" for _ in values)
        clauses.append(f"{column} IN ({placeholders})")
        params.extend(values)

    add_in_clause("status", statuses)
    add_in_clause("priority", priorities)
    add_in_clause("category", categories)

    assignee_values = list(assignees or [])
    if assignee_values:
        named = [value for value in assignee_values if value != "Unassigned"]
        parts: list[str] = []
        if named:
            parts.append(f"assignee IN ({', '.join('?' for _ in named)})")
            params.extend(named)
        if "Unassigned" in assignee_values:
            parts.append("assignee IS NULL")
        clauses.append("(" + " OR ".join(parts) + ")")

    if requester_email:
        clauses.append("LOWER(requester_email) = ?")
        params.append(requester_email.strip().lower())

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        clauses.append(
            "(LOWER(title) LIKE ? OR LOWER(description) LIKE ?"
            " OR LOWER(requester_name) LIKE ? OR CAST(id AS TEXT) LIKE ?)"
        )
        params.extend([term, term, term, term])

    query = "SELECT * FROM tickets"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id DESC"

    with get_connection() as connection:
        return [dict(row) for row in connection.execute(query, params)]


def update_ticket(
    ticket_id: int,
    actor: str,
    changes: dict[str, Any],
    note: str | None = None,
    now: datetime | None = None,
) -> list[str]:
    """Apply field changes, writing one audit event per field that moved.

    Returns the list of fields that actually changed. Moving into a closed
    status stamps ``resolved_at``; moving back out clears it, so the SLA clock
    resumes instead of staying frozen at the old resolution time.
    """
    ticket = get_ticket(ticket_id)
    if ticket is None:
        raise ValueError(f"Ticket {ticket_id} does not exist")

    moment = now or datetime.now()
    stamp = format_timestamp(moment)
    applied: list[str] = []

    with get_connection() as connection:
        for field in EDITABLE_FIELDS:
            if field not in changes:
                continue
            new_value = changes[field]
            if isinstance(new_value, str):
                new_value = new_value.strip() or None
            old_value = ticket[field]
            if new_value == old_value:
                continue

            if field == "status" and new_value not in STATUSES:
                raise ValueError(f"Unknown status: {new_value}")
            if field == "priority" and new_value not in PRIORITIES:
                raise ValueError(f"Unknown priority: {new_value}")
            if field == "category" and new_value not in CATEGORIES:
                raise ValueError(f"Unknown category: {new_value}")

            connection.execute(
                f"UPDATE tickets SET {field} = ? WHERE id = ?", (new_value, ticket_id)
            )
            connection.execute(
                """
                INSERT INTO ticket_events (
                    ticket_id, event_type, field, old_value, new_value,
                    actor, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    f"{field}_change",
                    field,
                    old_value,
                    new_value,
                    actor,
                    stamp,
                ),
            )
            applied.append(field)

            if field == "status":
                if new_value in CLOSED_STATUSES and ticket["resolved_at"] is None:
                    connection.execute(
                        "UPDATE tickets SET resolved_at = ? WHERE id = ?",
                        (stamp, ticket_id),
                    )
                elif new_value in OPEN_STATUSES and ticket["resolved_at"] is not None:
                    connection.execute(
                        "UPDATE tickets SET resolved_at = NULL WHERE id = ?",
                        (ticket_id,),
                    )

        if note and note.strip():
            connection.execute(
                """
                INSERT INTO ticket_events (
                    ticket_id, event_type, note, actor, created_at
                ) VALUES (?, 'comment', ?, ?, ?)
                """,
                (ticket_id, note.strip(), actor, stamp),
            )
            applied.append("comment")

        if applied:
            connection.execute(
                "UPDATE tickets SET updated_at = ? WHERE id = ?", (stamp, ticket_id)
            )

    return applied


def add_comment(
    ticket_id: int, actor: str, note: str, now: datetime | None = None
) -> None:
    update_ticket(ticket_id, actor, changes={}, note=note, now=now)


def list_events(ticket_id: int) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM ticket_events WHERE ticket_id = ? ORDER BY id ASC",
            (ticket_id,),
        )
        return [dict(row) for row in rows]


def reset_database() -> None:
    """Drop everything and recreate the schema. Used by seeding and tests."""
    with get_connection() as connection:
        connection.executescript(
            "DROP TABLE IF EXISTS ticket_events;"
            "DROP TABLE IF EXISTS tickets;"
            "DROP TABLE IF EXISTS agents;"
        )
    init_db()
