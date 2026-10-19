import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from schema import Event, LogEntry, Stats

EVENT_ENQUEUE: Event = "enqueue"
EVENT_FETCH: Event = "fetch"
EVENT_SKIP: Event = "skip"
EVENT_ERROR: Event = "error"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _write_line(f: TextIO, obj: Mapping[str, object]) -> None:
    f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    f.flush()


def write_page(f: TextIO, record: Mapping[str, object]) -> None:
    _write_line(f, record)


def log_decision(
    f: TextIO,
    event: Event,
    url: str,
    *,
    failure_reason: str | None = None,
    status: int | None = None,
    target: str | None = None,
) -> None:
    entry: LogEntry = {
        "ts": utc_now(),
        "event": event,
        "url": url,
        "failure_reason": failure_reason,
        "status": status,
        "target": target,
    }

    _write_line(f, entry)


def write_stats(path: Path, stats: Stats) -> None:
    # use a tmp file and replace to atomically swap a fully written file,
    # to avoid leaving a half-written stats.json
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def cache_path(cache_dir: Path, url: str) -> Path:
    # URL -> filename is deterministic so the analysis stage can find a page's
    # raw HTML from its canonical URL without an index.
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / f"{digest}.html"


def write_cached_html(cache_dir: Path, url: str, html: str) -> Path:
    path = cache_path(cache_dir, url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path
