"""A bounded JSON plan interpreter; model output is never Python/eval input.

Plans come only from isolated planner calls. Values from tools, quarantined
models and child agents carry host-owned dependencies through every operation.
Only dependency-free strings can enter a child planner's instruction channel.
This is a restricted reimplementation, not the upstream Sequrity interpreter.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


class IsolationError(ValueError):
    """Fail closed without sending external errors back to the planner."""


def freeze(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


@dataclass(frozen=True)
class Value:
    payload: str
    dependencies: frozenset[str] = frozenset()
    field: tuple[str, str] | None = None

    @classmethod
    def of(cls, value, dependencies=(), field=None):
        payload = freeze(value)
        if len(payload) > 1000000:
            raise IsolationError("Runtime value exceeds its size bound.")
        return cls(payload, frozenset(dependencies), field)

    @property
    def data(self):
        return json.loads(self.payload)

    def instruction(self):
        if self.dependencies or not isinstance(self.data, str):
            raise IsolationError("Untrusted or non-string value cannot enter an instruction channel.")
        return self.data


def combine(value, *inputs, control=()):
    return Value.of(value, frozenset(control).union(*(v.dependencies for v in inputs)))


def name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", value):
        raise IsolationError("Invalid static identifier.")
    return value


def keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or not set(required) <= set(value):
        raise IsolationError("Unsupported plan fields.")


class PlanInterpreter:
    def __init__(self, session, context, variables):
        self.session, self.context = session, context
        self.variables = dict(variables)
        self.seen = set(context.dependencies).union(*(v.dependencies for v in variables.values()))
        self._validation_nodes = 0

    def _node(self, depth):
        self._validation_nodes += 1
        if depth > 20 or self._validation_nodes > 2000:
            raise IsolationError("Plan structure exceeds its bound.")

    def validate_expr(self, expr, depth=0):
        self._node(depth)
        if not isinstance(expr, dict):
            raise IsolationError("Expressions must use an explicit operation tag.")
        if set(expr) == {"literal"}:
            freeze(expr["literal"])
        elif set(expr) <= {"ref", "path"} and "ref" in expr:
            name(expr["ref"])
            path = expr.get("path", [])
            if not isinstance(path, list) or any(type(p) not in {int, str} for p in path):
                raise IsolationError("Field paths must be static strings or indices.")
        elif set(expr) in ({"object"}, {"array"}, {"concat"}, {"eq"}, {"not"}):
            op, body = next(iter(expr.items()))
            if op == "object":
                if not isinstance(body, dict):
                    raise IsolationError("Object expression requires static field names.")
                children = body.values()
            elif op == "not":
                children = [body]
            else:
                if not isinstance(body, list) or (op == "eq" and len(body) != 2):
                    raise IsolationError("Invalid expression operands.")
                children = body
            for child in children:
                self.validate_expr(child, depth + 1)
        else:
            raise IsolationError("Unknown expression operation.")

    def validate_steps(self, steps, depth=0):
        self._node(depth)
        if not isinstance(steps, list):
            raise IsolationError("Plan steps must be an array.")
        for step in steps:
            self._node(depth)
            if not isinstance(step, dict):
                raise IsolationError("Invalid statement.")
            op = step.get("op")
            if op == "tool":
                keys(step, {"op", "name", "args", "out"})
                if step["name"] not in self.context.tools:
                    raise IsolationError("Tool is not assigned to this role.")
                if not isinstance(step["args"], dict):
                    raise IsolationError("Tool arguments must have static names.")
                for expr in step["args"].values():
                    self.validate_expr(expr, depth + 1)
            elif op == "agent":
                keys(step, {"op", "name", "message", "variables", "out"})
                if self.context.role != "orchestrator" or step["name"] not in self.session.roles:
                    raise IsolationError("Only the orchestrator can call a registered specialist.")
                self.validate_expr(step["message"], depth + 1)
                if not isinstance(step["variables"], dict):
                    raise IsolationError("Agent variable names must be static.")
                for key, expr in step["variables"].items():
                    name(key)
                    self.validate_expr(expr, depth + 1)
            elif op == "extract":
                keys(step, {"op", "instruction", "data", "out"})
                self.validate_expr(step["instruction"], depth + 1)
                self.validate_expr(step["data"], depth + 1)
            elif op == "let":
                keys(step, {"op", "value", "out"})
                self.validate_expr(step["value"], depth + 1)
            elif op == "if":
                keys(step, {"op", "condition", "then", "else"})
                self.validate_expr(step["condition"], depth + 1)
                self.validate_steps(step["then"], depth + 1)
                self.validate_steps(step["else"], depth + 1)
            elif op == "for_each":
                keys(step, {"op", "items", "item", "steps"})
                name(step["item"])
                self.validate_expr(step["items"], depth + 1)
                self.validate_steps(step["steps"], depth + 1)
            else:
                raise IsolationError("Unsupported plan statement.")
            if "out" in step:
                name(step["out"])

    def evaluate(self, expr):
        if "literal" in expr:
            return Value.of(expr["literal"])
        if "ref" in expr:
            if expr["ref"] not in self.variables:
                raise IsolationError("Undefined variable.")
            source = self.variables[expr["ref"]]
            data, field = source.data, source.field
            for part in expr.get("path", []):
                if isinstance(data, dict) and isinstance(part, str) and part in data:
                    data = data[part]
                elif isinstance(data, list) and type(part) is int and 0 <= part < len(data):
                    data = data[part]
                else:
                    raise IsolationError("Field unavailable; raw tool errors are not planner feedback.")
                if field:
                    field = (field[0], field[1] + "/" + str(part).replace("~", "~0").replace("/", "~1"))
            return Value.of(data, source.dependencies, field)
        op, body = next(iter(expr.items()))
        if op == "object":
            values = {key: self.evaluate(value) for key, value in body.items()}
            return combine({k: v.data for k, v in values.items()}, *values.values())
        if op == "not":
            value = self.evaluate(body)
            if type(value.data) is not bool:
                raise IsolationError("Boolean condition required.")
            return combine(not value.data, value)
        values = [self.evaluate(value) for value in body]
        if op == "array":
            return combine([v.data for v in values], *values)
        if op == "concat":
            if any(not isinstance(v.data, str) for v in values):
                raise IsolationError("Concatenation requires strings.")
            return combine("".join(v.data for v in values), *values)
        return combine(values[0].data == values[1].data, *values)

    def execute(self, steps, control=()):
        for step in steps:
            self.session.tick()
            op = step["op"]
            if op == "if":
                condition = self.evaluate(step["condition"])
                if type(condition.data) is not bool:
                    raise IsolationError("Boolean condition required.")
                self.seen.update(condition.dependencies)
                self.execute(
                    step["then"] if condition.data else step["else"], frozenset(control) | condition.dependencies
                )
                continue
            if op == "for_each":
                items = self.evaluate(step["items"])
                if not isinstance(items.data, list) or len(items.data) > self.session.limits.max_loop_items:
                    raise IsolationError("Iteration exceeds its bound or is not an array.")
                self.seen.update(items.dependencies)
                for index, item in enumerate(items.data):
                    field = (items.field[0], items.field[1] + f"/{index}") if items.field else None
                    self.variables[step["item"]] = Value.of(item, items.dependencies | frozenset(control), field)
                    self.execute(step["steps"], frozenset(control) | items.dependencies)
                continue
            if op == "let":
                value = self.evaluate(step["value"])
            elif op == "tool":
                args = {key: self.evaluate(expr) for key, expr in step["args"].items()}
                value = self.session.tool(self.context, step["name"], args, control)
            elif op == "agent":
                instruction = self.evaluate(step["message"]).instruction()
                variables = {key: self.evaluate(expr) for key, expr in step["variables"].items()}
                value = self.session.delegate(self.context, step["name"], instruction, variables, control)
            else:
                instruction = self.evaluate(step["instruction"]).instruction()
                data = self.evaluate(step["data"])
                value = self.session.extract(
                    self.context, instruction, Value.of(data.data, data.dependencies | frozenset(control), data.field)
                )
            self.seen.update(value.dependencies)
            self.variables[step["out"]] = Value.of(value.data, value.dependencies | frozenset(control), value.field)

    def run(self, plan: dict[str, Any]):
        # Validate the entire plan, including untaken branches, before effects.
        keys(plan, {"steps", "return"})
        self.validate_steps(plan["steps"])
        self.validate_expr(plan["return"])
        self.execute(plan["steps"], self.context.dependencies)
        result = self.evaluate(plan["return"])
        return Value.of(result.data, result.dependencies | self.seen, result.field)
