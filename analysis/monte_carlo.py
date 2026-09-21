"""Part J: Monte Carlo simulation of build cost and four-year NPV.

The deterministic NPV in analysis/npv.py uses the team's single most-likely
value for every input. That is the mode of each distribution, not its mean, and
because software effort is right-skewed the two are not the same number. This
simulation exists to find out how far apart they are.

Six uncertain variables are sampled per trial:
    1. engineering effort in person-weeks         triangular
    2. blended loaded build rate                  truncated normal
    3. SSO/Banner rework occurrence and cost      Bernoulli x triangular
    4. minutes of staff time saved per ticket     triangular
    5. steady-state adoption share                triangular
    6. annual run cost                            uniform

Run directly:
    python -m analysis.monte_carlo
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from analysis import assumptions as A
from analysis import npv as npv_module

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

PERCENTILES = (5, 10, 25, 50, 75, 80, 90, 95)


@dataclass
class SimulationResult:
    trials: int
    seed: int
    cost: np.ndarray
    npv_values: np.ndarray
    inputs: dict[str, np.ndarray]

    # Deterministic baseline for comparison.
    deterministic_cost: float
    deterministic_npv: float

    def cost_percentile(self, percentile: float) -> float:
        return float(np.percentile(self.cost, percentile))

    def npv_percentile(self, percentile: float) -> float:
        return float(np.percentile(self.npv_values, percentile))

    @property
    def mean_cost(self) -> float:
        return float(self.cost.mean())

    @property
    def mean_npv(self) -> float:
        return float(self.npv_values.mean())

    @property
    def probability_over_budget(self) -> float:
        return float((self.cost > A.COST_OVERRUN_THRESHOLD).mean())

    @property
    def probability_negative_npv(self) -> float:
        return float((self.npv_values < A.NPV_THRESHOLD).mean())

    @property
    def optimism_gap(self) -> float:
        """How much the point estimate understates the expected cost."""
        return self.mean_cost - self.deterministic_cost


def _triangular(
    rng: np.random.Generator, spec: tuple[float, float, float], size: int
) -> np.ndarray:
    low, mode, high = spec
    return rng.triangular(low, mode, high, size)


def simulate(
    trials: int = A.MONTE_CARLO_TRIALS, seed: int = A.MONTE_CARLO_SEED
) -> SimulationResult:
    """Run the simulation and return cost and NPV distributions."""
    rng = np.random.default_rng(seed)

    effort = _triangular(rng, A.EFFORT_PERSON_WEEKS_TRIANGULAR, trials)

    rate_mean, rate_sd = A.BUILD_RATE_NORMAL
    rate = rng.normal(rate_mean, rate_sd, trials)
    # A loaded rate cannot realistically fall outside the university's pay bands,
    # so the normal draw is clipped rather than allowed to produce absurd values.
    rate = np.clip(rate, *A.BUILD_RATE_BOUNDS)

    rework_occurs = rng.random(trials) < A.SSO_REWORK_PROBABILITY
    rework_cost = _triangular(rng, A.SSO_REWORK_COST_TRIANGULAR, trials)
    rework = np.where(rework_occurs, rework_cost, 0.0)

    minutes_saved = _triangular(rng, A.MINUTES_SAVED_TRIANGULAR, trials)
    steady_adoption = _triangular(rng, A.STEADY_ADOPTION_TRIANGULAR, trials)
    run_cost = rng.uniform(*A.RUN_COST_UNIFORM, trials)

    cost = (
        effort * A.HOURS_PER_PERSON_WEEK * rate + A.FIXED_ONE_TIME_COSTS + rework
    )

    npv_values = _vectorized_npv(cost, minutes_saved, steady_adoption, run_cost)

    baseline = npv_module.compute_npv()

    return SimulationResult(
        trials=trials,
        seed=seed,
        cost=cost,
        npv_values=npv_values,
        inputs={
            "effort_person_weeks": effort,
            "build_rate": rate,
            "sso_rework_cost": rework,
            "minutes_saved": minutes_saved,
            "steady_adoption": steady_adoption,
            "annual_run_cost": run_cost,
        },
        deterministic_cost=baseline.initial_cost,
        deterministic_npv=baseline.npv,
    )


def _vectorized_npv(
    cost: np.ndarray,
    minutes_saved: np.ndarray,
    steady_adoption: np.ndarray,
    run_cost: np.ndarray,
) -> np.ndarray:
    """Four-year NPV for every trial at once.

    Mirrors ``analysis.npv.compute_npv`` exactly, except that the adoption ramp
    is rescaled by each trial's sampled steady-state adoption so a trial where
    departments never fully move over is penalised in every year.
    """
    terminal_ramp = A.ADOPTION_RAMP[A.ANALYSIS_YEARS]
    present_value = np.zeros_like(cost)

    for year in range(1, A.ANALYSIS_YEARS + 1):
        volume = A.ANNUAL_TICKET_VOLUME * (
            (1 + A.TICKET_VOLUME_GROWTH) ** (year - 1)
        )
        labor = volume * (minutes_saved / 60.0) * A.BLENDED_SUPPORT_RATE
        gross_at_full = labor + A.ANNUAL_TOOL_CONSOLIDATION_SAVINGS

        ramp_shape = A.ADOPTION_RAMP[year] / terminal_ramp
        adoption = steady_adoption * ramp_shape

        net = gross_at_full * adoption - run_cost
        present_value += net / ((1 + A.DISCOUNT_RATE) ** year)

    return present_value - cost


def summary(result: SimulationResult) -> dict[str, object]:
    """Flat summary used by the appendix and the generated deliverables."""
    return {
        "trials": result.trials,
        "seed": result.seed,
        "deterministic_cost": round(result.deterministic_cost, 2),
        "mean_cost": round(result.mean_cost, 2),
        "median_cost": round(result.cost_percentile(50), 2),
        "cost_p10": round(result.cost_percentile(10), 2),
        "cost_p80": round(result.cost_percentile(80), 2),
        "cost_p90": round(result.cost_percentile(90), 2),
        "cost_p95": round(result.cost_percentile(95), 2),
        "optimism_gap": round(result.optimism_gap, 2),
        "budget_threshold": A.COST_OVERRUN_THRESHOLD,
        "probability_over_budget": round(result.probability_over_budget, 4),
        "deterministic_npv": round(result.deterministic_npv, 2),
        "mean_npv": round(result.mean_npv, 2),
        "median_npv": round(result.npv_percentile(50), 2),
        "npv_p5": round(result.npv_percentile(5), 2),
        "npv_p10": round(result.npv_percentile(10), 2),
        "npv_p90": round(result.npv_percentile(90), 2),
        "npv_p95": round(result.npv_percentile(95), 2),
        "probability_negative_npv": round(result.probability_negative_npv, 4),
    }


def percentile_table(result: SimulationResult) -> list[dict[str, object]]:
    return [
        {
            "Percentile": f"P{percentile}",
            "Total build cost": round(result.cost_percentile(percentile), 2),
            "Four-year NPV": round(result.npv_percentile(percentile), 2),
        }
        for percentile in PERCENTILES
    ]


def input_table(result: SimulationResult) -> list[dict[str, object]]:
    """Distribution definitions, for the appendix."""
    return [
        {
            "Variable": "Engineering effort (person-weeks)",
            "Distribution": "Triangular",
            "Parameters": f"min {A.EFFORT_PERSON_WEEKS_TRIANGULAR[0]:.0f}, "
                          f"likely {A.EFFORT_PERSON_WEEKS_TRIANGULAR[1]:.0f}, "
                          f"max {A.EFFORT_PERSON_WEEKS_TRIANGULAR[2]:.0f}",
            "Sampled mean": round(
                float(result.inputs["effort_person_weeks"].mean()), 2
            ),
        },
        {
            "Variable": "Blended loaded build rate ($/hr)",
            "Distribution": "Normal, clipped",
            "Parameters": f"mean {A.BUILD_RATE_NORMAL[0]:.0f}, "
                          f"sd {A.BUILD_RATE_NORMAL[1]:.0f}, "
                          f"clipped to [{A.BUILD_RATE_BOUNDS[0]:.0f}, "
                          f"{A.BUILD_RATE_BOUNDS[1]:.0f}]",
            "Sampled mean": round(float(result.inputs["build_rate"].mean()), 2),
        },
        {
            "Variable": "SSO / Banner rework cost ($)",
            "Distribution": "Bernoulli x Triangular",
            "Parameters": f"p {A.SSO_REWORK_PROBABILITY:.0%}, then triangular "
                          f"{A.SSO_REWORK_COST_TRIANGULAR[0]:,.0f} / "
                          f"{A.SSO_REWORK_COST_TRIANGULAR[1]:,.0f} / "
                          f"{A.SSO_REWORK_COST_TRIANGULAR[2]:,.0f}",
            "Sampled mean": round(
                float(result.inputs["sso_rework_cost"].mean()), 2
            ),
        },
        {
            "Variable": "Minutes saved per ticket",
            "Distribution": "Triangular",
            "Parameters": f"min {A.MINUTES_SAVED_TRIANGULAR[0]:.0f}, "
                          f"likely {A.MINUTES_SAVED_TRIANGULAR[1]:.0f}, "
                          f"max {A.MINUTES_SAVED_TRIANGULAR[2]:.0f}",
            "Sampled mean": round(float(result.inputs["minutes_saved"].mean()), 2),
        },
        {
            "Variable": "Steady-state adoption share",
            "Distribution": "Triangular",
            "Parameters": f"min {A.STEADY_ADOPTION_TRIANGULAR[0]:.0%}, "
                          f"likely {A.STEADY_ADOPTION_TRIANGULAR[1]:.0%}, "
                          f"max {A.STEADY_ADOPTION_TRIANGULAR[2]:.0%}",
            "Sampled mean": round(
                float(result.inputs["steady_adoption"].mean()), 4
            ),
        },
        {
            "Variable": "Annual run cost ($)",
            "Distribution": "Uniform",
            "Parameters": f"{A.RUN_COST_UNIFORM[0]:,.0f} to "
                          f"{A.RUN_COST_UNIFORM[1]:,.0f}",
            "Sampled mean": round(
                float(result.inputs["annual_run_cost"].mean()), 2
            ),
        },
    ]


def sensitivity_table(result: SimulationResult) -> list[dict[str, object]]:
    """Correlation of each input with NPV — which uncertainty actually matters."""
    rows = []
    for name, values in result.inputs.items():
        if values.std() == 0:
            correlation = 0.0
        else:
            correlation = float(np.corrcoef(values, result.npv_values)[0, 1])
        rows.append(
            {
                "Variable": name,
                "Correlation with NPV": round(correlation, 4),
                "Share of NPV variance explained": round(correlation**2, 4),
            }
        )
    return sorted(
        rows, key=lambda row: abs(row["Correlation with NPV"]), reverse=True
    )


def write_charts(result: SimulationResult, output_dir: Path = OUTPUT_DIR) -> list[Path]:
    """Write the cost histogram and the NPV distribution chart."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    # Chart 1: build cost distribution against the approved budget.
    figure, axis = plt.subplots(figsize=(9, 5.2))
    axis.hist(result.cost, bins=60, color="#5a8fc4", edgecolor="white", linewidth=0.4)
    axis.axvline(
        result.deterministic_cost,
        color="#2f6b46",
        linestyle="--",
        linewidth=2,
        label=f"Team point estimate  ${result.deterministic_cost:,.0f}",
    )
    axis.axvline(
        result.mean_cost,
        color="#c4504b",
        linestyle="-",
        linewidth=2,
        label=f"Simulated mean  ${result.mean_cost:,.0f}",
    )
    axis.axvline(
        A.COST_OVERRUN_THRESHOLD,
        color="#111111",
        linestyle=":",
        linewidth=2,
        label=f"Approved budget  ${A.COST_OVERRUN_THRESHOLD:,.0f}",
    )
    axis.axvline(
        result.cost_percentile(80),
        color="#e0952b",
        linestyle="-.",
        linewidth=2,
        label=f"P80  ${result.cost_percentile(80):,.0f}",
    )
    axis.set_title(
        f"HelpDesk165 build cost, {result.trials:,} Monte Carlo trials\n"
        f"P(cost exceeds approved budget) = "
        f"{result.probability_over_budget:.1%}",
        fontsize=12,
    )
    axis.set_xlabel("Total build cost (USD)")
    axis.set_ylabel("Trials")
    axis.legend(fontsize=9)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    cost_path = output_dir / "monte_carlo_cost_histogram.png"
    figure.savefig(cost_path, dpi=150)
    plt.close(figure)
    written.append(cost_path)

    # Chart 2: NPV histogram plus cumulative probability on a shared axis.
    figure, axis = plt.subplots(figsize=(9, 5.2))
    axis.hist(
        result.npv_values, bins=60, color="#7aa98c", edgecolor="white", linewidth=0.4
    )
    axis.axvline(0, color="#111111", linestyle=":", linewidth=2, label="Break even")
    axis.axvline(
        result.deterministic_npv,
        color="#2f6b46",
        linestyle="--",
        linewidth=2,
        label=f"Deterministic NPV  ${result.deterministic_npv:,.0f}",
    )
    axis.axvline(
        result.npv_percentile(10),
        color="#c4504b",
        linestyle="-.",
        linewidth=2,
        label=f"P10  ${result.npv_percentile(10):,.0f}",
    )
    axis.set_xlabel("Four-year NPV (USD)")
    axis.set_ylabel("Trials")
    axis.spines[["top", "right"]].set_visible(False)

    cumulative = axis.twinx()
    ordered = np.sort(result.npv_values)
    cumulative.plot(
        ordered,
        np.arange(1, ordered.size + 1) / ordered.size,
        color="#404040",
        linewidth=1.5,
    )
    cumulative.set_ylabel("Cumulative probability")
    cumulative.set_ylim(0, 1)
    cumulative.spines[["top"]].set_visible(False)

    axis.set_title(
        f"HelpDesk165 four-year NPV, {result.trials:,} trials\n"
        f"P(NPV below zero) = {result.probability_negative_npv:.1%}",
        fontsize=12,
    )
    axis.legend(fontsize=9, loc="upper left")
    figure.tight_layout()
    npv_path = output_dir / "monte_carlo_npv_distribution.png"
    figure.savefig(npv_path, dpi=150)
    plt.close(figure)
    written.append(npv_path)

    # Chart 3: tornado of which uncertainty drives NPV.
    sensitivity = sensitivity_table(result)
    labels = [row["Variable"].replace("_", " ") for row in sensitivity][::-1]
    values = [row["Correlation with NPV"] for row in sensitivity][::-1]
    figure, axis = plt.subplots(figsize=(9, 4.4))
    colors = ["#4c9a6a" if value >= 0 else "#c4504b" for value in values]
    axis.barh(labels, values, color=colors)
    axis.axvline(0, color="#111111", linewidth=1)
    axis.set_xlabel("Correlation with four-year NPV")
    axis.set_title("Which uncertainty actually moves the business case", fontsize=12)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    tornado_path = output_dir / "monte_carlo_sensitivity.png"
    figure.savefig(tornado_path, dpi=150)
    plt.close(figure)
    written.append(tornado_path)

    return written


