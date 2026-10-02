"""Shared interface for exact and probabilistic membership structures."""

from __future__ import annotations

from typing import Protocol


class MembershipStore(Protocol):
    """Minimal interface used by the benchmark runner."""

    def add(self, value: str) -> None:
        """Insert one username into the structure.

        Input: username string. Output: none.
        """

    def contains(self, value: str) -> bool:
        """Report whether a username is stored.

        Input: username string. Output: True if value was added before
        (for the two probabilistic filters, "True" means possibly present
        rather than definitely present).
        """

