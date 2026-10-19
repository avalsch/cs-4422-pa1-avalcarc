import json
import sys
from argparse import ArgumentParser
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

DEFAULT_PAGES = Path("artifacts/pages.jsonl")
DEFAULT_LOG = Path("artifacts/crawl.log")
DEFAULT_STATS = Path("artifacts/stats.json")


@dataclass
class AnalyzeConfig:
    pages: Path = DEFAULT_PAGES
    log: Path = DEFAULT_LOG
    stats: Path = DEFAULT_STATS


def parse_args(argv: list[str] | None = None) -> AnalyzeConfig:
    parser = ArgumentParser(description="")  # TODO: description

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

    args = parser.parse_args(argv)

    return AnalyzeConfig(pages=args.pages, log=args.log, stats=args.stats)


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
            gaps[host] = min((b - a).total_seconds() for a, b in zip(times, times[1:]))

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
            f"**Q8.a delay compliance.** {len(gaps)} hosts, minimum gap {min_gap:.2f} s, "
            f"{below} below the {delay:.2f} s floor.",
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
            f"**Q8.c request rate.** {pages} pages / {wall:.1f} s = {pages / wall:.2f} pages/s; "
            f"{requests} requests / {wall:.1f} s = {requests / wall:.2f} requests/s.",
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
                q3_errors(log),
                q8_politeness(log, stats),
            ]
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
