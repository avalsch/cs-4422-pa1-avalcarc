import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag
from bs4.element import PreformattedString

from canonicalize import canonicalize, is_in_scope

_REFRESH_EQUIV = re.compile(r"^\s*refresh\s*$", re.IGNORECASE)
_REFRESH_URL = re.compile(r"(?:^|[;\s])url\s*=\s*([^;]+)", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")

_SKIP_TEXT_TAGS = frozenset({"head", "title", "script", "style", "template"})

# tags delimitting blocks of text.
_BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "ul",
    }
)


@dataclass(frozen=True)
class ParseResult:
    title: str
    text: str
    out_links: list[str]
    canonical_link: str | None


def parse(html: str, base_url: str) -> ParseResult:
    soup = BeautifulSoup(html, "lxml")
    effective_base = _effective_base(soup, base_url)

    return ParseResult(
        title=soup.title.get_text(strip=True) if soup.title else "",
        text=_text(soup),
        out_links=_out_links(soup, effective_base),
        canonical_link=_canonical_link(soup, effective_base),
    )


def _effective_base(soup: BeautifulSoup, base_url: str) -> str:
    base_tag = soup.head.find("base", href=True) if soup.head else None
    if not base_tag:
        return base_url

    candidate = urljoin(base_url, _attr(base_tag, "href").strip())
    return candidate if is_in_scope(candidate) else base_url


def _text(soup: BeautifulSoup) -> str:
    parts: list[str] = []

    def walk(node: Tag) -> None:
        for child in node.children:
            if isinstance(child, Tag):
                if child.name in _SKIP_TEXT_TAGS:
                    continue

                block = child.name in _BLOCK_TAGS
                parts.append(" " if block else "")
                walk(child)
                parts.append(" " if block else "")
            elif isinstance(child, NavigableString) and not isinstance(
                child, PreformattedString
            ):
                parts.append(str(child))

    walk(soup.body or soup)
    return _WHITESPACE.sub(" ", "".join(parts)).strip()


def _out_links(soup: BeautifulSoup, base: str) -> list[str]:
    candidates = [_attr(a, "href") for a in soup.find_all("a", href=True)]
    candidates.extend(
        target
        for meta in soup.find_all("meta", attrs={"http-equiv": _REFRESH_EQUIV})
        if (target := _refresh_target(_attr(meta, "content")))
    )

    resolved = (_resolve(candidate, base) for candidate in candidates if candidate)
    return list(dict.fromkeys(link for link in resolved if link))


def _canonical_link(soup: BeautifulSoup, base: str) -> str | None:
    for link in soup.find_all("link", href=True):
        if "canonical" in _rel_tokens(link):
            resolved = _resolve(_attr(link, "href"), base)
            if resolved is not None:
                return resolved
    return None


def _rel_tokens(tag: Tag) -> set[str]:
    return {token.lower() for token in tag.get("rel") or []}


def _refresh_target(content: str) -> str | None:
    match = _REFRESH_URL.search(content)
    return match.group(1).strip().strip("\"'").strip() if match else None


def _resolve(raw: str, base: str) -> str | None:
    href = _WHITESPACE.sub("", raw)
    if not href or href.startswith("#"):
        return None
    return canonicalize(urljoin(base, href))


def _attr(tag: Tag, name: str) -> str:
    value = tag.get(name)
    return value if isinstance(value, str) else ""
