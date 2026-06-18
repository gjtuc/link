"""
파이프라인 종료 후 그래프 시각화 공개 API
========================================

  open_graph_in_browser()     — 수동 호출·스크립트용
  maybe_visualize_after_pipeline() — CLI --db 후처리 훅
"""

from deconstructor.viz.export import maybe_visualize_after_pipeline, open_graph_in_browser

__all__ = ["maybe_visualize_after_pipeline", "open_graph_in_browser"]
