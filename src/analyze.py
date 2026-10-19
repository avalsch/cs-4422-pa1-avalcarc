import itertools
import json
import random
import re
import sys
from argparse import ArgumentParser
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

import numpy as np
import pandas as pd
import trafilatura
from sklearn.feature_extraction.text import (
    ENGLISH_STOP_WORDS,
    CountVectorizer,
    TfidfVectorizer,
)

from storage import cache_path

DEFAULT_PAGES = Path("artifacts/pages.jsonl")
DEFAULT_LOG = Path("artifacts/crawl.log")
DEFAULT_STATS = Path("artifacts/stats.json")
DEFAULT_CACHE = Path("cache")

DEFAULT_NEAR_DUP = 0.8
NEAR_DUP_BANDS = (0.9, 0.8, 0.7, 0.5)
MIN_WORDS = 50


@dataclass
class AnalyzeConfig:
    pages: Path = DEFAULT_PAGES
    log: Path = DEFAULT_LOG
    stats: Path = DEFAULT_STATS
    cache_dir: Path = DEFAULT_CACHE


def parse_args(argv: list[str] | None = None) -> AnalyzeConfig:
    parser = ArgumentParser(
        description="Stage two: compute Q1-Q8 numbers from crawl artifacts"
    )

    parser.add_argument(
        "-p",
        "--pages",
        type=Path,
        default=DEFAULT_PAGES,
        help="pages.jsonl written by stage one (one JSON record per fetched page)",
    )

    parser.add_argument(
        "-l",
        "--log",
        type=Path,
        default=DEFAULT_LOG,
        help="crawl.log written by stage one (one JSON decision per line)",
    )

    parser.add_argument(
        "-s",
        "--stats",
        type=Path,
        default=DEFAULT_STATS,
        help="stats.json written by stage one (crawl summary counters)",
    )

    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE,
        help="directory holding the raw HTML cache written by stage one",
    )

    args = parser.parse_args(argv)

    return AnalyzeConfig(
        pages=args.pages,
        log=args.log,
        stats=args.stats,
        cache_dir=args.cache_dir,
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def header(
    pages: list[dict[str, Any]], log: list[dict[str, Any]], stats: dict[str, Any]
) -> str:
    return "\n".join(
        [
            "# Stage two: analysis numbers",
            "",
            f"- pages: {len(pages)} in pages.jsonl, {stats['pages_fetched']} in stats.json",
            f"- URLs seen: {stats['urls_seen']}",
            f"- wall clock: {stats['wall_clock_seconds']:.1f} s",
            f"- logged decisions: {len(log)}",
        ]
    )


_DIGITS = re.compile(r"^\d+$")
_DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def _shape_segment(segment: str) -> str:
    if _UUID.match(segment):
        return "<id>"

    if _DATE.match(segment):
        return "<date>"

    if _DIGITS.match(segment):
        return "<num>"

    return segment


def shape(url: str) -> str:
    parts = urlsplit(url)
    path = "/".join(_shape_segment(s) for s in parts.path.split("/"))
    names = sorted({name for name, _ in parse_qsl(parts.query, keep_blank_values=True)})
    query = f"?{'&'.join(names)}" if names else ""

    return f"{parts.hostname}{path}{query}"


def q1_patterns(pages: list[dict[str, Any]], top: int = 15) -> str:
    frame = pd.DataFrame(pages)
    frame["pattern"] = frame["url_canonical"].map(shape)

    grouped = (
        frame.groupby("pattern")
        .agg(pages=("url_canonical", "size"), hashes=("content_hash", "nunique"))
        .sort_values(["pages", "pattern"], ascending=[False, True])
        .reset_index()
    )

    rows = [
        f"| {i} | `{r.pattern}` | {r.pages} | {r.hashes} |"
        for i, r in enumerate(grouped.head(top).itertuples(index=False), 1)
    ]

    return "\n".join(
        [
            "## Q1: URL patterns by budget",
            "",
            (
                f"{len(frame)} pages across {len(grouped)} patterns; "
                f"top {min(top, len(grouped))} by pages:"
            ),
            "",
            "| rank | pattern | pages | distinct hashes |",
            "| --- | --- | --- | --- |",
            *rows,
        ]
    )


def q2_duplicates(
    pages: list[dict[str, Any]], threshold: float = DEFAULT_NEAR_DUP
) -> str:
    frame = pd.DataFrame(pages)
    urls = frame["url_canonical"].tolist()
    hashes = frame["content_hash"].to_numpy()

    groups = [
        group
        for group in frame.groupby("content_hash")["url_canonical"].apply(list)
        if len(group) > 1
    ]
    identical_pages = sum(len(group) for group in groups)

    matrix = CountVectorizer(ngram_range=(5, 5), binary=True).fit_transform(
        frame["text"]
    )

    # pairwise Jaccard = |A and B| / |A or B|, from the sparse shingle matrix
    intersection = np.asarray((matrix @ matrix.T).todense(), dtype=float)
    sizes = np.asarray(matrix.sum(axis=1)).ravel().astype(float)
    union = sizes[:, None] + sizes[None, :] - intersection
    similarity = np.divide(
        intersection, union, out=np.zeros_like(intersection), where=union > 0
    )

    upper = np.triu_indices(len(frame), k=1)
    sims = similarity[upper]
    differing = hashes[upper[0]] != hashes[upper[1]]

    near_pairs = int(((sims >= threshold) & differing).sum())
    involved = np.argwhere((sims >= threshold) & differing).ravel()
    near_pages = len(set(upper[0][involved]) | set(upper[1][involved]))

    bands = [(band, int(((sims >= band) & differing).sum())) for band in NEAR_DUP_BANDS]

    canonical = frame["canonical_link"]
    declared = frame[canonical.notna() & (canonical != frame["url_canonical"])]

    total = len(frame)

    def share(count: int) -> str:
        return f"{count} pages ({100 * count / total:.1f}%)" if total else "0 pages"

    lines = [
        "## Q2: duplicate content",
        "",
        f"Near-duplicate threshold: {threshold:.2f} (5-gram word shingles, Jaccard).",
        "",
        f"- byte-identical: {share(identical_pages)}, {len(groups)} duplicate groups",
        f"- near-duplicate: {share(near_pages)}, {near_pairs} pairs at Jaccard >= {threshold:.2f}",
        f"- self-declared canonical: {share(len(declared))}",
        "",
        "Non-identical pairs by similarity band:",
        "",
        "| Jaccard >= | pairs |",
        "| --- | --- |",
        *[f"| {band:.2f} | {count} |" for band, count in bands],
        "",
        "Examples:",
    ]

    if groups:
        lines.append(f"- identical: {groups[0][0]} == {groups[0][1]}")

    if differing.any():
        best = int(np.argmax(np.where(differing, sims, -1.0)))
        lines.append(
            f"- near: {urls[upper[0][best]]} ~ {urls[upper[1][best]]} "
            f"(Jaccard {sims[best]:.2f})"
        )

    if len(declared):
        row = declared.iloc[0]
        lines.append(
            f"- self-declared: {row['url_canonical']} -> {row['canonical_link']}"
        )

    return "\n".join(lines)


def q3_errors(log: list[dict[str, Any]]) -> str:
    counts = Counter(e["failure_reason"] for e in log if e["event"] == "error")
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]

    rows = [
        f"| {i} | {reason} | {count} |" for i, (reason, count) in enumerate(ranked, 1)
    ]

    return "\n".join(
        [
            "## Q3: most common fetch failures",
            "",
            "| rank | failure_reason | count |",
            "| --- | --- | --- |",
            *rows,
            "",
            f"Total: {sum(counts.values())} errors.",
        ]
    )


