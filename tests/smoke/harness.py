"""Micro-step smoke test harness."""

from __future__ import annotations

from typing import Callable


class StepRunner:
    """Numbered PASS/FAIL output for granular smoke phases."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self._section = ""

    def section(self, title: str) -> None:
        self._section = title
        print(f"\n== {title} ==")

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        label = f"{self._section} / {name}" if self._section else name
        if condition:
            self.passed += 1
            suffix = f" ({detail})" if detail else ""
            print(f"  [PASS] {label}{suffix}")
        else:
            self.failed += 1
            suffix = f" - {detail}" if detail else ""
            print(f"  [FAIL] {label}{suffix}")
            raise AssertionError(f"{label}{suffix}")

    def ok(self, name: str, condition: bool, detail: str = "") -> None:
        """Alias for skeptic smoke phases."""
        self.check(name, condition, detail)

    def run(self, name: str, fn: Callable[[], None]) -> None:
        try:
            fn()
            self.passed += 1
            print(f"  [PASS] {self._section} / {name}")
        except Exception as exc:
            self.failed += 1
            print(f"  [FAIL] {self._section} / {name} - {exc}")
            raise
