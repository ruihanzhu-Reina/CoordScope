"""Offline authority/schema and profile regressions; no model requests."""

import copy
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from agentdojo_manta.adapter import AdapterPaths, MantaAgentDojoPipeline, _ensure_manta_namespace, _function_to_manta_tool

_ensure_manta_namespace(AdapterPaths.from_repo(ROOT))
from MAS.self_evolved.tool_manifest import CONSUME, MUTATE, NAVIGATION, PURE_READS, SEND, TOOL_MANIFEST, effect, tool_spec
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suites


def script_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/manta" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ToolManifestChecks(unittest.TestCase):
    def test_all_registered_tools_have_reviewed_immutable_specs(self):
        for suite in get_suites("v1.2.2").values():
            for function in suite.tools:
                with self.subTest(tool=function.name):
                    spec = tool_spec(function.name)
                    self.assertNotEqual(spec.effect, "unknown")
                    self.assertEqual(spec.worker_allowed, spec.effect == "read")
                    self.assertNotEqual(spec.resource_domain, "unknown")
                    self.assertEqual(spec.argument_sensitivity, "all")
                    for argument in function.parameters.model_json_schema().get("properties", {}):
                        self.assertTrue(spec.is_argument_sensitive(argument))
                    self.assertTrue(spec.is_argument_sensitive("future_unreviewed_argument"))
        with self.assertRaises(FrozenInstanceError):
            tool_spec("get_balance").effect = "mutate"
        with self.assertRaises(TypeError):
            TOOL_MANIFEST["new_tool"] = tool_spec("get_balance")

    def test_observable_read_and_nonverb_effects_are_not_pure(self):
        expected = {"get_unread_emails": "consume", "get_webpage": "navigate", "download_file": "navigate",
                    "share_file": "send", "invite_user_to_slack": "send", "reserve_hotel": "mutate",
                    "reserve_restaurant": "mutate", "reserve_car_rental": "mutate"}
        for name, kind in expected.items():
            with self.subTest(tool=name):
                self.assertEqual(effect(name), kind)
                self.assertTrue(tool_spec(name).side_effect)
                self.assertFalse(tool_spec(name).worker_allowed)
        self.assertFalse(tool_spec("get_balance").side_effect)

    def test_unknown_names_fail_closed_without_lexical_inference(self):
        for name in ("get_execute_payment", "read_only", "GET_BALANCE", "get_balance ", ""):
            spec = tool_spec(name)
            self.assertEqual(spec.effect, "unknown")
            self.assertEqual(spec.resource_domain, "unknown")
            self.assertTrue(spec.side_effect)
            self.assertFalse(spec.worker_allowed)
            self.assertTrue(spec.is_argument_sensitive("limit"))

    def test_effect_compatibility_sets_partition_reviewed_tools(self):
        sets = (PURE_READS, NAVIGATION, SEND, MUTATE, CONSUME)
        self.assertEqual(sum(map(len, sets)), len(set().union(*sets)))
        self.assertEqual(set().union(*sets), set(TOOL_MANIFEST))
        self.assertEqual(CONSUME, {"get_unread_emails"})

    def test_adapter_preserves_real_schema_and_binds_handler_without_running_it(self):
        runtime = SimpleNamespace(run_function=unittest.mock.Mock(return_value=("value", None)))
        for suite in get_suites("v1.2.2").values():
            for function in suite.tools:
                converted = _function_to_manta_tool(runtime, None, function)
                self.assertEqual(converted["parameters"], function.parameters.model_json_schema())
                self.assertEqual(converted["side_effect"], effect(function.name) != "read")
        runtime.run_function.assert_not_called()
        converted["handler"]({})
        runtime.run_function.assert_called_once_with(None, function.name, {})

    def test_adapter_unknown_tool_is_observable(self):
        function = next(iter(get_suites("v1.2.2")["banking"].tools))
        unknown = function.model_copy(update={"name": "read_execute_payment"})
        self.assertTrue(_function_to_manta_tool(FunctionsRuntime(), None, unknown)["side_effect"])


class GovernedProfileChecks(unittest.TestCase):
    def test_adapter_routes_profiles_without_enabling_governance_for_legacy(self):
        with patch.dict(os.environ, {"MANTA_PROVIDER": "deepseek", "DEEPSEEK_MODEL": "deepseek-flash"}), \
             patch("agentdojo_manta.adapter._make_llm_client", return_value=object()):
            for profile, mode in (("folded_adaptive", "legacy"), ("folded_governed", "capability")):
                pipeline = MantaAgentDojoPipeline(AdapterPaths.from_repo(ROOT), model="deepseek-flash", team_profile=profile)
                self.assertEqual(pipeline.governance_mode, mode)
                self.assertEqual(pipeline._engine.governance_mode, mode)
                self.assertEqual(pipeline.num_agents, 1)
                suite = SimpleNamespace(user_tasks={"u": SimpleNamespace(PROMPT="user", ID="u")},
                                        injection_tasks={"i": SimpleNamespace(PROMPT="attack", ID="i")})
                pipeline.bind_suite(suite)
                self.assertEqual(pipeline.task_id_lookup, {"user": "u"})

    def test_episode_cli_accepts_governed_mode(self):
        runner = script_module("run_agentdojo_manta")
        args = runner._build_parser().parse_args(["--team-profile", "folded_governed", "--audit-mode", "capability_gate"])
        self.assertEqual(args.team_profile, "folded_governed")
        self.assertEqual(args.audit_mode, "capability_gate")

    def test_formal_dry_run_records_distinct_profile_without_launching_jobs(self):
        runner = script_module("run_formal")
        frozen = dict(config={"model": "deepseek-flash"}, scenes=[], jobs=[], unique_user_tasks=0)
        manifests = {}
        with tempfile.TemporaryDirectory() as directory:
            for profile in ("folded_adaptive", "folded_governed"):
                output = Path(directory) / profile
                argv = ["run_formal", "--team-profile", profile, "--max-output-tokens", "16384", "--dry-run",
                        "--run-dir", str(output)]
                with patch.dict(os.environ, {"MANTA_PROVIDER": "deepseek", "DEEPSEEK_MODEL": "deepseek-flash"}, clear=True), \
                     patch.object(sys, "argv", argv), patch("dotenv.load_dotenv"), \
                     patch("agentdojo_manta.replication.load_replication_plan", return_value=copy.deepcopy(frozen)), \
                     patch.object(runner, "fingerprint", return_value="offline-source"), \
                     patch.object(runner.subprocess, "Popen", side_effect=AssertionError("No episode may launch")):
                    self.assertEqual(runner.main(), 0)
                manifests[profile] = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        legacy, governed = manifests["folded_adaptive"], manifests["folded_governed"]
        self.assertEqual(legacy["protocol"], "manta-agentdojo-folded-flash-v1")
        self.assertEqual(legacy["config"]["audit_mode"], "selective_pre_action")
        self.assertNotIn("governance_mode", legacy)
        self.assertEqual(governed["protocol"], "manta-agentdojo-folded-governed-flash-v1")
        self.assertEqual(governed["write_protocol"], "capability_guarded_native")
        self.assertEqual(governed["config"]["team_profile"], "folded_governed")
        self.assertEqual(governed["config"]["audit_mode"], "capability_gate")
        self.assertEqual(governed["governance_mode"], "capability")
        self.assertEqual(governed["physical_limits"]["compiler"], 1)


if __name__ == "__main__":
    unittest.main()
