import re
from typing import get_args, get_type_hints

from parse import ParseResult
from schema import (
    Event,
    LogEntry,
    PageRecord,
    Stats,
    content_hash,
    make_page_record,
    normalize_text,
)

FETCHED_AT = "2026-10-18T09:30:00Z"
SHA256_HEX = re.compile(r"[0-9a-f]{64}")

# sha256 of the normalized text "" and "hello world"
EMPTY_TEXT_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
HELLO_WORLD_HASH = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def make_result(
    title: str = "Title",
    text: str = "Hello world",
    out_links: list[str] | None = None,
    canonical_link: str | None = None,
) -> ParseResult:
    return ParseResult(
        title,
        text,
        ["http://kennesaw.edu/a"] if out_links is None else out_links,
        canonical_link,
    )


def test_page_record_fields_match_spec():
    assert set(get_type_hints(PageRecord)) == {
        "url_canonical",
        "status",
        "fetched_at",
        "title",
        "text",
        "word_count",
        "out_links",
        "content_hash",
        "canonical_link",
    }


def test_log_entry_fields_match_spec():
    assert set(get_type_hints(LogEntry)) == {
        "ts",
        "event",
        "url",
        "failure_reason",
        "status",
        "target",
    }


def test_stats_fields_match_spec():
    assert set(get_type_hints(Stats)) == {
        "pages_fetched",
        "urls_seen",
        "wall_clock_seconds",
        "robots_skips",
        "random_seed",
        "delay",
    }


def test_event_values_match_spec():
    assert set(get_args(Event)) == {"enqueue", "fetch", "skip", "error"}


def test_make_page_record_has_exactly_the_page_record_fields():
    record = make_page_record("u", 200, make_result(), FETCHED_AT)

    assert set(record) == set(get_type_hints(PageRecord))


def test_normalize_text_lowercases_and_collapses_whitespace():
    assert normalize_text("  Hello\n\tWorld  ") == "hello world"


def test_content_hash_is_sha256_hex():
    assert SHA256_HEX.fullmatch(content_hash("hello"))


def test_content_hash_ignores_case_and_whitespace():
    assert content_hash("Hello   World") == content_hash("hello world")


def test_content_hash_differs_for_different_text():
    assert content_hash("a") != content_hash("b")


def test_content_hash_matches_known_digests():
    assert content_hash("") == EMPTY_TEXT_HASH
    assert content_hash("Hello World") == HELLO_WORLD_HASH


def test_make_page_record_schema():
    record = make_page_record("http://kennesaw.edu/a", 200, make_result(), FETCHED_AT)

    assert record == {
        "url_canonical": "http://kennesaw.edu/a",
        "status": 200,
        "fetched_at": FETCHED_AT,
        "title": "Title",
        "text": "Hello world",
        "word_count": 2,
        "out_links": ["http://kennesaw.edu/a"],
        "content_hash": content_hash("Hello world"),
        "canonical_link": None,
    }


def test_make_page_record_word_count():
    record = make_page_record("u", 200, make_result(text="one two three"), FETCHED_AT)

    assert record["word_count"] == 3


def test_make_page_record_empty_text_hashes_and_counts_zero():
    record = make_page_record("u", 200, make_result(text=""), FETCHED_AT)

    assert record["word_count"] == 0
    assert record["content_hash"] == EMPTY_TEXT_HASH


def test_make_page_record_copies_out_links():
    out_links = ["http://kennesaw.edu/a"]

    record = make_page_record("u", 200, make_result(out_links=out_links), FETCHED_AT)

    assert record["out_links"] == out_links
    assert record["out_links"] is not out_links


def test_make_page_record_includes_canonical_link():
    result = make_result(canonical_link="http://kennesaw.edu/c")

    assert make_page_record("u", 200, result, FETCHED_AT)["canonical_link"] == (
        "http://kennesaw.edu/c"
    )
