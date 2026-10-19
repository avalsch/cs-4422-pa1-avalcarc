import time
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, TextIO
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from requests import Session

from crawl_config import (
    Config,
)
from fetch import FetchError, fetch
from parse import parse
from schema import Stats, make_page_record
from storage import (
    EVENT_ENQUEUE,
    EVENT_ERROR,
    EVENT_FETCH,
    EVENT_SKIP,
    log_decision,
    utc_now,
    write_page,
    write_stats,
)

STATS_FLUSH_INTERVAL = 50


def crawl(
    config: Config,
    session: Session,
    pages_f: TextIO,
    log_f: TextIO,
    stats: Stats,
    stats_path: Path,
    start_time: float,
) -> None:
    frontier: deque[str] = deque()
    seen: set[str] = set()
    stored: set[str] = set()
    last_request: dict[str, float] = {}

    def wait(target: str) -> None:
        # fetch calls this before every request it makes, including redirect
        # hops, so each host's delay is enforced independently.
        host = urlsplit(target).hostname or ""
        _wait_for_host(host, config.delay, last_request)
        last_request[host] = time.monotonic()

    def mark_seen(target: str) -> None:
        seen.add(target)
        stats["urls_seen"] = len(seen)

    for seed in config.seeds:
        if seed in seen:
            log_decision(log_f, EVENT_SKIP, seed, failure_reason="already_seen")
            continue

        mark_seen(seed)
        frontier.append(seed)
        log_decision(log_f, EVENT_ENQUEUE, seed)

    while frontier and stats["pages_fetched"] < config.budget:
        url = frontier.popleft()

        log_decision(log_f, EVENT_FETCH, url)

        result = fetch(url, config, session, wait=wait)

        if isinstance(result, FetchError):
            log_decision(
                log_f,
                EVENT_ERROR,
                url,
                failure_reason=result.error,
                status=result.status,
            )
            continue

        if result.final_url in stored:
            log_decision(log_f, EVENT_SKIP, url, failure_reason="duplicate_final_url")
            continue

        parsed = parse(result.html, result.final_url)

        record = make_page_record(result.final_url, result.status, parsed, utc_now())
        write_page(pages_f, record)
        stored.add(result.final_url)
        stats["pages_fetched"] += 1

        mark_seen(result.final_url)

        for link in parsed.out_links:
            if link in seen:
                log_decision(log_f, EVENT_SKIP, link, failure_reason="already_seen")
                continue

            mark_seen(link)
            frontier.append(link)
            log_decision(log_f, EVENT_ENQUEUE, link)

        if stats["pages_fetched"] % STATS_FLUSH_INTERVAL == 0:
            stats["wall_clock_seconds"] = time.time() - start_time
            write_stats(stats_path, stats)


def _wait_for_host(host: str, delay: float, last_request: dict[str, float]) -> None:
    if delay <= 0 or not host:
        return

    last = last_request.get(host)

    if last is None:
        return

    remaining = delay - (time.monotonic() - last)

    if remaining > 0:
        time.sleep(remaining)
