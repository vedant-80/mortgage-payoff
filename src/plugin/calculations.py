"""Integer-cent computation. No model calls or scenario lookup."""

from dataclasses import asdict, is_dataclass


def plain(value):
    return asdict(value) if is_dataclass(value) else value


def integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer from {low} to {high}")
    return value


def rounded(numerator, denominator=10000):
    sign = -1 if numerator < 0 else 1
    return sign * ((2 * abs(numerator) + denominator) // (2 * denominator))


def normalize(value):
    args = plain(value)
    fields = {"balance_cents", "annual_interest_bps", "monthly_payment_cents", "extra_monthly_payment_cents"}
    if type(args) is not dict or set(args) != fields:
        raise ValueError("Supply balance, interest, payment, and extra payment; use null for zero extra")
    result = {}
    for key in ("balance_cents", "monthly_payment_cents"):
        result[key] = integer(args[key], key, 0, 10**15)
    result["annual_interest_bps"] = integer(args["annual_interest_bps"], "annual_interest_bps", 0, 10000)
    extra = args["extra_monthly_payment_cents"]
    defaults = ["extra_monthly_payment_cents"] if extra is None else []
    result["extra_monthly_payment_cents"] = integer(
        0 if extra is None else extra, "extra_monthly_payment_cents", 0, 10**15
    )
    result["max_payoff_months"] = 1200
    return result, defaults


def amortize(balance, rate, payment):
    interest_total = paid_total = months = 0
    reason = "paid_off" if balance == 0 else "search_limit"
    if balance and payment <= rounded(balance * rate, 120000):
        reason = "non_amortizing"
    else:
        for month in range(1, 1201):
            if not balance:
                break
            charge = rounded(balance * rate, 120000)
            paid = min(payment, balance + charge)
            balance += charge - paid
            interest_total += charge
            paid_total += paid
            months = month
        if not balance:
            reason = "paid_off"
    success = reason == "paid_off"
    return {
        "paid_off": success,
        "reason": reason,
        "payoff_months": months if success else None,
        "payoff_years": months // 12 if success else None,
        "payoff_additional_months": months % 12 if success else None,
        "months_simulated": months,
        "total_interest_cents": interest_total,
        "total_paid_cents": paid_total,
        "remaining_balance_cents": balance,
    }


def solve(value):
    a, defaults = normalize(value)
    balance, rate, regular = (a[k] for k in ("balance_cents", "annual_interest_bps", "monthly_payment_cents"))
    plan = amortize(balance, rate, regular + a["extra_monthly_payment_cents"])
    baseline = amortize(balance, rate, regular)
    comparable = plan["paid_off"] and baseline["paid_off"]
    return {
        "plan": plan,
        "baseline": baseline,
        "months_saved": baseline["payoff_months"] - plan["payoff_months"] if comparable else None,
        "interest_saved_cents": baseline["total_interest_cents"] - plan["total_interest_cents"] if comparable else None,
        "assumptions": a,
        "defaults_applied": defaults,
    }
