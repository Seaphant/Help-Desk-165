"""Tests for the project-management analysis.

These check the invariants the assignment actually grades: weights that sum to
100 percent, probabilities that sum to 1.0, discounting that is arithmetically
correct, and a simulation that is reproducible. They also lock in the
qualitative conclusions the report argues for, so if someone edits an assumption
the failing test points at the paragraph that has to change with it.
"""

import math

import pytest

from analysis import assumptions as A
from analysis import decision_tree, monte_carlo, npv, risk_register, weighted_scoring


class TestWeightedScoring:
    def test_weights_sum_to_one_hundred_percent(self):
        total = sum(criterion.weight for criterion in A.SCORING_CRITERIA)
        assert math.isclose(total, 1.0)

    def test_the_assignment_minimum_of_five_criteria_is_met(self):
        assert len(A.SCORING_CRITERIA) >= 5

    def test_both_projects_are_scored_on_every_criterion(self):
        names = {criterion.name for criterion in A.SCORING_CRITERIA}
        assert set(A.PROJECT_A_SCORES) == names
        assert set(A.PROJECT_B_SCORES) == names

    def test_scores_are_on_the_documented_one_to_ten_scale(self):
        for scores in (A.PROJECT_A_SCORES, A.PROJECT_B_SCORES):
            assert all(1 <= score <= 10 for score in scores.values())

    def test_weighted_totals_are_computed_correctly(self):
        result = weighted_scoring.score_projects()
        expected_a = sum(
            criterion.weight * A.PROJECT_A_SCORES[criterion.name]
            for criterion in A.SCORING_CRITERIA
        )
        assert math.isclose(result.total_a, round(expected_a, 3), abs_tol=0.001)

    def test_project_a_wins(self):
        result = weighted_scoring.score_projects()
        assert result.total_a > result.total_b
        assert result.winner == A.PROJECT_A_NAME

    def test_rejects_weights_that_do_not_sum_to_one(self, monkeypatch):
        broken = (A.Criterion("Only criterion", 0.5, "deliberately wrong"),)
        monkeypatch.setattr(A, "SCORING_CRITERIA", broken)
        with pytest.raises(ValueError, match="sum to"):
            weighted_scoring.score_projects({"Only criterion": 5}, {"Only criterion": 5})

    def test_result_is_not_an_artifact_of_one_heavy_weight(self):
        """No single criterion weight flips the recommendation to Project B."""
        for criterion in A.SCORING_CRITERIA:
            assert weighted_scoring.sensitivity_flip_weight(criterion.name) is None


class TestNpv:
    def test_initial_cost_is_labor_plus_fixed_costs(self):
        expected = (
            A.ENGINEERING_PERSON_WEEKS * A.HOURS_PER_PERSON_WEEK * A.BLENDED_BUILD_RATE
            + A.FIXED_ONE_TIME_COSTS
        )
        assert math.isclose(npv.initial_cost(), expected)

    def test_the_analysis_covers_at_least_four_years(self):
        assert A.ANALYSIS_YEARS >= 4
        assert len(npv.compute_npv().rows) >= 4

    def test_discount_factors_match_the_formula(self):
        result = npv.compute_npv()
        for row in result.rows:
            expected = 1.0 / ((1 + A.DISCOUNT_RATE) ** row.year)
            assert math.isclose(row.discount_factor, round(expected, 5))

    def test_present_value_equals_cash_flow_times_discount_factor(self):
        for row in npv.compute_npv().rows:
            assert math.isclose(
                row.present_value,
                round(row.net_cash_flow * row.discount_factor, 2),
                abs_tol=0.05,
            )

    def test_npv_is_present_values_less_the_investment(self):
        result = npv.compute_npv()
        assert math.isclose(
            result.npv,
            round(result.total_present_value - result.initial_cost, 2),
            abs_tol=0.05,
        )

    def test_benefits_are_scaled_by_adoption(self):
        result = npv.compute_npv()
        year_one, year_three = result.rows[0], result.rows[2]
        assert year_one.adoption < year_three.adoption
        assert year_one.gross_benefit < year_three.gross_benefit

    def test_run_cost_is_charged_in_full_from_year_one(self):
        """Hosting and maintenance do not wait for adoption to ramp."""
        assert all(row.run_cost == A.ANNUAL_RUN_COST for row in npv.compute_npv().rows)

    def test_base_case_npv_is_positive(self):
        assert npv.compute_npv().npv > 0

    def test_a_higher_discount_rate_lowers_npv(self):
        assert npv.compute_npv(discount_rate=0.20).npv < npv.compute_npv().npv

    def test_zero_benefit_makes_npv_negative(self):
        pessimistic = npv.compute_npv(minutes_saved=0.0, tool_savings=0.0)
        assert pessimistic.npv < 0

    def test_irr_makes_npv_zero(self):
        result = npv.compute_npv()
        flows = [-result.initial_cost] + [row.net_cash_flow for row in result.rows]
        assert result.irr is not None
        assert abs(npv.npv_of(flows, result.irr)) < 1.0

    def test_irr_exceeds_the_hurdle_rate_when_npv_is_positive(self):
        result = npv.compute_npv()
        assert result.irr > A.DISCOUNT_RATE

    def test_irr_returns_none_without_a_sign_change(self):
        assert npv.irr([100.0, 200.0, 300.0]) is None

    def test_payback_lands_inside_the_analysis_window(self):
        result = npv.compute_npv()
        assert result.simple_payback_year is not None
        assert result.simple_payback_year <= A.ANALYSIS_YEARS
        assert result.discounted_payback_year >= result.simple_payback_year


