import analyze
from analyze import (
    _cleaned_words,
    _term_counts,
    fetch_gaps,
    q1_patterns,
    q2_duplicates,
    q3_errors,
    q4_links,
    q5_boilerplate,
    q6_words,
    q8_politeness,
    shape,
    zipf_fit,
)
from storage import write_cached_html


def test_shape_replaces_number_date_and_id_segments():
    uuid = "123e4567-e89b-12d3-a456-426614174000"

    assert shape("http://kennesaw.edu/a/12/b") == "kennesaw.edu/a/<num>/b"
    assert shape("http://kennesaw.edu/a/2024-01-02") == "kennesaw.edu/a/<date>"
    assert shape(f"http://kennesaw.edu/a/{uuid}") == "kennesaw.edu/a/<id>"


def test_shape_keeps_query_names_without_values():
    assert shape("http://kennesaw.edu/s?b=2&a=1") == "kennesaw.edu/s?a&b"
    assert shape("http://kennesaw.edu/s") == "kennesaw.edu/s"


def test_q1_ranks_patterns_by_pages_and_counts_hashes():
    pages = [
        {"url_canonical": "http://kennesaw.edu/cal/1", "content_hash": "h1"},
        {"url_canonical": "http://kennesaw.edu/cal/2", "content_hash": "h1"},
        {"url_canonical": "http://kennesaw.edu/cal/3", "content_hash": "h2"},
        {"url_canonical": "http://kennesaw.edu/about", "content_hash": "h3"},
    ]

    text = q1_patterns(pages)

    assert "4 pages across 2 patterns" in text
    assert "| 1 | `kennesaw.edu/cal/<num>` | 3 | 2 |" in text
    assert "| 2 | `kennesaw.edu/about` | 1 | 1 |" in text


def test_q4_ranks_in_and_out_links():
    pages = [
        {"url_canonical": "http://k/s", "out_links": ["http://k/a", "http://k/b"]},
        {"url_canonical": "http://k/a", "out_links": ["http://k/b"]},
        {"url_canonical": "http://k/b", "out_links": []},
        {"url_canonical": "http://k/c", "out_links": ["http://k/b", "http://k/off"]},
    ]

    text = q4_links(pages)

    assert "| 1 | http://k/b | 3 |" in text
    assert "| 2 | http://k/a | 1 |" in text
    assert "| 1 | http://k/c | 2 |" in text
    assert "| 2 | http://k/s | 2 |" in text
    assert "http://k/off" not in text


def test_q2_detects_identical_near_and_self_declared():
    pages = [
        {
            "url_canonical": "http://k/a",
            "content_hash": "h1",
            "text": "alpha beta gamma delta epsilon zeta eta theta",
            "canonical_link": None,
        },
        {
            "url_canonical": "http://k/b",
            "content_hash": "h1",
            "text": "alpha beta gamma delta epsilon zeta eta theta",
            "canonical_link": None,
        },
        {
            "url_canonical": "http://k/c",
            "content_hash": "h2",
            "text": "alpha beta gamma delta epsilon zeta eta theta iota",
            "canonical_link": "http://k/a",
        },
        {
            "url_canonical": "http://k/d",
            "content_hash": "h3",
            "text": "completely different words here nothing shared at all",
            "canonical_link": None,
        },
    ]

    text = q2_duplicates(pages, threshold=0.5)

    assert "byte-identical: 2 pages" in text
    assert "1 duplicate groups" in text
    assert "near-duplicate: 3 pages" in text
    assert "2 pairs at Jaccard >= 0.50" in text
    assert "self-declared canonical: 1 pages" in text
    assert "identical: http://k/a == http://k/b" in text
    assert "near: http://k/a ~ http://k/c (Jaccard 0.80)" in text
    assert "self-declared: http://k/c -> http://k/a" in text


def test_q5_boilerplate_reports_means_and_tables(monkeypatch, tmp_path):
    pages = [
        {
            "url_canonical": "http://k/a",
            "text": "one two three four five six seven eight",
        },
        {"url_canonical": "http://k/b", "text": "one two three four"},
    ]
    sizes = {"http://k/a": 4, "http://k/b": 2}
    monkeypatch.setattr(analyze, "_cleaned_words", lambda _dir, url: sizes[url])

    text = q5_boilerplate(pages, tmp_path)

    assert "- pages: 2 of 2 with cached HTML" in text
    assert "- mean words before: 6.0" in text
    assert "- mean words after: 3.0 (50.0% removed)" in text
    assert "| 1 | http://k/a | 8 |" in text
    assert "| 1 | http://k/a | 4 |" in text


def test_cleaned_words_missing_cache_returns_none(tmp_path):
    assert _cleaned_words(tmp_path, "http://k/none") is None


