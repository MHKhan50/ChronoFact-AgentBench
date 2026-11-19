from datetime import date

import pytest

from chronofact_agentbench.safe_expr import UnsafeExpression, evaluate_label_expression

ENV = {"cs": date(2001, 1, 1), "ce": date(2001, 12, 31), "fs": date(1999, 5, 1), "fe": date(2001, 6, 30)}
RULE = '"correct" if fs <= cs and ce <= fe else ("incorrect" if ce < fs or cs > fe else "transitional")'


def test_rule_expression_gives_partial_overlap():
    assert evaluate_label_expression(RULE, ENV) == "transitional"


def test_rule_expression_gives_containment_and_no_overlap():
    inside = dict(ENV, cs=date(2000, 1, 1), ce=date(2000, 12, 31))
    outside = dict(ENV, cs=date(2005, 1, 1), ce=date(2005, 12, 31))
    assert evaluate_label_expression(RULE, inside) == "correct"
    assert evaluate_label_expression(RULE, outside) == "incorrect"


@pytest.mark.parametrize("expression", [
    "__import__('os').system('ls')",
    "open('x').read()",
    "cs.year",
    "(fe - fs)",
    "x if cs < fe else 'correct'",
    "'correct' if cs > fe else open('x')",
    "",
    "'correct' if",
    "cs < fe",
])
def test_unsafe_or_invalid_expressions_are_rejected(expression):
    with pytest.raises(UnsafeExpression):
        evaluate_label_expression(expression, ENV)