class TestRiskRegister:
    def test_at_least_six_risks_across_multiple_categories(self):
        assert len(A.RISKS) >= 6
        assert len({risk.category for risk in A.RISKS}) >= 5

    def test_ids_are_unique(self):
        ids = [risk.risk_id for risk in A.RISKS]
        assert len(ids) == len(set(ids))

    def test_scores_are_on_the_one_to_five_scale(self):
        for risk in A.RISKS:
            assert 1 <= risk.probability_score <= 5
            assert 1 <= risk.impact_score <= 5
            assert 0.0 < risk.probability <= 1.0
            assert risk.dollar_impact > 0

    def test_qualitative_score_is_probability_times_impact(self):
        for risk in A.RISKS:
            assert risk.qualitative_score == risk.probability_score * risk.impact_score

    def test_exposure_is_probability_times_dollar_impact(self):
        for risk in A.RISKS:
            assert math.isclose(
                risk.exposure, round(risk.probability * risk.dollar_impact, 2)
            )

    def test_register_is_ranked_by_exposure_descending(self):
        exposures = [risk.exposure for risk in risk_register.build_register().risks]
        assert exposures == sorted(exposures, reverse=True)

    def test_total_exposure_is_the_sum_of_parts(self):
        result = risk_register.build_register()
        assert math.isclose(
            result.total_exposure, round(sum(r.exposure for r in A.RISKS), 2)
        )

    def test_every_risk_has_an_early_warning_trigger(self):
        assert all(len(risk.trigger) > 20 for risk in A.RISKS)

    def test_part_k_covers_exactly_the_top_three_risks(self):
        top_ids = {risk.risk_id for risk in risk_register.build_register().top_risks}
        assert top_ids == set(risk_register.RESPONSES)

    def test_each_response_has_mitigation_contingency_and_warning(self):
        for risk_id, response in risk_register.RESPONSES.items():
            assert set(response) == {
                "strategy", "mitigation", "contingency", "warning"
            }, risk_id
            assert len(response["strategy"]) > 10, risk_id
            for key in ("mitigation", "contingency", "warning"):
                assert len(response[key]) > 80, f"{risk_id}.{key} is too thin"


class TestDecisionTree:
    def test_at_least_two_choices_with_at_least_two_outcomes_each(self):
        assert len(A.DECISION_CHOICES) >= 2
        assert all(len(choice.outcomes) >= 2 for choice in A.DECISION_CHOICES)

    def test_outcome_probabilities_sum_to_one_on_every_branch(self):
        for choice in A.DECISION_CHOICES:
            total = sum(outcome.probability for outcome in choice.outcomes)
            assert math.isclose(total, 1.0), choice.label

    def test_emv_is_the_probability_weighted_sum(self):
        for choice in A.DECISION_CHOICES:
            branch = decision_tree.evaluate_choice(choice)
            expected = sum(o.probability * o.net_value for o in choice.outcomes)
            assert math.isclose(branch.emv, round(expected, 2))

    def test_rejects_probabilities_that_do_not_sum_to_one(self):
        broken = A.Choice(
            "Broken branch",
            "test fixture",
            (
                A.Outcome("Good", 0.5, 100.0, "test"),
                A.Outcome("Bad", 0.2, -100.0, "test"),
            ),
        )
        with pytest.raises(ValueError, match="sum to"):
            decision_tree.evaluate_choice(broken)

    def test_the_pilot_branch_has_the_highest_emv(self):
        """The recommendation in the report depends on this."""
        result = decision_tree.evaluate()
        assert "pilot" in result.recommended.label.lower()

    def test_the_pilot_caps_the_downside_versus_building_now(self):
        result = decision_tree.evaluate()
        build_now = next(
            branch for branch in result.branches if branch.label.startswith("Build")
        )
        assert result.recommended.worst_case > build_now.worst_case

    def test_mermaid_diagram_contains_every_branch(self):
        result = decision_tree.evaluate()
        diagram = decision_tree.mermaid_diagram(result)
        assert diagram.startswith("flowchart")
        for branch in result.branches:
            assert branch.label in diagram


