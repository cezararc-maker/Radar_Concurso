"""Compose DOE-MS edition discovery with official PDF extraction."""

from __future__ import annotations

from datetime import date
from typing import Callable

from backend.app.collectors.base import Collector, CollectorError, CollectorResult
from backend.app.collectors.doe_ms import DoeMsCollector
from backend.app.collectors.pdf import OfficialPdfCollector


PdfCollectorFactory = Callable[..., OfficialPdfCollector]


class DoeMsDocumentCollector(Collector):
    """Discover DOE-MS editions and collect the text of each official PDF."""

    name = "doe_ms_documents"

    def __init__(
        self,
        edition_collector: DoeMsCollector | None = None,
        *,
        pdf_collector_factory: PdfCollectorFactory = OfficialPdfCollector,
    ) -> None:
        self.edition_collector = edition_collector or DoeMsCollector()
        self.pdf_collector_factory = pdf_collector_factory

    def collect(self) -> CollectorResult:
        edition_result = self.edition_collector.collect()
        documents = []

        for edition in edition_result.items:
            if not edition.url or not edition.data_publicacao or not edition.identificador:
                raise CollectorError(
                    "Edição DOE-MS sem URL, data de publicação ou identificador."
                )

            pdf_collector = self.pdf_collector_factory(
                edition.url,
                source=edition.fonte or edition_result.source,
                publication_date=edition.data_publicacao,
                identifier=edition.identificador,
            )
            pdf_result = pdf_collector.collect()
            documents.extend(pdf_result.items)

        return CollectorResult(
            source=edition_result.source,
            collected_at=date.today(),
            items=tuple(documents),
        )
