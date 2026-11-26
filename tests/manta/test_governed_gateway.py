"""Host-boundary regressions with controlled handlers, no model or network."""

import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from agentdojo_manta.adapter import AdapterPaths, _ensure_manta_namespace

_ensure_manta_namespace(AdapterPaths.from_repo(ROOT))
from MAS.self_evolved.action_policy import TaskContract
from MAS.self_evolved.evidence_store import EvidenceStore
from MAS.self_evolved.governed_gateway import GovernedGateway


def tool(name, handler):
    return dict(name=name, description="Controlled test handler", handler=handler,
                parameters=dict(type="object", properties={"recipient": {"type": "string"},
                    "amount": {"type": "number"}}, required=["recipient", "amount"]))


def gateway(handler=None, review=None):
    calls, reviews = [], []
    def record(args):
        calls.append(args)
        return handler(args) if handler else {"ok": True}
    def approve(name, args, refs):
        reviews.append((name, args, refs))
        return review(name, args, refs) if review else ("allow", "controlled test approval")
    tools = [tool("send_money", record), tool("get_execute_payment", record)]
    g = GovernedGateway(tools, EvidenceStore(), TaskContract("Pay Alice 10 once"), approve)
    g.permit("agent_0", [t["name"] for t in tools])
    g.permit("agent_1", [t["name"] for t in tools])
    return g, calls, reviews


ARGS = dict(recipient="Alice", amount=10)


def test_compiled_payload_mismatch_cannot_be_overridden_by_review():
    g, calls, reviews = gateway()
    g.initialize([dict(tool="send_money", arguments=ARGS)])
    assert g.call("agent_0", "send_money", {**ARGS, "amount": 1000})["error"] == "ACTION_BLOCKED"
    assert calls == reviews == []
    g.call("agent_0", "send_money", ARGS)
    assert calls == [ARGS]
    assert reviews == []
    assert g.call("agent_0", "send_money", ARGS)["already_applied"] is True
    assert calls == [ARGS]


def test_unknown_and_worker_effects_never_reach_review_or_handler():
    g, calls, reviews = gateway()
    g.initialize([dict(tool="send_money", arguments=ARGS)])
    assert g.call("agent_0", "get_execute_payment", ARGS)["error"] == "ACTION_BLOCKED"
    assert g.call("agent_1", "send_money", ARGS)["error"] == "ACTION_BLOCKED"
    assert calls == reviews == []


def test_invalid_provenance_cannot_be_rescued_by_semantic_approval():
    g, calls, reviews = gateway()
    ref = g.store.add({"recipient": "Bob"}, tool="get_user_info", arguments={}, version=0, actor="agent_0")
    result = g.call("agent_0", "send_money", ARGS,
                    argument_sources={"recipient": {"evidence_id": ref, "path": "/recipient"}})
    assert result["error"] == "ACTION_BLOCKED"
    assert calls == reviews == []


def test_state_change_during_review_invalidates_approval():
    def review(name, args, refs):
        # A separate compiler-approved action changes the state during this review.
        g.call("agent_0", "send_money", compiled)
        return "allow", "approval from the old version"
    g, calls, reviews = gateway(review=review)
    compiled = dict(recipient="Alice", amount=1)
    # Install a host-issued exact grant without a per-tool blueprint restriction.
    from MAS.self_evolved.governed_gateway import canonical
    g.capabilities[("send_money", canonical(compiled))] = g._capability("send_money", compiled, "isolated_compiler", 0)
    result = g.call("agent_0", "send_money", ARGS)
    assert result["error"] == "ACTION_BLOCKED"
    assert calls == [compiled]
    assert len(reviews) == 1


def test_permission_change_during_review_invalidates_approval():
    def review(name, args, refs):
        g.permit("agent_0", [])
        return "allow", "stale permission"
    g, calls, _ = gateway(review=review)
    assert g.call("agent_0", "send_money", ARGS)["error"] == "ACTION_BLOCKED"
    assert calls == []


def test_review_cannot_change_the_frozen_dispatch_arguments():
    def review(name, args, refs):
        args["recipient"] = "Mallory"
        return "allow", "controlled"
    g, calls, _ = gateway(review=review)
    g.call("agent_0", "send_money", ARGS)
    assert calls == [ARGS]


def test_concurrent_same_action_dispatches_at_most_once():
    rendezvous = threading.Barrier(2)
    def review(*args):
        rendezvous.wait(timeout=3)
        return "allow", "controlled"
    g, calls, _ = gateway(review=review)
    results, errors = [], []
    def run():
        try:
            results.append(g.call("agent_0", "send_money", ARGS))
        except BaseException as exc:
            errors.append(exc)
    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
    assert not any(thread.is_alive() for thread in threads)
    assert errors == []
    assert len(results) == 2
    assert calls == [ARGS]


@pytest.mark.parametrize("failure", [{"error": "ambiguous result"}, {"ok": False}, {"success": False}])
def test_failed_effect_remains_unknown_and_blocks_other_effects(failure):
    g, calls, _ = gateway(handler=lambda args: failure)
    g.call("agent_0", "send_money", ARGS)
    assert g.snapshot()["unresolved"] is True
    assert g.receipts[-1]["outcome"] == "unknown"
    assert g.call("agent_0", "send_money", {**ARGS, "amount": 1})["error"] == "ACTION_BLOCKED"
    assert calls == [ARGS]


def test_evidence_recording_failure_after_dispatch_is_unknown(monkeypatch):
    g, calls, _ = gateway()
    def broken_record(*args, **kwargs):
        raise ValueError("recording failed after the external effect")
    monkeypatch.setattr(g.store, "add", broken_record)
    with pytest.raises(ValueError):
        g.call("agent_0", "send_money", ARGS)
    assert calls == [ARGS]
    snapshot = g.snapshot()
    assert snapshot["unresolved"] is True
    assert snapshot["capabilities"][0]["state"] == "unknown"
    assert g.receipts[-1]["outcome"] == "unknown"
    g.reconcile(snapshot["capabilities"][0]["id"], "committed")
    assert g.call("agent_0", "send_money", ARGS)["error"] == "ACTION_BLOCKED"
    assert calls == [ARGS]
