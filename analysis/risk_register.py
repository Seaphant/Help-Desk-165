"""Part H: risk register with qualitative scores and dollar exposure.

Two scores are computed for every risk because they answer different questions.
Probability x Impact on a 1-5 scale is what fits on a heat map and drives
conversation; probability x dollar impact is what a budget decision needs. The
register is ranked on exposure, with the qualitative score reported alongside.

Run directly:
    python -m analysis.risk_register
"""

from __future__ import annotations

from dataclasses import dataclass

from analysis import assumptions as A
from analysis.assumptions import Risk

TOP_RISK_COUNT = 3


@dataclass
class RiskRegisterResult:
    risks: list[Risk]
    total_exposure: float
    top_risks: list[Risk]
    contingency_reserve: float


def ranked_risks() -> list[Risk]:
    """Risks ordered by dollar exposure, then by qualitative score."""
    return sorted(
        A.RISKS,
        key=lambda risk: (risk.exposure, risk.qualitative_score),
        reverse=True,
    )


def build_register() -> RiskRegisterResult:
    ordered = ranked_risks()
    total = round(sum(risk.exposure for risk in ordered), 2)
    return RiskRegisterResult(
        risks=ordered,
        total_exposure=total,
        top_risks=ordered[:TOP_RISK_COUNT],
        # A contingency reserve sized at total expected exposure is the standard
        # quantitative starting point; the report explains why CTS should hold
        # less than the full figure.
        contingency_reserve=total,
    )


def severity_band(risk: Risk) -> str:
    """Heat-map band for the 1-5 x 1-5 qualitative score."""
    score = risk.qualitative_score
    if score >= 15:
        return "Critical"
    if score >= 10:
        return "High"
    if score >= 5:
        return "Moderate"
    return "Low"


def as_table(result: RiskRegisterResult) -> list[dict[str, object]]:
    return [
        {
            "ID": risk.risk_id,
            "Category": risk.category,
            "Risk": risk.description,
            "P (1-5)": risk.probability_score,
            "I (1-5)": risk.impact_score,
            "P x I": risk.qualitative_score,
            "Band": severity_band(risk),
            "Probability": f"{risk.probability:.0%}",
            "Dollar impact": risk.dollar_impact,
            "Exposure (P x $)": risk.exposure,
            "Early warning trigger": risk.trigger,
        }
        for risk in result.risks
    ]


# ---------------------------------------------------------------------------
# Part K: mitigation, contingency, and monitoring for the top risks
# ---------------------------------------------------------------------------

RESPONSES: dict[str, dict[str, str]] = {
    "R3": {
        "strategy": "Mitigate, then transfer the decision to a gate",
        "mitigation": (
            "Do not build campus-wide first. Run the eight-week paid pilot in "
            "Classroom Technology and Canvas support, close the shared inbox for "
            "those two categories so the tool is the only intake path, and "
            "publish the SLA dashboard to the department's own leadership so "
            "they see the benefit in their own numbers. Name a department "
            "champion who is accountable for intake share, not the project team."
        ),
        "contingency": (
            "If intake share is still under 60 percent at week four, stop "
            "feature work and spend the remaining pilot weeks on the adoption "
            "blocker instead. If it is still under 60 percent at week eight, "
            "invoke the decision-tree stop branch: the full build is not funded "
            "and CTS loses the pilot cost rather than the build cost."
        ),
        "warning": (
            "Weekly intake share for the pilot categories, measured as tickets "
            "created in HelpDesk165 divided by total requests including those "
            "still arriving by email and walk-up."
        ),
    },
    "R2": {
        "strategy": "Mitigate through scope control and reserve sizing",
        "mitigation": (
            "Budget to the simulation's 80th-percentile cost rather than the "
            "point estimate, timebox the SSO integration spike to two weeks, and "
            "fix the launch scope in writing at the four features the pilot "
            "validated. Track sprint velocity from sprint one so the trend is "
            "visible before it becomes a slip."
        ),
        "contingency": (
            "Hold a pre-approved contingency drawdown the CTS director can "
            "release without a new funding request. If velocity misses twice, "
            "cut the roster-sync integration to a nightly CSV import, which the "
            "team estimated at one week instead of five."
        ),
        "warning": (
            "Two consecutive sprints closing below 70 percent of committed "
            "points, or the integration spike passing its timebox without a "
            "working token exchange."
        ),
    },
    "R5": {
        "strategy": "Avoid the exposure rather than manage it",
        "mitigation": (
            "Treat FERPA as a design constraint, not a launch checklist item. "
            "Ship role-based access control before the pilot handles a single "
            "real ticket, restrict ticket visibility to the requester plus "
            "assigned agents, and put a standing notice on the intake form "
            "telling requesters not to paste student IDs or grades. Book the "
            "campus security review at project start instead of before launch."
        ),
        "contingency": (
            "If the security review finds a defect, the pilot pauses and the "
            "affected tickets are purged and re-created without the sensitive "
            "field. A documented incident-response path to the campus privacy "
            "officer exists before the pilot opens, not after an incident."
        ),
        "warning": (
            "Any automated scan hit for a nine-digit student ID pattern in a "
            "ticket body, or any access-log entry showing a ticket read by an "
            "account that is neither the requester nor the assignee."
        ),
    },
}


def response_for(risk_id: str) -> dict[str, str]:
    return RESPONSES[risk_id]


def main() -> RiskRegisterResult:
    result = build_register()
    header = f"{'ID':<4}{'Category':<26}{'PxI':>5}{'Band':>10}{'Exposure':>12}"
    print(header)
    print("-" * len(header))
    for risk in result.risks:
        print(
            f"{risk.risk_id:<4}{risk.category:<26}{risk.qualitative_score:>5}"
            f"{severity_band(risk):>10}{risk.exposure:>12,.0f}"
        )
    print("-" * len(header))
    print(f"Total expected exposure: ${result.total_exposure:,.0f}")
    print(f"\nTop {TOP_RISK_COUNT} by exposure:")
    for rank, risk in enumerate(result.top_risks, start=1):
        print(f"  {rank}. {risk.risk_id} ({risk.category}) — ${risk.exposure:,.0f}")
    return result


if __name__ == "__main__":
    main()
