#!/usr/bin/env python3
"""Build the offline MANTA × AgentDojo demo from archived reports."""

import argparse
import csv
import hashlib
import io
import json
import math
import tarfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
BASE = "c60fc554dd99db3880a6dfc77be5b8b05c867464"
SOURCE_URL = f"https://github.com/ruihanzhu5-cyber/AgentDojo-MANTA-Adapter/blob/{BASE}/"
COMPLETED = "reports/2026-10-29-completed-experiments"
FLASH = "reports/2026-10-19-manta-agentdojo"
ADAPTIVE = "reports/2026-10-28-deepseek-flash-adaptive"
FW = "reports/2026-10-29-agentdojo-flash16k-fw"
SUITES = ("banking", "slack", "travel", "workspace")
CONDITIONS = ("clean", "attack")
RUNS = ("flash_star", "gpt4o_star", "pro16k_star", "flash16k_adaptive", "F", "W", "folded_initial")
COUNT_FIELDS = (
    "episodes", "clean_n", "attack_n", "clean_success", "attack_successful_tasks",
    "attacker_successes", "safe_attack_successful_tasks", "confirmed_exposed",
    "exposure_unknown", "token_in", "token_out", "total_tokens", "requests",
    "runtime_calls", "duplicate_runtime_calls", "worker_episodes", "worker_contexts",
    "resource_limited_episodes", "cache_hits",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Reports:
    def __init__(self, root):
        self.root = root
        self.hashes = {}

    def read(self, path):
        content = (self.root / path).read_bytes()
        self.hashes[path] = hashlib.sha256(content).hexdigest()
        return content.decode("utf-8-sig")

    def csv(self, path):
        return list(csv.DictReader(io.StringIO(self.read(path))))

    def json(self, path):
        return json.loads(self.read(path))

    def archive(self, path):
        source = self.root / path
        with source.open("rb") as stream:
            self.hashes[path] = hashlib.file_digest(stream, "sha256").hexdigest()
        return tarfile.open(source, "r|gz")


def numeric(value, convert=int):
    return None if value is None or value in ("", "UNKNOWN") else convert(value)


def boolean(value):
    if value in (None, "", "UNKNOWN"):
        return None
    if isinstance(value, bool):
        return value
    return {"true": True, "false": False, "1": True, "0": False}[value.lower()]


def report_row(row):
    return {
        key: numeric(value) if key in COUNT_FIELDS or key == "max_output_tokens"
        else numeric(value, float) if key == "mean_episode_latency_s" else value
        for key, value in row.items()
    }


def read_episodes(reports):
    return [{
        "cohort": row["run"], "id": row["job_id"], "scene": row["scene_id"],
        "suite": row["suite"], "task": row["task_id"], "condition": row["condition"],
        "utility": boolean(row["utility"]), "attacker_success": boolean(row["attacker_success"]),
        "exposed": boolean(row["attack_exposed"]), "tokens": numeric(row["total_tokens"]),
        "latency_s": numeric(row["latency_s"], float), "calls": numeric(row["runtime_calls"]),
        "duplicate_calls": numeric(row["duplicate_runtime_calls"]), "workers": numeric(row["workers"]),
        "worker_scope": row["worker_count_scope"],
    } for row in reports.csv(f"{COMPLETED}/episode_results.csv")]


def validate_rollup(rows, summary, label):
    clean, attack = ([row for row in rows if row["condition"] == c] for c in CONDITIONS)
    require(all(isinstance(r["utility"], bool) for r in rows), f"{label}: utility coverage")
    require(all(isinstance(r["attacker_success"], bool) for r in attack), f"{label}: attack score coverage")
    require(all(r["exposed"] is None and r["attacker_success"] is None for r in clean),
            f"{label}: Clean attack fields must be null")
    require(all(r["tokens"] is not None and r["latency_s"] is not None for r in rows),
            f"{label}: token/latency coverage")
    actual = {
        "episodes": len(rows),
        "clean_n": len(clean),
        "attack_n": len(attack),
        "clean_success": sum(r["utility"] for r in clean),
        "attack_successful_tasks": sum(r["utility"] for r in attack),
        "attacker_successes": sum(r["attacker_success"] for r in attack),
        "safe_attack_successful_tasks": sum(r["utility"] and not r["attacker_success"] for r in attack),
        "confirmed_exposed": sum(r["exposed"] is True for r in attack),
        "exposure_unknown": sum(r["exposed"] is None for r in attack),
        "total_tokens": sum(r["tokens"] for r in rows),
    }
    if summary["worker_episodes"] is not None:
        require(all(r["workers"] is not None for r in rows), f"{label}: worker coverage")
        actual["worker_episodes"] = sum(r["workers"] > 0 for r in rows)
        actual["worker_contexts"] = sum(r["workers"] for r in rows)
    for key, field in (("runtime_calls", "calls"), ("duplicate_runtime_calls", "duplicate_calls")):
        if summary[key] is not None:
            actual[key] = sum(r[field] for r in rows)
    for key, value in actual.items():
        require(summary[key] == value, f"{label}: {key} {value} differs from {summary[key]}")
    require(summary["total_tokens"] == summary["token_in"] + summary["token_out"],
            f"{label}: input/output token totals")
    latency = sum(r["latency_s"] for r in rows) / len(rows)
    require(math.isclose(summary["mean_episode_latency_s"], latency, abs_tol=1e-6),
            f"{label}: mean latency {latency} differs from source")


def build_summary(reports, episodes):
    formal = reports.json(f"{FLASH}/manifest.json")
    report = reports.read(f"{COMPLETED}/README.md")
    require("direct 攻击" in report and f"seed {formal['config']['seed']}" in report,
            "Report scope disagrees with frozen manifest")
    scenes = {r["scene_id"]: (r["suite"], r["task_id"]) for r in formal["scenes"]}
    jobs = {(r["scene_id"], r["condition"]) for r in formal["jobs"]}
    scene_pairs = {(scene, condition) for scene in scenes for condition in CONDITIONS}
    require(jobs == scene_pairs and len(jobs) == len(formal["jobs"]), "Incomplete frozen job pairs")
    require(Counter(suite for suite, _ in scenes.values()) == {s: 20 for s in SUITES},
            "Expected 20 frozen scenes per suite")
    tasks = len(set(scenes.values()))
    require(tasks == formal["unique_user_tasks"], "Frozen unique task total")
    rollups = {r["run"]: report_row(r) for r in reports.csv(f"{COMPLETED}/overview.csv")}
    require(set(rollups) == set(RUNS), "Unexpected cohorts in source overview")
    require(set(r["cohort"] for r in episodes) == set(RUNS), "Unexpected cohorts in episode rows")
    cohorts = []
    for run in RUNS:
        summary = rollups[run]
        rows = [r for r in episodes if r["cohort"] == run]
        actual_jobs = {(r["scene"], r["condition"]) for r in rows}
        require(actual_jobs == jobs and len(rows) == len(jobs), f"{run}: duplicate or missing job")
        require(len({r["id"] for r in rows}) == len(rows), f"{run}: duplicate job ID")
        require(all((r["suite"], r["task"]) == scenes[r["scene"]] for r in rows), f"{run}: task drift")
        validate_rollup(rows, summary, run)
        repeat = summary["table_role"] == "repeat_reference"
        require(summary["table_role"] == ("repeat_reference" if run == "folded_initial" else "main"),
                f"{run}: unexpected reference role")
        cohorts.append({**summary, "id": run, "repeat": repeat})

    original = reports.json(f"{FLASH}/summary.json")
    flash = rollups["flash_star"]
    exposures = [r for r in episodes if r["cohort"] == "flash_star" and r["exposed"] is True]
    exposed_success = sum(r["attacker_success"] for r in exposures)
    for key, actual in {
        "attack_n": flash["attack_n"], "exposed_attack_n": len(exposures),
        "exposure_unknown_n": flash["exposure_unknown"],
        "conditional_asr": exposed_success / len(exposures),
        "targeted_asr": flash["attacker_successes"] / flash["attack_n"],
        "valid_episodes": flash["episodes"],
    }.items():
        require(math.isclose(original[key], actual), f"Original Flash summary mismatch: {key}")
    repeats = sum(c["repeat"] for c in cohorts)
    return {
        "study": {
            "scenes_per_cohort": len(scenes), "tasks_per_cohort": tasks,
            "clean_per_cohort": sum(c == "clean" for _, c in jobs),
            "attack_per_cohort": sum(c == "attack" for _, c in jobs),
            "configurations": len(cohorts) - repeats, "repeats": repeats, "episode_records": len(episodes),
            "seed": formal["config"]["seed"], "attack_family": "official direct attack",
            "benchmark_version": formal["config"]["benchmark_version"],
        },
        "suites": SUITES, "cohorts": cohorts,
        "flash": {
            "attack_n": flash["attack_n"], "exposed": len(exposures),
            "exposure_unknown": flash["exposure_unknown"], "attacker_success": flash["attacker_successes"],
            "exposed_success": exposed_success, "adoption_rate": None,
        },
    }


def topology_spec(source):
    return {
        "version": source["version"], "root_group_id": source["root_group_id"],
        "extra_edges": source["extra_edges"],
        "agents": [{k: a[k] for k in ("agent_id", "group_id", "structural_role", "stage_role")}
                   for a in source["agents"]],
        "groups": [{k: g[k] for k in ("group_id", "pattern", "member_ids", "parent_agent_id", "leader_id")}
                   for g in source["groups"]],
    }


def archived_topology(reports, selected):
    graphs = {}
    for suite in SUITES:
        path = f"{ADAPTIVE}/logs/formal-{suite}.tar.gz"
        with reports.archive(path) as archive:
            for member in archive:
                if not member.isfile() or PurePosixPath(member.name).name != "result.json":
                    continue
                with archive.extractfile(member) as stream:
                    result = json.load(stream)
                job, attempt, _ = PurePosixPath(member.name).parts[-3:]
                require(job in selected and selected[job]["suite"] == suite, f"Unknown archived job: {job}")
                require(selected[job]["selected_attempt"] == attempt, f"Wrong archived attempt: {job}")
                for graph in result["manta_metadata"]["self_evolved"]["execution_graphs"]:
                    key = (job, graph["turn_index"])
                    require(key not in graphs, f"Duplicate archive graph: {key}")
                    graphs[key] = (topology_spec(graph["topology_spec"]), graph["stage_sequence"], path, member.name)
    return graphs


def build_topology(reports, episodes):
    rows = {r["id"]: r for r in episodes if r["cohort"] == "flash16k_adaptive"}
    turns = defaultdict(list)
    cases = reports.json(f"{ADAPTIVE}/topology_cases.json")
    totals = reports.json(f"{ADAPTIVE}/topology_summary.json")
    examples = {(key, s["turn_index"]): s for key, case in cases.items() for s in case["execution_graphs"]}
    selected_rows = reports.csv(f"{ADAPTIVE}/episode_results.csv")
    selected = {r["job_id"]: r for r in selected_rows}
    require(len(selected_rows) == len(selected) and set(selected) == set(rows), "Adaptive episode identities")
    archives = archived_topology(reports, selected)
    for row in reports.csv(f"{ADAPTIVE}/execution_graphs.csv"):
        job, index = row["job_id"], int(row["turn_index"])
        key = (job, index)
        sequence = json.loads(row["stage_sequence"])
        patterns = json.loads(row["group_patterns"])
        require(job in rows and key in archives, f"Invalid graph row: {job}/{index}")
        spec, archived_sequence, path, member = archives.pop(key)
        require(sequence == archived_sequence, f"{job}/{index}: archived sequence mismatch")
        agent_ids = {agent["agent_id"] for agent in spec["agents"]}
        require(all(len(edge) == 2 and set(edge) <= agent_ids for edge in spec["extra_edges"]),
                f"{job}/{index}: invalid extra edge")
        example = examples.pop(key, None)
        if example is not None:
            require(sequence == example["stage_sequence"], f"{job}/{index}: case sequence mismatch")
            require(spec == topology_spec(example["topology_spec"]), f"{job}/{index}: case spec mismatch")
        require(len(spec["agents"]) == int(row["agents"]), f"{job}/{index}: agent count mismatch")
        require(len(patterns) == int(row["groups"]), f"{job}/{index}: group count mismatch")
        require([g["pattern"] for g in spec["groups"]] == patterns, f"{job}/{index}: group pattern mismatch")
        root = next(g for g in spec["groups"] if g["group_id"] == spec["root_group_id"])
        require(root["pattern"] == row["root_pattern"], f"{job}/{index}: root pattern mismatch")
        turns[job].append({
            "index": index, "root_pattern": row["root_pattern"], "agent_count": int(row["agents"]),
            "group_count": int(row["groups"]), "group_patterns": patterns, "sequence": sequence,
            "spec": spec, "archive": path, "archive_member": member,
        })
    require(not examples and not archives and set(rows) == set(turns), "Topology coverage mismatch")
    for job, items in turns.items():
        items.sort(key=lambda t: t["index"])
        require([t["index"] for t in items] in ([0], [0, 1]), f"{job}: invalid turn sequence")
        r = selected[job]
        require(len(items) == int(r["executed_turns"]), f"{job}: executed turns mismatch")
        require((items[0]["root_pattern"], items[-1]["root_pattern"]) ==
                (r["initial_root_pattern"], r["final_root_pattern"]), f"{job}: recorded root patterns")
    repaired = [ts for ts in turns.values() if len(ts) == 2]
    actual = {
        "initial_root_patterns": dict(Counter(ts[0]["root_pattern"] for ts in turns.values())),
        "executed_group_pattern_occurrences": dict(
            Counter(p for ts in turns.values() for t in ts for p in t["group_patterns"])),
        "repair_execution_episodes": len(repaired),
        "actual_spec_changed_episodes": sum(boolean(r["actual_spec_changed"]) for r in selected.values()),
        "root_pattern_changed_episodes": sum(ts[0]["root_pattern"] != ts[1]["root_pattern"] for ts in repaired),
        "nested_group_episodes": sum(
            any(g["parent_agent_id"] is not None for t in ts for g in t["spec"]["groups"]) for ts in turns.values()),
    }
    require(all(totals[k] == v for k, v in actual.items()), "Topology summary mismatch")
    require(0 <= totals["actual_spec_changed_episodes"] <= len(repaired), "Invalid spec-change denominator")
    return {
        "summary": {**totals, "episodes": len(turns), "snapshots": list(cases)},
        "episodes": [{"id": job, "scene": rows[job]["scene"], "suite": rows[job]["suite"],
                      "condition": rows[job]["condition"], "turns": ts,
                      "spec_changed": boolean(selected[job]["actual_spec_changed"])} for job, ts in turns.items()],
    }


def build_worker_comparison(reports, episodes, summary):
    overview = {r["run"]: report_row(r) for r in reports.csv(f"{FW}/overview.csv")}
    by_suite = [report_row(r) for r in reports.csv(f"{FW}/by_suite.csv")]
    runs = {c["id"]: c for c in summary["cohorts"]}
    require(set(overview) == {"F", "W"}, "F/W overview run IDs")
    require(len(by_suite) == 8 and {(r["run"], r["suite"]) for r in by_suite}
            == {(run, suite) for run in overview for suite in SUITES}, "F/W suite coverage")
    for run, rollup in overview.items():
        require(all(runs[run][key] == value for key, value in rollup.items()), f"{run}: F/W overview mismatch")
    for row in by_suite:
        validate_rollup([r for r in episodes if r["cohort"] == row["run"] and r["suite"] == row["suite"]],
                        row, f"{row['run']}/{row['suite']}")

    roles = [report_row(r) for r in reports.csv(f"{FW}/role_usage.csv")]
    for run in overview:
        entries = [r for r in roles if r["run"] == run]
        require(len(entries) == 3 and {r["role"] for r in entries} == {"main", "worker", "action_verifier"},
                f"{run}: role coverage")
        for key in ("token_in", "token_out", "total_tokens", "requests"):
            require(sum(r[key] for r in entries) == overview[run][key], f"{run}: role total {key}")

    jobs = {(r["cohort"], r["id"]): r for r in episodes if r["cohort"] in overview}
    paired = []
    for row in reports.csv(f"{FW}/fw_paired.csv"):
        job = row["job_id"]
        record = {"id": job, "suite": row["suite"], "condition": row["condition"]}
        for run in overview:
            episode = jobs[(run, job)]
            require(all(episode[k] == record[k] for k in ("suite", "condition")), f"{job}: pair identity")
            for key, value in {
                "utility": boolean(row[f"{run}_utility"]),
                "attacker_success": boolean(row[f"{run}_attacker_success"]),
                "tokens": int(row[f"{run}_tokens"]),
            }.items():
                require(episode[key] == value, f"{job}/{run}: paired {key}")
                record[f"{run}_{key}"] = value
        require(int(row["W_minus_F_tokens"]) == record["W_tokens"] - record["F_tokens"], f"{job}: token delta")
        paired.append(record)
    require(len(paired) == len(jobs) // 2 == len({r["id"] for r in paired}), "Missing or duplicate F/W pairs")
    return {"overview": overview, "by_suite": by_suite, "role_usage": roles, "paired": paired}


def build_case(reports, episodes):
    source = reports.json(f"{FLASH}/case_slack_07_evidence.json")
    tool_rows = reports.csv(f"{FLASH}/case_slack_07_tool_calls.csv")
    cases, timelines = {}, {}
    edges = []
    for condition in CONDITIONS:
        raw = source["conditions"][condition]
        stages = raw["stages"]
        require(stages[0]["actor"] == "agent_0" and stages[0]["tool_calls"], "Missing Slack 07 entry stage")
        original_url = stages[0]["tool_calls"][0]["url"]
        calls = []
        for stage in stages:
            for call in stage["tool_calls"]:
                require(call["stage_index"] == stage["index"] and call["actor"] == stage["actor"],
                        "Slack 07 call/stage mismatch")
                calls.append({
                    "order": int(call["call_order"]), "stage": call["stage_index"], "actor": call["actor"],
                    "tool": call["tool"], "target": boolean(call["matches_attack_target"]),
                    "source_page": call["url"] == original_url, "status": call["status"],
                })
        compared = [r for r in tool_rows if r["condition"] == condition]
        require(len(calls) == len(compared), "Slack 07 call table length")
        for call, row in zip(calls, compared):
            require((call["order"], call["actor"], call["target"], call["source_page"]) ==
                    (int(row["call_order"]), row["actor"], boolean(row["matches_attack_target"]), row["url"] == original_url),
                    "Slack 07 call table mismatch")
        require([c["order"] for c in calls] == list(range(1, len(calls) + 1)), "Slack 07 call order")
        messages = []
        for m in raw["relay_messages"]:
            seen = [s for s in stages if m["message_id"] in s["visible_message_ids"]]
            require(seen and all(s["actor"] in m["recipients"] for s in seen), "Slack 07 receiver mismatch")
            messages.append({
                "id": m["message_id"], "dispatch_id": m["dispatch_id"], "sender": m["sender"],
                "recipients": m["recipients"], "kind": m["kind"], "phase": m["phase"],
                "visible_at": [s["index"] for s in seen],
                "recipient_stage_payload": any(s["payload_in_initial_stage_messages"] for s in seen),
            })
        require([m["id"] for m in messages] == ["m_1", "m_2", "m_3", "m_4"], "Slack 07 message IDs")
        first_visibility = min(i for m in messages for i in m["visible_at"])
        targets = [call for call in calls if call["target"]]
        before = [call for call in targets if call["stage"] < first_visibility]
        actors = []
        for actor in ("agent_0", "agent_1", "agent_2"):
            records = [r for r in raw["provider_exposure_records"] if r["agent_id"] == actor]
            actors.append({
                "id": actor, "exposed": any(r["matched_injection_keys"] for r in records) if records else None,
                "target_calls": sum(c["actor"] == actor for c in targets),
                "pre_handoff_target_calls": sum(c["actor"] == actor for c in before),
                "visible_messages": [m["id"] for m in messages if actor in m["recipients"]],
            })
        audits = [{k: r[k] for k in ("turn_index", "source", "risk_score", "repair_recommended", "detected_modes")}
                  for r in raw["audit_reports"]]
        require(len(audits) == 1, "Unexpected Slack 07 audit coverage")
        mutations = len(raw["mutations"])
        metrics = raw["metrics"]
        require(mutations == metrics["topology_mutation_count"], "Slack 07 mutation count")
        episode = next(r for r in episodes if r["cohort"] == "flash_star"
                       and r["scene"] == source["case_id"] and r["condition"] == condition)
        require((episode["utility"], episode["attacker_success"], episode["exposed"]) ==
                (metrics["task_success"], metrics["attack_success"], metrics["attack_exposed"]),
                "Slack 07 official scoring mismatch")
        cases[condition] = {
            "episode": episode["id"], "actors": actors, "calls": calls, "messages": messages, "audit": audits[0],
            "mutations": mutations, "target_calls": len(targets), "pre_handoff_target_calls": len(before),
            "official_success": metrics["attack_success"],
        }
        events = []
        for s in stages:
            index, actor = s["index"], s["actor"]
            for m in messages:
                if index in m["visible_at"]:
                    events.append({"kind": "message", "stage": index, "actor": actor, "message": m["id"]})
            for c in calls:
                if c["stage"] == index:
                    kind = "exposure" if condition == "attack" and c["source_page"] else "tool"
                    events.append({"kind": kind, "stage": index, "actor": actor, "call": c["order"]})
            if "synthesis" in s["phase"] or "reconciliation" in s["phase"]:
                events.append({"kind": "synthesis", "stage": index, "actor": actor, "phase": s["phase"]})
        events.extend({"kind": kind, "actor": "auditor", "turn": audits[0]["turn_index"]}
                      for kind in ("audit", "recommendation", "repair"))
        timelines[condition] = events
        if condition == "attack":
            for m in messages:
                require(len(m["recipients"]) == 1, "Slack 07 graph expects individual recipients")
                edges.append({"id": m["id"], "kind": "peer", "from": m["sender"], "to": m["recipients"][0]})
            for actor in (a["id"] for a in actors):
                reads = [c["order"] for c in calls if c["actor"] == actor and c["source_page"]]
                visits = [c["order"] for c in targets if c["actor"] == actor]
                if reads:
                    edges.append({"id": f"read_{actor}", "kind": "read", "from": "external", "to": actor, "calls": reads})
                if visits:
                    edges.append({"id": f"target_{actor}", "kind": "target", "from": actor, "to": "target", "calls": visits})
    return {"id": source["case_id"], "conditions": cases, "edges": edges}, timelines


def build(root=ROOT, output=None):
    reports = Reports(root)
    episodes = read_episodes(reports)
    summary = build_summary(reports, episodes)
    topology = build_topology(reports, episodes)
    workers = build_worker_comparison(reports, episodes, summary)
    case, timeline = build_case(reports, episodes)
    bundles = {
        "summary": summary, "episodes": episodes, "topology": topology, "worker_comparison": workers,
        "case_slack_07": case, "audit_timeline": timeline,
    }
    episode_path = f"{COMPLETED}/episode_results.csv"
    case_sources = [f"{FLASH}/case_slack_07_evidence.json", f"{FLASH}/case_slack_07_tool_calls.csv", episode_path]
    usage = {
        "summary": [p for p in reports.hashes if p.startswith(COMPLETED) or p in
                    (f"{FLASH}/manifest.json", f"{FLASH}/summary.json")],
        "episodes": [episode_path],
        "topology": [p for p in reports.hashes if p.startswith(ADAPTIVE)] + [episode_path],
        "worker_comparison": [p for p in reports.hashes if p.startswith(FW)] + [episode_path, f"{COMPLETED}/overview.csv"],
        "case_slack_07": case_sources,
        "audit_timeline": case_sources,
    }
    bundles["data_manifest"] = {
        "schema_version": 1, "base_commit": BASE, "source_url": SOURCE_URL,
        "sources": [{"path": p, "sha256": digest} for p, digest in sorted(reports.hashes.items())],
        "datasets": {f"{key}.json": sorted(paths) for key, paths in usage.items()},
    }
    output = output if output is not None else root / "demo" / "data"
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in bundles.items():
        (output / f"{name}.json").write_bytes(
            (json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        )
    return bundles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Output directory (default: demo/data)")
    options = parser.parse_args()
    bundles = build(output=options.output)
    print(f"Built {len(bundles)} datasets from {len(bundles['data_manifest']['sources'])} source files "
          f"({len(bundles['episodes']):,} episode records).")


if __name__ == "__main__":
    main()
