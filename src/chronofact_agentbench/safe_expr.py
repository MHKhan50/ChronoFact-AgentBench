"""Evaluate a model-written label expression over four dates, without running arbitrary code.

The code-writing agent condition asks the model for one Python expression such as::

    "correct" if fs <= cs and ce <= fe else ("incorrect" if ce < fs or cs > fe else "transitional")

Only conditional expressions, boolean operators, comparisons, the four date names and string
constants are allowed. Anything else (calls, attributes, arithmetic, other names) is rejected,
so the expression is evaluated by this module, not by ``eval``.
"""

from __future__ import annotations

import ast
import operator
from datetime import date
from typing import Mapping

ALLOWED_NAMES = ("cs", "ce", "fs", "fe")
MAX_LENGTH = 400

_COMPARE = {
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}


class UnsafeExpression(ValueError):
    pass


def _eval(node: ast.AST, env: Mapping[str, date]):
    if isinstance(node, ast.Expression):
        return _eval(node.body, env)
    if isinstance(node, ast.IfExp):
        return _eval(node.body, env) if _eval(node.test, env) else _eval(node.orelse, env)
    if isinstance(node, ast.BoolOp):
        values = [_eval(value, env) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _eval(node.operand, env)
    if isinstance(node, ast.Compare):
        left = _eval(node.left, env)
        for op, comparator in zip(node.ops, node.comparators):
            if type(op) not in _COMPARE:
                raise UnsafeExpression("Comparison not allowed: {}".format(type(op).__name__))
            right = _eval(comparator, env)
            if not _COMPARE[type(op)](left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.Name):
        if node.id not in ALLOWED_NAMES:
            raise UnsafeExpression("Name not allowed: {}".format(node.id))
        return env[node.id]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise UnsafeExpression("Syntax not allowed: {}".format(type(node).__name__))


_ALLOWED_NODES = (ast.Expression, ast.IfExp, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.Compare,
                  ast.Name, ast.Load, ast.Constant) + tuple(_COMPARE)


def _check(tree: ast.AST) -> None:
    """Reject the whole expression if any part of it, evaluated or not, is outside the allowed set."""
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise UnsafeExpression("Syntax not allowed: {}".format(type(node).__name__))
        if isinstance(node, ast.Name) and node.id not in ALLOWED_NAMES:
            raise UnsafeExpression("Name not allowed: {}".format(node.id))
        if isinstance(node, ast.Constant) and not isinstance(node.value, str):
            raise UnsafeExpression("Only string constants are allowed")
        if isinstance(node, ast.UnaryOp) and not isinstance(node.op, ast.Not):
            raise UnsafeExpression("Only 'not' is allowed")


def evaluate_label_expression(expression: str, env: Mapping[str, date]) -> str:
    """Return the string the expression evaluates to; raise UnsafeExpression on anything else."""
    if not isinstance(expression, str) or not expression.strip():
        raise UnsafeExpression("Empty expression")
    if len(expression) > MAX_LENGTH:
        raise UnsafeExpression("Expression too long")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpression("Not a Python expression: {}".format(exc.msg))
    _check(tree)
    result = _eval(tree, env)
    if not isinstance(result, str):
        raise UnsafeExpression("Expression did not return a label")
    return result
