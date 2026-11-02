from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from plugin import calculations
from plugin.data import scenarios
from verifier import oracle
import verifier

class MortgageBoundaryTests(unittest.TestCase):
    def test_zero_rate_and_final_partial_payment(self):
        out = calculations.solve({'scenario_id': 'zero-interest'})
        self.assertEqual(out['scheduled_payment_cents'], 8334)
        self.assertEqual(out['total_interest_cents'], 0)
        self.assertEqual(len(out['schedule']), 11)
        self.assertEqual(out['schedule'][-1]['scheduled_payment_cents'], 6661)
        self.assertEqual(out['baseline_schedule'][-1]['scheduled_payment_cents'], 8327)

    def test_no_extra_means_identical_schedules(self):
        out = calculations.solve({'scenario_id': 'no-extra'})
        self.assertEqual(out['interest_saved_cents'], 0)
        self.assertEqual(out['schedule'], out['baseline_schedule'])

    def test_overpayment_is_capped_and_dates_roll_over(self):
        out = calculations.solve({'scenario_id': 'immediate-payoff'})
        self.assertEqual(len(out['schedule']), 1)
        self.assertEqual(out['schedule'][0]['interest_cents'], 1000)
        self.assertEqual(out['schedule'][0]['closing_balance_cents'], 0)
        self.assertEqual(out['baseline_schedule'][1]['payment_month'], '2028-01')

    def test_half_cent_interest_rounds_up(self):
        fixture = {'loan': {'principal_cents': 100, 'annual_rate_bps': 600, 'term_months': 1, 'start_month': '2027-01'}, 'extra_payments': []}
        with patch.object(calculations, 'scenario', return_value=fixture), patch.object(oracle, 'scenario', return_value=fixture):
            out = calculations.solve({'scenario_id': 'half-cent'})
            self.assertEqual(out['schedule'][0]['interest_cents'], 1)
            self.assertEqual(out['scheduled_payment_cents'], 101)
            self.assertEqual(out, oracle.expected({'scenario_id': 'half-cent'}))

    def test_payment_conserves_principal_and_interest(self):
        for identifier, item in scenarios().items():
            out = calculations.solve({'scenario_id': identifier})
            for key in ('schedule', 'baseline_schedule'):
                paid = sum(r['scheduled_payment_cents'] + r['extra_payment_cents'] for r in out[key])
                interest = sum(r['interest_cents'] for r in out[key])
                self.assertEqual(paid, item['loan']['principal_cents'] + interest)

    def test_final_contractual_payment_settles_rounding_residue(self):
        fixture = {'loan': {'principal_cents': 6135732, 'annual_rate_bps': 2229,
                            'term_months': 340, 'start_month': '2027-01'}, 'extra_payments': []}
        with patch.object(calculations, 'scenario', return_value=fixture), patch.object(oracle, 'scenario', return_value=fixture):
            out = calculations.solve({'scenario_id': 'rounding-residue'})
            self.assertEqual(len(out['schedule']), 340)
            self.assertEqual(out['schedule'][-1]['closing_balance_cents'], 0)
            self.assertGreater(out['schedule'][-1]['scheduled_payment_cents'], out['scheduled_payment_cents'])
            self.assertEqual(out, oracle.expected({'scenario_id': 'rounding-residue'}))

    def test_month_range_boundaries(self):
        for start,end in ((0,1),(2,1),(1,361),(True,2),(1,2.0)):
            self.assertFalse(verifier.verify_input('get_extra_payments', {'scenario_id': 'starter-home', 'start_month': start, 'end_month': end})['valid'])

    def test_seeded_independent_replay(self):
        rng = random.Random(20261102)
        for _ in range(100):
            fixture = {'loan': {'principal_cents': rng.randrange(1,10000000), 'annual_rate_bps': rng.randrange(0,3000),
                                'term_months': rng.randrange(1,361), 'start_month': '2027-01'}, 'extra_payments': []}
            fixture['extra_payments'] = [{'month': rng.randrange(1,fixture['loan']['term_months']+1), 'amount_cents': rng.randrange(0,100000)} for _ in range(10)]
            with patch.object(calculations, 'scenario', return_value=fixture), patch.object(oracle, 'scenario', return_value=fixture):
                self.assertEqual(calculations.solve({'scenario_id': 'random'}), oracle.expected({'scenario_id': 'random'}))