@pytest.fixture(scope="module")
def simulation():
    """One 4,000-trial run shared by the Monte Carlo tests."""
    return monte_carlo.simulate(trials=4000)


class TestMonteCarlo:
    @pytest.fixture
    def result(self, simulation):
        return simulation

    def test_the_assignment_minimum_of_one_thousand_trials_is_met(self):
        assert A.MONTE_CARLO_TRIALS >= 1000

    def test_at_least_three_uncertain_variables(self):
        assert len(monte_carlo.simulate(trials=100).inputs) >= 3

    def test_every_trial_produces_a_cost_and_an_npv(self, result):
        assert result.cost.shape == (4000,)
        assert result.npv_values.shape == (4000,)

    def test_the_simulation_is_reproducible(self):
        first = monte_carlo.simulate(trials=500, seed=42)
        second = monte_carlo.simulate(trials=500, seed=42)
        assert math.isclose(first.mean_cost, second.mean_cost)
        assert math.isclose(first.mean_npv, second.mean_npv)

    def test_a_different_seed_gives_a_different_draw(self):
        first = monte_carlo.simulate(trials=500, seed=1)
        second = monte_carlo.simulate(trials=500, seed=2)
        assert not math.isclose(first.mean_cost, second.mean_cost)

    def test_sampled_inputs_respect_their_declared_bounds(self, result):
        effort = result.inputs["effort_person_weeks"]
        low, _, high = A.EFFORT_PERSON_WEEKS_TRIANGULAR
        assert effort.min() >= low and effort.max() <= high

        rate = result.inputs["build_rate"]
        assert rate.min() >= A.BUILD_RATE_BOUNDS[0]
        assert rate.max() <= A.BUILD_RATE_BOUNDS[1]

        adoption = result.inputs["steady_adoption"]
        assert adoption.min() >= A.STEADY_ADOPTION_TRIANGULAR[0]
        assert adoption.max() <= A.STEADY_ADOPTION_TRIANGULAR[2]

    def test_percentiles_are_monotonic(self, result):
        values = [result.cost_percentile(p) for p in monte_carlo.PERCENTILES]
        assert values == sorted(values)

    def test_probabilities_are_valid(self, result):
        assert 0.0 <= result.probability_over_budget <= 1.0
        assert 0.0 <= result.probability_negative_npv <= 1.0

    def test_the_point_estimate_understates_expected_cost(self, result):
        """The central finding of Part J: effort risk is one-sided."""
        assert result.mean_cost > result.deterministic_cost
        assert result.optimism_gap > 0

    def test_expected_npv_is_well_below_the_deterministic_npv(self, result):
        assert result.mean_npv < result.deterministic_npv

    def test_there_is_a_real_chance_of_a_negative_npv(self, result):
        """Why the recommendation is conditional rather than an unqualified go."""
        assert result.probability_negative_npv > 0.05

    def test_benefit_assumptions_dominate_the_variance(self, result):
        """Which is what makes a cheap pilot the highest-value next step."""
        top = monte_carlo.sensitivity_table(result)[0]
        assert top["Variable"] in ("minutes_saved", "steady_adoption")

    def test_summary_exposes_every_number_the_report_quotes(self, result):
        summary = monte_carlo.summary(result)
        for key in (
            "mean_cost", "cost_p80", "cost_p90", "optimism_gap",
            "probability_over_budget", "mean_npv", "npv_p10", "npv_p95",
            "probability_negative_npv",
        ):
            assert key in summary

    def test_charts_are_written(self, tmp_path, result):
        paths = monte_carlo.write_charts(result, output_dir=tmp_path)
        assert len(paths) >= 1
        assert all(path.exists() and path.stat().st_size > 0 for path in paths)


class TestCrossPartConsistency:
    def test_decision_tree_reflects_a_build_cost_near_the_npv_model(self):
        """The two parts must describe the same project, not two different ones."""
        build_cost = npv.compute_npv().initial_cost
        assert 140_000 <= build_cost <= 180_000
        assert A.PILOT_COST < build_cost

    def test_the_adoption_risk_dollar_impact_matches_the_tree_downside(self):
        adoption_risk = next(risk for risk in A.RISKS if risk.risk_id == "R3")
        build_now = next(
            choice for choice in A.DECISION_CHOICES
            if choice.label.startswith("Build")
        )
        worst = min(outcome.net_value for outcome in build_now.outcomes)
        assert math.isclose(adoption_risk.dollar_impact, abs(worst))

    def test_the_budget_threshold_exceeds_the_point_estimate(self):
        """Otherwise the project would be over budget before it started."""
        assert A.APPROVED_CAPITAL_BUDGET > npv.compute_npv().initial_cost
