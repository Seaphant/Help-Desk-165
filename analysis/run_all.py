"""Regenerate every analysis artifact in analysis/outputs/.

    python -m analysis.run_all

Writes one CSV per analysis part, three PNG charts, and summary.json, which the
deliverable generator in tools/build_deliverables.py reads so the Word and
PowerPoint files carry exactly the numbers the code produced.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Sequence

from analysis import assumptions as A
from analysis import decision_tree, monte_carlo, npv, risk_register, weighted_scoring

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def write_csv(filename: str, rows: Sequence[dict[str, Any]]) -> Path:
    path = OUTPUT_DIR / filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return path
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def build_summary() -> dict[str, Any]:
    """Every headline number the report and slides quote, in one structure."""
    scoring = weighted_scoring.score_projects()
    financials = npv.compute_npv()
    register = risk_register.build_register()
    decision = decision_tree.evaluate()
    simulation = monte_carlo.simulate()

    return {
        "meta": {
            "organization": A.ORGANIZATION,
            "product": A.PRODUCT,
            "discount_rate": A.DISCOUNT_RATE,
            "analysis_years": A.ANALYSIS_YEARS,
            "annual_ticket_volume": A.ANNUAL_TICKET_VOLUME,
            "approved_capital_budget": A.APPROVED_CAPITAL_BUDGET,
        },
        "part_c_weighted_scoring": {
            "project_a": scoring.project_a,
            "project_b": scoring.project_b,
            "total_a": scoring.total_a,
            "total_b": scoring.total_b,
            "winner": scoring.winner,
            "margin": scoring.margin,
            "table": weighted_scoring.as_table(scoring),
        },
        "part_d_npv": {
            "initial_cost": financials.initial_cost,
            "total_present_value": financials.total_present_value,
            "npv": financials.npv,
            "roi": financials.roi,
            "irr": financials.irr,
            "simple_payback_year": financials.simple_payback_year,
            "discounted_payback_year": financials.discounted_payback_year,
            "table": npv.as_table(financials),
        },
        "part_h_risks": {
            "total_exposure": register.total_exposure,
            "top_risk_ids": [risk.risk_id for risk in register.top_risks],
            "table": risk_register.as_table(register),
        },
        "part_i_decision_tree": {
            "question": decision.question,
            "recommended": decision.recommended.label,
            "recommended_emv": decision.recommended.emv,
            "runner_up": decision.runner_up.label,
            "runner_up_emv": decision.runner_up.emv,
            "margin": decision.emv_margin,
            "worst_case_recommended": decision.recommended.worst_case,
            "worst_case_runner_up": decision.runner_up.worst_case,
            "table": decision_tree.as_table(decision),
            "mermaid": decision_tree.mermaid_diagram(decision),
        },
        "part_j_monte_carlo": monte_carlo.summary(simulation)
        | {
            "percentiles": monte_carlo.percentile_table(simulation),
            "inputs": monte_carlo.input_table(simulation),
            "sensitivity": monte_carlo.sensitivity_table(simulation),
        },
    }


def main() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = build_summary()
    written: list[Path] = []

    written.append(
        write_csv(
            "part_c_weighted_scoring.csv", summary["part_c_weighted_scoring"]["table"]
        )
    )
    written.append(write_csv("part_d_npv.csv", summary["part_d_npv"]["table"]))
    written.append(write_csv("part_h_risk_register.csv", summary["part_h_risks"]["table"]))
    written.append(
        write_csv("part_i_decision_tree.csv", summary["part_i_decision_tree"]["table"])
    )
    written.append(
        write_csv(
            "part_j_monte_carlo_percentiles.csv",
            summary["part_j_monte_carlo"]["percentiles"],
        )
    )
    written.append(
        write_csv(
            "part_j_monte_carlo_inputs.csv", summary["part_j_monte_carlo"]["inputs"]
        )
    )
    written.append(
        write_csv(
            "part_j_monte_carlo_sensitivity.csv",
            summary["part_j_monte_carlo"]["sensitivity"],
        )
    )

    simulation = monte_carlo.simulate()
    written.extend(monte_carlo.write_charts(simulation))

    summary_path = OUTPUT_DIR / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    written.append(summary_path)

    print(f"Wrote {len(written)} artifacts to {OUTPUT_DIR}:")
    for path in written:
        print(f"  {path.name}")
    return summary


if __name__ == "__main__":
    main()
