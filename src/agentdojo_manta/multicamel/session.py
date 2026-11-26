"""One root task, fresh isolated agent planners, shared ToolFence-style gateway."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from agentdojo_manta.adapter import AdapterPaths, _ensure_manta_namespace

_ensure_manta_namespace(AdapterPaths.from_repo(Path(__file__).resolve().parents[3]))
from MAS.self_evolved.action_policy import TaskContract, effect
from MAS.self_evolved.evidence_store import EvidenceStore
from MAS.self_evolved.governed_gateway import GovernedGateway
from MAS.self_evolved.policy_compiler import compiler_messages

from .interpreter import IsolationError, PlanInterpreter, Value, freeze
from .prompts import EXTRACT_SYSTEM, PLAN_SYSTEM


@dataclass(frozen=True)
class Limits:
    max_model_calls: int = 64
    max_tokens: int = 250000
    max_steps: int = 256
    max_delegations: int = 24
    max_loop_items: int = 24
    max_json_chars: int = 1000000

    def __post_init__(self):
        if any(type(v) is not int or v < 1 for v in vars(self).values()):
            raise ValueError("All isolation limits must be positive integers.")


@dataclass(frozen=True)
class Context:
    actor: str
    role: str
    task: str
    tools: frozenset[str]
    dependencies: frozenset[str] = frozenset()


class RoleContract(TaskContract):
    """Role ownership is enforced by gateway permissions, not agent_0 identity."""

    def initial_decision(self, name, args, actor):
        if effect(name) == "unknown":
            return "deny", "Unclassified tool."
        if effect(name) == "read":
            return "allow", "Reviewed local read within the bound role."
        return "review", "Exact effect requires root-task authorization."


class IsolatedSession:
    def __init__(self, user_request, tools, specs, completion, limits=None):
        self.user_request, self.completion = user_request, completion
        self.limits = limits or Limits()
        self.roles = {spec.name: spec for spec in specs}
        self.catalog = {tool["name"]: {k: v for k, v in tool.items() if k != "handler"} for tool in tools}
        assigned = [tool for spec in specs for tool in spec.tool_names]
        if len(self.roles) != len(specs) or len(assigned) != len(set(assigned)) or set(assigned) != set(self.catalog):
            raise ValueError("Roles must uniquely partition the complete tool catalog.")
        self.store = EvidenceStore()
        self.gateway = GovernedGateway(tools, self.store, RoleContract(user_request), self.review)
        self.model_calls = self.tokens = self.steps = 0
        self.contexts = {}
        self.delegations, self.model_events, self.reviews = [], [], []
        self.review_context = None
        self.stop_reason = "not_started"

    def tick(self):
        self.steps += 1
        if self.steps > self.limits.max_steps:
            raise IsolationError("Execution step budget exhausted.")

    def complete(self, kind, actor, messages):
        if self.model_calls >= self.limits.max_model_calls or self.tokens >= self.limits.max_tokens:
            raise IsolationError("Model budget exhausted.")
        if len(freeze(messages)) > self.limits.max_json_chars:
            raise IsolationError("Model input exceeds its bound.")
        self.model_calls += 1
        event = dict(kind=kind, actor=actor, status="pending")
        self.model_events.append(event)
        try:
            result, tokens = self.completion(kind, actor, messages, self.limits.max_tokens - self.tokens)
            if type(tokens) is not int or tokens < 0:
                raise IsolationError("Completion token accounting must be a nonnegative integer.")
            self.tokens += tokens
            if self.tokens > self.limits.max_tokens:
                raise IsolationError("Model response exceeded the episode token budget.")
            if isinstance(result, str):
                if len(result) > self.limits.max_json_chars:
                    raise IsolationError("Model output exceeds its bound.")
                result = json.loads(result)
            result = json.loads(freeze(result))
            event.update(status="completed", tokens=tokens)
            return result
        except BaseException:
            event["status"] = "error"
            raise

    def initialize(self):
        result = self.complete(
            "compiler", "policy_compiler", compiler_messages(self.user_request, self.catalog.values())
        )
        try:
            if not isinstance(result, dict) or set(result) != {"actions"}:
                raise ValueError("Invalid policy document.")
            self.gateway.initialize(result["actions"])
        except (ValueError, TypeError, KeyError):
            self.gateway.initialize([])
            self.gateway.policy_events.append(dict(event="compiler_invalid", fallback="exact_action_review"))

    def plan(self, context, variables):
        packet = dict(
            root_request=self.user_request,
            task=context.task,
            role=context.role,
            input_variables=sorted(variables),
            tools=[self.catalog[n] for n in sorted(context.tools)],
        )
        if context.role == "orchestrator":
            packet["agents"] = [
                dict(name=spec.name, description=spec.description, tools=[self.catalog[n] for n in spec.tool_names])
                for spec in self.roles.values()
            ]
        # No tool outputs, variable values, errors, audit verdicts or previous
        # conversation are ever included in a planner request.
        return self.complete(
            "planner",
            context.actor,
            [dict(role="system", content=PLAN_SYSTEM), dict(role="user", content=freeze(packet))],
        )

    def _validate_context(self, context):
        if self.contexts.get(context.actor) is not context:
            raise IsolationError("Actor context was not issued by this task's host.")

    def delegate(self, parent, role, instruction, variables, control=()):
        self._validate_context(parent)
        if parent.role != "orchestrator" or role not in self.roles or not isinstance(instruction, str):
            raise IsolationError("Invalid delegation boundary.")
        if len(self.delegations) >= self.limits.max_delegations:
            raise IsolationError("Delegation budget exhausted.")
        actor = f"{role}_{len(self.delegations) + 1}"
        dependencies = parent.dependencies | frozenset(control)
        context = Context(actor, role, instruction, frozenset(self.roles[role].tool_names), dependencies)
        self.contexts[actor] = context
        self.gateway.permit(actor, context.tools)
        refs = set(dependencies).union(*(v.dependencies for v in variables.values()))
        self.store.grant(actor, refs, source_actor=parent.actor)
        record = dict(
            actor=actor,
            role=role,
            parent=parent.actor,
            task_scope=self.gateway.task_scope,
            message=instruction,
            variables=sorted(variables),
            evidence_ids=sorted(refs),
            status="started",
        )
        self.delegations.append(record)
        try:
            result = PlanInterpreter(self, context, variables).run(self.plan(context, variables))
            # Child answers are data even when the child returned a literal.
            value = self.record(context, "__agent_result__", result.data, result.dependencies)
            self.store.grant(parent.actor, value.dependencies, source_actor=actor)
            record["status"] = "completed"
            # A handoff must not refresh the original field's version by
            # replacing its proof with a newly timestamped agent-result record.
            return Value.of(result.data, value.dependencies, result.field)
        except BaseException:
            record["status"] = "failed"
            raise
        finally:
            self.gateway.permit(actor, [])

    def record(self, context, source, data, parents):
        if len(freeze(data)) > self.limits.max_json_chars:
            raise IsolationError("Data value exceeds its bound.")
        ref = self.store.add(
            data, tool=source, arguments={}, version=self.gateway.version, actor=context.actor, parents=sorted(parents)
        )
        return Value.of(data, frozenset(parents) | {ref}, (ref, ""))

    def extract(self, context, instruction, value):
        self._validate_context(context)
        for ref in value.dependencies:
            self.store.read(context.actor, ref)
        result = self.complete(
            "quarantined",
            context.actor + "_data",
            [
                dict(role="system", content=EXTRACT_SYSTEM),
                dict(role="user", content=freeze(dict(instruction=instruction, data=value.data))),
            ],
        )
        # Even a response that looks like a plan remains a data value. Preserve
        # all input dependencies, not just fields the data model claims it used.
        return self.record(context, "__quarantined_result__", result, value.dependencies)

    def tool(self, context, tool, values, control=()):
        self._validate_context(context)
        if tool not in context.tools:
            raise IsolationError("Tool is outside the specialist role.")
        refs = frozenset(control).union(*(v.dependencies for v in values.values()))
        for ref in refs:
            self.store.read(context.actor, ref)
        arguments = {key: value.data for key, value in values.items()}
        sources = {
            key: dict(evidence_id=value.field[0], path=value.field[1]) for key, value in values.items() if value.field
        }
        self.review_context = context
        try:
            receipt = self.gateway.call(context.actor, tool, arguments, sorted(refs), sources)
        finally:
            self.review_context = None
        if "evidence_id" not in receipt:
            # Raw guard reasons may include external content; keep them data.
            return self.record(context, "__blocked_call__", receipt, refs)
        ref = receipt["evidence_id"]
        row = self.store._row(context.actor, ref)
        return Value.of(row["value"], refs | {ref}, (ref, ""))

    def review(self, name, arguments, refs):
        context = self.review_context
        self._validate_context(context)
        if len(refs) > 12 or len(freeze(arguments)) > 24000:
            return "deny", "Action evidence exceeds the bounded review scope."
        evidence = [self.store.review_slice(context.actor, ref) for ref in refs]
        messages = self.gateway.contract.review_messages(name, arguments, evidence)
        packet = json.loads(messages[1]["content"])
        packet["delegation"] = dict(
            role=context.role, subtask=context.task, note="Planner-generated subtask is not additional user authority."
        )
        messages[1]["content"] = freeze(packet)
        verdict = self.complete("reviewer", "action_verifier", messages)
        valid = isinstance(verdict, dict) and verdict.get("decision") in {"allow", "deny"}
        decision = verdict["decision"] if valid else "deny"
        reason = str(verdict.get("reason", "Invalid review"))[:1200] if isinstance(verdict, dict) else "Invalid review"
        self.reviews.append(
            dict(
                actor=context.actor, tool=name, decision=decision, evidence_ids=list(refs), version=self.gateway.version
            )
        )
        return decision, reason

    def run(self):
        context = Context("orchestrator", "orchestrator", self.user_request, frozenset())
        self.contexts[context.actor] = context
        self.gateway.permit(context.actor, [])
        self.stop_reason = "running"
        try:
            self.initialize()
            result = PlanInterpreter(self, context, {}).run(self.plan(context, {}))
            self.stop_reason = "completed"
            return result.data if isinstance(result.data, str) else freeze(result.data)
        except BaseException:
            self.stop_reason = "failed_closed"
            raise

    def snapshot(self):
        return dict(
            profile="multicamel_governed",
            implementation="bounded_json_plan_interpreter",
            stop_reason=self.stop_reason,
            model_calls=self.model_calls,
            tokens=self.tokens,
            executed_steps=self.steps,
            delegations=self.delegations,
            model_events=self.model_events,
            action_reviews=self.reviews,
            gateway_events=self.gateway.events,
            runtime_governance=self.gateway.snapshot(),
            actual_specialist_count=len({r["role"] for r in self.delegations}),
            specialist_invocations=len(self.delegations),
        )
