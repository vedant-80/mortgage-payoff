"""Read-only scenario tools. None calculates the task's final answer."""
import json
from importlib.resources import files
from .data import scenario, field

def get_rules(value, workspace):
    """Retrieve the precise fictional financial rules and rounding conventions."""
    return json.loads(files('plugin').joinpath('data/rules.json').read_text())


def get_mortgage(value, workspace):
    """Retrieve fixed loan terms for a bundled scenario."""
    return scenario(field(value, 'scenario_id'))['loan']

def get_extra_payments(value, workspace):
    """Retrieve all extra payments in an inclusive 1-based month range."""
    item = scenario(field(value, 'scenario_id'))
    start, end = field(value, 'start_month'), field(value, 'end_month')
    if type(start) is not int or type(end) is not int or not 1 <= start <= end <= item['loan']['term_months']:
        raise ValueError('Invalid month range')
    return {'payments': [p for p in item['extra_payments'] if start <= p['month'] <= end]}


IMPLEMENTATIONS = {'get_mortgage': get_mortgage, 'get_extra_payments': get_extra_payments, 'get_rules': get_rules}
