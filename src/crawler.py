import sys
import time
from argparse import ArgumentParser
from pathlib import Path

from canonicalize import canonicalize
from crawl_config import (
    DEFAULT_BUDGET,
    DEFAULT_DELAY,
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_REDIRECT,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    Config,
)
from schema import Stats
from storage import write_stats


def crawl(_config, _pages_f, _log_f, _stats, _stats_path, _start_time): ...


def parse_args() -> Config:
    parser = ArgumentParser(description="")  # TODO: description

    parser.add_argument(
        "seeds",
        nargs="+",
        help="One or more seed URLs (within kennesaw.edu).",
    )

    parser.add_argument(
        "-b",
        "--budget",
        type=int,
        default=DEFAULT_BUDGET,
        help="max number of pages to fetch",
    )

    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help="min seconds between requests to the same host",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("artifacts"),
        help="directory for pages.jsonl, crawl.log, stats.json",
    )

    parser.add_argument(
        "-u",
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="User-Agent header for every request",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="per-request timeout in seconds",
    )

    parser.add_argument(
        "-c",
        "--checkpoint",
        type=Path,
        default=None,
        help="path to checkpoint file for resume support",
    )

    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help="max response size (in bytes)",
    )

    parser.add_argument(
        "--max-redirects",
        type=int,
        default=DEFAULT_MAX_REDIRECT,
        help="max redirect hops per request",
    )

    parser.add_argument(
        "--random-seed",
        type=int,
        default=None,
        help="seed for random sampling",
    )

    args = parser.parse_args()

    if args.budget < 1:
        parser.error("--budget must be >= 1")

    if args.delay < 0:
        parser.error("--delay must be >= 0")

    seeds = [
        canonicalize(s) or parser.error(f"seed URL out of scope or invalid: {s}")
        for s in args.seeds
    ]

    return Config(
        seeds=seeds,
        budget=args.budget,
        delay=args.delay,
        output_dir=args.output,
        user_agent=args.user_agent,
        max_bytes=args.max_bytes,
        timeout=args.timeout,
        checkpoint_path=args.checkpoint,
        random_seed=args.random_seed,
    )


def main() -> int:
    config = parse_args()

    config.output_dir.mkdir(parents=True, exist_ok=True)

    pages_path = config.output_dir / "pages.jsonl"
    log_path = config.output_dir / "crawl.log"
    stats_path = config.output_dir / "stats.json"

    with (
        open(pages_path, "w", buffering=1, encoding="utf-8", newline="\n") as pages,
        open(log_path, "w", buffering=1, encoding="utf-8", newline="\n") as log,
    ):
        start_time = time.time()

        stats: Stats = {
            "pages_fetched": 0,
            "urls_seen": 0,
            "wall_clock_seconds": 0.0,
            "robots_skips": 0,
            "random_seed": config.random_seed,
        }

        try:
            crawl(config, pages, log, stats, stats_path, start_time)
        except KeyboardInterrupt:
            print("\nInterrupted - flushing and writing stats.", file=sys.stderr)
        finally:
            stats["wall_clock_seconds"] = time.time() - start_time
            write_stats(stats_path, stats)
            print(
                f"Done: {stats['pages_fetched']} pages in {stats['wall_clock_seconds']:.1f}s",
                file=sys.stderr,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