def write_presentation_chart(
    result: SimulationResult, output_dir: Path = OUTPUT_DIR
) -> Path:
    """A taller, larger-type build-cost chart sized for a projected slide.

    The report figure is designed to be read on paper at full page width. Shrunk
    into a slide column it becomes illegible, so the slide gets its own render
    with fewer annotations and much bigger type.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(7.4, 6.8))
    axis.hist(result.cost, bins=45, color="#5a8fc4", edgecolor="white", linewidth=0.5)
    axis.axvline(
        result.deterministic_cost,
        color="#2f6b46",
        linestyle="--",
        linewidth=3,
        label=f"We estimated  ${result.deterministic_cost:,.0f}",
    )
    axis.axvline(
        result.mean_cost,
        color="#c4504b",
        linestyle="-",
        linewidth=3,
        label=f"Trials expect  ${result.mean_cost:,.0f}",
    )
    axis.axvline(
        A.COST_OVERRUN_THRESHOLD,
        color="#111111",
        linestyle=":",
        linewidth=3,
        label=f"Approved  ${A.COST_OVERRUN_THRESHOLD:,.0f}",
    )
    axis.set_title(
        f"{result.probability_over_budget:.0%} chance we exceed\n"
        "the approved budget",
        fontsize=21,
        fontweight="bold",
        color="#1a1a1a",
        pad=14,
    )
    axis.set_xlabel("Total build cost (USD)", fontsize=15)
    axis.set_ylabel("Trials", fontsize=15)
    axis.tick_params(labelsize=13)
    axis.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda value, _: f"${value/1000:,.0f}K")
    )
    axis.legend(fontsize=14, loc="upper right", framealpha=0.95)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()

    path = output_dir / "monte_carlo_cost_presentation.png"
    figure.savefig(path, dpi=170)
    plt.close(figure)
    return path


def main() -> SimulationResult:
    result = simulate()
    data = summary(result)

    print(f"Monte Carlo simulation — {result.trials:,} trials (seed {result.seed})\n")
    print("BUILD COST")
    print(f"  Team point estimate      ${data['deterministic_cost']:>12,.0f}")
    print(f"  Simulated mean           ${data['mean_cost']:>12,.0f}")
    print(f"  Median (P50)             ${data['median_cost']:>12,.0f}")
    print(f"  Low case (P10)           ${data['cost_p10']:>12,.0f}")
    print(f"  P80                      ${data['cost_p80']:>12,.0f}")
    print(f"  High case (P90)          ${data['cost_p90']:>12,.0f}")
    print(f"  Optimism gap             ${data['optimism_gap']:>12,.0f}")
    print(
        f"  P(cost > ${data['budget_threshold']:,.0f} budget) = "
        f"{data['probability_over_budget']:.1%}\n"
    )
    print("FOUR-YEAR NPV")
    print(f"  Deterministic NPV        ${data['deterministic_npv']:>12,.0f}")
    print(f"  Simulated mean           ${data['mean_npv']:>12,.0f}")
    print(f"  Median (P50)             ${data['median_npv']:>12,.0f}")
    print(f"  Worst case (P5)          ${data['npv_p5']:>12,.0f}")
    print(f"  Best case (P95)          ${data['npv_p95']:>12,.0f}")
    print(f"  P(NPV < 0) = {data['probability_negative_npv']:.1%}\n")
    print("SENSITIVITY (correlation with NPV)")
    for row in sensitivity_table(result):
        print(f"  {row['Variable']:<24}{row['Correlation with NPV']:>8.3f}")

    charts = write_charts(result)
    charts.append(write_presentation_chart(result))
    print("\nCharts written:")
    for path in charts:
        print(f"  {path}")
    return result


if __name__ == "__main__":
    main()
