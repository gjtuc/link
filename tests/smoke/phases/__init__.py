"""Pipeline smoke phase registry."""

from tests.smoke.phases.p01_pydantic import phase_1_pydantic
from tests.smoke.phases.p02_stub import phase_2_stub_isolated
from tests.smoke.phases.p03_nodes import phase_3_nodes_isolated
from tests.smoke.phases.p04_routing import phase_4_routing
from tests.smoke.phases.p05_pipeline import phase_5_traced_pipeline
from tests.smoke.phases.p06_matrix import phase_6_matrix
from tests.smoke.phases.p07_package import phase_7_package_split
from tests.smoke.phases.p08_depth_cap import phase_8_depth_cap
from tests.smoke.phases.p09_partial import phase_9_partial_run_isolated
from tests.smoke.phases.p10_weaver import phase_10_weaver_dry
from tests.smoke.phases.p11_report import phase_11_report_sections
from tests.smoke.phases.p12_llm_deconstruct import phase_12_llm_deconstruct
from tests.smoke.phases.p13_truth_table import phase_13_truth_table
from tests.smoke.phases.p14_mechanism import phase_14_mechanism_llm

__all__ = [
    "phase_1_pydantic",
    "phase_2_stub_isolated",
    "phase_3_nodes_isolated",
    "phase_4_routing",
    "phase_5_traced_pipeline",
    "phase_6_matrix",
    "phase_7_package_split",
    "phase_8_depth_cap",
    "phase_9_partial_run_isolated",
    "phase_10_weaver_dry",
    "phase_11_report_sections",
    "phase_12_llm_deconstruct",
    "phase_13_truth_table",
    "phase_14_mechanism_llm",
]
