import io
import json
import re
from pathlib import Path

import pytest

from schema import Stats
from storage import (
    EVENT_ENQUEUE,
    EVENT_ERROR,
    EVENT_FETCH,
    log_decision,
    utc_now,
    write_page,
    write_stats,
)

ISO_Z = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")


def make_stats() -> Stats:
    return {
        "pages_fetched": 0,
        "urls_seen": 0,
        "wall_clock_seconds": 0.0,
        "robots_skips": 0,
        "random_seed": None,
    }


def test_utc_now_is_iso8601_z():
    assert ISO_Z.fullmatch(utc_now())


def test_write_page_writes_one_json_line():
    buf = io.StringIO()

    write_page(buf, {"a": 1})

    assert buf.getvalue() == '{"a": 1}\n'


def test_write_page_appends():
    buf = io.StringIO()

    write_page(buf, {"a": 1})
    write_page(buf, {"b": 2})

    lines = [json.loads(line) for line in buf.getvalue().splitlines()]
    assert lines == [{"a": 1}, {"b": 2}]


def test_write_page_keeps_unicode_readable():
    buf = io.StringIO()

    write_page(buf, {"text": "café"})

    assert "café" in buf.getvalue()


def test_log_decision_entry_schema():
    buf = io.StringIO()

    log_decision(
        buf, EVENT_ERROR, "http://kennesaw.edu/x", failure_reason="timeout", status=503
    )

    entry = json.loads(buf.getvalue())
    assert entry["event"] == "error"
    assert entry["url"] == "http://kennesaw.edu/x"
    assert entry["failure_reason"] == "timeout"
    assert entry["status"] == 503
    assert ISO_Z.fullmatch(entry["ts"])


def test_log_decision_defaults_to_no_failure_or_status():
    buf = io.StringIO()

    log_decision(buf, EVENT_FETCH, "http://kennesaw.edu/a")

    entry = json.loads(buf.getvalue())
    assert entry["failure_reason"] is None
    assert entry["status"] is None


def test_log_decision_appends_one_line_per_call():
    buf = io.StringIO()

    log_decision(buf, EVENT_ENQUEUE, "http://kennesaw.edu/a")
    log_decision(buf, EVENT_FETCH, "http://kennesaw.edu/a")

    lines = [json.loads(line) for line in buf.getvalue().splitlines()]
    assert [line["event"] for line in lines] == ["enqueue", "fetch"]


def test_write_stats_round_trips(tmp_path):
    path = tmp_path / "stats.json"
    stats = make_stats()
    stats["pages_fetched"] = 5
    stats["urls_seen"] = 9

    write_stats(path, stats)

    assert json.loads(path.read_text()) == stats


def test_write_stats_overwrites(tmp_path):
    path = tmp_path / "stats.json"
    first = make_stats()
    first["pages_fetched"] = 1
    second = make_stats()
    second["pages_fetched"] = 2

    write_stats(path, first)
    write_stats(path, second)

    assert json.loads(path.read_text()) == second


def test_write_stats_is_indented(tmp_path):
    path = tmp_path / "stats.json"

    write_stats(path, make_stats())

    assert path.read_text() == (
        "{\n"
        '  "pages_fetched": 0,\n'
        '  "urls_seen": 0,\n'
        '  "wall_clock_seconds": 0.0,\n'
        '  "robots_skips": 0,\n'
        '  "random_seed": null\n'
        "}\n"
    )


def test_write_stats_leaves_nothing_behind(tmp_path):
    path = tmp_path / "stats.json"

    write_stats(path, make_stats())

    assert list(tmp_path.iterdir()) == [path]


def test_write_stats_keeps_the_old_file_when_the_write_fails(tmp_path, monkeypatch):
    path = tmp_path / "stats.json"
    previous = make_stats()
    previous["pages_fetched"] = 1
    write_stats(path, previous)

    real_write_text = Path.write_text

    def fail(self: Path, data: str, *, encoding: str | None = None) -> None:
        real_write_text(self, "partial", encoding=encoding)
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", fail)

    with pytest.raises(OSError):
        write_stats(path, make_stats())

    assert json.loads(path.read_text()) == previous
