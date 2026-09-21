"""Part D: net present value of the HelpDesk165 investment.

Run directly to print the year-by-year table:
    python -m analysis.npv
"""

from __future__ import annotations

from dataclasses import dataclass

from analysis import assumptions as A


@dataclass
class YearRow:
    year: int
    ticket_volume: float
    adoption: float
    labor_savings: float
    tool_savings: float
    gross_benefit: float
    run_cost: float
    net_cash_flow: float
    discount_factor: float
    present_value: float


@dataclass
class NpvResult:
    initial_cost: float
    discount_rate: float
    rows: list[YearRow]
    total_present_value: float
    npv: float
    roi: float
    irr: float | None
    simple_payback_year: int | None
    discounted_payback_year: int | None


def initial_cost(
    person_weeks: float = A.ENGINEERING_PERSON_WEEKS,
    build_rate: float = A.BLENDED_BUILD_RATE,
    fixed_costs: float = A.FIXED_ONE_TIME_COSTS,
) -> float:
    """Engineering labor plus the one-time costs that are not labor."""
    labor = person_weeks * A.HOURS_PER_PERSON_WEEK * build_rate
    return labor + fixed_costs


def annual_labor_savings(
    year: int,
    minutes_saved: float = A.MINUTES_SAVED_PER_TICKET,
    rate: float = A.BLENDED_SUPPORT_RATE,
    base_volume: float = A.ANNUAL_TICKET_VOLUME,
    growth: float = A.TICKET_VOLUME_GROWTH,
) -> tuple[float, float]:
    """Labor saving for a year, and the ticket volume it was computed from.

    Volume grows from year 2 onward as additional departments are onboarded.
    """
    volume = base_volume * ((1 + growth) ** (year - 1))
    savings = volume * (minutes_saved / 60.0) * rate
    return savings, volume


def compute_npv(
    person_weeks: float = A.ENGINEERING_PERSON_WEEKS,
    build_rate: float = A.BLENDED_BUILD_RATE,
    fixed_costs: float = A.FIXED_ONE_TIME_COSTS,
    minutes_saved: float = A.MINUTES_SAVED_PER_TICKET,
    support_rate: float = A.BLENDED_SUPPORT_RATE,
    run_cost: float = A.ANNUAL_RUN_COST,
    adoption_ramp: dict[int, float] | None = None,
    discount_rate: float = A.DISCOUNT_RATE,
    years: int = A.ANALYSIS_YEARS,
    tool_savings: float = A.ANNUAL_TOOL_CONSOLIDATION_SAVINGS,
) -> NpvResult:
    """Four-year NPV of building HelpDesk165.

    Benefits are scaled by the adoption ramp because a tool nobody uses saves
    nothing; the run cost is charged in full from year one because hosting and
    maintenance do not wait for adoption.
    """
    ramp = adoption_ramp or A.ADOPTION_RAMP
    investment = initial_cost(person_weeks, build_rate, fixed_costs)

    rows: list[YearRow] = []
    for year in range(1, years + 1):
        adoption = ramp.get(year, max(ramp.values()))
        labor, volume = annual_labor_savings(
            year, minutes_saved, support_rate, A.ANNUAL_TICKET_VOLUME,
            A.TICKET_VOLUME_GROWTH,
        )
        gross = (labor + tool_savings) * adoption
        net = gross - run_cost
        factor = 1.0 / ((1 + discount_rate) ** year)
        rows.append(
            YearRow(
                year=year,
                ticket_volume=round(volume),
                adoption=adoption,
                labor_savings=round(labor * adoption, 2),
                tool_savings=round(tool_savings * adoption, 2),
                gross_benefit=round(gross, 2),
                run_cost=run_cost,
                net_cash_flow=round(net, 2),
                discount_factor=round(factor, 5),
                present_value=round(net * factor, 2),
            )
        )

    total_pv = sum(row.present_value for row in rows)
    npv = total_pv - investment
    cash_flows = [-investment] + [row.net_cash_flow for row in rows]

    return NpvResult(
        initial_cost=round(investment, 2),
        discount_rate=discount_rate,
        rows=rows,
        total_present_value=round(total_pv, 2),
        npv=round(npv, 2),
        roi=round(npv / investment, 4) if investment else 0.0,
        irr=irr(cash_flows),
        simple_payback_year=_payback_year(
            investment, [row.net_cash_flow for row in rows]
        ),
        discounted_payback_year=_payback_year(
            investment, [row.present_value for row in rows]
        ),
    )


