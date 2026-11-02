"""Offline sample solver. The MCP server exposes data tools only."""
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction
from .data import scenario

def solve(arguments):
    item = scenario(arguments['scenario_id'])
    loan = item['loan']
    principal, term = loan['principal_cents'], loan['term_months']
    with localcontext() as ctx:
        ctx.prec = 80
        exact_rate = Fraction(loan['annual_rate_bps'], 120000)
        exact_payment = (Fraction(principal, term) if not exact_rate else
                         principal * exact_rate / (1 - (1 + exact_rate) ** -term))
        payment = -(-exact_payment.numerator // exact_payment.denominator)
        def project(extras):
            balance, rows = principal, []
            year, month = map(int, loan['start_month'].split('-'))
            for index in range(1, term + 1):
                interest = int((Decimal(balance * loan['annual_rate_bps']) / 120000)
                               .to_integral_value(rounding=ROUND_HALF_UP))
                paid = balance + interest if index == term else min(payment, balance + interest)
                extra = min(extras.get(index, 0), balance + interest - paid)
                closing = balance + interest - paid - extra
                stamp = f'{year + (month + index - 2) // 12:04d}-{(month + index - 2) % 12 + 1:02d}'
                rows.append(dict(month=index, payment_month=stamp, opening_balance_cents=balance,
                                 interest_cents=interest, scheduled_payment_cents=paid,
                                 extra_payment_cents=extra, closing_balance_cents=closing))
                balance = closing
                if not balance:
                    return rows
            if balance:
                raise ValueError('Loan not amortized within contractual term')
            return rows
        extras = {}
        for event in item['extra_payments']:
            extras[event['month']] = extras.get(event['month'], 0) + event['amount_cents']
        rows, baseline = project(extras), project({})
        interest = sum(r['interest_cents'] for r in rows)
        base_interest = sum(r['interest_cents'] for r in baseline)
        return dict(scenario_id=arguments['scenario_id'], scheduled_payment_cents=payment,
                    payoff_month=rows[-1]['payment_month'], baseline_payoff_month=baseline[-1]['payment_month'],
                    total_interest_cents=interest, baseline_interest_cents=base_interest,
                    interest_saved_cents=base_interest-interest, schedule=rows, baseline_schedule=baseline)
