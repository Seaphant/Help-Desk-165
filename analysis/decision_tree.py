"""Part I: decision tree and expected monetary value.

Run directly:
    python -m analysis.decision_tree
"""

from __future__ import annotations

from dataclasses import dataclass

from analysis import assumptions as A
from analysis.assumptions import Choice


@dataclass
class BranchResult:
    choice: Choice
    emv: float
    best_case: float
    worst_case: float
    downside_probability: float

    @property
    def label(self) -> str:
        return self.choice.label


@dataclass
class DecisionResult:
    question: str
    branches: list[BranchResult]
    recommended: BranchResult
    runner_up: BranchResult
    emv_margin: float


def evaluate_choice(choice: Choice) -> BranchResult:
    """EMV of one decision branch, plus the shape of its downside."""
    total_probability = sum(outcome.probability for outcome in choice.outcomes)
    if abs(total_probability - 1.0) > 1e-9:
        raise ValueError(
            f"Outcome probabilities for '{choice.label}' sum to "
            f"{total_probability:.4f}, not 1.0"
        )

    emv = sum(
        outcome.probability * outcome.net_value for outcome in choice.outcomes
    )
    values = [outcome.net_value for outcome in choice.outcomes]
    downside = sum(
        outcome.probability
        for outcome in choice.outcomes
        if outcome.net_value < 0
    )

    return BranchResult(
        choice=choice,
        emv=round(emv, 2),
        best_case=max(values),
        worst_case=min(values),
        downside_probability=round(downside, 4),
    )


def evaluate() -> DecisionResult:
    branches = [evaluate_choice(choice) for choice in A.DECISION_CHOICES]
    ordered = sorted(branches, key=lambda branch: branch.emv, reverse=True)
    return DecisionResult(
        question=A.DECISION_QUESTION,
        branches=branches,
        recommended=ordered[0],
        runner_up=ordered[1],
        emv_margin=round(ordered[0].emv - ordered[1].emv, 2),
    )


def as_table(result: DecisionResult) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for branch in result.branches:
        for outcome in branch.choice.outcomes:
            rows.append(
                {
                    "Decision": branch.label,
                    "Outcome": outcome.label,
                    "Probability": f"{outcome.probability:.0%}",
                    "Net value (4 yr)": outcome.net_value,
                    "P x value": round(outcome.probability * outcome.net_value, 2),
                    "Branch EMV": "",
                }
            )
        rows.append(
            {
                "Decision": branch.label,
                "Outcome": "EMV of branch",
                "Probability": "",
                "Net value (4 yr)": "",
                "P x value": "",
                "Branch EMV": branch.emv,
            }
        )
    return rows


def mermaid_diagram(result: DecisionResult) -> str:
    """Decision tree as a Mermaid flowchart for the written report."""
    lines = ["flowchart LR", '    Decision{"Fund HelpDesk165 how?"}']
    for index, branch in enumerate(result.branches, start=1):
        node = f"C{index}"
        lines.append(
            f'    Decision -->|"{branch.label}"| {node}'
            f'["EMV ${branch.emv:,.0f}"]'
        )
        for outcome_index, outcome in enumerate(branch.choice.outcomes, start=1):
            leaf = f"L{index}{outcome_index}"
            sign = "-" if outcome.net_value < 0 else ""
            lines.append(
                f'    {node} -->|"{outcome.probability:.0%} {outcome.label}"| '
                f'{leaf}["{sign}${abs(outcome.net_value):,.0f}"]'
            )
    return "\n".join(lines)


def main() -> DecisionResult:
    result = evaluate()
    print(f"Decision: {result.question}\n")
    for branch in result.branches:
        print(f"{branch.label}  ({branch.choice.upfront_note})")
        for outcome in branch.choice.outcomes:
            contribution = outcome.probability * outcome.net_value
            print(
                f"    {outcome.probability:>5.0%}  {outcome.label:<42} "
                f"${outcome.net_value:>10,.0f}  ->  ${contribution:>10,.0f}"
            )
        print(
            f"    EMV = ${branch.emv:,.0f}   worst case ${branch.worst_case:,.0f}"
            f"   P(loss) = {branch.downside_probability:.0%}\n"
        )
    print(
        f"Highest EMV: {result.recommended.label} at "
        f"${result.recommended.emv:,.0f}, ahead of {result.runner_up.label} by "
        f"${result.emv_margin:,.0f}."
    )
    return result


if __name__ == "__main__":
    main()
