"""Service-level-agreement rules for HelpDesk165.

Campus Technology Services publishes its response targets in *business hours*,
not calendar hours: a Low-priority ticket filed at 5pm Friday is not late on
Saturday morning. Every SLA number in the app therefore runs through
``business_hours_between`` rather than a plain timedelta.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

# Support window: Monday-Friday, 08:00-18:00 campus local time.
WORKDAY_START = time(8, 0)
WORKDAY_END = time(18, 0)
WORKDAY_HOURS = 10.0

# Hours of support time allowed before a ticket is considered late.
SLA_TARGET_HOURS: dict[str, float] = {
    "Urgent": 4.0,
    "High": 8.0,
    "Medium": 24.0,
    "Low": 72.0,
}

# Fraction of the target that may be consumed before we warn the assignee.
AT_RISK_THRESHOLD = 0.75

# Campus holidays where no support hours accrue.
HOLIDAYS: frozenset[date] = frozenset(
    {
        date(2026, 1, 1),
        date(2026, 1, 19),
        date(2026, 5, 25),
        date(2026, 7, 3),
        date(2026, 9, 7),
        date(2026, 11, 26),
        date(2026, 11, 27),
        date(2026, 12, 25),
    }
)


def is_support_day(day: date) -> bool:
    """True when the campus help desk is staffed on ``day``."""
    return day.weekday() < 5 and day not in HOLIDAYS


def business_hours_between(start: datetime, end: datetime) -> float:
    """Support hours elapsed between two timestamps.

    Time outside the support window contributes nothing, so this is the clock
    the SLA targets are measured against. Returns 0.0 if ``end`` precedes
    ``start``.
    """
    if end <= start:
        return 0.0

    total = 0.0
    day = start.date()
    last_day = end.date()

    while day <= last_day:
        if is_support_day(day):
            window_open = datetime.combine(day, WORKDAY_START)
            window_close = datetime.combine(day, WORKDAY_END)
            overlap_start = max(start, window_open)
            overlap_end = min(end, window_close)
            if overlap_end > overlap_start:
                total += (overlap_end - overlap_start).total_seconds() / 3600.0
        day += timedelta(days=1)

    return round(total, 3)


def target_hours(priority: str) -> float:
    """SLA target for a priority, defaulting to the Medium target."""
    return SLA_TARGET_HOURS.get(priority, SLA_TARGET_HOURS["Medium"])


def elapsed_hours(
    created_at: datetime,
    resolved_at: datetime | None = None,
    now: datetime | None = None,
) -> float:
    """Support hours a ticket has consumed.

    Resolved tickets stop the clock at ``resolved_at``; open tickets keep
    accruing until ``now``.
    """
    end = resolved_at or now or datetime.now()
    return business_hours_between(created_at, end)


def sla_status(
    priority: str,
    created_at: datetime,
    resolved_at: datetime | None = None,
    now: datetime | None = None,
) -> str:
    """Classify a ticket as Met, Breached, At Risk, or On Track."""
    consumed = elapsed_hours(created_at, resolved_at, now)
    target = target_hours(priority)

    if resolved_at is not None:
        return "Met" if consumed <= target else "Breached"

    if consumed > target:
        return "Breached"
    if consumed >= target * AT_RISK_THRESHOLD:
        return "At Risk"
    return "On Track"


def hours_remaining(
    priority: str,
    created_at: datetime,
    resolved_at: datetime | None = None,
    now: datetime | None = None,
) -> float:
    """Support hours left before breach. Negative once the target is blown."""
    return round(
        target_hours(priority) - elapsed_hours(created_at, resolved_at, now), 2
    )
