"""Independent Decimal replay of the declared financial model."""

from dataclasses import asdict, is_dataclass
from decimal import ROUND_HALF_UP, Decimal, localcontext


def plain(value):
    return asdict(value) if is_dataclass(value) else value


def integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer from {low} to {high}")
    return value


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


def expected(value):
    a, defaults = normalize(value)
    with localcontext() as context:
        context.prec = 100
        outcomes = []
        for extra in (a["extra_monthly_payment_cents"], 0):
            balance = Decimal(a["balance_cents"])
            payment = Decimal(a["monthly_payment_cents"] + extra)
            rate = Decimal(a["annual_interest_bps"]) / 120000
            elapsed, interest, paid_total = 0, Decimal(0), Decimal(0)
            initial_charge = (balance * rate).quantize(Decimal(1), rounding=ROUND_HALF_UP)
            reason = "non_amortizing" if balance and payment <= initial_charge else "search_limit"
            if reason != "non_amortizing":
                while balance > 0 and elapsed < a["max_payoff_months"]:
                    charge = (balance * rate).quantize(Decimal(1), rounding=ROUND_HALF_UP)
                    installment = min(payment, balance + charge)
                    interest += charge
                    paid_total += installment
                    balance += charge - installment
                    elapsed += 1
            if balance == 0:
                reason = "paid_off"
            success = reason == "paid_off"
            outcomes.append(
                {
                    "paid_off": success,
                    "reason": reason,
                    "payoff_months": elapsed if success else None,
                    "payoff_years": elapsed // 12 if success else None,
                    "payoff_additional_months": elapsed % 12 if success else None,
                    "months_simulated": elapsed,
                    "total_interest_cents": int(interest),
                    "total_paid_cents": int(paid_total),
                    "remaining_balance_cents": int(balance),
                }
            )
        plan, baseline = outcomes
        comparable = plan["paid_off"] and baseline["paid_off"]
        return {
            "plan": plan,
            "baseline": baseline,
            "months_saved": baseline["payoff_months"] - plan["payoff_months"] if comparable else None,
            "interest_saved_cents": baseline["total_interest_cents"] - plan["total_interest_cents"]
            if comparable
            else None,
            "assumptions": a,
            "defaults_applied": defaults,
        }
