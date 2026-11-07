"""Independent integer/rational amortization oracle; never imports the example solver."""
from .fixtures import scenario

def validate_arguments(args):
    if type(args) is not dict or set(args) != {'scenario_id'}:
        raise ValueError('Expected scenario_id')
    scenario(args['scenario_id'])

def expected(args):
    item = scenario(args['scenario_id'])
    loan = item['loan']
    p, n, bps = loan['principal_cents'], loan['term_months'], loan['annual_rate_bps']
    if bps:
        power = (120000 + bps) ** n
        numerator = p * bps * power
        denominator = 120000 * (power - 120000 ** n)
    else:
        numerator, denominator = p, n
    due = -(-numerator // denominator)
    extra_by_month = {}
    for event in item['extra_payments']:
        extra_by_month[event['month']] = extra_by_month.get(event['month'], 0) + event['amount_cents']
    schedules = []
    for accelerated in (True, False):
        debt, schedule = p, []
        for m in range(1, n + 1):
            # Round the exact nonnegative rational half-up.
            charge = (2 * debt * bps + 120000) // 240000
            regular = debt + charge if m == n else min(due, debt + charge)
            additional = min(extra_by_month.get(m, 0) if accelerated else 0, debt + charge - regular)
            end = debt + charge - regular - additional
            y, mo = [int(x) for x in loan['start_month'].split('-')]
            absolute_month = y * 12 + mo - 1 + m - 1
            date = f'{absolute_month // 12:04d}-{absolute_month % 12 + 1:02d}'
            schedule.append({'month': m, 'payment_month': date, 'opening_balance_cents': debt,
                             'interest_cents': charge, 'scheduled_payment_cents': regular,
                             'extra_payment_cents': additional, 'closing_balance_cents': end})
            debt = end
            if debt == 0:
                break
        if debt:
            raise ValueError('Fixture cannot amortize')
        schedules.append(schedule)
    accelerated, baseline = schedules
    interest, baseline_interest = [sum(row['interest_cents'] for row in s) for s in schedules]
    return {'scenario_id': args['scenario_id'], 'scheduled_payment_cents': due,
            'payoff_month': accelerated[-1]['payment_month'], 'baseline_payoff_month': baseline[-1]['payment_month'],
            'total_interest_cents': interest, 'baseline_interest_cents': baseline_interest,
            'interest_saved_cents': baseline_interest-interest, 'schedule': accelerated, 'baseline_schedule': baseline}
