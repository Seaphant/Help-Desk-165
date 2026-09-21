"""Tests for ticket persistence, filtering, and the audit trail."""

from datetime import datetime

import pytest

from app import db

MONDAY_9AM = datetime(2026, 9, 21, 9, 0)


def make_ticket(**overrides) -> int:
    payload = {
        "title": "Projector in BBC 202 shows no signal",
        "description": "No HDMI signal from the podium PC or from my laptop.",
        "category": "Classroom Technology",
        "priority": "High",
        "requester_name": "Jordan Nguyen",
        "requester_email": "jordan.nguyen@sjsu.edu",
        "created_at": MONDAY_9AM,
    }
    payload.update(overrides)
    return db.create_ticket(**payload)


class TestCreateTicket:
    def test_returns_an_id_and_persists_the_row(self):
        ticket_id = make_ticket()
        ticket = db.get_ticket(ticket_id)
        assert ticket is not None
        assert ticket["title"] == "Projector in BBC 202 shows no signal"
        assert ticket["status"] == "New"
        assert ticket["assignee"] is None

    def test_writes_an_opening_audit_event(self):
        ticket_id = make_ticket()
        events = db.list_events(ticket_id)
        assert len(events) == 1
        assert events[0]["event_type"] == "created"

    def test_rejects_an_empty_title(self):
        with pytest.raises(ValueError, match="title is required"):
            make_ticket(title="   ")

    @pytest.mark.parametrize(
        "field,value",
        [
            ("category", "Telepathy"),
            ("priority", "Catastrophic"),
            ("status", "Vibes"),
        ],
    )
    def test_rejects_unknown_enum_values(self, field, value):
        with pytest.raises(ValueError):
            make_ticket(**{field: value})

    def test_strips_surrounding_whitespace(self):
        ticket_id = make_ticket(title="  Padded title here  ")
        assert db.get_ticket(ticket_id)["title"] == "Padded title here"

    def test_missing_ticket_returns_none(self):
        assert db.get_ticket(9999) is None


class TestUpdateTicket:
    def test_applies_changes_and_reports_which_fields_moved(self):
        ticket_id = make_ticket()
        changed = db.update_ticket(
            ticket_id,
            actor="Priya Raman",
            changes={"status": "In Progress", "assignee": "Priya Raman"},
        )
        assert set(changed) == {"status", "assignee"}
        ticket = db.get_ticket(ticket_id)
        assert ticket["status"] == "In Progress"
        assert ticket["assignee"] == "Priya Raman"

    def test_unchanged_values_are_not_recorded(self):
        ticket_id = make_ticket()
        changed = db.update_ticket(
            ticket_id, actor="Priya Raman", changes={"priority": "High"}
        )
        assert changed == []
        assert len(db.list_events(ticket_id)) == 1

    def test_one_audit_event_per_changed_field(self):
        ticket_id = make_ticket()
        db.update_ticket(
            ticket_id,
            actor="Priya Raman",
            changes={"status": "Open", "priority": "Urgent"},
            note="Escalating, the room has a class in 20 minutes.",
        )
        events = db.list_events(ticket_id)
        kinds = [event["event_type"] for event in events]
        assert kinds == ["created", "status_change", "priority_change", "comment"]
        status_event = events[1]
        assert status_event["old_value"] == "New"
        assert status_event["new_value"] == "Open"

    def test_closing_stamps_resolved_at(self):
        ticket_id = make_ticket()
        db.update_ticket(
            ticket_id, actor="Priya Raman", changes={"status": "Resolved"}
        )
        assert db.get_ticket(ticket_id)["resolved_at"] is not None

    def test_reopening_clears_resolved_at(self):
        """Otherwise the SLA clock would stay frozen at the old resolution time."""
        ticket_id = make_ticket()
        db.update_ticket(ticket_id, actor="Agent", changes={"status": "Resolved"})
        db.update_ticket(ticket_id, actor="Agent", changes={"status": "Open"})
        assert db.get_ticket(ticket_id)["resolved_at"] is None

    def test_unassigning_is_possible(self):
        ticket_id = make_ticket(assignee="Priya Raman")
        db.update_ticket(ticket_id, actor="Lead", changes={"assignee": None})
        assert db.get_ticket(ticket_id)["assignee"] is None

    def test_rejects_an_invalid_status(self):
        ticket_id = make_ticket()
        with pytest.raises(ValueError, match="Unknown status"):
            db.update_ticket(ticket_id, actor="Agent", changes={"status": "Vibes"})

    def test_rejects_an_unknown_ticket(self):
        with pytest.raises(ValueError, match="does not exist"):
            db.update_ticket(4242, actor="Agent", changes={"status": "Open"})

    def test_comment_only_update_records_a_comment(self):
        ticket_id = make_ticket()
        db.add_comment(ticket_id, actor="Jordan Nguyen", note="Still broken today.")
        events = db.list_events(ticket_id)
        assert events[-1]["event_type"] == "comment"
        assert events[-1]["note"] == "Still broken today."


