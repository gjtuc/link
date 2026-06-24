"""
Step 1 — Provenance 태깅 헬퍼 (Micro-step S1-3)
================================================

verify 노드가 atomic fact 를 completed_facts 로 이동할 때
source_type=extracted, check_status=active 를 강제한다.

Sprint 1 (G-ING-META): ``document_meta`` 가 있으면 source_file/page_range/chunk_id 도 부착.
"""

from __future__ import annotations

import logging

from deconstructor.models import AtomicFact
from deconstructor.provenance.source_meta import SourceDocumentMeta
from deconstructor.provenance.types import DEFAULT_CHECK_STATUS, DEFAULT_SOURCE_TYPE

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    line = f"[PROV-S1-3] {msg}"
    logger.info(line)
    print(line)


def tag_as_extracted(
    facts: list[AtomicFact],
    *,
    document_meta: dict | SourceDocumentMeta | None = None,
) -> list[AtomicFact]:
    """
    원문 추출 팩트에 provenance 꼬리표 부착.

    Micro-step:
      S1-3-a  입력 fact 수 로그
      S1-3-b  각 fact model_copy update
      S1-3-c  완료 로그
    """
    if not facts:
        _log("skip: no atomic facts to tag")
        return []

    meta = SourceDocumentMeta.from_state_dict(
        document_meta.to_state_dict() if isinstance(document_meta, SourceDocumentMeta) else document_meta
    )
    doc_fields = meta.to_fact_update()

    _log(f"tagging {len(facts)} atomic fact(s) as source_type={DEFAULT_SOURCE_TYPE!r}")
    tagged = []
    for fact in facts:
        update: dict = {
            "source_type": DEFAULT_SOURCE_TYPE,
            "check_status": DEFAULT_CHECK_STATUS,
        }
        if doc_fields.get("chunk_id"):
            update.update(doc_fields)
        tagged.append(fact.model_copy(update=update))
    _log(f"complete: {len(tagged)} fact(s) tagged extracted/active")
    return tagged
