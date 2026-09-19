"""Run normalized collector output through publication tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from backend.app.collectors.base import Collector
from backend.app.services.publication_tracker import PublicationTracker, TrackingResult


@dataclass(frozen=True)
class CollectionPipelineResult:
    """Outcome of collecting, classifying and staging publications."""

    source: str
    collected_at: date
    tracked_items: tuple[TrackingResult, ...]


class CollectionPipeline:
    """Connect a collector to deduplication, classification and persistence."""

    def __init__(self, collector: Collector, tracker: PublicationTracker) -> None:
        self.collector = collector
        self.tracker = tracker

    def run(self) -> CollectionPipelineResult:
        collected = self.collector.collect()
        tracked = tuple(self.tracker.register(item) for item in collected.items)
        return CollectionPipelineResult(
            source=collected.source,
            collected_at=collected.collected_at,
            tracked_items=tracked,
        )