def _payback_year(investment: float, flows: list[float]) -> int | None:
    """First year in which cumulative inflows cover the investment."""
    cumulative = 0.0
    for index, flow in enumerate(flows, start=1):
        cumulative += flow
        if cumulative >= investment:
            return index
    return None


def npv_of(cash_flows: list[float], rate: float) -> float:
    """NPV of a cash-flow list whose first element is the time-zero outflow."""
    return sum(flow / ((1 + rate) ** period) for period, flow in enumerate(cash_flows))


def irr(cash_flows: list[float], low: float = -0.95, high: float = 10.0) -> float | None:
    """Internal rate of return by bisection.

    numpy dropped ``npv``/``irr`` from its top-level API, and adding a financial
    library for one number was not worth the dependency, so this is solved
    directly. Returns None when no sign change exists in the bracket.
    """
    f_low = npv_of(cash_flows, low)
    f_high = npv_of(cash_flows, high)
    if f_low * f_high > 0:
        return None

    for _ in range(200):
        mid = (low + high) / 2.0
        value = npv_of(cash_flows, mid)
        if abs(value) < 1e-6:
            return round(mid, 6)
        if f_low * value < 0:
            high = mid
            f_high = value
        else:
            low = mid
            f_low = value
    return round((low + high) / 2.0, 6)


def as_table(result: NpvResult) -> list[dict[str, object]]:
    """Rows shaped for CSV export and the calculation appendix."""
    table = [
        {
            "Year": 0,
            "Ticket volume": "",
            "Adoption": "",
            "Labor savings": "",
            "Tool savings": "",
            "Gross benefit": "",
            "Run cost": "",
            "Net cash flow": -result.initial_cost,
            "Discount factor": 1.0,
            "Present value": -result.initial_cost,
        }
    ]
    for row in result.rows:
        table.append(
            {
                "Year": row.year,
                "Ticket volume": row.ticket_volume,
                "Adoption": f"{row.adoption:.0%}",
                "Labor savings": row.labor_savings,
                "Tool savings": row.tool_savings,
                "Gross benefit": row.gross_benefit,
                "Run cost": -row.run_cost,
                "Net cash flow": row.net_cash_flow,
                "Discount factor": row.discount_factor,
                "Present value": row.present_value,
            }
        )
    table.append(
        {
            "Year": "NPV",
            "Ticket volume": "",
            "Adoption": "",
            "Labor savings": "",
            "Tool savings": "",
            "Gross benefit": "",
            "Run cost": "",
            "Net cash flow": "",
            "Discount factor": "",
            "Present value": result.npv,
        }
    )
    return table


def main() -> NpvResult:
    result = compute_npv()
    print(f"Initial development cost: ${result.initial_cost:,.0f}")
    print(f"Discount rate: {result.discount_rate:.0%}\n")
    header = (
        f"{'Yr':>3} {'Adopt':>6} {'Gross benefit':>14} {'Run cost':>10} "
        f"{'Net flow':>11} {'DF':>8} {'PV':>12}"
    )
    print(header)
    print("-" * len(header))
    for row in result.rows:
        print(
            f"{row.year:>3} {row.adoption:>6.0%} {row.gross_benefit:>14,.0f} "
            f"{-row.run_cost:>10,.0f} {row.net_cash_flow:>11,.0f} "
            f"{row.discount_factor:>8.5f} {row.present_value:>12,.0f}"
        )
    print("-" * len(header))
    print(f"Sum of present values: ${result.total_present_value:,.0f}")
    print(f"Less initial cost:     ${result.initial_cost:,.0f}")
    print(f"NET PRESENT VALUE:     ${result.npv:,.0f}")
    print(f"ROI on invested capital: {result.roi:.1%}")
    if result.irr is not None:
        print(f"IRR: {result.irr:.1%}")
    print(f"Simple payback: year {result.simple_payback_year}")
    print(f"Discounted payback: year {result.discounted_payback_year}")
    return result


if __name__ == "__main__":
    main()
