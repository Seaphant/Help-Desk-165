"""Build the calculation appendix workbook the assignment asks for.

Where a figure is a calculation rather than an input, the cell carries a live
Excel formula instead of a baked value. A grader can click any weighted score,
discount factor, present value, or expected monetary value and see the
arithmetic, and can change an assumption and watch the totals move.

Run:
    python -m tools.build_workbook docs/deliverables/CMPE165_Project1_Calculations.xlsx
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from analysis import assumptions as A
from analysis import decision_tree, monte_carlo, npv, risk_register, weighted_scoring

HEADER_FILL = PatternFill("solid", fgColor="0055A2")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(bold=True, size=14, color="0055A2")
NOTE_FONT = Font(italic=True, size=9, color="555555")
TOTAL_FONT = Font(bold=True)
FORMULA_FILL = PatternFill("solid", fgColor="FFF6E0")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

MONEY = '"$"#,##0'
MONEY_CENTS = '"$"#,##0.00'
PERCENT = "0.0%"
FACTOR = "0.00000"


def write_title(sheet, title: str, note: str = "") -> int:
    """Write the sheet title and optional note. Returns the next free row."""
    sheet["A1"] = title
    sheet["A1"].font = TITLE_FONT
    if note:
        sheet["A2"] = note
        sheet["A2"].font = NOTE_FONT
        sheet["A2"].alignment = Alignment(wrap_text=True, vertical="top")
        sheet.row_dimensions[2].height = 30
        return 4
    return 3


def write_header(sheet, row: int, headers: list[str]) -> None:
    for column, heading in enumerate(headers, start=1):
        cell = sheet.cell(row=row, column=column, value=heading)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        cell.border = BORDER
    sheet.row_dimensions[row].height = 30
    sheet.freeze_panes = sheet.cell(row=row + 1, column=1)


def set_widths(sheet, widths: dict[str, int]) -> None:
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width


def mark_formula(cell) -> None:
    cell.fill = FORMULA_FILL


# ---------------------------------------------------------------------------
# Sheets
# ---------------------------------------------------------------------------


def sheet_read_me(workbook: Workbook) -> None:
    sheet = workbook.active
    sheet.title = "Read me"
    row = write_title(
        sheet,
        "HelpDesk165 — Calculation Appendix",
        "CMPE 165 Project 1. Every number in the written report and the class "
        "deck is produced by the scripts in analysis/ and reproduced here. "
        "Shaded cells are live Excel formulas, not pasted values.",
    )

    entries = [
        ("Organization", A.ORGANIZATION),
        ("Product", A.PRODUCT),
        ("Recommendation", "GO WITH CONDITIONS"),
        ("", ""),
        ("Regenerate everything", "python -m analysis.run_all"),
        ("Rebuild this workbook", "python -m tools.build_workbook"),
        ("Run the test suite", "python -m pytest -q"),
        ("Run the prototype", "streamlit run app/Home.py"),
        ("", ""),
        ("Sheet", "What it contains"),
        ("Assumptions", "Every input, with the reasoning behind it"),
        ("Part C Scoring", "Weighted scoring model, Project A vs Project B"),
        ("Part D NPV", "Four-year discounted cash flow and NPV"),
        ("Part H Risks", "Risk register with qualitative score and dollar exposure"),
        ("Part I Decision Tree", "Three funding options and their expected values"),
        ("Part J Inputs", "Monte Carlo distributions for six uncertain variables"),
        ("Part J Results", "Simulated cost and NPV, percentiles, and thresholds"),
        ("Part J Sensitivity", "Which uncertainty actually moves the business case"),
    ]

    for label, value in entries:
        if label:
            sheet.cell(row=row, column=1, value=label).font = Font(bold=True)
            sheet.cell(row=row, column=2, value=value)
        row += 1

    set_widths(sheet, {"A": 26, "B": 74})


def sheet_assumptions(workbook: Workbook) -> None:
    sheet = workbook.create_sheet("Assumptions")
    row = write_title(
        sheet,
        "Assumptions",
        "These are the only inputs. Everything else in this workbook is derived "
        "from them. Source: analysis/assumptions.py.",
    )
    write_header(sheet, row, ["Input", "Value", "Unit", "Basis"])
    row += 1

    rows = [
        ("Annual ticket volume", A.ANNUAL_TICKET_VOLUME, "tickets/year",
         "About 2,000 requests a month across the shared inbox, three "
         "departmental spreadsheets, and walk-ups."),
        ("Ticket volume growth", A.TICKET_VOLUME_GROWTH, "per year",
         "Additional departments onboarded after launch."),
        ("Blended support labor rate", A.BLENDED_SUPPORT_RATE, "$/hour",
         "Tier 1 student assistants near $22 loaded and Tier 2 staff near $48 "
         "loaded, weighted by ticket mix."),
        ("Minutes saved per ticket", A.MINUTES_SAVED_PER_TICKET, "minutes",
         "Six minutes of screenshot back-and-forth removed by structured "
         "intake, plus four minutes of manual triage removed by routing."),
        ("Tool consolidation savings", A.ANNUAL_TOOL_CONSOLIDATION_SAVINGS,
         "$/year", "Three departmental trackers retired."),
        ("Engineering effort", A.ENGINEERING_PERSON_WEEKS, "person-weeks",
         "Bottom-up estimate for the production build: SSO, real database, "
         "roster sync, reporting, accessibility, hardening."),
        ("Hours per person-week", A.HOURS_PER_PERSON_WEEK, "hours", "Standard."),
        ("Blended build rate", A.BLENDED_BUILD_RATE, "$/hour",
         "Loaded cost of the delivery team."),
        ("SSO and roster integration", A.SSO_INTEGRATION_COST, "$ one-time",
         "Okta/Duo plus the Banner roster sync."),
        ("Security and accessibility review", A.SECURITY_AND_ACCESSIBILITY_REVIEW,
         "$ one-time", "Required before any campus launch."),
        ("Infrastructure setup", A.INFRASTRUCTURE_SETUP_COST, "$ one-time",
         "Managed Postgres, CI, monitoring."),
        ("Annual run cost", A.ANNUAL_RUN_COST, "$/year",
         "Hosting, monitoring, and about 0.25 FTE of maintenance."),
        ("Approved capital budget", A.APPROVED_CAPITAL_BUDGET, "$",
         "What the CTS Director can approve without a supplemental request."),
        ("Discount rate", A.DISCOUNT_RATE, "per year",
         "The university's stated hurdle rate for internal IT investments."),
        ("Analysis horizon", A.ANALYSIS_YEARS, "years", "Assignment minimum."),
        ("Pilot cost", A.PILOT_COST, "$",
         "Eight-week paid pilot in two support categories."),
        ("Monte Carlo trials", A.MONTE_CARLO_TRIALS, "trials",
         "Assignment minimum is 1,000."),
        ("Random seed", A.MONTE_CARLO_SEED, "", "Makes every figure reproducible."),
    ]

    for label, value, unit, basis in rows:
        sheet.cell(row=row, column=1, value=label)
        cell = sheet.cell(row=row, column=2, value=value)
        if unit.startswith("$"):
            cell.number_format = MONEY
        elif unit == "per year" and isinstance(value, float) and value < 1:
            cell.number_format = PERCENT
        sheet.cell(row=row, column=3, value=unit)
        note = sheet.cell(row=row, column=4, value=basis)
        note.alignment = Alignment(wrap_text=True, vertical="top")
        for column in range(1, 5):
            sheet.cell(row=row, column=column).border = BORDER
        row += 1

    sheet.cell(row=row + 1, column=1, value="Adoption ramp (share of volume in the tool)").font = TOTAL_FONT
    row += 2
    for year, adoption in A.ADOPTION_RAMP.items():
        sheet.cell(row=row, column=1, value=f"Year {year}")
        cell = sheet.cell(row=row, column=2, value=adoption)
        cell.number_format = PERCENT
        row += 1

    set_widths(sheet, {"A": 34, "B": 14, "C": 14, "D": 62})


def sheet_scoring(workbook: Workbook) -> None:
    result = weighted_scoring.score_projects()
    sheet = workbook.create_sheet("Part C Scoring")
    row = write_title(
        sheet,
        "Part C — Weighted Scoring Model",
        "Weights total 100 percent. Scores are 1-10. The weighted columns are "
        "live formulas: weight x score.",
    )
    write_header(
        sheet,
        row,
        ["Criterion", "Weight", "A score", "A weighted", "B score", "B weighted",
         "Why this criterion carries this weight"],
    )
    header_row = row
    row += 1
    first_data = row

    for score_row in result.rows:
        sheet.cell(row=row, column=1, value=score_row.criterion)
        weight = sheet.cell(row=row, column=2, value=score_row.weight)
        weight.number_format = PERCENT
        sheet.cell(row=row, column=3, value=score_row.score_a)
        weighted_a = sheet.cell(row=row, column=4, value=f"=B{row}*C{row}")
        weighted_a.number_format = "0.00"
        mark_formula(weighted_a)
        sheet.cell(row=row, column=5, value=score_row.score_b)
        weighted_b = sheet.cell(row=row, column=6, value=f"=B{row}*E{row}")
        weighted_b.number_format = "0.00"
        mark_formula(weighted_b)
        rationale = sheet.cell(row=row, column=7, value=score_row.rationale)
        rationale.alignment = Alignment(wrap_text=True, vertical="top")
        for column in range(1, 8):
            sheet.cell(row=row, column=column).border = BORDER
        row += 1

    last_data = row - 1
    sheet.cell(row=row, column=1, value="TOTAL").font = TOTAL_FONT
    total_weight = sheet.cell(row=row, column=2, value=f"=SUM(B{first_data}:B{last_data})")
    total_weight.number_format = PERCENT
    total_weight.font = TOTAL_FONT
    mark_formula(total_weight)
    for column, letter in ((4, "D"), (6, "F")):
        cell = sheet.cell(
            row=row, column=column,
            value=f"=SUM({letter}{first_data}:{letter}{last_data})",
        )
        cell.number_format = "0.00"
        cell.font = TOTAL_FONT
        mark_formula(cell)

    verdict = row + 2
    sheet.cell(row=verdict, column=1, value="Project A").font = TOTAL_FONT
    sheet.cell(row=verdict, column=2, value=result.project_a)
    sheet.cell(row=verdict + 1, column=1, value="Project B").font = TOTAL_FONT
    sheet.cell(row=verdict + 1, column=2, value=result.project_b)
    sheet.cell(row=verdict + 2, column=1, value="Margin").font = TOTAL_FONT
    margin = sheet.cell(row=verdict + 2, column=2, value=f"=D{row}-F{row}")
    margin.number_format = "0.00"
    mark_formula(margin)
    sheet.cell(row=verdict + 3, column=1, value="Decision").font = TOTAL_FONT
    sheet.cell(row=verdict + 3, column=2, value=f"Fund {result.winner}")
    sheet.cell(
        row=verdict + 4, column=1,
        value="Sensitivity: no single criterion weight between 0 and 100 percent "
              "reverses this result. See analysis/weighted_scoring.py.",
    ).font = NOTE_FONT

    chart = BarChart()
    chart.title = "Weighted score by criterion"
    chart.y_axis.title = "Weighted contribution"
    data = Reference(sheet, min_col=4, max_col=4, min_row=header_row, max_row=last_data)
    data_b = Reference(sheet, min_col=6, max_col=6, min_row=header_row, max_row=last_data)
    categories = Reference(sheet, min_col=1, min_row=first_data, max_row=last_data)
    chart.add_data(data, titles_from_data=True)
    chart.add_data(data_b, titles_from_data=True)
    chart.set_categories(categories)
    chart.height = 8
    chart.width = 18
    sheet.add_chart(chart, f"A{verdict + 7}")

    set_widths(sheet, {"A": 34, "B": 10, "C": 10, "D": 12, "E": 10, "F": 12, "G": 60})


def sheet_npv(workbook: Workbook) -> None:
    result = npv.compute_npv()
    sheet = workbook.create_sheet("Part D NPV")
    row = write_title(
        sheet,
        "Part D — Net Present Value",
        "NPV = -C0 + sum over t of Bt / (1 + r)^t. Discount factors, present "
        "values, and the NPV total are live formulas.",
    )

    sheet.cell(row=row, column=1, value="Discount rate (r)").font = TOTAL_FONT
    rate_cell = sheet.cell(row=row, column=2, value=A.DISCOUNT_RATE)
    rate_cell.number_format = PERCENT
    rate_ref = f"$B${row}"
    row += 1
    sheet.cell(row=row, column=1, value="Initial development cost (C0)").font = TOTAL_FONT
    cost_cell = sheet.cell(row=row, column=2, value=result.initial_cost)
    cost_cell.number_format = MONEY
    cost_ref = f"$B${row}"
    row += 2

    write_header(
        sheet, row,
        ["Year", "Ticket volume", "Adoption", "Labor savings", "Tool savings",
         "Gross benefit", "Run cost", "Net cash flow", "Discount factor",
         "Present value"],
    )
    row += 1
    first_data = row

    for year_row in result.rows:
        sheet.cell(row=row, column=1, value=year_row.year)
        sheet.cell(row=row, column=2, value=year_row.ticket_volume)
        adoption = sheet.cell(row=row, column=3, value=year_row.adoption)
        adoption.number_format = PERCENT
        for column, value in (
            (4, year_row.labor_savings),
            (5, year_row.tool_savings),
        ):
            cell = sheet.cell(row=row, column=column, value=value)
            cell.number_format = MONEY
        gross = sheet.cell(row=row, column=6, value=f"=D{row}+E{row}")
        gross.number_format = MONEY
        mark_formula(gross)
        run_cost = sheet.cell(row=row, column=7, value=-year_row.run_cost)
        run_cost.number_format = MONEY
        net = sheet.cell(row=row, column=8, value=f"=F{row}+G{row}")
        net.number_format = MONEY
        mark_formula(net)
        factor = sheet.cell(
            row=row, column=9, value=f"=ROUND(1/(1+{rate_ref})^A{row},5)"
        )
        factor.number_format = FACTOR
        mark_formula(factor)
        present = sheet.cell(row=row, column=10, value=f"=H{row}*I{row}")
        present.number_format = MONEY
        mark_formula(present)
        for column in range(1, 11):
            sheet.cell(row=row, column=column).border = BORDER
        row += 1

    last_data = row - 1
    sheet.cell(row=row, column=1, value="Sum of present values").font = TOTAL_FONT
    total_pv = sheet.cell(row=row, column=10, value=f"=SUM(J{first_data}:J{last_data})")
    total_pv.number_format = MONEY
    total_pv.font = TOTAL_FONT
    mark_formula(total_pv)
    pv_row = row
    row += 1

    sheet.cell(row=row, column=1, value="Less initial cost").font = TOTAL_FONT
    less = sheet.cell(row=row, column=10, value=f"=-{cost_ref}")
    less.number_format = MONEY
    mark_formula(less)
    row += 1

    sheet.cell(row=row, column=1, value="NET PRESENT VALUE").font = TOTAL_FONT
    npv_cell = sheet.cell(row=row, column=10, value=f"=J{pv_row}-{cost_ref}")
    npv_cell.number_format = MONEY
    npv_cell.font = Font(bold=True, size=12, color="1E6F45")
    mark_formula(npv_cell)
    row += 2

    extras = [
        ("ROI on invested capital", f"=J{row - 2}/{cost_ref}", PERCENT),
        ("IRR", result.irr, PERCENT),
        ("Simple payback", f"Year {result.simple_payback_year}", None),
        ("Discounted payback", f"Year {result.discounted_payback_year}", None),
    ]
    for label, value, number_format in extras:
        sheet.cell(row=row, column=1, value=label).font = TOTAL_FONT
        cell = sheet.cell(row=row, column=2, value=value)
        if number_format:
            cell.number_format = number_format
        if isinstance(value, str) and value.startswith("="):
            mark_formula(cell)
        row += 1

    sheet.cell(
        row=row + 1, column=1,
        value="Benefits are scaled by the adoption ramp because a tool nobody "
              "uses saves nothing. The run cost is charged in full from year one "
              "because hosting does not wait for adoption. Part J shows why this "
              "positive NPV is not sufficient grounds to fund the full build.",
    ).font = NOTE_FONT

    set_widths(
        sheet,
        {"A": 26, "B": 14, "C": 11, "D": 15, "E": 13, "F": 15, "G": 12,
         "H": 15, "I": 15, "J": 15},
    )


def sheet_risks(workbook: Workbook) -> None:
    result = risk_register.build_register()
    sheet = workbook.create_sheet("Part H Risks")
    row = write_title(
        sheet,
        "Part H — Risk Register",
        "Two scores per risk. Probability x Impact on a 1-5 scale drives the heat "
        "map; probability x dollar impact drives the budget. Ranked on exposure.",
    )
    write_header(
        sheet, row,
        ["ID", "Category", "Risk", "P (1-5)", "I (1-5)", "P x I", "Band",
         "Probability", "Dollar impact", "Exposure", "Early warning trigger"],
    )
    row += 1
    first_data = row

    for risk in result.risks:
        sheet.cell(row=row, column=1, value=risk.risk_id)
        sheet.cell(row=row, column=2, value=risk.category)
        description = sheet.cell(row=row, column=3, value=risk.description)
        description.alignment = Alignment(wrap_text=True, vertical="top")
        sheet.cell(row=row, column=4, value=risk.probability_score)
        sheet.cell(row=row, column=5, value=risk.impact_score)
        product = sheet.cell(row=row, column=6, value=f"=D{row}*E{row}")
        mark_formula(product)
        sheet.cell(row=row, column=7, value=risk_register.severity_band(risk))
        probability = sheet.cell(row=row, column=8, value=risk.probability)
        probability.number_format = PERCENT
        impact = sheet.cell(row=row, column=9, value=risk.dollar_impact)
        impact.number_format = MONEY
        exposure = sheet.cell(row=row, column=10, value=f"=H{row}*I{row}")
        exposure.number_format = MONEY
        mark_formula(exposure)
        trigger = sheet.cell(row=row, column=11, value=risk.trigger)
        trigger.alignment = Alignment(wrap_text=True, vertical="top")
        for column in range(1, 12):
            sheet.cell(row=row, column=column).border = BORDER
        sheet.row_dimensions[row].height = 46
        row += 1

    last_data = row - 1
    sheet.cell(row=row, column=3, value="Total expected exposure").font = TOTAL_FONT
    total = sheet.cell(row=row, column=10, value=f"=SUM(J{first_data}:J{last_data})")
    total.number_format = MONEY
    total.font = TOTAL_FONT
    mark_formula(total)
    row += 2

    sheet.cell(row=row, column=1, value="Part K — response for the three highest exposures").font = TITLE_FONT
    row += 1
    write_header(sheet, row, ["ID", "Strategy", "Mitigation", "Contingency", "Early warning"])
    row += 1
    for risk in result.top_risks:
        response = risk_register.response_for(risk.risk_id)
        sheet.cell(row=row, column=1, value=risk.risk_id)
        for column, key in enumerate(
            ("strategy", "mitigation", "contingency", "warning"), start=2
        ):
            cell = sheet.cell(row=row, column=column, value=response[key])
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = BORDER
        sheet.row_dimensions[row].height = 116
        row += 1

    set_widths(
        sheet,
        {"A": 7, "B": 24, "C": 52, "D": 9, "E": 9, "F": 8, "G": 11, "H": 12,
         "I": 14, "J": 13, "K": 48},
    )


def sheet_decision_tree(workbook: Workbook) -> None:
    result = decision_tree.evaluate()
    sheet = workbook.create_sheet("Part I Decision Tree")
    row = write_title(
        sheet,
        "Part I — Decision Tree and Expected Monetary Value",
        f"Decision: {result.question} EMV = sum of probability x value. The "
        "contribution and EMV columns are live formulas.",
    )
    write_header(
        sheet, row,
        ["Decision", "Outcome", "Probability", "Net value (4 yr)",
         "P x value", "Branch EMV", "Reasoning"],
    )
    row += 1

    branch_rows: list[tuple[str, int]] = []
    for branch in result.branches:
        start = row
        for outcome in branch.choice.outcomes:
            sheet.cell(row=row, column=1, value=branch.label)
            sheet.cell(row=row, column=2, value=outcome.label)
            probability = sheet.cell(row=row, column=3, value=outcome.probability)
            probability.number_format = PERCENT
            value = sheet.cell(row=row, column=4, value=outcome.net_value)
            value.number_format = MONEY
            contribution = sheet.cell(row=row, column=5, value=f"=C{row}*D{row}")
            contribution.number_format = MONEY
            mark_formula(contribution)
            reasoning = sheet.cell(row=row, column=7, value=outcome.rationale)
            reasoning.alignment = Alignment(wrap_text=True, vertical="top")
            for column in range(1, 8):
                sheet.cell(row=row, column=column).border = BORDER
            row += 1
        emv = sheet.cell(row=start, column=6, value=f"=SUM(E{start}:E{row - 1})")
        emv.number_format = MONEY
        emv.font = TOTAL_FONT
        mark_formula(emv)
        branch_rows.append((branch.label, start))
        row += 1

    sheet.cell(row=row, column=1, value="Comparison").font = TITLE_FONT
    row += 1
    write_header(sheet, row, ["Option", "EMV", "Best case", "Worst case", "P(loss)"])
    row += 1
    compare_first = row
    for branch in sorted(result.branches, key=lambda item: item.emv, reverse=True):
        source = next(start for label, start in branch_rows if label == branch.label)
        sheet.cell(row=row, column=1, value=branch.label)
        emv = sheet.cell(row=row, column=2, value=f"=F{source}")
        emv.number_format = MONEY
        mark_formula(emv)
        best = sheet.cell(row=row, column=3, value=branch.best_case)
        best.number_format = MONEY
        worst = sheet.cell(row=row, column=4, value=branch.worst_case)
        worst.number_format = MONEY
        loss = sheet.cell(row=row, column=5, value=branch.downside_probability)
        loss.number_format = PERCENT
        for column in range(1, 6):
            sheet.cell(row=row, column=column).border = BORDER
        row += 1

    compare_last = row - 1
    row += 1
    sheet.cell(row=row, column=1, value="Decision").font = TOTAL_FONT
    sheet.cell(
        row=row, column=2,
        value=f"{result.recommended.label} — highest EMV at "
              f"${result.recommended.emv:,.0f}, "
              f"${result.emv_margin:,.0f} ahead of {result.runner_up.label}, "
              f"and it caps the downside at ${abs(result.recommended.worst_case):,.0f} "
              f"instead of ${abs(result.branches[0].worst_case):,.0f}.",
    ).alignment = Alignment(wrap_text=True, vertical="top")
    sheet.row_dimensions[row].height = 46

    chart = BarChart()
    chart.title = "Expected monetary value by funding option"
    chart.y_axis.title = "EMV (USD)"
    data = Reference(sheet, min_col=2, min_row=compare_first - 1, max_row=compare_last)
    categories = Reference(sheet, min_col=1, min_row=compare_first, max_row=compare_last)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    chart.height = 8
    chart.width = 18
    sheet.add_chart(chart, f"A{row + 3}")

    set_widths(
        sheet,
        {"A": 34, "B": 34, "C": 12, "D": 16, "E": 14, "F": 14, "G": 52},
    )


def sheet_monte_carlo(workbook: Workbook, chart_dir: Path) -> None:
    result = monte_carlo.simulate()
    data = monte_carlo.summary(result)

    inputs = workbook.create_sheet("Part J Inputs")
    row = write_title(
        inputs,
        "Part J — Monte Carlo Input Distributions",
        f"{result.trials:,} trials, seed {result.seed}. Six uncertain variables; "
        "the assignment asks for at least three.",
    )
    write_header(inputs, row, ["Variable", "Distribution", "Parameters", "Sampled mean"])
    row += 1
    for entry in monte_carlo.input_table(result):
        inputs.cell(row=row, column=1, value=entry["Variable"])
        inputs.cell(row=row, column=2, value=entry["Distribution"])
        inputs.cell(row=row, column=3, value=entry["Parameters"])
        inputs.cell(row=row, column=4, value=entry["Sampled mean"])
        for column in range(1, 5):
            inputs.cell(row=row, column=column).border = BORDER
        row += 1
    inputs.cell(
        row=row + 1, column=1,
        value="Effort is triangular and right-skewed because software effort "
              "overruns far more often than it underruns. That asymmetry is the "
              "reason the simulated mean cost exceeds the team's point estimate.",
    ).font = NOTE_FONT
    set_widths(inputs, {"A": 36, "B": 22, "C": 52, "D": 14})

    results = workbook.create_sheet("Part J Results")
    row = write_title(
        results,
        "Part J — Simulation Results",
        "The deterministic figures in Part D use the mode of every input. These "
        "are the distributions those single values were hiding.",
    )

    results.cell(row=row, column=1, value="Build cost").font = TITLE_FONT
    row += 1
    cost_rows = [
        ("Team point estimate (Part D)", data["deterministic_cost"]),
        ("Simulated mean", data["mean_cost"]),
        ("Median (P50)", data["median_cost"]),
        ("Low case (P10)", data["cost_p10"]),
        ("P80 — recommended budget", data["cost_p80"]),
        ("High case (P90)", data["cost_p90"]),
        ("Optimism gap (mean minus estimate)", data["optimism_gap"]),
        ("Approved capital budget", data["budget_threshold"]),
    ]
    for label, value in cost_rows:
        results.cell(row=row, column=1, value=label)
        cell = results.cell(row=row, column=2, value=value)
        cell.number_format = MONEY
        row += 1
    results.cell(row=row, column=1, value="P(cost exceeds approved budget)").font = TOTAL_FONT
    over = results.cell(row=row, column=2, value=data["probability_over_budget"])
    over.number_format = PERCENT
    over.font = Font(bold=True, color="C4504B")
    row += 2

    results.cell(row=row, column=1, value="Four-year NPV").font = TITLE_FONT
    row += 1
    npv_rows = [
        ("Deterministic NPV (Part D)", data["deterministic_npv"]),
        ("Simulated mean", data["mean_npv"]),
        ("Median (P50)", data["median_npv"]),
        ("Worst case (P5)", data["npv_p5"]),
        ("Low case (P10)", data["npv_p10"]),
        ("High case (P90)", data["npv_p90"]),
        ("Best case (P95)", data["npv_p95"]),
    ]
    for label, value in npv_rows:
        results.cell(row=row, column=1, value=label)
        cell = results.cell(row=row, column=2, value=value)
        cell.number_format = MONEY
        row += 1
    results.cell(row=row, column=1, value="P(NPV below zero)").font = TOTAL_FONT
    negative = results.cell(row=row, column=2, value=data["probability_negative_npv"])
    negative.number_format = PERCENT
    negative.font = Font(bold=True, color="C4504B")
    row += 2

    write_header(results, row, ["Percentile", "Total build cost", "Four-year NPV"])
    row += 1
    for entry in monte_carlo.percentile_table(result):
        results.cell(row=row, column=1, value=entry["Percentile"])
        cost = results.cell(row=row, column=2, value=entry["Total build cost"])
        cost.number_format = MONEY
        value = results.cell(row=row, column=3, value=entry["Four-year NPV"])
        value.number_format = MONEY
        for column in range(1, 4):
            results.cell(row=row, column=column).border = BORDER
        row += 1

    results.cell(
        row=row + 1, column=1,
        value="Decision this changes: hold capital against the P80 cost, not the "
              "point estimate, and spend $46,000 on a pilot to measure the two "
              "variables that dominate NPV before committing the rest.",
    ).font = NOTE_FONT
    set_widths(results, {"A": 40, "B": 20, "C": 20})

    sensitivity = workbook.create_sheet("Part J Sensitivity")
    row = write_title(
        sensitivity,
        "Part J — Sensitivity",
        "Correlation of each sampled input with the resulting NPV. The square of "
        "the correlation is roughly the share of NPV variance it explains.",
    )
    write_header(
        sensitivity, row,
        ["Variable", "Correlation with NPV", "Share of NPV variance"],
    )
    row += 1
    first_data = row
    for entry in monte_carlo.sensitivity_table(result):
        sensitivity.cell(row=row, column=1, value=entry["Variable"].replace("_", " "))
        correlation = sensitivity.cell(
            row=row, column=2, value=entry["Correlation with NPV"]
        )
        correlation.number_format = "0.000"
        share = sensitivity.cell(row=row, column=3, value=f"=B{row}^2")
        share.number_format = PERCENT
        mark_formula(share)
        for column in range(1, 4):
            sensitivity.cell(row=row, column=column).border = BORDER
        row += 1
    last_data = row - 1

    sensitivity.cell(
        row=row + 1, column=1,
        value="Minutes saved per ticket and adoption dominate. Engineering effort, "
              "the variable teams normally pad, is third. CTS is buying a behavior "
              "change more than a software project, which is exactly what a pilot "
              "can test cheaply.",
    ).font = NOTE_FONT

    chart = BarChart()
    chart.type = "bar"
    chart.title = "Which uncertainty moves NPV"
    data_ref = Reference(sensitivity, min_col=2, min_row=first_data - 1, max_row=last_data)
    categories = Reference(sensitivity, min_col=1, min_row=first_data, max_row=last_data)
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(categories)
    chart.height = 9
    chart.width = 18
    sensitivity.add_chart(chart, f"A{row + 4}")

    set_widths(sensitivity, {"A": 34, "B": 22, "C": 22})

    _ = chart_dir


def build(destination: Path) -> Path:
    workbook = Workbook()
    sheet_read_me(workbook)
    sheet_assumptions(workbook)
    sheet_scoring(workbook)
    sheet_npv(workbook)
    sheet_risks(workbook)
    sheet_decision_tree(workbook)
    sheet_monte_carlo(workbook, monte_carlo.OUTPUT_DIR)

    destination.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(str(destination))
    return destination


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "destination",
        type=Path,
        nargs="?",
        default=Path("docs/deliverables/CMPE165_Project1_Calculations.xlsx"),
    )
    arguments = parser.parse_args()
    path = build(arguments.destination)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