def test_cleaned_words_reads_cached_html(tmp_path):
    write_cached_html(
        tmp_path,
        "http://k/a",
        "<html><body><main><article><p>alpha beta gamma</p></article></main></body></html>",
    )

    words = _cleaned_words(tmp_path, "http://k/a")

    assert words is not None
    assert words > 0


def test_zipf_fit_recovers_exponent():
    counts = [max(1, round(100000 / (rank**1.5))) for rank in range(1, 150)]

    exponent, r2 = zipf_fit(counts)

    assert 1.45 < exponent < 1.55
    assert r2 > 0.99


def test_term_counts_drop_stopwords():
    texts = ["the cat sat on the mat", "the dog sat"]

    all_terms = dict(_term_counts(texts, stop_words=None))
    content = dict(_term_counts(texts, stop_words="english"))

    assert all_terms["the"] == 3
    assert "the" not in content
    assert content["sat"] == 2


def test_q6_reports_top_words_and_fit(monkeypatch, tmp_path):
    monkeypatch.setattr(
        analyze, "clean_texts", lambda _pages, _dir: ["alpha alpha beta gamma"]
    )
    pages = [{"url_canonical": "http://k/a"}]

    text = q6_words(pages, tmp_path)

    assert "1 boilerplate-removed pages, 4 tokens" in text
    assert "| 1 | alpha | 2 |" in text
    assert "exponent s = " in text


def test_q3_ranks_by_count_then_name():
    log = [
        {"event": "error", "failure_reason": "timeout"},
        {"event": "error", "failure_reason": "timeout"},
        {"event": "error", "failure_reason": "http_error"},
        {"event": "error", "failure_reason": "connection_error"},
        {"event": "fetch", "failure_reason": None},
    ]

    assert q3_errors(log) == (
        "## Q3: most common fetch failures\n"
        "\n"
        "| rank | failure_reason | count |\n"
        "| --- | --- | --- |\n"
        "| 1 | timeout | 2 |\n"
        "| 2 | connection_error | 1 |\n"
        "| 3 | http_error | 1 |\n"
        "\n"
        "Total: 4 errors."
    )


def test_q3_limits_to_five_rows():
    log = [{"event": "error", "failure_reason": f"r{i}"} for i in range(7)]

    text = q3_errors(log)

    assert "| 5 | r4 | 1 |" in text
    assert "r5" not in text


def test_q3_with_no_errors():
    assert q3_errors([]) == (
        "## Q3: most common fetch failures\n"
        "\n"
        "| rank | failure_reason | count |\n"
        "| --- | --- | --- |\n"
        "\n"
        "Total: 0 errors."
    )


def test_fetch_gaps_are_per_host_and_ignore_single_requests():
    log = [
        {
            "event": "fetch",
            "ts": "2026-01-01T00:00:00.000Z",
            "url": "http://kennesaw.edu/a",
        },
        {
            "event": "fetch",
            "ts": "2026-01-01T00:00:02.000Z",
            "url": "http://kennesaw.edu/b",
        },
        {
            "event": "fetch",
            "ts": "2026-01-01T00:00:05.000Z",
            "url": "http://cs.kennesaw.edu/a",
        },
    ]

    assert fetch_gaps(log) == {"kennesaw.edu": 2.0}


def test_q8_politeness_section():
    log = [
        {
            "event": "fetch",
            "ts": "2026-01-01T00:00:00.000Z",
            "url": "http://kennesaw.edu/a",
        },
        {
            "event": "fetch",
            "ts": "2026-01-01T00:00:01.000Z",
            "url": "http://kennesaw.edu/b",
        },
        {
            "event": "fetch",
            "ts": "2026-01-01T00:00:03.000Z",
            "url": "http://cs.kennesaw.edu/a",
        },
        {
            "event": "fetch",
            "ts": "2026-01-01T00:00:03.500Z",
            "url": "http://cs.kennesaw.edu/b",
        },
        {
            "event": "skip",
            "failure_reason": "robots_blocked",
            "url": "http://kennesaw.edu/private",
        },
        {
            "event": "skip",
            "failure_reason": "robots_blocked",
            "url": "http://campus.kennesaw.edu/private",
        },
        {
            "event": "skip",
            "failure_reason": "already_seen",
            "url": "http://kennesaw.edu/x",
        },
    ]
    stats = {"pages_fetched": 4, "wall_clock_seconds": 8.0, "delay": 1.0}

    text = q8_politeness(log, stats)

    assert "2 hosts, minimum gap 0.50 s, 1 below the 1.00 s floor." in text
    assert "| cs.kennesaw.edu | 0.50 |" in text
    assert "| kennesaw.edu | 1.00 |" in text
    assert "| kennesaw.edu | 1 |" in text
    assert "| campus.kennesaw.edu | 1 |" in text
    assert "4 pages / 8.0 s = 0.50 pages/s" in text
    assert "4 requests / 8.0 s = 0.50 requests/s" in text
