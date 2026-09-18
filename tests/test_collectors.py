import unittest
from unittest.mock import patch

from backend.app.collectors.base import Collector, CollectorError
from backend.app.collectors.http import HttpCollector


class FakeCollector(Collector):
    name = "fake"

    def collect(self):
        raise NotImplementedError


class TestCollectors(unittest.TestCase):
    def test_collector_is_abstract(self):
        with self.assertRaises(TypeError):
            Collector()

    @patch("backend.app.collectors.http.urlopen")
    def test_http_collector_fetches_with_timeout(self, urlopen):
        class Headers:
            def get_content_charset(self):
                return "utf-8"

        class Response:
            headers = Headers()

            def read(self):
                return "<html>ok</html>".encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return False

        urlopen.return_value = Response()
        collector = HttpCollector("https://example.org", source="Fonte teste", timeout=7)

        self.assertEqual(collector.fetch(), "<html>ok</html>")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 7)

    @patch("backend.app.collectors.http.urlopen", side_effect=TimeoutError("tempo esgotado"))
    def test_http_collector_wraps_network_errors(self, _urlopen):
        collector = HttpCollector("https://example.org", source="Fonte teste")
        with self.assertRaises(CollectorError):
            collector.fetch()


if __name__ == "__main__":
    unittest.main()
