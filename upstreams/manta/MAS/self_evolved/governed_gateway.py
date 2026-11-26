"""Task-local exact capabilities and host-owned execution receipts.

Semantic approval is still a trust assumption. No tool output, model-provided
source label, or progress claim can issue a capability. This first version uses
whole-environment versions and serial dispatch, not resource-level concurrency.
"""
import copy
import json
import uuid

from .action_policy import effect
from .tool_gateway import ToolGateway


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


class GovernedGateway(ToolGateway):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_scope = uuid.uuid4().hex
        self.capabilities = {}
        self.blueprint = {}
        self.receipts = []
        self.policy_events = []
        self.initialized = False

    def initialize(self, actions):
        """Host-only: accept the isolated compiler's exact, complete actions.

        Validate the entire batch before publishing anything. Partial/derived
        plans stay on the semantic slow path instead of guessing authority.
        """
        if self.initialized:
            raise ValueError("The initial blueprint is immutable within a task.")
        if not isinstance(actions, list) or len(actions) > 16:
            raise ValueError("Expected at most sixteen exact actions.")
        pending = {}
        for row in actions:
            if not isinstance(row, dict) or set(row) != {"tool", "arguments"}:
                raise ValueError("Invalid blueprint action.")
            name, arguments = row["tool"], row["arguments"]
            self._validate(name, arguments)
            if effect(name) in {"read", "unknown"}:
                raise ValueError("Only reviewed observable actions belong in this blueprint.")
            key = (name, canonical(arguments))
            pending[key] = self._capability(name, arguments, "isolated_compiler", 0)
        with self.lock:
            self.capabilities.update(pending)
            self.blueprint = dict(pending)
            self.initialized = True

    def _validate(self, name, args):
        if name not in self.tools or effect(name) == "unknown" or not isinstance(args, dict):
            raise ValueError("Unknown tool or invalid argument object.")
        schema = self.tools[name]["parameters"]
        if set(args) - set(schema.get("properties", {})):
            raise ValueError("Undeclared arguments cannot receive authority.")
        if not set(schema.get("required", ())) <= set(args):
            raise ValueError("Missing required arguments.")
        canonical(args)

    def _capability(self, name, args, origin, version, sources=()):
        return dict(id=uuid.uuid4().hex, task_scope=self.task_scope, tool=name,
                    arguments_json=canonical(args), origin=origin, version=version,
                    state="available", max_uses=1, sources=copy.deepcopy(list(sources)))

    def _sources(self, actor, arguments, sources, version):
        if not isinstance(sources, dict) or set(sources) - set(arguments):
            raise ValueError("Argument sources must name actual arguments.")
        proofs = []
        for parameter, ref in sources.items():
            proof = self.store.resolve(actor, ref, arguments[parameter], current_version=version)
            proofs.append(dict(parameter=parameter, **proof))
        return proofs

    def call(self, actor, name, arguments, evidence_ids=(), argument_sources=None):
        # Freeze once: caller and reviewer cannot mutate the dispatched payload.
        arguments = json.loads(canonical(arguments))
        refs = tuple(evidence_ids)
        sources = {} if argument_sources is None else copy.deepcopy(argument_sources)
        event = dict(actor=actor, tool=name, arguments=copy.deepcopy(arguments),
                     handler_invoked=False, environment_version=self.version)
        def deny(reason):
            event.update(status="blocked", policy_decision="deny", reason=reason)
            return dict(error="ACTION_BLOCKED", reason=reason,
                        instruction="Resolve the missing evidence or use an authorized alternative.")
        with self.lock:
            self.events.append(event)
            if name not in self.permissions.get(actor, set()):
                return deny("Tool is outside this actor's capabilities.")
            try:
                self._validate(name, arguments)
                for ref in refs:
                    self.store.read(actor, ref)
                proofs = self._sources(actor, arguments, sources, self.version)
                refs = tuple(dict.fromkeys((*refs, *(p["evidence_id"] for p in proofs))))
            except (ValueError, KeyError, TypeError) as exc:
                return deny(str(exc))
            kind = effect(name)
            decision, reason = self.contract.initial_decision(name, arguments, actor)
            if decision == "deny":
                return deny(reason)
            if kind == "read":
                # The reviewed read permission and original single-flight cache
                # remain unchanged. No model call occurs under this lock.
                self.events.pop()  # the legacy read gateway records its own event
                return super().call(actor, name, arguments, refs)
            signature = (name, canonical(arguments))
            cap = self.capabilities.get(signature)
            if cap and cap["state"] == "committed":
                self.store.grant(actor, [cap["evidence_id"]])
                event.update(status="already_applied", capability_id=cap["id"])
                return dict(already_applied=True, **self.store.read(actor, cap["evidence_id"]))
            if any(c["state"] in {"reserved", "unknown"} for c in self.capabilities.values()):
                return deny("An effect is pending or unknown; host reconciliation is required before more effects.")
            if any(key[0] == name for key in self.blueprint) and signature not in self.blueprint:
                return deny("Arguments violate the isolated initial blueprint; review cannot override it.")
            version = self.version
            needs_review = cap is None or (cap["origin"] != "isolated_compiler" and cap["version"] != version)
            if cap and cap["state"] == "revoked":
                return deny("Capability was revoked.")
        if needs_review:
            # Do not hold the execution lock across a network/model request.
            try:
                decision, reason = self.review(name, copy.deepcopy(arguments), refs)
            except Exception as exc:
                event.update(status="review_error", error_type=type(exc).__name__, phase="before_handler")
                raise
            if decision != "allow":
                return deny(reason)
        with self.lock:
            # Review is an exact task/version-scoped proposal, never dispatch.
            if self.version != version or name not in self.permissions.get(actor, set()):
                return deny("State or permissions changed during review; obtain fresh evidence and retry.")
            if any(c["state"] in {"reserved", "unknown"} for c in self.capabilities.values()):
                return deny("Another action reserved authority during review.")
            try:
                proofs = self._sources(actor, arguments, sources, version)
            except (ValueError, KeyError, TypeError) as exc:
                return deny(str(exc))
            cap = self.capabilities.get(signature)
            if cap and cap["state"] == "committed":
                self.store.grant(actor, [cap["evidence_id"]])
                event.update(status="already_applied")
                return dict(already_applied=True, **self.store.read(actor, cap["evidence_id"]))
            if needs_review:
                cap = self._capability(name, arguments, "semantic_grant", version, proofs)
                self.capabilities[signature] = cap
            if not cap or cap["state"] != "available" or cap["arguments_json"] != canonical(arguments):
                return deny("No available exact capability.")
            cap["state"] = "reserved"
            event.update(capability_id=cap["id"], policy_decision="allow",
                         authorization_route="semantic_grant" if needs_review else "capability_fast_path",
                         argument_provenance=proofs)
            try:
                event["handler_invoked"] = True
                output = self.tools[name]["handler"](copy.deepcopy(arguments))
            except BaseException as exc:
                cap["state"] = "unknown"
                self.version += 1
                self.cache.clear()
                event.update(status="handler_exception", outcome="unknown", error_type=type(exc).__name__)
                self.receipts.append(dict(capability_id=cap["id"], outcome="unknown", version=self.version))
                raise
            failed = isinstance(output, dict) and (bool(output.get("error")) or
                    output.get("ok") is False or output.get("success") is False)
            self.version += 1
            self.cache.clear()
            try:
                ref = self.store.add(output, tool=name, arguments=arguments, version=self.version, actor=actor)
            except BaseException as exc:
                cap["state"] = "unknown"
                event.update(status="receipt_exception", outcome="unknown", error_type=type(exc).__name__)
                self.receipts.append(dict(capability_id=cap["id"], outcome="unknown", version=self.version))
                raise
            cap.update(state="unknown" if failed else "committed", evidence_id=ref)
            event.update(status="runtime_error" if failed else "executed", outcome=cap["state"], evidence_id=ref)
            self.receipts.append(dict(capability_id=cap["id"], outcome=cap["state"], evidence_id=ref, version=self.version))
            return self.store.read(actor, ref)

    def reconcile(self, capability_id, outcome):
        """Host-only attestation hook; never exposed as an agent tool.

        Caller must establish the actual external outcome. This does not infer
        success from a model answer. Unknown is sticky until such attestation.
        """
        if outcome not in {"not_applied", "committed"}:
            raise ValueError("A verified outcome is required.")
        with self.lock:
            cap = next(c for c in self.capabilities.values() if c["id"] == capability_id)
            if cap["state"] != "unknown":
                raise ValueError("Only unknown outcomes need reconciliation.")
            # A committed outcome without a usable original result is revoked,
            # never replayed or represented by a fabricated success receipt.
            cap["state"] = "revoked" if outcome == "committed" else "available"
            self.version += 1
            self.cache.clear()
            self.receipts.append(dict(capability_id=capability_id, outcome=outcome, host_reconciled=True))

    def snapshot(self):
        return copy.deepcopy(dict(task_scope=self.task_scope, capabilities=list(self.capabilities.values()),
                                  receipts=self.receipts, policy_events=self.policy_events,
                                  provenance=self.store.graph.export(),
                                  unresolved=any(c["state"] in {"unknown", "reserved"} for c in self.capabilities.values())))
