"""Collectors for configured official public sources."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser

from backend.app.collectors.base import CollectorResult
from backend.app.collectors.http import HttpCollector
from backend.app.services.publication_tracker import PublicationInput


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.parts.append(text)

    @property
    def text(self) -> str:
        return " ".join(self.parts)


@dataclass(frozen=True)
class OfficialSourceConfig:
    id: str
    name: str
    url: str
    transport: str
    parser: str


class OfficialHttpCollector(HttpCollector):
    """Generic collector for an enabled official HTTP source.

    It intentionally does not claim that every page is an edital. The next
    parser/classifier stage decides whether the collected page is relevant.
    """

    name = "official_http"

    def __init__(self, config: OfficialSourceConfig, *, timeout: float = 20.0):
        super().__init__(config.url, source=config.name, timeout=timeout)
        self.config = config

    def collect(self) -> CollectorResult:
        raw = self.fetch()
        parser = _TextParser()
        parser.feed(raw)
        text = parser.text
        item = PublicationInput(
            titulo=self.config.name,
            conteudo=text,
            fonte=self.config.name,
            url=self.config.url,
            data_publicacao=date.today(),
            tipo="pagina_oficial",
            identificador=f"{self.config.id}:{date.today().isoformat()}",
        )
        return CollectorResult(
            source=self.config.name,
            collected_at=date.today(),
            items=(item,),
        )
