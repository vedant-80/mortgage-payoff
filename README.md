# Mortgage Payoff Simulator

Compare a fixed-rate mortgage with and without extra principal payments. Submit both monthly amortization schedules, payoff dates, interest totals, and interest savings.

Task ID: `simulate-payoff`. Runner: `agent`. Each monetary value is an integer number of cents; a basis point is 1/100 of a percentage point. No tool solves the task or calls an LLM. All scenarios are synthetic, bundled JSON fixtures, not live financial data.

## Task input and output

Example task input:

```json
{
  "scenario_id": "starter-home"
}
```

The complete typed output is `PayoffOutput` in `contract.py`; nested row types also live there. All fields and rows are required. Month/year indices start at 1. Only the scenario IDs listed below are accepted. Arbitrary financial inputs are deliberately outside this task's scope.

Every submitted row and summary must match a fresh replay from the loan and extra-payment fixtures. Both complete schedules are required; fabricated balances, omitted rows, uncapped overpayments, wrong payoff dates, and wrong interest savings fail.

## Tools

| Tool | Input | Output |
|---|---|---|
| `get_mortgage` | scenario_id | Principal in cents, annual rate in basis points, term in months, first payment month. |
| `get_extra_payments` | scenario_id, start_month, end_month | Every extra payment in the inclusive 1-based month range. Query the entire term or multiple ranges. |
| `get_rules` | none | Precise payment, rounding, timing, and baseline rules. |

## Exact financial rules

1. All money is integer cents. Months are 1-based from start_month.
2. Monthly rate is annual_rate_bps / 120000. Round monthly interest to nearest cent, ties up.
3. Scheduled payment is the exact amortizing payment rounded UP to a whole cent; zero-rate payment is ceil(principal/term).
4. Each month: accrue interest, pay min(scheduled_payment, balance plus interest), then apply the extra principal capped at remaining balance. In the final contractual month, the regular payment instead settles the entire balance plus interest, including any cent-rounding residue.
5. No fees, escrow, penalties, or refinancing. Stop at payoff. Ignore extra payments dated after payoff.
6. Compare against the same loan without any extra payments. Report both schedules, payoff months, interest totals and their difference.

## Bundled scenarios

- `starter-home`
- `no-extra`
- `zero-interest`
- `immediate-payoff`
- `rounding`

Data: `src/plugin/data/scenarios.json`; authoritative rule text: `src/plugin/data/rules.json`. Scenario IDs are dictionary keys, never paths. Tools reread packaged fixtures and do not mutate data or use the workspace. Permission declarations request no network hosts or filesystem writes.

## Reproduce locally

Use Python 3.12 or later. From this plugin's directory:

```bash
# Financial calculations, fixture tools, malformed-output tests, and boundary tests:
python3 scripts/validate.py

# Sample candidate output plus the independent verifier verdict; no dependencies needed:
python3 scripts/solve.py starter-home > /tmp/mortgage-payoff-example.json

# Full typed-contract and MCP integration, after installing uv:
uv sync --frozen --extra dev
uv run python scripts/validate.py --require-runtime
uv run ruff check .
```

The standard-library test command explicitly skips the integration tests if runtime dependencies are missing. `--require-runtime` fails if any tests are skipped, so a partial run cannot count as complete runtime validation. Integration tests round-trip real slimconfig contracts, call every MCP handler, and launch the actual stdio server with an MCP client.

`uv.lock` inherits the resolved dependency graph and package hashes from the supplied arxiv-source reference, with this project's identity updated and slimconfig pinned to that reference's exact commit. Runtime dependency installation requires network access once; the task itself runs offline afterward. The frozen lock still needs a successful uv sync on a network-enabled machine to confirm installation.

To start the server directly after installation:

```bash
NANOAGENT_WORKSPACE=/tmp uv run --frozen python -m plugin
```

The server communicates via MCP stdio; it is normally launched by NanoAgent, not used as an interactive terminal program. `scripts/solve.py` is an offline example candidate generator, excluded from the MCP tool list; it is not an agent evaluation run.

## Verifier

The verifier computes the scheduled payment with exact integer powers and ceiling division, and replays cent-rounded monthly interest with integer arithmetic. The demonstration solver uses Fraction for the amortization formula and Decimal for interest. Neither verifier imports the demonstration solver.

The verifier accepts either contract dataclass instances (the harness interface) or raw dictionaries (local checks). Public entry points follow the reference: `verify_input(tool, value)`, `verify_output(tool, input_value, output_value, workspace)`, and `verify_task(task, arguments, output, reference, workspace)`. Verdicts contain `valid`, `score`, `message`, and `details`. The task check ignores any supplied reference answer and recomputes from fixtures.

Checks reject missing/extra fields, changed values, truncated or duplicated rows, incorrect ordering, booleans/floats substituted for integer cents, unknown scenarios, and invalid input bounds. Tool verifiers compare retrieved data to fixtures; task verifiers use independent financial implementations. Tests include hand-calculated cases, all bundled scenarios, negative-output mutations, and 100 deterministically seeded scenario variations per plugin.

## Layout and reference

```text
contract.py             Typed task/tool schemas and registries
nanoagent.yaml          NanoAgent runtime, permissions, tools, and agent task
pyproject.toml, uv.lock Standalone package metadata and pinned dependencies
src/plugin/            MCP server, read-only tools, bundled data, offline sample calculations
verifier/              Semantic validation and independent financial replay
tests/                 Standard-library tests plus optional real runtime integration
scripts/               Local validation and demonstration CLI
product/, ui/          Catalog metadata, icon, and default host-renderer declaration
```

Layout and MCP integration follow [arxiv-source at commit 30b5534](https://github.com/zeyuyang8/arxiv-source/tree/30b5534a8ed17f53c3e87d7a092ae20b1e5f6d24). The financial tasks, tools, data, and checks are original implementations. This directory is standalone and does not import either sibling finance plugin or the reference checkout.

## Limitations and submission evidence

Fixed rates only; no closing costs, property taxes, insurance, escrow, prepayment penalties, refinancing, or lender-specific conventions. The final contractual payment settles any cent-rounding residue and can differ slightly from the regular scheduled amount. Long mortgages require large structured outputs because both complete schedules are submitted.

These scenarios demonstrate calculations under stated assumptions and are not personalized financial advice. No RUSH Lab publication or live agent run is claimed. Collect actual task inputs, validation logs, and verifier verdicts outside this repository for the assignment PDF; the example command above writes to `/tmp` for that reason. A passing sample solver run demonstrates the verifier path, not that an agent successfully completed the task.