def q4_links(pages: list[dict[str, Any]], top: int = 5) -> str:
    frame = pd.DataFrame(pages)
    crawled = set(frame["url_canonical"])

    edges = frame[["url_canonical", "out_links"]].explode("out_links")
    edges = edges[edges["out_links"].isin(crawled)]

    indegree = (
        edges.groupby("out_links")
        .size()
        .reset_index(name="count")
        .sort_values(["count", "out_links"], ascending=[False, True])
    )
    outdegree = (
        frame.assign(count=frame["out_links"].map(len))
        .loc[:, ["url_canonical", "count"]]
        .sort_values(["count", "url_canonical"], ascending=[False, True])
    )

    in_rows = [
        f"| {i} | {r.out_links} | {r.count} |"
        for i, r in enumerate(indegree.head(top).itertuples(index=False), 1)
    ]
    out_rows = [
        f"| {i} | {r.url_canonical} | {r.count} |"
        for i, r in enumerate(outdegree.head(top).itertuples(index=False), 1)
    ]

    return "\n".join(
        [
            "## Q4: top pages by links",
            "",
            "Top 5 by incoming links (from crawled pages):",
            "",
            "| rank | url | in-links |",
            "| --- | --- | --- |",
            *in_rows,
            "",
            "Top 5 by outgoing links:",
            "",
            "| rank | url | out-links |",
            "| --- | --- | --- |",
            *out_rows,
        ]
    )


