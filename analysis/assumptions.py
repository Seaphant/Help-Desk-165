"""Single source of truth for every number used in the Project 1 analysis.

Changing a value here changes the NPV, the decision tree, the Monte Carlo
simulation, the report, and the generated deliverables together. Each figure
carries the reasoning that justifies it, because the assignment grades the
quality of the assumptions rather than the precision of the arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ORGANIZATION = "SJSU Campus Technology Services (CTS)"
PRODUCT = "HelpDesk165"
CURRENCY = "USD"


# ---------------------------------------------------------------------------
# Baseline operations (the "before HelpDesk165" picture)
# ---------------------------------------------------------------------------

# Derived from the prototype's own intake mix: CTS logs roughly 2,000 requests a
# month across the shared inbox, three departmental spreadsheets, and walk-ups.
ANNUAL_TICKET_VOLUME = 24_000

# Annual growth in request volume once more departments are onboarded.
TICKET_VOLUME_GROWTH = 0.05

# Blended loaded hourly cost of the people who touch a ticket: Tier 1 student
# assistants at roughly $22/hr loaded and Tier 2 staff at roughly $48/hr loaded,
# weighted by how many tickets each tier handles.
BLENDED_SUPPORT_RATE = 32.0

# Minutes of staff time removed per ticket. Two sources: structured intake
# eliminates the average 6 minutes of "please send a screenshot" back-and-forth,
# and category-based routing removes the 4 minutes a lead currently spends
# hand-assigning each request.
MINUTES_SAVED_PER_TICKET = 10.0

# Three departments each pay for a separate low-end tracker today. Consolidating
# onto one campus tool retires those subscriptions.
ANNUAL_TOOL_CONSOLIDATION_SAVINGS = 12_000.0


# ---------------------------------------------------------------------------
# Build cost (the "initial investment" in the NPV)
# ---------------------------------------------------------------------------

# Two engineers plus a part-time designer and product manager. 38 person-weeks
# is the team's bottom-up estimate for the production version: auth and SSO,
# real database, roster sync, reporting, accessibility, and hardening.
ENGINEERING_PERSON_WEEKS = 38.0
HOURS_PER_PERSON_WEEK = 40.0

# Loaded hourly cost of the delivery team (salary, benefits, overhead).
BLENDED_BUILD_RATE = 88.0

# One-time costs that are not engineering labor.
SSO_INTEGRATION_COST = 12_000.0          # Okta/Duo plus Banner roster sync
SECURITY_AND_ACCESSIBILITY_REVIEW = 8_000.0  # required before campus launch
INFRASTRUCTURE_SETUP_COST = 4_000.0     # managed Postgres, CI, monitoring

FIXED_ONE_TIME_COSTS = (
    SSO_INTEGRATION_COST
    + SECURITY_AND_ACCESSIBILITY_REVIEW
    + INFRASTRUCTURE_SETUP_COST
)

# Capital the CTS director has authority to approve without going back to the
# Vice President for Information Technology for a supplemental request.
APPROVED_CAPITAL_BUDGET = 185_000.0


# ---------------------------------------------------------------------------
# Run cost and adoption
# ---------------------------------------------------------------------------

# Hosting, monitoring, and roughly 0.25 FTE of ongoing maintenance.
ANNUAL_RUN_COST = 26_000.0

# Share of campus request volume flowing through HelpDesk165 each year. A tool
# nobody uses saves nothing, so benefits are scaled by this ramp while the run
# cost is incurred in full from year one.
ADOPTION_RAMP = {1: 0.55, 2: 0.90, 3: 1.00, 4: 1.00}

ANALYSIS_YEARS = 4

# The university's stated hurdle rate for internal IT investments.
DISCOUNT_RATE = 0.08


# ---------------------------------------------------------------------------
# Part C: weighted scoring model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Criterion:
    name: str
    weight: float
    rationale: str


SCORING_CRITERIA: tuple[Criterion, ...] = (
    Criterion(
        "Strategic alignment",
        0.25,
        "How directly the project advances the CTS goal of measurable service "
        "quality. Weighted highest because the division is funded against that "
        "goal.",
    ),
    Criterion(
        "Expected financial return",
        0.20,
        "Four-year NPV and the size of the recurring saving.",
    ),
    Criterion(
        "Time to first value",
        0.15,
        "How quickly a usable slice reaches real users. The division needs a win "
        "inside one academic year.",
    ),
    Criterion(
        "Delivery and technical risk",
        0.15,
        "Scored inversely: a higher score means lower risk.",
    ),
    Criterion(
        "Stakeholder demand and sponsorship",
        0.15,
        "Strength of the pull from departments and the presence of an executive "
        "sponsor.",
    ),
    Criterion(
        "Staffing feasibility",
        0.10,
        "Whether the current team can build it without new headcount.",
    ),
)

PROJECT_A_NAME = "Project A — HelpDesk165 ticketing and SLA reporting"
PROJECT_B_NAME = "Project B — Campus room and equipment booking portal"

# Scores are 1-10. The justification for each appears in the report.
PROJECT_A_SCORES = {
    "Strategic alignment": 9,
    "Expected financial return": 8,
    "Time to first value": 9,
    "Delivery and technical risk": 7,
    "Stakeholder demand and sponsorship": 9,
    "Staffing feasibility": 8,
}

PROJECT_B_SCORES = {
    "Strategic alignment": 6,
    "Expected financial return": 7,
    "Time to first value": 5,
    "Delivery and technical risk": 6,
    "Stakeholder demand and sponsorship": 6,
    "Staffing feasibility": 5,
}


# ---------------------------------------------------------------------------
# Part H: risk register
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Risk:
    risk_id: str
    category: str
    description: str
    probability_score: int      # 1-5 qualitative likelihood
    impact_score: int           # 1-5 qualitative severity
    probability: float          # quantitative likelihood for exposure
    dollar_impact: float        # cost to the project if it occurs
    trigger: str

    @property
    def qualitative_score(self) -> int:
        return self.probability_score * self.impact_score

    @property
    def exposure(self) -> float:
        return round(self.probability * self.dollar_impact, 2)


RISKS: tuple[Risk, ...] = (
    Risk(
        "R1", "Technical",
        "Okta/Duo single sign-on and the Banner roster sync take substantially "
        "longer than estimated because campus identity APIs are undocumented.",
        4, 4, 0.35, 34_000,
        "Integration spike runs past its two-week timebox without a working "
        "token exchange.",
    ),
    Risk(
        "R2", "Schedule / Cost",
        "Engineering effort is underestimated, pushing the build past the "
        "spring registration change freeze and over the approved capital budget.",
        5, 4, 0.45, 42_000,
        "Two consecutive sprints close below 70 percent of committed points.",
    ),
    Risk(
        "R3", "Organizational / Adoption",
        "Departments keep using the shared inbox and spreadsheets, so the "
        "labor savings that justify the whole business case never materialize.",
        3, 5, 0.30, 95_000,
        "Fewer than 60 percent of a pilot department's requests arrive through "
        "the tool after four weeks.",
    ),
    Risk(
        "R4", "People / Key person",
        "Only one engineer understands the SLA and reporting logic, so any "
        "absence stops that work entirely.",
        3, 4, 0.30, 22_000,
        "More than 60 percent of commits to the SLA and reporting modules come "
        "from a single author.",
    ),
    Risk(
        "R5", "Security / Compliance",
        "Ticket descriptions contain FERPA-protected student information while "
        "the prototype has no access control, creating a disclosure exposure and "
        "a failed pre-launch security review.",
        3, 5, 0.25, 60_000,
        "Any ticket body containing a student ID is readable by an account "
        "without a demonstrated need to know.",
    ),
    Risk(
        "R6", "External / Vendor",
        "Canvas and Banner API changes during the summer upgrade window break "
        "the roster and course sync.",
        2, 4, 0.20, 18_000,
        "Vendor release notes announce a breaking change to an endpoint the "
        "integration depends on.",
    ),
    Risk(
        "R7", "Scope",
        "Stakeholders demand a knowledge base, live chat, and a native mobile "
        "app before they will approve launch.",
        4, 3, 0.45, 30_000,
        "More than three new must-have features are added in a single steering "
        "committee meeting.",
    ),
    Risk(
        "R8", "Quality",
        "SLA and breach calculations go untested, management catches an "
        "incorrect number in a service review, and trust in the reporting is "
        "lost.",
        3, 4, 0.30, 20_000,
        "A stakeholder disputes a dashboard figure that the team cannot trace "
        "back to individual tickets.",
    ),
    Risk(
        "R9", "Operational / Architecture",
        "The prototype's single-file SQLite database does not survive "
        "concurrent campus-wide use and has to be migrated mid-project.",
        3, 3, 0.30, 16_000,
        "Database lock errors appear in logs once more than about 20 agents "
        "work the queue at once.",
    ),
)


# ---------------------------------------------------------------------------
# Part I: decision tree
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Outcome:
    label: str
    probability: float
    net_value: float
    rationale: str


@dataclass(frozen=True)
class Choice:
    label: str
    upfront_note: str
    outcomes: tuple[Outcome, ...] = field(default_factory=tuple)


DECISION_QUESTION = (
    "How should CTS fund the production version of HelpDesk165: build it "
    "outright now, license a commercial IT service-management product, or fund "
    "a small paid pilot first and decide afterwards?"
)

PILOT_COST = 46_000.0

DECISION_CHOICES: tuple[Choice, ...] = (
    Choice(
        "Build the full product now",
        "Commit the full ~$158K build immediately.",
        (
            Outcome(
                "Campus-wide adoption takes hold",
                0.60,
                205_000,
                "Four-year net value if departments move their intake onto the "
                "tool and the labor savings land as modeled.",
            ),
            Outcome(
                "Adoption stalls at a few departments",
                0.40,
                -95_000,
                "The build is paid for but most volume stays in the shared "
                "inbox, so only a fraction of the savings is realized.",
            ),
        ),
    ),
    Choice(
        "License a commercial ITSM product",
        "$58K/year licensing plus $30K implementation.",
        (
            Outcome(
                "Product fits campus processes as sold",
                0.55,
                120_000,
                "Savings arrive quickly but recurring license fees consume most "
                "of them.",
            ),
            Outcome(
                "Heavy customization is required",
                0.45,
                15_000,
                "Consultants and workflow rework erode almost all of the "
                "benefit.",
            ),
        ),
    ),
    Choice(
        "Fund an eight-week paid pilot, then decide",
        f"Spend ${PILOT_COST:,.0f} on a single-department pilot first.",
        (
            Outcome(
                "Pilot validates demand, then build",
                0.65,
                176_000,
                "Same build as option one, minus the pilot spend and one "
                "quarter of delayed benefit, but with adoption de-risked.",
            ),
            Outcome(
                "Pilot does not validate demand, stop",
                0.35,
                -PILOT_COST,
                "The pilot cost is lost, but the full build is never funded.",
            ),
        ),
    ),
)


# ---------------------------------------------------------------------------
# Part J: Monte Carlo input distributions
# ---------------------------------------------------------------------------

MONTE_CARLO_TRIALS = 10_000
MONTE_CARLO_SEED = 165

# Triangular distributions are given as (minimum, most likely, maximum).
EFFORT_PERSON_WEEKS_TRIANGULAR = (30.0, 38.0, 62.0)
"""Right-skewed: the team can beat the estimate a little, but software effort
overruns far more than it underruns."""

BUILD_RATE_NORMAL = (88.0, 7.0)
"""Mean and standard deviation of the blended loaded rate, truncated below."""
BUILD_RATE_BOUNDS = (70.0, 118.0)

SSO_REWORK_PROBABILITY = 0.35
SSO_REWORK_COST_TRIANGULAR = (8_000.0, 15_000.0, 34_000.0)
"""Matches risk R1: campus identity integration is the most likely source of
unplanned work."""

MINUTES_SAVED_TRIANGULAR = (4.0, 10.0, 14.0)
"""If structured intake works less well than hoped, the saving shrinks."""

STEADY_ADOPTION_TRIANGULAR = (0.55, 0.92, 1.00)
"""Steady-state share of campus volume in the tool, scaling the year 3-4 ramp."""

RUN_COST_UNIFORM = (20_000.0, 34_000.0)
"""Hosting and maintenance, which depends on the database tier chosen."""

# Thresholds the simulation reports probabilities against.
COST_OVERRUN_THRESHOLD = APPROVED_CAPITAL_BUDGET
NPV_THRESHOLD = 0.0
