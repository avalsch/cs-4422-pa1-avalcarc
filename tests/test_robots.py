from pathlib import Path

import pytest
import requests

from crawl_config import Config
from robots import MAX_CRAWL_DELAY, RobotsCache

HOST = "http://kennesaw.edu/"
ROBOTS_URL = "http://kennesaw.edu/robots.txt"


def make_config(**overrides) -> Config:
    opts = {
        "seeds": [HOST],
        "budget": 10,
        "delay": 0.0,
        "output_dir": Path("out"),
    }
    opts.update(overrides)

    return Config(**opts)  # ty: ignore[invalid-argument-type]


class FakeResponse:
    def __init__(self, status_code, body=b"", headers=None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}

    def iter_content(self, chunk_size):
        for start in range(0, len(self._body), chunk_size):
            yield self._body[start : start + chunk_size]

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


class FakeSession:
    def __init__(self, responses=None, error=None):
        self.responses = responses or {}
        self.error = error
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))

        if self.error is not None:
            raise self.error

        return self.responses.get(url, FakeResponse(404))


def cache(session, config=None, wait=None, delays=None):
    return RobotsCache(
        config or make_config(),
        session,
        wait=wait,
        delays=delays,
    )


def test_parses_and_caches_rules():
    body = b"User-agent: *\nDisallow: /private\n"
    session = FakeSession({ROBOTS_URL: FakeResponse(200, body)})
    robots = cache(session)

    assert robots.can_fetch("http://kennesaw.edu/public") is True
    assert robots.can_fetch("http://kennesaw.edu/private/x") is False
    assert len(session.calls) == 1


def test_sends_user_agent():
    session = FakeSession({ROBOTS_URL: FakeResponse(200, b"")})
    robots = cache(session, make_config(user_agent="KSU TestBot/9"))

    robots.can_fetch(HOST)

    _url, kwargs = session.calls[0]
    assert kwargs["headers"]["User-Agent"] == "KSU TestBot/9"


def test_records_crawl_delay_for_host():
    body = b"User-agent: *\nCrawl-delay: 2.5\n"
    session = FakeSession({ROBOTS_URL: FakeResponse(200, body)})
    delays: dict[str, float] = {}

    cache(session, delays=delays).can_fetch(HOST)

    assert delays == {"kennesaw.edu": 2.5}


def test_clamps_extreme_crawl_delay():
    body = b"User-agent: *\nCrawl-delay: 100000000000000000000\n"
    session = FakeSession({ROBOTS_URL: FakeResponse(200, body)})
    delays: dict[str, float] = {}

    cache(session, delays=delays).can_fetch(HOST)

    assert delays == {"kennesaw.edu": MAX_CRAWL_DELAY}


def test_calls_wait_before_requesting_robots():
    session = FakeSession({ROBOTS_URL: FakeResponse(200, b"")})
    waits: list[str] = []

    cache(session, wait=waits.append).can_fetch(HOST)

    assert waits == [ROBOTS_URL]


@pytest.mark.parametrize("status", [403, 404, 410])
def test_unavailable_robots_allows_all(status):
    session = FakeSession({ROBOTS_URL: FakeResponse(status)})
    robots = cache(session)

    assert robots.can_fetch("http://kennesaw.edu/anything") is True


@pytest.mark.parametrize("status", [429, 500, 503])
def test_unreachable_robots_disallows_all(status):
    session = FakeSession({ROBOTS_URL: FakeResponse(status)})
    robots = cache(session)

    assert robots.can_fetch("http://kennesaw.edu/anything") is False


def test_connection_error_disallows_all():
    session = FakeSession(error=requests.exceptions.ConnectionError())
    robots = cache(session)

    assert robots.can_fetch(HOST) is False


def test_fetches_robots_once_per_origin():
    session = FakeSession({ROBOTS_URL: FakeResponse(200, b"")})
    robots = cache(session)

    robots.can_fetch("http://kennesaw.edu/a")
    robots.can_fetch("http://kennesaw.edu/b")
    robots.can_fetch("http://cs.kennesaw.edu/c")

    assert [url for url, _ in session.calls] == [
        ROBOTS_URL,
        "http://cs.kennesaw.edu/robots.txt",
    ]


def test_origin_distinguishes_scheme_and_port():
    session = FakeSession({})
    robots = cache(session)

    robots.can_fetch("http://kennesaw.edu/a")
    robots.can_fetch("https://kennesaw.edu/a")

    assert [url for url, _ in session.calls] == [
        ROBOTS_URL,
        "https://kennesaw.edu/robots.txt",
    ]
