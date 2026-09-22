"""Shared interface for exact and probabilistic membership structures."""

from __future__ import annotations

from typing import Protocol


class MembershipStore(Protocol):
    """Minimal interface used by the benchmark runner."""

    def add(self, value: str) -> None:
        """Insert one username into the structure."""

    def contains(self, value: str) -> bool:
        """Return whether the username may be stored in the structure."""

