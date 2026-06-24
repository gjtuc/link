"""
STAGE 0-SPINE — μ-SPINE-01
계약: docs/design/BRANCH-SPINE-spec.md
철학: §1d R4, §1e R6, §1d-8 폴백
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from deconstructor.spine.contract import LinkRationale
from deconstructor.viz.neo4j_utils import GraphEdge, GraphNode

MAX_R4_LEN = 120
MAX_R6_LEN = 240

_CAUSAL_PATTERNS = re.compile(
    r"(유발|때문에|일으키|초래|causes|because|leads\s+to)",
    re.IGNORECASE,
)


def _truncate(text: str, max_len: int) -> str:
    text = " ".join(str(text).split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _as_node_map(nodes: Mapping[str, Any] | Sequence[Any]) -> dict[str, dict[str, Any]]:
    if isinstance(nodes, Mapping):
        out: dict[str, dict[str, Any]] = {}
        for key, value in nodes.items():
            if isinstance(value, GraphNode):
                out[str(key)] = {
                    "subject": value.subject,
                    "state_change": value.state_change,
                    "reasoning": value.reasoning,
                    "source_file": value.source_file,
                }
            else:
                out[str(key)] = dict(value)
        return out
    out = {}
    for item in nodes:
        if isinstance(item, GraphNode):
            out[item.id] = {
                "subject": item.subject,
                "state_change": item.state_change,
                "reasoning": item.reasoning,
                "source_file": item.source_file,
            }
        elif isinstance(item, dict) and item.get("id"):
            nid = str(item["id"])
            out[nid] = {k: v for k, v in item.items() if k != "id"}
        else:
            raise TypeError(f"unsupported node entry: {type(item)!r}")
    return out


def _normalize_edges(edges: Sequence[Any]) -> list[tuple[str, str, str]]:
    normalized: list[tuple[str, str, str]] = []
    for edge in edges:
        if isinstance(edge, GraphEdge):
            kind = (edge.edge_kind or "CAUSES").upper()
            normalized.append((edge.source_id, edge.target_id, kind))
        elif isinstance(edge, dict):
            kind = str(edge.get("edge_kind") or "CAUSES").upper()
            normalized.append(
                (str(edge["source_fact_id"]), str(edge["target_fact_id"]), kind)
            )
        else:
            raise TypeError(f"unsupported edge entry: {type(edge)!r}")
    return normalized


def _subject(node: dict[str, Any]) -> str:
    subject = str(node.get("subject") or "").strip()
    if not subject:
        raise ValueError("subject required for link rationale")
    return subject


def _infer_locale(nodes: dict[str, dict[str, Any]], default: str = "ko") -> str:
    subjects = " ".join(_subject(n) for n in nodes.values() if n.get("subject"))
    if not subjects:
        return default
    ascii_letters = sum(1 for ch in subjects if ch.isascii() and ch.isalpha())
    if ascii_letters >= len(subjects) * 0.6:
        return "en"
    return default


def _build_causes_r4(source: dict[str, Any], target: dict[str, Any]) -> str:
    a_subj = _subject(source)
    b_subj = _subject(target)
    state = str(source.get("state_change") or "").strip()
    if state:
        sentence = f"{a_subj}에서 {state}이 일어나 {b_subj}로 이어진다"
    else:
        sentence = f"{a_subj}와(과) 관련된 변화가 {b_subj}로 이어진다"
    return _truncate(sentence, MAX_R4_LEN)


def _build_bridge_r4(source: dict[str, Any], target: dict[str, Any]) -> str:
    a_subj = _subject(source)
    b_subj = _subject(target)
    sentence = f"「{a_subj}」와 「{b_subj}」가 문서·주제를 넘어 연결됩니다(인과 미검증)."
    if _CAUSAL_PATTERNS.search(sentence):
        sentence = f"「{a_subj}」와 「{b_subj}」가 같은 분석 안에서 연결됩니다(인과 미검증)."
    return _truncate(sentence, MAX_R4_LEN)


def _build_causes_r6(source: dict[str, Any], target: dict[str, Any]) -> str:
    reasoning = str(source.get("reasoning") or "").strip()
    if reasoning:
        return _truncate(reasoning, MAX_R6_LEN)
    state = str(source.get("state_change") or "").strip()
    if state:
        return _truncate(f"원인 측 변화: {state}", MAX_R6_LEN)
    return ""


def build_link_rationales(
    nodes: Mapping[str, Any] | Sequence[Any],
    edges: Sequence[Any],
    *,
    locale: str | None = None,
) -> list[LinkRationale]:
    """Build R4/R6 rationales for CAUSES and BRIDGE edges (mechanical fallback only)."""
    node_map = _as_node_map(nodes)
    loc = locale or _infer_locale(node_map)
    rationales: list[LinkRationale] = []

    for source_id, target_id, edge_kind in _normalize_edges(edges):
        if source_id not in node_map or target_id not in node_map:
            raise KeyError(f"missing node for edge {source_id!r} -> {target_id!r}")
        source = node_map[source_id]
        target = node_map[target_id]

        if edge_kind == "BRIDGE":
            link_sentence = _build_bridge_r4(source, target)
            link_mechanism = ""
        elif edge_kind == "CAUSES":
            link_sentence = _build_causes_r4(source, target)
            link_mechanism = _build_causes_r6(source, target)
        else:
            raise ValueError(f"unsupported edge_kind: {edge_kind!r}")

        rationales.append(
            LinkRationale(
                source_fact_id=source_id,
                target_fact_id=target_id,
                edge_kind=edge_kind,
                link_sentence=link_sentence,
                link_mechanism=link_mechanism,
                locale=loc,
            )
        )
    return rationales
