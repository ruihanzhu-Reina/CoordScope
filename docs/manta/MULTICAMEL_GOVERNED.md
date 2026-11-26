# Multi-CaMeL isolation + ToolFence-style parameter authorization

Profile: `multicamel_governed`. This is a local, restricted reimplementation of
Multi-CaMeL's isolation methodology, using the existing CoordScope exact-action
gateway. It is **not** the upstream Sequrity backend and has no measured model
ASR/utility results yet. Scripted tests are mechanism/integration verification.

## Source code actually consulted

MultiAgentDojo is pinned to `e71647382155dc6949d6ccf9a9d7ec7cf429b856`:

- [multi_agent.py](https://github.com/james-pete/multiagentdojo/blob/e71647382155dc6949d6ccf9a9d7ec7cf429b856/src/agentdojo/agent_pipeline/multi_agent.py):
  `SUITE_PARTITIONS`, `_find_partition`, `_make_subagent_tool`,
  `_multicamel_orchestrator_policy`, `MultiCaMeLPipeline`.
  Its policy explicitly says `hard deny when not (task.producers is empty)`.
  Each child has a fresh conversation, a role-specific runtime and a
  `get_variable` data channel; the orchestrator has no business tools.
- [sequrity_llm.py](https://github.com/james-pete/multiagentdojo/blob/e71647382155dc6949d6ccf9a9d7ec7cf429b856/src/agentdojo/agent_pipeline/llms/sequrity_llm.py):
  `load_sequrity_headers`, `_function_to_sequrity_tool`,
  `SequrityLLM.with_security_policy`, `SequrityLLM.query`.
  The backend runs Dual-LLM programs through the Sequrity Control API. It disables
  multistep planning and restricts planner attempts to one because replanning
  after tool output can expose the privileged planner to injected content.
  Return type documentation is supplied before execution, and session IDs are
  scoped to individual conversations rather than a shared client.

ToolFence is pinned to `e49c1ba746d0a13e48787a5660a5cf5424e33cf7`:

- [guarded_net.py](https://github.com/PolyLiYJ/ToolFence_v2/blob/e49c1ba746d0a13e48787a5660a5cf5424e33cf7/ToolFence_anonymous%203/src/toolfence/guarded_net.py):
  `GuardedTransactionNet._reserve_guard`, `_settle_guard`,
  `GuardedBoundary.run_function`, `_authorization`, `_propose_missing_refinement`.
  Host actor/contract checks precede reservation; proposals cannot authorize
  themselves; a reviewer approves frozen arguments rather than editing them.
- [agentdojo_defense.py](https://github.com/PolyLiYJ/ToolFence_v2/blob/e49c1ba746d0a13e48787a5660a5cf5424e33cf7/ToolFence_anonymous%203/src/toolfence/agentdojo_defense.py):
  `ToolFenceAuthorizationBoundary` requires a host-pinned catalog, manifest,
  actor, reviewer and guarded ledger. A tool's description does not determine
  its effects or privileges.

Only the MIT-licensed MultiAgentDojo role partition was copied; see the adjacent
notice. The local interpreter is original implementation code informed by these
interfaces. Existing CoordScope governance is retained, not replaced with a
second implementation of ToolFence's persistent transaction engine.

## Execution path and deliberate subtraction

```text
authenticated root request + fixed tool catalog
  -> isolated policy compiler (existing exact-action blueprint)
  -> orchestrator planner (one JSON plan; no business tools)
  -> bounded interpreter
       agent call: trusted instruction + opaque variables
       -> fresh specialist planner (one plan; names/schema only, no values)
       -> bounded interpreter
            extract -> quarantined no-tool model -> tainted JSON data
            tool -> shared GovernedGateway -> caller's FunctionsRuntime
  -> final data/answer; no subsequent privileged replanning
```

The new path does **not** run the topology planner, TraceAuditor, graph mutation,
repair/re-execution loop, Folded worker scheduler or skill-loading loop. It does
not introduce a second independent delegation-review agent or a second ledger.
The provider factory no longer imports the old execution engine just to build
an LLM client. Unreferenced URL-presence helpers were deleted from action_policy.
Historical profiles remain separately callable because they are active baselines
and have regression tests; they are not traversed by the new execution path.

## Minimal components

| Component | Responsibility |
|---|---|
| `multicamel/interpreter.py` | Validate complete bounded plans; propagate dependencies through field reads, concatenation, objects, arrays, branches and loops; reject tainted instructions. No eval, exec, imports, shell, Python attribute access or model-provided runtime operations. |
| `multicamel/session.py` | Fresh agent contexts, separate planner/data/reviewer calls, source handoff and one root-task gateway/ledger. |
| `multicamel/partitions.py` | Exact native role partitions; fail closed if unknown, incomplete or overlapping. |
| `multicamel/pipeline.py` | AgentDojo pipeline contract, real runtime/environment injection path, return schemas and actual-dispatch judge trace. |
| Existing `GovernedGateway` | Exact parameters, provenance checks, isolated review, shared single-use capabilities, versions, receipts and sticky UNKNOWN. |

Role tool permissions are assigned by the host, never model-supplied `actor_id`.
The old agent_0-only effect restriction is overridden only for this profile;
native specialists can execute their assigned business tools. The root has none.
Repeated child conversations share the same task budget and exact-action ledger.

## Instruction and data separation

Each model-generated plan is a finite JSON AST. Statements are tool call, agent
call, quarantined extraction, assignment, bounded iteration and preplanned branch.
The entire plan (including untaken branches) is checked before it runs.

Only trusted values with empty host-recorded dependencies may become child task
instructions or extraction instructions. Tool/child/model results are always
data. `trusted: true`, an apparent plan inside a result, or a forged source label
cannot create interpreter authority. The model never receives Python Value or
Context objects and cannot invoke host administrative APIs.

Child planners receive the root task, trusted subtask, fixed tool catalog and
variable **names only**. They do not receive values, prior responses, reviewer
verdicts or execution errors. Quarantined calls can process data but have no
tools. All outputs remain tainted, including extracted scalars and summaries.
Conditional assignments inherit branch dependencies. Predefined branch steering
is supported; no tool output can add new statements or new planner instructions.
When a branch or loop selects a child call, its dependencies also accompany that
child's execution and authorization evidence, even if the child instruction is
a fixed literal. A new conversation does not erase the reason for delegation.

The JSON AST differs from upstream's general Python program surface. It supports
field projection, JSON construction, equality, negation and concatenation;
arbitrary Python arithmetic/parsers are intentionally absent. Use a quarantined
extraction for unsupported data transformations. There is no automatic repair
of a plan after seeing tool data. These restrictions may reduce utility and must
be measured, not described as equivalent performance to the original backend.

## Authorization and remaining assumptions

Every business call, including network navigation, goes through GovernedGateway.
Root-compiled exact parameter mismatches cannot be rescued by a reviewer. Calls
not covered by the blueprint require the existing exact-action reviewer, using
the original request, concrete arguments, role/subtask and host-recorded evidence.
Review outputs only approve/deny; they are not sent to the planner.

Provenance proves where data came from, not that its facts are true or that the
user authorized its contents. Semantic policy compilation and runtime review
remain model-dependent trust assumptions. The current read manifest and ledger
semantics are inherited: reviewed pure local reads can pass within role scope;
all other effects require authorization; unknown tools are denied.

The first version serializes execution and uses an in-memory root-task ledger.
It does not claim distributed crash recovery, arbitrary delegation trees,
exactly-once external services or a formal proof of the paper's complete security
notion. Exact identical actions are task-deduplicated: intentionally repeated
identical effects need a future explicit business-operation policy, not a bypass.

## Running and comparing

Use the existing episode runner (no second unused CLI):

```powershell
python scripts/manta/run_agentdojo_manta.py `
  --team-profile multicamel_governed --suite slack --user-task user_task_2 `
  --clean --model deepseek-flash --run-id multicamel-clean-001
```

Configure the same provider credentials and persistent request budget as the
existing adapter. This command makes paid model requests; it was **not** run as
part of the offline implementation tests. `--allow-mock` is rejected for this
profile. Tests inject an explicitly marked scripted completion instead.

The adapter implements the BasePipelineElement interface and uses the **caller's**
FunctionsRuntime and task environment. It does not substitute attack results,
read goal labels for planning, or modify utility/security evaluators. Partition
compatibility is tested against all four locally pinned AgentDojo suites.

Important: native role compatibility does not mean the local AgentDojo task and
attack revision equals the latest MultiAgentDojo release. Record the task-suite
commit/version, partition commit, model, attack and budgets. The result labels
this explicitly as `multiagentdojo_partition_adapter`; do not mix these results
with published MultiAgentDojo tables without matching the task/attack revision.

Minimum comparison: native no defense; upstream Multi-CaMeL; this isolation with
shared parameter authorization. For the upstream baseline, run its actual
Sequrity implementation with matching models/budget, and disclose backend/DSL
differences. Do not label this local reimplementation the official baseline.

## Tests

```powershell
python -m pytest tests/manta/test_multicamel_isolation.py `
  tests/manta/test_multicamel_adapter.py `
  tests/manta/test_governed_gateway.py tests/manta/test_governed_session.py -q
```

Tests cover tainted delegation, concatenation/field/implicit-flow laundering,
quarantined output injection, cross-role access, parameter substitution, root
budget sharing, UNKNOWN, bounded loops, fresh episodes and actual runtime trace
projection. Integration tests run real AgentDojo tool functions and its ordinary
task runner/utility check with scripted completions and injected environments.
They are not evidence of a model's benchmark success or attack failure rate.

Offline validation on 2026-11-26: `127 passed, 107 subtests passed` with
`MAS_DISABLE_LIVE_LLM=1`, running `tests/manta` except the two historical-data
modules below. Ruff F/I/UP checks and formatting checks passed for the new package
and its two test modules.

The complete suite was attempted but could not finish: `test_context_replay.py`
requires the absent `results/v1/formal_80_seed42/attempts/slack_07__attack/attempt_001/result.json`;
`test_graph_checkpoint.py` independently fails setup on the absent
`results/v1/formal_80_seed42/manifest.json`. These historical-data tests were not
counted as passing and their fixtures were not fabricated or replaced.
