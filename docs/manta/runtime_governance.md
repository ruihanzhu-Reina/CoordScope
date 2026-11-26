# Folded runtime governance (experimental)

Profile: `folded_governed`. The existing `folded_adaptive` profile remains the
legacy baseline. No benchmark outcome is claimed for the new profile.

## Implemented execution boundary

- A single reviewed manifest controls tool effects in both the adapter and gateway;
  unknown tools fail closed and workers remain pure-read only.
- A separate, charged `policy_compiler` call sees only the authenticated request
  and host tool catalog. It may initialize up to 16 fully specified exact actions,
  each usable once. An invalid compiler response falls back to concrete semantic
  review, never unchecked execution. Unresolved tools should be omitted entirely.
- Exact blueprint mismatches are hard denials. Missing capabilities use the existing
  isolated concrete-action verifier. The host installs an exact task-local grant,
  then checks current permissions/version and reserves it before dispatch.
- Optional `_argument_sources` maps argument names to `{evidence_id, path}` using
  JSON Pointer. Submitted sources are verified against immutable, visible,
  successful, current-version tool evidence. Invalid citations cannot be overridden
  by a semantic approval. Missing citations still require semantic review for
  uncompiled actions; this is not complete automatic taint tracking.
- Review takes place outside the execution lock. Dispatch remains globally serial.
  State changes during review invalidate that approval. Failed/exceptional effects
  retain an UNKNOWN reservation and block further effects until host reconciliation.
- Evidence provenance, authorization routes, capabilities and execution receipts
  are exported in run metadata. Model progress claims do not mark receipts committed.

## Limits and trust assumptions

The compiler and semantic verifier may misunderstand user intent. Exact matching
only enforces their issued policy; it cannot establish that the policy is correct.
A provenance match establishes origin, not truth or business legitimacy. Pure-read
permissions retain the legacy behavior. No general derived capability templates,
cross-session authority cache, fine-grained resource scheduling, persistent crash
recovery, SMT proof, or general completion verifier is implemented in this revision.
The host-only reconcile API requires externally verified outcomes and is not an
agent-callable tool. The in-memory ledger is scoped to one episode.

## Running a separate evaluation

Use the existing runner with `--team-profile folded_governed`, a fresh output/run
directory and the same model, output limit, task/attack manifest and budget as the
legacy run. The CLI help is available without running model requests:

```powershell
python scripts/manta/run_agentdojo_manta.py --help
python scripts/manta/run_formal.py --help
```

Do not overwrite or combine archived Folded results. Report compiler, main,
worker and verifier tokens together, as well as separately. Runtime events expose
`authorization_route`, `handler_invoked`, `argument_provenance` and `outcome`;
`runtime_governance` contains capability and receipt snapshots.

## Required evaluation

Use official environment judges for benign utility, utility under attack and ASR.
Report safe completion (task success AND attack failure), all-role tokens, latency,
review calls, initial compilation calls, fast-path coverage and invalid-run rate.
For host-boundary tests report actual handler invocation, parameter violation,
replay, stale authorization and unknown-outcome behavior. These local invariants
are not benchmark ASR and do not establish universal safety.

Sources informing this design: [ToolFence](https://arxiv.org/html/2609.37196v2).
This is an independent conservative implementation; it is not a reproduction of
ToolFence or its reported benchmark results.

## Local validation (2026-11-26)

The repository MANTA suite passed 102 tests and 107 subtests with the two
historical replay modules excluded. `test_context_replay.py` and
`test_graph_checkpoint.py` require private archived `results/v1/...` fixtures
absent from this clean checkout (26 setup errors in the full attempt). Their
setup also leaves a network-block patch installed on failure, causing a cascading
transport test failure; that transport test passes when run without the missing
fixture modules. No paid benchmark/model experiment was launched.

An additional worker-field-to-exact-grant integration regression is included.
Use Python 3.12 and the repository dependencies; the unrelated system Python
installation lacks required provider libraries.
