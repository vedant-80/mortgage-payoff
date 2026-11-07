# Mortgage Payoff Calculator

A custom-input deterministic calculator, not a bundled-scenario exercise. Money is integer cents in one currency. Rates are integer basis points (100 basis points = 1%). The host chat translates a description into typed input and asks for missing personal facts. The task itself runs one Python tool without an inner LLM loop. The model does not produce schedules.

## Tools

Task `simulate-payoff` directly runs `calculate_mortgage_payoff`. Both share the same typed input and compact output in `contract.py`. Essential personal inputs have no defaults; ask for them. Nullable assumption keys are still required in machine input: pass `null` to use their documented defaults. Zero is an explicit value, not a request for a default. Effective assumptions and the names of defaulted fields are always returned.

```json
{
  "balance_cents": 25000000,
  "annual_interest_bps": 600,
  "monthly_payment_cents": 180000,
  "extra_monthly_payment_cents": 20000
}
```

## Financial rules

Required inputs: outstanding balance, fixed nominal annual interest rate, and the monthly principal-and-interest payment (exclude escrow). Missing essentials must be requested. Recurring extra payment defaults to zero only when passed as null. Balances/payments are integer cents from 0 to 10^15; annual interest is 0 to 10000 bps. Use one currency. Zero starting balance is already paid off, with zero months and interest.

At each month: compute interest on the opening balance as balance × annual_interest_bps / 120000, round to nearest cent with half-cent ties up, then apply the regular plus extra payment. Cap the final payment at balance plus interest. Repeat in Python, comparing with an independent baseline that has no extras. The monthly payment is specified by the user; the tool does not infer a contractual term or force a balloon settlement.

If a positive balance's first rounded interest charge is >= the planned payment, that plan cannot amortize: return `non_amortizing` before applying any payment. Otherwise simulate up to 1200 months (100 years); return `search_limit` if unpaid. Interest/payment totals for unsuccessful simulations cover only `months_simulated`, not a lifetime. Baseline failure does not prevent the extra-payment plan from succeeding. Savings are null unless both plans pay off.

Output: compact plan and baseline summaries with payoff months, whole years plus remaining months, interest, applied payments, remaining balance, status, savings, and effective inputs. No monthly schedules or dates. Earliest payoff means payoff under the specified payment plan, not an optimization with unlimited funds.

Out of scope: variable rates, refinancing, fees, escrow, penalties, tax deductions, currency conversion, and lump-sum or irregular extras.

## Layout

`contract.py` declares the typed task/tool. `nanoagent.yaml` selects `runner: tool`. `src/plugin/` contains the deterministic calculator and MCP server. `verifier/` independently replays the calculation using Decimal arithmetic, with no imports from the calculator. `tests/` covers boundaries, malformed data, default handling, differential replay, and real MCP transport. `product/` and `ui/` provide catalog metadata and the host's standard structured-output display.

## Develop and run

Use Python 3.12+:

```bash
python3 tests/validate.py
uv sync --frozen --extra dev
uv run python tests/validate.py --require-runtime
uv run ruff check .
# With NanoAgent installed, check publication rules too:
nanoagent plugin inspect .
```

The dependency-free run skips integration tests when dependencies are absent. `--require-runtime` fails on skipped tests. For a direct local calculation from the editable example:

```bash
PYTHONPATH=src python3 -c 'import json; from plugin.calculations import solve; print(json.dumps(solve(json.load(open("tests/example.json"))), indent=2))'
```

The MCP server requires `NANOAGENT_WORKSPACE`; after installation it starts with `NANOAGENT_WORKSPACE=/tmp uv run --frozen python -m plugin`. No network access or filesystem writes are requested by this plugin. Every calculation is independently verified; verification ignores supplied reference answers and rejects wrong assumptions, missing/extra fields, booleans in integer fields, and changed results. Invalid essential inputs return clear MCP error results.

The standard layout follows arxiv-source at commit 30b5534 and NanoAgent v0001. The slimconfig source follows NanoAgent's required master declaration; `uv.lock` pins its resolved commit. Version 0.2.0 replaces the incompatible scenario-based API. Old scenario IDs, schedule outputs, and offline scenario solver are intentionally removed.

For the assignment, collect live task inputs, logs, and verifier verdicts outside this repository for the report. Passing local checks is not a claim of marketplace publication or a successful live chat run. Interpreting ambiguous natural-language facts is the outer chat's responsibility; deterministic verification validates the structured calculation request, not the user's intended meaning.
