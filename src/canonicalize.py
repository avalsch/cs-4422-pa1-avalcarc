from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from w3lib.url import canonicalize_url

TRACKING_PARAMS = frozenset(
    [
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
    ]
)

URL_SCHEME_DEFAULT_PORT = {"http": 80, "https": 443}

ALLOWED_HOST = "kennesaw.edu"


def canonicalize(url: str, base: str | None = None) -> str | None:
    # join to base if base is provided
    if base:
        url = urljoin(base, url)

    # mechanical normalization
    try:
        canon = canonicalize_url(url, keep_fragments=False)
    except ValueError:
        return None

    parts = urlsplit(canon)

    scheme = parts.scheme.lower()
    host = parts.hostname
    port = parts.port
    netloc = parts.netloc
    path = parts.path
    query = parts.query

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
        [
            (k, v)
            for k, v in parse_qsl(query, keep_blank_values=True)
            if k.lower() not in TRACKING_PARAMS
        ]
    )

    return urlunsplit((scheme, netloc, path, query, ""))
