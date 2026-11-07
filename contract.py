"""Typed custom financial inputs and compact outputs. No field defaults: null selects documented assumptions."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    CALCULATE = "calculate_mortgage_payoff"


class Task(Enum):
    CALCULATE = "simulate-payoff"


@dataclass
class MortgageInput(Output):
    balance_cents: Annotated[int, "Current outstanding mortgage balance in integer cents; ask if missing."]
    annual_interest_bps: Annotated[
        int, "Fixed nominal annual interest rate in basis points (6% = 600); ask if missing."
    ]
    monthly_payment_cents: Annotated[
        int, "Monthly principal-and-interest payment in cents, excluding escrow and extras; ask if missing."
    ]
    extra_monthly_payment_cents: Annotated[
        int | None, "Recurring extra principal payment in cents each month. Null defaults to zero. No lump sums."
    ]


@dataclass
class MortgageAssumptions(Output):
    balance_cents: Annotated[int, "Current outstanding mortgage balance in integer cents; ask if missing."]
    annual_interest_bps: Annotated[
        int, "Fixed nominal annual interest rate in basis points (6% = 600); ask if missing."
    ]
    monthly_payment_cents: Annotated[
        int, "Monthly principal-and-interest payment in cents, excluding escrow and extras; ask if missing."
    ]
    extra_monthly_payment_cents: Annotated[
        int, "Recurring extra principal payment in cents each month. Null defaults to zero. No lump sums."
    ]
    max_payoff_months: Annotated[int, "Fixed 1200-month simulation limit."]


@dataclass
class PayoffSummary(Output):
    paid_off: Annotated[bool, "Whether the loan is fully repaid within the simulation limit."]
    reason: Annotated[str, "paid_off, non_amortizing, or search_limit."]
    payoff_months: Annotated[
        int | None, "Number of monthly payments to payoff; zero for zero starting balance, null if unpaid."
    ]
    payoff_years: Annotated[int | None, "Complete years to payoff, null if unpaid."]
    payoff_additional_months: Annotated[int | None, "Months beyond complete years, null if unpaid."]
    months_simulated: Annotated[
        int, "Months actually simulated. Zero when non-amortization is detected before the first payment."
    ]
    total_interest_cents: Annotated[int, "Interest accrued only over months_simulated; not a lifetime total if unpaid."]
    total_paid_cents: Annotated[int, "Total payments actually applied over months_simulated."]
    remaining_balance_cents: Annotated[int, "Outstanding balance at the end of the simulation."]


@dataclass
class PayoffOutput(Output):
    plan: Annotated[PayoffSummary, "Result including recurring extra payments."]
    baseline: Annotated[PayoffSummary, "Result with only the specified regular payment."]
    months_saved: Annotated[int | None, "Baseline months minus plan months; null unless both pay off."]
    interest_saved_cents: Annotated[int | None, "Baseline interest minus plan interest; null unless both pay off."]
    assumptions: Annotated[MortgageAssumptions, "All effective inputs and fixed simulation limit."]
    defaults_applied: Annotated[list[str], "Names of nullable input fields that used defaults."]


TOOLS = {Tool.CALCULATE: (MortgageInput, PayoffOutput)}
TASKS = {Task.CALCULATE: (MortgageInput, PayoffOutput)}
