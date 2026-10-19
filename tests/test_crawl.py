import io
import json
import time
from pathlib import Path

import pytest
import requests

import crawl
from crawl_config import Config
from fetch import ERR_HTTP, ERR_TIMEOUT, FetchError, FetchSuccess
from schema import Stats

SEED = "http://kennesaw.edu/"
PAGE_A = "http://kennesaw.edu/a"
PAGE_B = "http://kennesaw.edu/b"


def make_config(**overrides) -> Config:
    opts = {
        "seeds": [SEED],
        "budget": 10,
        "delay": 0.0,
        "output_dir": Path("out"),
    }
    opts.update(overrides)

    return Config(**opts)  # ty: ignore[invalid-argument-type]


def make_stats() -> Stats:
    return {
        "pages_fetched": 0,
        "urls_seen": 0,
        "wall_clock_seconds": 0.0,
        "robots_skips": 0,
        "random_seed": None,
    }


class FakeFetcher:
    def __init__(self, pages, errors=None, finals=None):
        self.pages = pages
        self.errors = errors or {}
        self.finals = finals or {}
        self.calls = []

    def __call__(self, url, _config, _session=None, wait=None):
        if wait is not None:
            wait(url)

        self.calls.append(url)

        if url in self.errors:
            return self.errors[url]

        if url in self.pages:
            final = self.finals.get(url, url)

            if wait is not None and final != url:
                wait(final)

            return FetchSuccess(200, self.pages[url], final)

        return FetchError(ERR_HTTP, 404, url)


def run(monkeypatch, fetcher, tmp_path, config=None, stats=None):
    config = config or make_config()
    stats = stats or make_stats()
    pages_f = io.StringIO()
    log_f = io.StringIO()

    monkeypatch.setattr(crawl, "fetch", fetcher)
    crawl.crawl(
        config,
        requests.Session(),
        pages_f,
        log_f,
        stats,
        tmp_path / "stats.json",
        time.time(),
    )

    return pages_f, log_f, stats


def records(pages_f):
    return [json.loads(line) for line in pages_f.getvalue().splitlines()]


def events(log_f):
    return [json.loads(line) for line in log_f.getvalue().splitlines()]


def test_stores_seed_page(monkeypatch, tmp_path):
    fetcher = FakeFetcher({SEED: "<title>Home</title><p>hi</p>"})

    pages_f, _log_f, stats = run(monkeypatch, fetcher, tmp_path)

    assert [r["url_canonical"] for r in records(pages_f)] == [SEED]
    assert stats["pages_fetched"] == 1


def test_duplicate_seeds_enqueued_once(monkeypatch, tmp_path):
    fetcher = FakeFetcher({SEED: "<p>hi</p>"})

    _pages_f, log_f, _stats = run(
        monkeypatch, fetcher, tmp_path, config=make_config(seeds=[SEED, SEED])
    )

    assert fetcher.calls == [SEED]
    assert [e["url"] for e in events(log_f) if e["event"] == "enqueue"] == [SEED]


def test_follows_discovered_links(monkeypatch, tmp_path):
    fetcher = FakeFetcher({SEED: "<a href='/a'>A</a>", PAGE_A: "<p>page a</p>"})

    pages_f, log_f, _stats = run(monkeypatch, fetcher, tmp_path)

    assert [r["url_canonical"] for r in records(pages_f)] == [SEED, PAGE_A]
    assert [e["url"] for e in events(log_f) if e["event"] == "enqueue"] == [SEED, PAGE_A]


def test_stops_at_budget(monkeypatch, tmp_path):
    fetcher = FakeFetcher({SEED: "<a href='/a'>A</a>", PAGE_A: "<a href='/b'>B</a>"})

    pages_f, _log_f, _stats = run(
        monkeypatch, fetcher, tmp_path, config=make_config(budget=1)
    )

    assert len(records(pages_f)) == 1
    assert fetcher.calls == [SEED]


def test_dedupes_links_before_fetching(monkeypatch, tmp_path):
    html = "<a href='/a'>1</a><a href='/a/'>2</a><a href='/a#f'>3</a>"
    fetcher = FakeFetcher({SEED: html, PAGE_A: "<p>a</p>"})

    _pages_f, _log_f, stats = run(monkeypatch, fetcher, tmp_path)

    assert fetcher.calls == [SEED, PAGE_A]
    assert stats["urls_seen"] == 2


def test_redirect_target_is_not_enqueued_again(monkeypatch, tmp_path):
    fetcher = FakeFetcher({SEED: f"<a href='{PAGE_B}'>B</a>"}, finals={SEED: PAGE_B})

    pages_f, _log_f, stats = run(monkeypatch, fetcher, tmp_path)

    assert fetcher.calls == [SEED]
    assert [r["url_canonical"] for r in records(pages_f)] == [PAGE_B]
    assert stats["urls_seen"] == 2


