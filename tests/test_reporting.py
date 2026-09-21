"""Tests for the derived metrics the dashboard displays."""

from datetime import datetime

from app import db, reporting, seed

MONDAY_9AM = datetime(2026, 9, 21, 9, 0)
MONDAY_2PM = datetime(2026, 9, 21, 14, 0)


def make_ticket(**overrides) -> int:
    payload = {
        "title": "Projector shows no signal",
        "description": "No HDMI signal from the podium PC.",
        "category": "Classroom Technology",
        "priority": "High",
        "requester_name": "Jordan Nguyen",
        "requester_email": "jordan.nguyen@sjsu.edu",
        "created_at": MONDAY_9AM,
    }
    payload.update(overrides)
    return db.create_ticket(**payload)


class TestEmptyState:
    def test_dataframe_has_columns_but_no_rows(self):
        frame = reporting.tickets_dataframe([])
        assert frame.empty
        assert "sla_status" in frame.columns

    def test_kpis_are_all_zero(self):
        metrics = reporting.kpis(reporting.tickets_dataframe([]))
        assert metrics["total"] == 0
        assert metrics["sla_compliance_pct"] == 0.0

    def test_charts_return_empty_frames(self):
        frame = reporting.tickets_dataframe([])
        assert reporting.volume_by_category(frame).empty
        assert reporting.sla_by_priority(frame).empty
        assert reporting.agent_workload(frame).empty
        assert reporting.weekly_intake(frame).empty

    def test_csv_export_still_has_a_header(self):
        csv_bytes = reporting.report_csv(reporting.tickets_dataframe([]))
        assert csv_bytes.decode().startswith("id,title,category")


class TestDerivedColumns:
    def test_open_ticket_is_flagged_open_and_unassigned_is_labelled(self):
        make_ticket(status="Open")
        frame = reporting.tickets_dataframe(db.list_tickets(), now=MONDAY_2PM)
        row = frame.iloc[0]
        assert row["is_open"] is True or bool(row["is_open"]) is True
        assert row["assignee"] == "Unassigned"

    def test_sla_columns_use_business_hours(self):
        make_ticket(status="Open", priority="High")
        frame = reporting.tickets_dataframe(db.list_tickets(), now=MONDAY_2PM)
        row = frame.iloc[0]
        assert row["support_hours_used"] == 5.0
        assert row["sla_target_hours"] == 8.0
        assert row["hours_remaining"] == 3.0
        assert row["sla_status"] == "On Track"

    def test_resolved_ticket_stops_the_clock(self):
        make_ticket(
            status="Resolved",
            priority="High",
            resolved_at=datetime(2026, 9, 21, 12, 0),
        )
        frame = reporting.tickets_dataframe(db.list_tickets(), now=MONDAY_2PM)
        row = frame.iloc[0]
        assert row["support_hours_used"] == 3.0
        assert row["sla_status"] == "Met"

    def test_age_buckets(self):
        make_ticket(status="Open", created_at=datetime(2026, 9, 21, 9, 0))
        frame = reporting.tickets_dataframe(
            db.list_tickets(), now=datetime(2026, 9, 30, 9, 0)
        )
        assert frame.iloc[0]["age_bucket"] == "> 7 days"


class TestKpis:
    def test_compliance_is_measured_on_closed_work_only(self):
        # One closed ticket inside its target, one closed ticket past it.
        make_ticket(
            status="Closed", priority="High",
            resolved_at=datetime(2026, 9, 21, 12, 0),
        )
        make_ticket(
            status="Closed", priority="Urgent",
            resolved_at=datetime(2026, 9, 21, 17, 0),
        )
        # An open ticket that has not passed or failed anything yet.
        make_ticket(status="Open", priority="Low")

        metrics = reporting.kpis(
            reporting.tickets_dataframe(db.list_tickets(), now=MONDAY_2PM)
        )
        assert metrics["total"] == 3
        assert metrics["open"] == 1
        assert metrics["resolved"] == 2
        assert metrics["sla_compliance_pct"] == 50.0

    def test_unassigned_counts_only_open_tickets(self):
        make_ticket(status="New")
        make_ticket(status="Closed", resolved_at=MONDAY_2PM)
        metrics = reporting.kpis(
            reporting.tickets_dataframe(db.list_tickets(), now=MONDAY_2PM)
        )
        assert metrics["unassigned"] == 1


class TestAgainstSeedData:
    def test_seed_produces_a_usable_dashboard(self):
        created = seed.seed_database(ticket_count=40)
        assert created == 40

        frame = reporting.tickets_dataframe(db.list_tickets())
        metrics = reporting.kpis(frame)

        assert metrics["total"] == 40
        assert metrics["open"] > 0, "the queue should not be empty in a demo"
        assert metrics["resolved"] > 0, "there should be history to report on"
        assert 0 < metrics["sla_compliance_pct"] < 100, (
            "the sample data needs both met and breached tickets for the "
            "dashboard to be worth showing"
        )
        assert not reporting.volume_by_category(frame).empty
        assert not reporting.sla_by_priority(frame).empty
        assert not reporting.weekly_intake(frame).empty

    def test_seeding_is_deterministic(self):
        first = seed.seed_database(ticket_count=25)
        titles_first = [ticket["title"] for ticket in db.list_tickets()]
        second = seed.seed_database(ticket_count=25)
        titles_second = [ticket["title"] for ticket in db.list_tickets()]
        assert first == second
        assert titles_first == titles_second

    def test_ensure_seeded_is_idempotent(self):
        assert seed.ensure_seeded() is True
        count = db.count_tickets()
        assert seed.ensure_seeded() is False
        assert db.count_tickets() == count

    def test_every_seeded_ticket_has_an_audit_trail(self):
        seed.seed_database(ticket_count=20)
        for ticket in db.list_tickets():
            assert db.list_events(ticket["id"]), (
                f"ticket {ticket['id']} has no history"
            )