class TestListTickets:
    @pytest.fixture(autouse=True)
    def sample_tickets(self):
        make_ticket(
            title="Wi-Fi drops in Engineering 285",
            description="My laptop disconnects from eduroam every five minutes.",
            category="Wi-Fi & Network",
            priority="Medium",
            status="Open",
            assignee="Lena Ortiz",
            requester_email="emily.patel@sjsu.edu",
        )
        make_ticket(
            title="Cannot log in to MySJSU",
            description="The portal rejects my credentials after a password reset.",
            category="Account & Login",
            priority="Urgent",
            status="New",
        )
        make_ticket(
            title="Printer quota not updating",
            description="I added twenty dollars and the balance still reads zero.",
            category="Printing",
            priority="Low",
            status="Closed",
            assignee="Marcus Webb",
        )

    def test_no_filters_returns_everything_newest_first(self):
        tickets = db.list_tickets()
        assert len(tickets) == 3
        assert tickets[0]["id"] > tickets[-1]["id"]

    def test_filter_by_status(self):
        assert len(db.list_tickets(statuses=["Open"])) == 1

    def test_filter_by_multiple_statuses(self):
        assert len(db.list_tickets(statuses=db.OPEN_STATUSES)) == 2

    def test_filter_by_priority(self):
        tickets = db.list_tickets(priorities=["Urgent"])
        assert [ticket["priority"] for ticket in tickets] == ["Urgent"]

    def test_filter_by_category(self):
        assert len(db.list_tickets(categories=["Printing"])) == 1

    def test_unassigned_sentinel_matches_null_owner(self):
        tickets = db.list_tickets(assignees=["Unassigned"])
        assert len(tickets) == 1
        assert tickets[0]["assignee"] is None

    def test_unassigned_can_combine_with_a_named_owner(self):
        tickets = db.list_tickets(assignees=["Unassigned", "Marcus Webb"])
        assert len(tickets) == 2

    def test_search_matches_the_title(self):
        assert len(db.list_tickets(search="wi-fi")) == 1

    def test_search_is_case_insensitive(self):
        assert len(db.list_tickets(search="MYSJSU")) == 1

    def test_search_matches_the_description(self):
        assert len(db.list_tickets(search="eduroam")) == 1

    def test_search_matches_a_ticket_number(self):
        target = db.list_tickets()[0]["id"]
        assert any(
            ticket["id"] == target for ticket in db.list_tickets(search=str(target))
        )

    def test_search_with_no_match_returns_nothing(self):
        assert db.list_tickets(search="zzzznotathing") == []

    def test_requester_scope_only_returns_that_persons_tickets(self):
        tickets = db.list_tickets(requester_email="EMILY.PATEL@sjsu.edu")
        assert len(tickets) == 1
        assert tickets[0]["requester_email"] == "emily.patel@sjsu.edu"

    def test_filters_combine_with_and(self):
        tickets = db.list_tickets(statuses=["Open"], categories=["Printing"])
        assert tickets == []


class TestAgents:
    def test_agents_are_unique_and_sorted(self):
        db.add_agent("Priya Raman", "Tier 1 Support")
        db.add_agent("Priya Raman", "Tier 1 Support")
        db.add_agent("Aisha Bello", "Classroom Technology")
        assert db.agent_names() == ["Aisha Bello", "Priya Raman"]