def _cleaned_text(cache_dir: Path, url: str) -> str | None:
    path = cache_path(cache_dir, url)

    if not path.exists():
        return None

    html = path.read_text(encoding="utf-8")
    text = trafilatura.extract(html, include_comments=False, include_tables=False)

    return text or ""


def _cleaned_words(cache_dir: Path, url: str) -> int | None:
    text = _cleaned_text(cache_dir, url)

    return None if text is None else len(text.split())


def clean_texts(pages: list[dict[str, Any]], cache_dir: Path) -> list[str]:
    return [_cleaned_text(cache_dir, p["url_canonical"]) or "" for p in pages]


def q5_boilerplate(pages: list[dict[str, Any]], cache_dir: Path, top: int = 5) -> str:
    frame = pd.DataFrame(pages)
    frame["raw_words"] = frame["text"].map(lambda text: len(text.split()))
    frame["clean_words"] = [
        _cleaned_words(cache_dir, url) for url in frame["url_canonical"]
    ]

    present = frame.dropna(subset=["clean_words"])
    raw_mean = present["raw_words"].mean()
    clean_mean = present["clean_words"].mean()
    removed = 100 * (1 - clean_mean / raw_mean) if raw_mean else 0.0

    raw_top = frame.sort_values(
        ["raw_words", "url_canonical"], ascending=[False, True]
    ).head(top)
    clean_top = present.sort_values(
        ["clean_words", "url_canonical"], ascending=[False, True]
    ).head(top)

    raw_urls = raw_top["url_canonical"].tolist()
    raw_counts = raw_top["raw_words"].tolist()
    clean_urls = clean_top["url_canonical"].tolist()
    clean_counts = clean_top["clean_words"].tolist()

    raw_rows = [
        f"| {i} | {url} | {words} |"
        for i, (url, words) in enumerate(zip(raw_urls, raw_counts), 1)
    ]
    clean_rows = [
        f"| {i} | {url} | {int(words)} |"
        for i, (url, words) in enumerate(zip(clean_urls, clean_counts), 1)
    ]

    return "\n".join(
        [
            "## Q5: boilerplate removal",
            "",
            "Strategy: trafilatura main-content extraction over the cached HTML.",
            "",
            f"- pages: {len(present)} of {len(frame)} with cached HTML",
            f"- mean words before: {raw_mean:.1f}",
            f"- mean words after: {clean_mean:.1f} ({removed:.1f}% removed)",
            "",
            "Top 5 longest by raw text:",
            "",
            "| rank | url | words |",
            "| --- | --- | --- |",
            *raw_rows,
            "",
            "Top 5 longest after removal:",
            "",
            "| rank | url | words |",
            "| --- | --- | --- |",
            *clean_rows,
        ]
    )


