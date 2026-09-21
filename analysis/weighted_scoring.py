"""Part C: weighted scoring model comparing two competing projects.

Run directly:
    python -m analysis.weighted_scoring
"""

from __future__ import annotations

from dataclasses import dataclass

from analysis import assumptions as A


@dataclass
class ScoreRow:
    criterion: str
    weight: float
    score_a: int
    score_b: int
    weighted_a: float
    weighted_b: float
    rationale: str


@dataclass
class ScoringResult:
    project_a: str
    project_b: str
    rows: list[ScoreRow]
    total_a: float
    total_b: float
    winner: str
    margin: float


def score_projects(
    scores_a: dict[str, int] | None = None,
    scores_b: dict[str, int] | None = None,
) -> ScoringResult:
    """Weighted totals for both projects on a 1-10 scale.

    Raises if the weights do not sum to 100 percent, since the assignment
    requires that and a silent rounding error would invalidate the comparison.
    """
    a_scores = scores_a or A.PROJECT_A_SCORES
    b_scores = scores_b or A.PROJECT_B_SCORES

    total_weight = sum(criterion.weight for criterion in A.SCORING_CRITERIA)
    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(f"Criterion weights sum to {total_weight:.4f}, not 1.0")

    rows: list[ScoreRow] = []
    for criterion in A.SCORING_CRITERIA:
        score_a = a_scores[criterion.name]
        score_b = b_scores[criterion.name]
        rows.append(
            ScoreRow(
                criterion=criterion.name,
                weight=criterion.weight,
                score_a=score_a,
                score_b=score_b,
                weighted_a=round(criterion.weight * score_a, 4),
                weighted_b=round(criterion.weight * score_b, 4),
                rationale=criterion.rationale,
            )
        )

    total_a = round(sum(row.weighted_a for row in rows), 3)
    total_b = round(sum(row.weighted_b for row in rows), 3)
    winner = A.PROJECT_A_NAME if total_a >= total_b else A.PROJECT_B_NAME

    return ScoringResult(
        project_a=A.PROJECT_A_NAME,
        project_b=A.PROJECT_B_NAME,
        rows=rows,
        total_a=total_a,
        total_b=total_b,
        winner=winner,
        margin=round(abs(total_a - total_b), 3),
    )


def as_table(result: ScoringResult) -> list[dict[str, object]]:
    table = [
        {
            "Criterion": row.criterion,
            "Weight": f"{row.weight:.0%}",
            "Project A score": row.score_a,
            "Project A weighted": row.weighted_a,
            "Project B score": row.score_b,
            "Project B weighted": row.weighted_b,
        }
        for row in result.rows
    ]
    table.append(
        {
            "Criterion": "TOTAL",
            "Weight": "100%",
            "Project A score": "",
            "Project A weighted": result.total_a,
            "Project B score": "",
            "Project B weighted": result.total_b,
        }
    )
    return table


def sensitivity_flip_weight(criterion_name: str) -> float | None:
    """Weight that ``criterion_name`` would need for Project B to win.

    Answers the obvious challenge from a skeptical reviewer: "you only picked A
    because you weighted your favorite criterion heavily." Returns None when no
    weight in [0, 1] flips the result, which is the stronger answer.
    """
    base = score_projects()
    target = next(
        (c for c in A.SCORING_CRITERIA if c.name == criterion_name), None
    )
    if target is None:
        raise ValueError(f"Unknown criterion: {criterion_name}")

    others = [c for c in A.SCORING_CRITERIA if c.name != criterion_name]
    other_weight_total = sum(c.weight for c in others)

    for step in range(0, 101):
        new_weight = step / 100.0
        if new_weight >= 1.0:
            continue
        scale = (1.0 - new_weight) / other_weight_total
        total_a = new_weight * A.PROJECT_A_SCORES[criterion_name]
        total_b = new_weight * A.PROJECT_B_SCORES[criterion_name]
        for criterion in others:
            weight = criterion.weight * scale
            total_a += weight * A.PROJECT_A_SCORES[criterion.name]
            total_b += weight * A.PROJECT_B_SCORES[criterion.name]
        if total_b > total_a:
            return round(new_weight, 2)

    _ = base
    return None


def main() -> ScoringResult:
    result = score_projects()
    print(f"{result.project_a}\nvs.\n{result.project_b}\n")
    header = (
        f"{'Criterion':<38}{'Wt':>6}{'A':>4}{'A*wt':>8}{'B':>4}{'B*wt':>8}"
    )
    print(header)
    print("-" * len(header))
    for row in result.rows:
        print(
            f"{row.criterion:<38}{row.weight:>6.0%}{row.score_a:>4}"
            f"{row.weighted_a:>8.2f}{row.score_b:>4}{row.weighted_b:>8.2f}"
        )
    print("-" * len(header))
    print(f"{'WEIGHTED TOTAL':<38}{'100%':>6}{'':>4}{result.total_a:>8.2f}"
          f"{'':>4}{result.total_b:>8.2f}")
    print(f"\nRecommendation: {result.winner} (margin {result.margin:.2f})")

    for name in ("Expected financial return", "Time to first value"):
        flip = sensitivity_flip_weight(name)
        if flip is None:
            print(
                f"Sensitivity: no weight on '{name}' between 0% and 100% makes "
                "Project B win."
            )
        else:
            print(f"Sensitivity: '{name}' would need a {flip:.0%} weight to flip.")
    return result


if __name__ == "__main__":
    main()
