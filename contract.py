"""Typed tool and task declarations; money is always integer cents."""
from dataclasses import dataclass
from enum import Enum
from slimconfig import Output

@dataclass
class ScenarioInput(Output):
    scenario_id: str

@dataclass
class RulesInput(Output):
    pass

@dataclass
class RulesOutput(Output):
    rules: list[str]

class Tool(Enum):
    GET_MORTGAGE = 'get_mortgage'
    GET_EXTRA_PAYMENTS = 'get_extra_payments'
    GET_RULES = 'get_rules'

class Task(Enum):
    SIMULATE_PAYOFF = 'simulate-payoff'

@dataclass
class MortgageOutput(Output):
    principal_cents: int
    annual_rate_bps: int
    term_months: int
    start_month: str

@dataclass
class ExtraPaymentsInput(Output):
    scenario_id: str
    start_month: int
    end_month: int

@dataclass
class ExtraPayment(Output):
    month: int
    amount_cents: int

@dataclass
class ExtraPaymentsOutput(Output):
    payments: list[ExtraPayment]

@dataclass
class PaymentRow(Output):
    month: int
    payment_month: str
    opening_balance_cents: int
    interest_cents: int
    scheduled_payment_cents: int
    extra_payment_cents: int
    closing_balance_cents: int

@dataclass
class PayoffOutput(Output):
    scenario_id: str
    scheduled_payment_cents: int
    payoff_month: str
    baseline_payoff_month: str
    total_interest_cents: int
    baseline_interest_cents: int
    interest_saved_cents: int
    schedule: list[PaymentRow]
    baseline_schedule: list[PaymentRow]

TOOLS = {
    Tool.GET_MORTGAGE: (ScenarioInput, MortgageOutput),
    Tool.GET_EXTRA_PAYMENTS: (ExtraPaymentsInput, ExtraPaymentsOutput),
    Tool.GET_RULES: (RulesInput, RulesOutput),
}
TASKS = {Task.SIMULATE_PAYOFF: (ScenarioInput, PayoffOutput)}
