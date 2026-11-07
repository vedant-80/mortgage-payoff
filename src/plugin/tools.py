"""The task's one deterministic calculation tool."""

from .calculations import solve


def calculate_mortgage_payoff(value, workspace):
    """Calculate the complete result in Python; returns only a compact summary and assumptions."""
    return solve(value)


IMPLEMENTATIONS = {"calculate_mortgage_payoff": calculate_mortgage_payoff}