def _term_counts(texts: list[str], stop_words: str | None) -> list[tuple[str, int]]:
    vectorizer = CountVectorizer(stop_words=stop_words)
    matrix = vectorizer.fit_transform(texts)
    totals = np.asarray(matrix.sum(axis=0)).ravel()
    names = vectorizer.get_feature_names_out()
    order = np.argsort(-totals, kind="stable")

    return [(str(names[i]), int(totals[i])) for i in order]


def zipf_fit(counts: list[int]) -> tuple[float, float]:
    freq = np.asarray(counts, dtype=float)
    ranks = np.arange(1, len(freq) + 1)
    slope, intercept = np.polyfit(np.log(ranks), np.log(freq), 1)
    predicted = slope * np.log(ranks) + intercept
    residual = np.sum((np.log(freq) - predicted) ** 2)
    total = np.sum((np.log(freq) - np.log(freq).mean()) ** 2)

    return -float(slope), float(1 - residual / total)


def q6_words(pages: list[dict[str, Any]], cache_dir: Path, top: int = 30) -> str:
    texts = clean_texts(pages, cache_dir)
    tokens = sum(len(text.split()) for text in texts)

    all_terms = _term_counts(texts, stop_words=None)
    content_terms = _term_counts(texts, stop_words="english")

    exponent, r2 = zipf_fit([count for _, count in content_terms])
    hapax = sum(1 for _, count in content_terms if count == 1)

    def rows(terms: list[tuple[str, int]]) -> list[str]:
        return [
            f"| {i} | {word} | {count} |"
            for i, (word, count) in enumerate(terms[:top], 1)
        ]

    return "\n".join(
        [
            "## Q6: word frequencies and Zipf",
            "",
            f"Corpus: {len(texts)} boilerplate-removed pages, {tokens} tokens.",
            "",
            f"Top {top} words (all):",
            "",
            "| rank | word | count |",
            "| --- | --- | --- |",
            *rows(all_terms),
            "",
            f"Top {top} words (stopwords removed):",
            "",
            "| rank | word | count |",
            "| --- | --- | --- |",
            *rows(content_terms),
            "",
            (
                f"Zipf fit on the stopword-removed distribution: exponent s = {exponent:.2f}, "
                f"R^2 = {r2:.2f}, {len(content_terms)} terms, {hapax} occurring once."
            ),
        ]
    )


def _keywords(
    texts: list[str], picks: list[int], vectorizer: TfidfVectorizer
) -> dict[int, list[tuple[str, float]]]:
    matrix = vectorizer.fit_transform(texts)
    names = vectorizer.get_feature_names_out()
    result: dict[int, list[tuple[str, float]]] = {}

    for index in picks:
        row = matrix[index].toarray().ravel()
        top = np.argsort(-row, kind="stable")[:5]
        result[index] = [(str(names[j]), float(row[j])) for j in top if row[j] > 0]

    return result


def _keyword_penalty(terms: list[tuple[str, float]]) -> int:
    return sum(1 for word, _ in terms if word in ENGLISH_STOP_WORDS or word.isdigit())


