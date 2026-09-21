"""Tests for the business-hours SLA engine.

These exist because an incorrect breach number shown to management is risk R8
in the register, and the whole point of the dashboard is that the figures can be
trusted.
"""

from datetime import datetime

import pytest

from app import sla

# 2026-09-21 is a Monday; 2026-09-26 is a Saturday.
MONDAY_9AM = datetime(2026, 9, 21, 9, 0)
MONDAY_5PM = datetime(2026, 9, 21, 17, 0)
FRIDAY_5PM = datetime(2026, 9, 25, 17, 0)
SATURDAY_NOON = datetime(2026, 9, 26, 12, 0)
MONDAY_NEXT_9AM = datetime(2026, 9, 28, 9, 0)


class TestBusinessHours:
    def test_same_day_inside_window(self):
        assert sla.business_hours_between(MONDAY_9AM, MONDAY_5PM) == 8.0

    def test_end_before_start_is_zero(self):
        assert sla.business_hours_between(MONDAY_5PM, MONDAY_9AM) == 0.0

    def test_identical_timestamps_are_zero(self):
        assert sla.business_hours_between(MONDAY_9AM, MONDAY_9AM) == 0.0

    def test_time_before_opening_does_not_count(self):
        before_open = datetime(2026, 9, 21, 5, 0)
        assert sla.business_hours_between(before_open, MONDAY_9AM) == 1.0

    def test_time_after_closing_does_not_count(self):
        late = datetime(2026, 9, 21, 23, 30)
        assert sla.business_hours_between(MONDAY_5PM, late) == 1.0

    def test_weekend_contributes_nothing(self):
        # Friday 17:00 to Saturday noon: only Friday 17:00-18:00 is support time.
        assert sla.business_hours_between(FRIDAY_5PM, SATURDAY_NOON) == 1.0

    def test_weekend_is_skipped_entirely(self):
        saturday = datetime(2026, 9, 26, 9, 0)
        sunday = datetime(2026, 9, 27, 17, 0)
        assert sla.business_hours_between(saturday, sunday) == 0.0

    def test_spans_a_full_weekend(self):
        # Friday 17:00 to the following Monday 09:00 accrues only Friday
        # 17:00-18:00 and Monday 08:00-09:00, so two support hours across
        # 64 calendar hours.
        assert sla.business_hours_between(FRIDAY_5PM, MONDAY_NEXT_9AM) == 2.0

    def test_full_week_is_five_workdays(self):
        start = datetime(2026, 9, 21, 8, 0)
        end = datetime(2026, 9, 25, 18, 0)
        assert sla.business_hours_between(start, end) == 5 * sla.WORKDAY_HOURS

    def test_holiday_contributes_nothing(self):
        holiday = next(iter(sorted(sla.HOLIDAYS)))
        start = datetime(holiday.year, holiday.month, holiday.day, 9, 0)
        end = datetime(holiday.year, holiday.month, holiday.day, 17, 0)
        assert sla.business_hours_between(start, end) == 0.0
        assert sla.is_support_day(holiday) is False


class TestTargets:
    @pytest.mark.parametrize(
        "priority,expected",
        [("Urgent", 4.0), ("High", 8.0), ("Medium", 24.0), ("Low", 72.0)],
    )
    def test_documented_targets(self, priority, expected):
        assert sla.target_hours(priority) == expected

    def test_unknown_priority_falls_back_to_medium(self):
        assert sla.target_hours("Nonsense") == sla.SLA_TARGET_HOURS["Medium"]


class TestSlaStatus:
    def test_resolved_inside_target_is_met(self):
        resolved = datetime(2026, 9, 21, 11, 0)  # 2 support hours
        assert sla.sla_status("Urgent", MONDAY_9AM, resolved) == "Met"

    def test_resolved_outside_target_is_breached(self):
        resolved = datetime(2026, 9, 21, 15, 0)  # 6 support hours vs 4 target
        assert sla.sla_status("Urgent", MONDAY_9AM, resolved) == "Breached"

    def test_open_with_plenty_of_time_is_on_track(self):
        now = datetime(2026, 9, 21, 10, 0)  # 1 of 4 hours used
        assert sla.sla_status("Urgent", MONDAY_9AM, None, now) == "On Track"

    def test_open_past_the_at_risk_threshold(self):
        # 3 of 4 hours used is exactly the 75 percent warning line.
        now = datetime(2026, 9, 21, 12, 0)
        assert sla.sla_status("Urgent", MONDAY_9AM, None, now) == "At Risk"

    def test_open_past_the_target_is_breached(self):
        now = datetime(2026, 9, 21, 16, 0)
        assert sla.sla_status("Urgent", MONDAY_9AM, None, now) == "Breached"

    def test_weekend_does_not_breach_a_friday_ticket(self):
        """The reason the SLA clock is business hours in the first place."""
        friday_evening = datetime(2026, 9, 25, 17, 30)
        monday_morning = datetime(2026, 9, 28, 9, 0)
        assert sla.sla_status("High", friday_evening, None, monday_morning) == "On Track"
        # A naive calendar-hour clock would have called this breached long ago.
        elapsed = (monday_morning - friday_evening).total_seconds() / 3600
        assert elapsed > sla.target_hours("High")


class TestHoursRemaining:
    def test_positive_when_inside_target(self):
        now = datetime(2026, 9, 21, 10, 0)
        assert sla.hours_remaining("Urgent", MONDAY_9AM, None, now) == 3.0

    def test_negative_once_breached(self):
        now = datetime(2026, 9, 21, 15, 0)
        assert sla.hours_remaining("Urgent", MONDAY_9AM, None, now) == -2.0
