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
from fetch import ERR_ROBOTS, FetchError, fetch
from parse import parse
from robots import RobotsCache, RobotsPolicy
from schema import Stats, make_page_record
from storage import (
    EVENT_ENQUEUE,
    EVENT_ERROR,
    EVENT_FETCH,
    EVENT_SKIP,
    log_decision,
    utc_now,
    write_cached_html,
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
    robots: RobotsPolicy | None = None,
) -> None:
    frontier: deque[str] = deque()
    seen: set[str] = set()
    stored: set[str] = set()
    last_request: dict[str, float] = {}
    crawl_delays: dict[str, float] = {}
    skip_logged: set[str] = set()

    def mark_seen(target: str) -> None:
        seen.add(target)
        stats["urls_seen"] = len(seen)

    def log_skip_once(target: str, reason: str) -> None:
        if target in skip_logged:
            return

        skip_logged.add(target)
        log_decision(log_f, EVENT_SKIP, target, failure_reason=reason)

    def wait(target: str) -> None:
        host = urlsplit(target).hostname or ""
        delay = max(config.delay, crawl_delays.get(host, 0.0))
        _wait_for_host(host, delay, last_request)
        last_request[host] = time.monotonic()
        log_decision(log_f, EVENT_FETCH, target)

    policy: RobotsPolicy = robots or RobotsCache(
        config, session, wait=wait, delays=crawl_delays
    )

    def permit(target: str) -> bool:
        if policy.can_fetch(target):
            return True

        if target not in seen:
            mark_seen(target)
            stats["robots_skips"] += 1
            log_skip_once(target, ERR_ROBOTS)

        return False

    for seed in config.seeds:
        if seed in seen:
            log_skip_once(seed, "already_seen")
            continue

        if not policy.can_fetch(seed):
            mark_seen(seed)
            stats["robots_skips"] += 1
            log_skip_once(seed, ERR_ROBOTS)
            continue

        mark_seen(seed)
        frontier.append(seed)
        log_decision(log_f, EVENT_ENQUEUE, seed)

    while frontier and stats["pages_fetched"] < config.budget:
        url = frontier.popleft()

        result = fetch(url, config, session, permit=permit, wait=wait)

        if isinstance(result, FetchError):
            if result.error == ERR_ROBOTS:
                continue

            log_decision(
                log_f,
                EVENT_ERROR,
                url,
                failure_reason=result.error,
                status=result.status,
                target=result.target,
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

        if config.cache_dir is not None:
            write_cached_html(config.cache_dir, result.final_url, result.html)

        mark_seen(result.final_url)

        for link in parsed.out_links:
            if link in seen:
                log_skip_once(link, "already_seen")
                continue

            if not policy.can_fetch(link):
                mark_seen(link)
                stats["robots_skips"] += 1
                log_skip_once(link, ERR_ROBOTS)
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