def q7_tfidf(
    pages: list[dict[str, Any]],
    cache_dir: Path,
    stats: dict[str, Any],
    sample: int = 5,
) -> str:
    texts = clean_texts(pages, cache_dir)
    urls = [p["url_canonical"] for p in pages]
    lengths = [len(text.split()) for text in texts]

    rng = random.Random(stats["random_seed"])
    picks = sorted(rng.sample(range(len(texts)), min(sample, len(texts))))

    before = _keywords(texts, picks, TfidfVectorizer())
    penalties = {index: _keyword_penalty(before[index]) for index in picks}
    worst = max(picks, key=lambda index: (penalties[index], -lengths[index], -index))
    after = _keywords(texts, [worst], TfidfVectorizer(min_df=2, sublinear_tf=True))[
        worst
    ]

    thin = sum(1 for length in lengths if length < MIN_WORDS)

    def keywords(terms: list[tuple[str, float]]) -> str:
        return ", ".join(f"{word} ({score:.2f})" for word, score in terms) or "(none)"

    rows = [
        f"| {i} | {lengths[index]} | {urls[index]} | {keywords(before[index])} |"
        for i, index in enumerate(picks, 1)
    ]

    return "\n".join(
        [
            "## Q7: TF-IDF keywords",
            "",
            f"Sampled {len(picks)} pages with random_seed = {stats['random_seed']}.",
            "",
            "| # | words | url | top 5 keywords |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            (
                f"Worst sampled page: {urls[worst]} ({lengths[worst]} words, "
                f"{penalties[worst]} of 5 keywords are stopwords or numbers)."
            ),
            f"- before: {keywords(before[worst])}",
            f"- after min_df=2 + sublinear_tf: {keywords(after)}",
            "",
            f"{thin} of {len(texts)} pages are shorter than {MIN_WORDS} words.",
        ]
    )


def fetch_gaps(log: list[dict[str, Any]]) -> dict[str, float]:
    stamps: dict[str, list[datetime]] = defaultdict(list)

    for e in log:
        if e["event"] == "fetch":
            host = urlsplit(e["url"]).hostname or ""
            stamps[host].append(datetime.fromisoformat(e["ts"]))

    gaps: dict[str, float] = {}

    for host, times in stamps.items():
        times.sort()

        if len(times) > 1:
            gaps[host] = min(
                (b - a).total_seconds() for a, b in itertools.pairwise(times)
            )

    return gaps


def q8_politeness(log: list[dict[str, Any]], stats: dict[str, Any]) -> str:
    gaps = fetch_gaps(log)
    delay = stats["delay"]
    below = sum(1 for gap in gaps.values() if gap < delay)
    min_gap = min(gaps.values()) if gaps else 0.0

    blocked = Counter(
        urlsplit(e["url"]).hostname or ""
        for e in log
        if e["event"] == "skip" and e["failure_reason"] == "robots_blocked"
    )

    requests = sum(1 for e in log if e["event"] == "fetch")
    wall = stats["wall_clock_seconds"]
    pages = stats["pages_fetched"]

    return "\n".join(
        [
            "## Q8: politeness evidence",
            "",
            (
                f"**Q8.a delay compliance.** {len(gaps)} hosts, minimum gap {min_gap:.2f} s, "
                f"{below} below the {delay:.2f} s floor."
            ),
            "",
            "| host | min gap (s) |",
            "| --- | --- |",
            *[
                f"| {h} | {g:.2f} |"
                for h, g in sorted(gaps.items(), key=lambda kv: kv[1])
            ],
            "",
            "**Q8.b robots.txt.**",
            "",
            "| host | blocked |",
            "| --- | --- |",
            *[f"| {h} | {c} |" for h, c in blocked.most_common()],
            "",
            (
                f"**Q8.c request rate.** {pages} pages / {wall:.1f} s = {pages / wall:.2f} pages/s; "
                f"{requests} requests / {wall:.1f} s = {requests / wall:.2f} requests/s."
            ),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)

    pages = load_jsonl(config.pages)
    log = load_jsonl(config.log)
    stats = load_json(config.stats)

    print(
        "\n\n".join(
            [
                header(pages, log, stats),
                q1_patterns(pages),
                q2_duplicates(pages),
                q3_errors(log),
                q4_links(pages),
                q5_boilerplate(pages, config.cache_dir),
                q6_words(pages, config.cache_dir),
                q7_tfidf(pages, config.cache_dir, stats),
                q8_politeness(log, stats),
            ]
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
