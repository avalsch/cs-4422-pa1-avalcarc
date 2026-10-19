import hashlib
from typing import Literal, Protocol, TypedDict

Event = Literal["enqueue", "fetch", "skip", "error"]


class LogEntry(TypedDict):
    ts: str
    event: Event
    url: str
    failure_reason: str | None
    status: int | None
    target: str | None


class Stats(TypedDict):
    pages_fetched: int
    urls_seen: int
    wall_clock_seconds: float
    robots_skips: int
    random_seed: int | None
    delay: float


class PageRecord(TypedDict):
    url_canonical: str
    status: int
    fetched_at: str
    title: str
    text: str
    word_count: int
    out_links: list[str]
    content_hash: str
    canonical_link: str | None


class ParsedPage(Protocol):
    @property
    def title(self) -> str: ...

    @property
    def text(self) -> str: ...

    @property
    def out_links(self) -> list[str]: ...

    @property
    def canonical_link(self) -> str | None: ...


def make_page_record(
    url: str, status: int, result: ParsedPage, fetched_at: str
) -> PageRecord:
    return {
        "url_canonical": url,
        "status": status,
        "fetched_at": fetched_at,
        "title": result.title,
        "text": result.text,
        "word_count": len(result.text.split()),
        "out_links": list(result.out_links),
        "content_hash": content_hash(result.text),
        "canonical_link": result.canonical_link,
    }


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    return " ".join(text.split()).lower()
