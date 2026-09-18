"""Small HTTP collector foundation used by official-source adapters."""

from __future__ import annotations

from datetime import date
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.app.collectors.base import Collector, CollectorError, CollectorResult


class HttpCollector(Collector):
    """Fetch a public HTTP endpoint with conservative defaults.

    Source-specific parsing belongs in subclasses; this class only handles
    transport so network concerns remain separate from parsing/classification.
    """

    name = "http"

    def __init__(self, url: str, *, source: str, timeout: float = 20.0, user_agent: str = "RadarConcurso/0.1"):
        self.url = url
        self.source = source
        self.timeout = timeout
        self.user_agent = user_agent

    def fetch(self) -> str:
        request = Request(
            self.url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise CollectorError(f"Falha ao consultar {self.source}: {exc}") from exc

    def collect(self) -> CollectorResult:
        """Fetch the source; parsing is intentionally delegated to adapters."""
        self.fetch()
        return CollectorResult(source=self.source, collected_at=date.today(), items=())
