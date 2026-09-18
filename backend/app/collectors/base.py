"""Contracts shared by all Radar Concurso collectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from backend.app.services.publication_tracker import PublicationInput


class CollectorError(RuntimeError):
    """Raised when a source cannot be collected successfully."""


@dataclass(frozen=True)
class CollectorResult:
    """Normalized output of a collector run."""

    source: str
    collected_at: date
    items: tuple[PublicationInput, ...]


class Collector(ABC):
    """Base contract for every source-specific collector."""

    name: str

    @abstractmethod
    def collect(self) -> CollectorResult:
        """Collect and normalize publications from the source."""
        raise NotImplementedError
