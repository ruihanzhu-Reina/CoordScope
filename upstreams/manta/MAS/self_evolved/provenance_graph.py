"""Host-recorded evidence lineage, not automatic taint tracking or authority."""
from collections.abc import Mapping
from dataclasses import dataclass
import json
import re


def json_snapshot(value):
    """Freeze the returned host value as JSON; never parse JSON-looking strings."""
    def encode(item):
        if hasattr(item, "model_dump"):
            return item.model_dump(mode="json")
        # Legacy non-JSON tool objects remain opaque strings, never fields.
        return str(item)
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False, default=encode)


@dataclass(frozen=True)
class SourceRef:
    evidence_id: str
    path: str = ""

    def __post_init__(self):
        if not isinstance(self.evidence_id, str) or not self.evidence_id:
            raise ValueError("Source reference needs an evidence ID.")
        pointer_tokens(self.path)

    @classmethod
    def parse(cls, value):
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping) or set(value) - {"evidence_id", "path"}:
            raise ValueError("Source reference contains unsupported fields.")
        if "evidence_id" not in value:
            raise ValueError("Source reference needs an evidence ID.")
        return cls(value["evidence_id"], value.get("path", ""))

    def to_dict(self):
        return {"evidence_id": self.evidence_id, "path": self.path}


def pointer_tokens(path):
    """Decode RFC 6901, including escaped '/' and '~' keys."""
    if not isinstance(path, str) or (path and not path.startswith("/")):
        raise ValueError("Source path must be a JSON Pointer (or empty for the root).")
    if re.search(r"~(?![01])", path):
        raise ValueError("Invalid JSON Pointer escape.")
    return [] if not path else [p.replace("~1", "/").replace("~0", "~") for p in path[1:].split("/")]


def pointer_value(value, path):
    for token in pointer_tokens(path):
        if isinstance(value, dict):
            if token not in value:
                raise ValueError("Source field does not exist in the original evidence.")
            value = value[token]
        elif isinstance(value, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token):
                raise ValueError("Source array index must be a canonical non-negative integer.")
            index = int(token)
            if index >= len(value):
                raise ValueError("Source array index is outside the original evidence.")
            value = value[index]
        else:
            raise ValueError("Source path traverses a scalar; strings are not parsed as JSON.")
    return value


class ProvenanceGraph:
    """Append-only host audit records; readers receive detached JSON snapshots.

    Parent links and handoffs never certify arbitrary generated text or grant
    execution permissions. EvidenceStore validates access before recording them.
    """
    def __init__(self):
        self._nodes = {}
        self._events = []

    @property
    def nodes(self):
        return {key: json.loads(row) for key, row in self._nodes.items()}

    @property
    def events(self):
        return [json.loads(row) for row in self._events]

    def add_evidence(self, evidence_id, *, actor, tool, version, sha256, parent_ids=()):
        parents = tuple(parent_ids)
        if evidence_id in self._nodes or any(parent not in self._nodes for parent in parents):
            raise ValueError("Duplicate evidence or unknown provenance parent.")
        row = dict(evidence_id=evidence_id, actor=actor, tool=tool,
                   environment_version=version, sha256=sha256,
                   parent_ids=list(parents), origin="external_tool_result", trust="data_not_authority")
        self._nodes[evidence_id] = json_snapshot(row)

    def record_handoff(self, source_actor, target_actor, evidence_ids):
        refs = tuple(evidence_ids)
        if any(ref not in self._nodes for ref in refs):
            raise ValueError("Unknown evidence in provenance handoff.")
        event = dict(event_id=f"p{len(self._events) + 1:04d}", kind="handoff",
                     source_actor=source_actor, target_actor=target_actor,
                     evidence_ids=list(refs), trust="data_not_authority")
        self._events.append(json_snapshot(event))
        return json.loads(self._events[-1])

    def record_resolution(self, actor, proof):
        if proof["evidence_id"] not in self._nodes:
            raise ValueError("Unknown evidence in provenance resolution.")
        event = dict(event_id=f"p{len(self._events) + 1:04d}", kind="field_resolution",
                     actor=actor, proof=proof, trust="data_not_authority")
        self._events.append(json_snapshot(event))
        return json.loads(self._events[-1])

    def export(self):
        return {"nodes": self.nodes, "events": self.events,
                "scope": "explicit_host_recorded_lineage_not_automatic_taint_tracking"}
