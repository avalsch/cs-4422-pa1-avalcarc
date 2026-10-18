from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from w3lib.url import canonicalize_url

TRACKING_PARAMS = [
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
]

URL_SCHEME_DEFAULT_PORT = {"http": 80, "https": 443}

ALLOWED_HOST = "kennesaw.edu"


def canonicalize(url: str, base: str | None = None) -> str | None:
    # join to base if base is provided
    if base:
        url = urljoin(base, url)

    # mechanical normalization
    try:
        canon = canonicalize_url(url, keep_fragments=False)
    except:  # noqa: E722
        return None

    parts = urlsplit(canon)

    scheme, host, port, netloc, path, query = (
        parts.scheme.lower(),
        parts.hostname,
        parts.port,
        parts.netloc,
        parts.path,
        parts.query,
    )

    # drop non-HTTP urls
    if scheme not in ("http", "https"):
        return None

    # drop hosts that are out of scope
    if not host or not (host == ALLOWED_HOST or host.endswith(f".{ALLOWED_HOST}")):
        return None

    # drop schema-default ports
    if port == URL_SCHEME_DEFAULT_PORT[scheme]:
        netloc = netloc.removesuffix(f":{port}")

    # drop trailing slash (canonicalize_url handles the rest)
    if path != "/":
        path = path.rstrip("/")

    # drop tracking parameters
    query = urlencode(
        list(
            filter(
                lambda p: p[0].lower() not in TRACKING_PARAMS,
                parse_qsl(query, keep_blank_values=True),
            )
        ),
    )

    return urlunsplit((scheme, netloc, path, query, ""))
