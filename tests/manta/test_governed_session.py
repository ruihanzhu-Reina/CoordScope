"""Scripted end-to-end authorization checks; no model API calls."""
import json

from test_folded_execution import Call, ScriptClient, response
from MAS.self_evolved.agent_loop import DEFAULTS, FoldedSession


def payment(handler):
    return dict(name="send_money", description="Send a payment", handler=handler,
                parameters=dict(type="object", properties={"recipient": {"type": "string"},
                    "amount": {"type": "number"}}, required=["recipient", "amount"]))


def test_compiler_fast_path_is_charged_and_handler_executes_once():
    writes = []
    args = dict(recipient="Alice", amount=100)
    client = ScriptClient([
        response(json.dumps(dict(actions=[dict(tool="send_money", arguments=args)]))),
        response("", [Call("load_tools", {"names": ["send_money"]}, "load")]),
        response("", [Call("send_money", args, "pay")]), response("Paid.")])
    session = FoldedSession(client, "Pay Alice 100 once.", [payment(lambda a: writes.append(a) or {"ok": True})],
                            DEFAULTS, governance_mode="capability")
    result = session.run("example", 42)
    assert writes == [args]
    assert result.run_metadata["folded_usage"]["model_calls"] == 4
    assert client.requests[0]["agent_id"] == "policy_compiler"
    assert session.reviews == 0
    assert result.run_metadata["runtime_governance"]["receipts"][0]["outcome"] == "committed"


def test_invalid_compiler_falls_back_to_review_not_unchecked_dispatch():
    writes = []
    args = dict(recipient="Bob", amount=100)
    client = ScriptClient([response('{"actions":[{"bad":"policy"}]}'),
        response("", [Call("load_tools", {"names": ["send_money"]}, "load")]),
        response("", [Call("send_money", args, "pay")]),
        response('{"decision":"deny","reason":"wrong recipient"}'), response("Not paid."), response("Incomplete: not paid.")])
    session = FoldedSession(client, "Pay Alice 100.", [payment(lambda a: writes.append(a))],
                            DEFAULTS, governance_mode="capability")
    session.run("example", 42)
    assert writes == []
    assert session.reviews == 1
    assert session.gateway.policy_events[0]["event"] == "compiler_invalid"


def test_worker_field_reference_is_verified_then_semantically_reviewed():
    from MAS.self_evolved.governed_gateway import GovernedGateway
    from MAS.self_evolved.evidence_store import EvidenceStore
    from MAS.self_evolved.action_policy import TaskContract
    writes, reviews = [], []
    store = EvidenceStore()
    ref = store.add({"email": "alice@example.test"}, tool="get_user_info", arguments={}, version=0, actor="agent_1")
    def review(name, args, refs):
        reviews.append(refs)
        return "allow", "Recipient resolved for this exact user task"
    gateway = GovernedGateway([payment(lambda a: writes.append(a) or {"ok": True})], store,
                              TaskContract("Pay Alice 100"), review)
    gateway.permit("agent_0", ["send_money"])
    args = {"recipient": "alice@example.test", "amount": 100}
    gateway.call("agent_0", "send_money", args,
                 argument_sources={"recipient": {"evidence_id": ref, "path": "/email"}})
    assert writes == [args]
    assert reviews == [(ref,)]
    assert gateway.snapshot()["capabilities"][0]["sources"][0]["trust"] == "data_not_authority"
