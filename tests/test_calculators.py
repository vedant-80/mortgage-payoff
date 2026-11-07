import json
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from plugin.calculations import solve
from verifier.oracle import expected


def example(**changes):
    return json.loads((ROOT / "tests/example.json").read_text()) | changes


class MortgageCalculationTests(unittest.TestCase):
    def test_custom_situation_compact_summary_and_savings(self):
        result = solve(example())
        self.assertTrue(result["plan"]["paid_off"])
        self.assertGreater(result["months_saved"], 0)
        self.assertGreater(result["interest_saved_cents"], 0)
        self.assertLess(len(json.dumps(result)), 2000)
        self.assertNotIn("schedule", result)
        self.assertNotIn("baseline_schedule", result)

    def test_zero_rate_hand_calculation_and_capped_final_payment(self):
        result = solve(
            example(
                balance_cents=10000, annual_interest_bps=0, monthly_payment_cents=3000, extra_monthly_payment_cents=1000
            )
        )
        self.assertEqual(result["plan"]["payoff_months"], 3)
        self.assertEqual(result["baseline"]["payoff_months"], 4)
        self.assertEqual(result["plan"]["total_paid_cents"], 10000)
        self.assertEqual(result["plan"]["total_interest_cents"], 0)
        self.assertEqual(result["months_saved"], 1)
        self.assertEqual(result["plan"]["payoff_years"], 0)
        self.assertEqual(result["plan"]["payoff_additional_months"], 3)

    def test_monthly_half_cent_interest_rounds_up(self):
        out = solve(
            example(
                balance_cents=100, annual_interest_bps=600, monthly_payment_cents=1000, extra_monthly_payment_cents=0
            )
        )
        self.assertEqual(out["plan"]["total_interest_cents"], 1)
        self.assertEqual(out["plan"]["total_paid_cents"], 101)
        self.assertEqual(out["plan"]["payoff_months"], 1)

    def test_null_extra_is_zero_and_explicit_zero_is_not_a_default(self):
        a = solve(example(extra_monthly_payment_cents=None))
        b = solve(example(extra_monthly_payment_cents=0))
        self.assertEqual(a["plan"], a["baseline"])
        self.assertEqual(a["plan"], b["plan"])
        self.assertEqual(a["defaults_applied"], ["extra_monthly_payment_cents"])
        self.assertEqual(b["defaults_applied"], [])

    def test_non_amortizing_baseline_does_not_hide_successful_plan(self):
        args = example(
            balance_cents=10000, annual_interest_bps=1200, monthly_payment_cents=100, extra_monthly_payment_cents=10000
        )
        out = solve(args)
        self.assertTrue(out["plan"]["paid_off"])
        self.assertEqual(out["baseline"]["reason"], "non_amortizing")
        self.assertEqual(out["baseline"]["months_simulated"], 0)
        self.assertIsNone(out["months_saved"])
        self.assertIsNone(out["interest_saved_cents"])

    def test_zero_payment_and_paid_off_balance(self):
        self.assertEqual(
            solve(
                example(
                    balance_cents=100, annual_interest_bps=0, monthly_payment_cents=0, extra_monthly_payment_cents=0
                )
            )["plan"]["reason"],
            "non_amortizing",
        )
        out = solve(example(balance_cents=0, monthly_payment_cents=0, extra_monthly_payment_cents=None))
        self.assertEqual(out["plan"]["payoff_months"], 0)
        self.assertEqual(out["plan"]["total_interest_cents"], 0)
        self.assertEqual(out["months_saved"], 0)

    def test_search_limit_never_fabricates_payoff_or_savings(self):
        out = solve(
            example(
                balance_cents=1000000, annual_interest_bps=0, monthly_payment_cents=1, extra_monthly_payment_cents=0
            )
        )
        self.assertEqual(out["plan"]["reason"], "search_limit")
        self.assertEqual(out["plan"]["months_simulated"], 1200)
        self.assertEqual(out["plan"]["remaining_balance_cents"], 998800)
        self.assertIsNone(out["plan"]["payoff_months"])
        self.assertIsNone(out["months_saved"])

    def test_payment_conserves_principal_and_interest(self):
        out = solve(example())
        for result in (out["plan"], out["baseline"]):
            self.assertEqual(
                result["total_paid_cents"] + result["remaining_balance_cents"],
                out["assumptions"]["balance_cents"] + result["total_interest_cents"],
            )
            self.assertEqual(result["payoff_years"] * 12 + result["payoff_additional_months"], result["payoff_months"])

    def test_seeded_custom_input_differential_replay(self):
        rng = random.Random(1702)
        for _ in range(300):
            args = example(
                balance_cents=rng.randrange(10**8),
                annual_interest_bps=rng.randrange(10001),
                monthly_payment_cents=rng.randrange(10**6),
                extra_monthly_payment_cents=rng.randrange(10**6),
            )
            self.assertEqual(solve(args), expected(args))
