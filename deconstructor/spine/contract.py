"""
STAGE 0-SPINE — μ-SPINE-01
계약: docs/design/BRANCH-SPINE-spec.md
철학: §1d R4, §1e R6, §1d-8 폴백
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

VALID_EDGE_KINDS = frozenset({"CAUSES", "BRIDGE"})


@dataclass(frozen=True)
class LinkRationale:
    source_fact_id: str
    target_fact_id: str
    edge_kind: str
    link_sentence: str
    link_mechanism: str
    locale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LinkRationale:
        edge_kind = str(data["edge_kind"]).upper()
        if edge_kind not in VALID_EDGE_KINDS:
            raise ValueError(f"invalid edge_kind: {edge_kind!r}")
        return cls(
            source_fact_id=str(data["source_fact_id"]),
            target_fact_id=str(data["target_fact_id"]),
            edge_kind=edge_kind,
            link_sentence=str(data.get("link_sentence") or ""),
            link_mechanism=str(data.get("link_mechanism") or ""),
            locale=str(data.get("locale") or "ko"),
        )


@dataclass(frozen=True)
class SpineRecord:
    """Spine list entry — populated by μ-SPINE-02 (index.py)."""

    spine_id: str
    index: int
    label: str
    bridge_count: int
    node_ids: tuple[str, ...]
    edge_ids: tuple[tuple[str, str], ...]
    main_path_node_ids: tuple[str, ...]
    is_branched: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "spine_id": self.spine_id,
            "index": self.index,
            "label": self.label,
            "bridge_count": self.bridge_count,
            "node_ids": list(self.node_ids),
            "edge_ids": [list(pair) for pair in self.edge_ids],
            "main_path_node_ids": list(self.main_path_node_ids),
            "is_branched": self.is_branched,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpineRecord:
        edge_ids = data.get("edge_ids") or []
        pairs = tuple((str(a), str(b)) for a, b in edge_ids)
        return cls(
            spine_id=str(data["spine_id"]),
            index=int(data["index"]),
            label=str(data["label"]),
            bridge_count=int(data["bridge_count"]),
            node_ids=tuple(str(x) for x in data["node_ids"]),
            edge_ids=pairs,
            main_path_node_ids=tuple(str(x) for x in data["main_path_node_ids"]),
            is_branched=bool(data["is_branched"]),
        )
