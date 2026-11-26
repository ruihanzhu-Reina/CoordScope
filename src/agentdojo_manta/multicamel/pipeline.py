"""AgentDojo-compatible adapter using MultiAgentDojo's pinned role partitions.

The caller's runtime/environment remain authoritative for injections and judges.
This module does not read injection goals, expected answers or security labels.
"""

from __future__ import annotations

import threading

from pydantic import TypeAdapter

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.functions_runtime import EmptyEnv
from agentdojo.logging import Logger
from agentdojo_manta.adapter import _build_agentdojo_messages, _function_to_manta_tool, _make_llm_client

from .partitions import match_partition
from .session import IsolatedSession, Limits

PARTITION_COMMIT = "e71647382155dc6949d6ccf9a9d7ec7cf429b856"


class MultiCaMeLGovernedPipeline(BasePipelineElement):
    name = "coordscope-multicamel-governed"

    def __init__(self, paths, *, model=None, completion=None, partitions=None, limits=None):
        self.paths, self.partitions = paths, partitions
        self.limits = limits or Limits()
        self._metrics_lock = threading.Lock()
        self.request_records, self.runtime_calls = [], []
        self.injections = {}
        self.mock_used = completion is not None
        self.execution_completed = False
        self.provider_fatal_error = None
        self.last_run_metadata, self.last_trace_events = {}, []
        self.seed = 0
        self._completion = completion
        from agentdojo_manta.providers import provider_config

        self.model = provider_config(model).model
        # Deterministic injected callbacks are only for offline verification.
        self.client = None if completion else _make_llm_client(paths, self.model, observer=self)

    def bind_suite(self, suite):
        # Deliberately do not inspect task/goal registries.
        match_partition({f.name for f in suite.tools}, self.partitions)

    def complete(self, kind, actor, messages, remaining_tokens):
        if self._completion is not None:
            return self._completion(kind, actor, messages, remaining_tokens)
        response = self.client.complete_isolated(
            messages=messages, agent_id=actor, remaining_tokens=remaining_tokens, kind=kind
        )
        return response.choices[0].message.content, response.usage.prompt_tokens + response.usage.completion_tokens

    def query(self, query, runtime, env=EmptyEnv(), messages=(), extra_args=None):
        if messages:
            raise ValueError("Isolated episodes must start with a fresh root request, not an external transcript.")
        self.request_records, self.runtime_calls = [], []
        self.execution_completed = False
        self.provider_fatal_error = None
        self.last_run_metadata, self.last_trace_events = {}, []
        # Observer-only attack exposure accounting; never goes to planning or policy.
        self.injections = dict(getattr(Logger.get(), "context", {}).get("injections", {}))
        suite_name, specs = match_partition(set(runtime.functions), self.partitions)
        tools = []
        for function in runtime.functions.values():
            tool = _function_to_manta_tool(runtime, env, function, observer=self)
            try:
                tool["returns"] = TypeAdapter(function.return_type).json_schema()
            except (TypeError, ValueError):
                tool["returns"] = {"description": "Opaque JSON result; parse with quarantined extract."}
            tools.append(tool)
        session = IsolatedSession(query, tools, specs, self.complete, self.limits)
        try:
            answer = session.run()
            self.execution_completed = True
        finally:
            metadata = session.snapshot()
            metadata.update(
                suite=suite_name,
                partition_upstream_commit=PARTITION_COMMIT,
                agentdojo_adapter="official_runtime_and_judges",
                benchmark_scope="pinned_MultiAgentDojo_roles_on_caller_supplied_tasks",
                agentdojo_runtime_calls=list(self.runtime_calls),
                topology_layout=dict(agent_ids=list(session.contexts)),
            )
            self.last_run_metadata = metadata
            self.last_trace_events = list(session.gateway.events)
        result_messages = _build_agentdojo_messages(query, metadata, answer)
        return query, runtime, env, result_messages, {**(extra_args or {}), "manta_run_metadata": metadata}