def test_redirect_aliases_stored_once(monkeypatch, tmp_path):
    target = "http://kennesaw.edu/c"
    a, b = "http://kennesaw.edu/a", "http://kennesaw.edu/b"
    fetcher = FakeFetcher({a: "<p>a</p>", b: "<p>b</p>"}, finals={a: target, b: target})

    pages_f, log_f, stats = run(
        monkeypatch, fetcher, tmp_path, config=make_config(seeds=[a, b])
    )

    assert [r["url_canonical"] for r in records(pages_f)] == [target]
    assert stats["pages_fetched"] == 1
    assert [e["failure_reason"] for e in events(log_f) if e["event"] == "skip"] == [
        "duplicate_final_url"
    ]


def test_logs_enqueue_fetch_and_error(monkeypatch, tmp_path):
    fetcher = FakeFetcher({}, errors={SEED: FetchError(ERR_TIMEOUT, url=SEED)})

    _pages_f, log_f, stats = run(monkeypatch, fetcher, tmp_path)

    entries = events(log_f)
    assert [e["event"] for e in entries] == ["enqueue", "fetch", "error"]
    assert entries[-1]["failure_reason"] == ERR_TIMEOUT
    assert stats["pages_fetched"] == 0


def test_errors_do_not_consume_budget(monkeypatch, tmp_path):
    second = "http://kennesaw.edu/second"
    fetcher = FakeFetcher(
        {second: "<p>ok</p>"}, errors={SEED: FetchError(ERR_TIMEOUT, url=SEED)}
    )

    pages_f, _log_f, stats = run(
        monkeypatch,
        fetcher,
        tmp_path,
        config=make_config(seeds=[SEED, second], budget=1),
    )

    assert fetcher.calls == [SEED, second]
    assert stats["pages_fetched"] == 1
    assert [r["url_canonical"] for r in records(pages_f)] == [second]


def test_updates_urls_seen(monkeypatch, tmp_path):
    html = "<a href='/a'>A</a><a href='/b'>B</a>"
    fetcher = FakeFetcher({SEED: html, PAGE_A: "<p>a</p>", PAGE_B: "<p>b</p>"})

    _pages_f, _log_f, stats = run(
        monkeypatch, fetcher, tmp_path, config=make_config(budget=3)
    )

    assert stats["pages_fetched"] == 3
    assert stats["urls_seen"] == 3


def test_periodic_stats_write(monkeypatch, tmp_path):
    fetcher = FakeFetcher({SEED: "<p>hi</p>"})
    monkeypatch.setattr(crawl, "STATS_FLUSH_INTERVAL", 1)

    run(monkeypatch, fetcher, tmp_path)

    stats = json.loads((tmp_path / "stats.json").read_text())
    assert stats["pages_fetched"] == 1


def test_waits_between_requests_to_same_host(monkeypatch, tmp_path):
    sleeps = []
    monkeypatch.setattr(crawl.time, "monotonic", lambda: 100.0)
    monkeypatch.setattr(crawl.time, "sleep", sleeps.append)

    fetcher = FakeFetcher(
        {
            SEED: "<a href='/a'>A</a><a href='/b'>B</a>",
            PAGE_A: "<p>a</p>",
            PAGE_B: "<p>b</p>",
        }
    )

    run(monkeypatch, fetcher, tmp_path, config=make_config(budget=3, delay=1.0))

    assert sleeps == [1.0, 1.0]


def test_does_not_wait_between_requests_to_different_hosts(monkeypatch, tmp_path):
    sleeps = []
    monkeypatch.setattr(crawl.time, "monotonic", lambda: 100.0)
    monkeypatch.setattr(crawl.time, "sleep", sleeps.append)

    other = "http://cs.kennesaw.edu/x"
    fetcher = FakeFetcher({SEED: f"<a href='{other}'>x</a>", other: "<p>x</p>"})

    run(monkeypatch, fetcher, tmp_path, config=make_config(delay=1.0))

    assert sleeps == []


def test_redirect_hop_waits_for_target_host(monkeypatch, tmp_path):
    sleeps = []
    monkeypatch.setattr(crawl.time, "monotonic", lambda: 100.0)
    monkeypatch.setattr(crawl.time, "sleep", sleeps.append)

    start = "http://cs.kennesaw.edu/start"
    target = "http://kennesaw.edu/target"
    after = "http://kennesaw.edu/after"
    fetcher = FakeFetcher(
        {
            start: f"<a href='{after}'>after</a>",
            after: "<p>after</p>",
            target: "<p>target</p>",
        },
        finals={start: target},
    )

    run(monkeypatch, fetcher, tmp_path, config=make_config(seeds=[start], delay=1.0))

    assert sleeps == [1.0]


@pytest.mark.parametrize(
    ("delay", "last_request", "expected"),
    [
        pytest.param(1.0, {}, [], id="first_request"),
        pytest.param(1.0, {"kennesaw.edu": 99.75}, [0.75], id="remaining"),
        pytest.param(0.0, {"kennesaw.edu": 0.0}, [], id="zero_delay"),
    ],
)
def test_wait_for_host(monkeypatch, delay, last_request, expected):
    sleeps = []
    monkeypatch.setattr(crawl.time, "monotonic", lambda: 100.0)
    monkeypatch.setattr(crawl.time, "sleep", sleeps.append)

    crawl._wait_for_host("kennesaw.edu", delay, last_request)

    assert sleeps == expected
