import json
import sys
from argparse import ArgumentParser
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
            ]
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
