import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import requests

from canonicalize import canonicalize
from crawl_config import Config

ERR_HTTP = "http_error"
ERR_CONN = "connection_error"
ERR_TIMEOUT = "timeout"
ERR_TLS = "tls_error"
ERR_REDIRECT_LOOP = "redirect_loop"
ERR_TOO_MANY_REDIRECTS = "too_many_redirects"
ERR_OVERSIZED = "oversized"
ERR_WRONG_CONTENT_TYPE = "wrong_content_type"
ERR_OUT_OF_SCOPE = "out_of_scope"
ERR_ROBOTS = "robots_blocked"

RETRY_STATUSES = frozenset({429, 503})
MAX_RETRIES = 1
DEFAULT_RETRY_DELAY = 10.0
MAX_RETRY_DELAY = 60.0
CHUNK_SIZE = 8192


@dataclass(frozen=True)
class FetchSuccess:
    status: int
    html: str
    final_url: str


@dataclass(frozen=True)
class FetchError:
    error: str
    status: int | None = None
    url: str | None = None
    target: str | None = None


def fetch(
    url: str,
    config: Config,
    session: requests.Session | None = None,
    permit: Callable[[str], bool] | None = None,
    wait: Callable[[str], None] | None = None,
) -> FetchSuccess | FetchError:
    session = session or requests.Session()

    current = canonicalize(url)

    if current is None:
        return FetchError(ERR_OUT_OF_SCOPE, url=url)

    visited = {current}
    hops = 0
    retries = 0

    while True:
        if wait is not None:
            wait(current)

        response = _request(current, config, session)

        if isinstance(response, FetchError):
            return response

        with response as resp:
            status = resp.status_code
            location = resp.headers.get("Location")

            if 300 <= status < 400 and location:
                if hops >= config.max_redirects:
                    return FetchError(ERR_TOO_MANY_REDIRECTS, status, current)

                target = canonicalize(location, base=current)

                if target is None:
                    return FetchError(
                        ERR_OUT_OF_SCOPE, status, current, target=location
                    )

                if target in visited:
                    return FetchError(ERR_REDIRECT_LOOP, status, current)

                if permit and not permit(target):
                    return FetchError(ERR_ROBOTS, status, current)

                visited.add(target)
                current = target
                hops += 1
                retries = 0
                continue

            if status in RETRY_STATUSES and retries < MAX_RETRIES:
                delay = _retry_delay(resp)
                retries += 1
                resp.close()
                time.sleep(delay)
                continue

            return _read_body(resp, current, status, config)


def _request(
    url: str, config: Config, session: requests.Session
) -> requests.Response | FetchError:
    try:
        return session.get(
            url,
            headers={"User-Agent": config.user_agent},
            timeout=config.timeout,
            stream=True,
            allow_redirects=False,
        )
    except requests.exceptions.Timeout:
        return FetchError(ERR_TIMEOUT, url=url)
    except requests.exceptions.SSLError:
        return FetchError(ERR_TLS, url=url)
    except requests.exceptions.ConnectionError, requests.exceptions.RequestException:
        return FetchError(ERR_CONN, url=url)


def _read_body(
    resp: requests.Response, url: str, status: int, config: Config
) -> FetchSuccess | FetchError:
    if not 200 <= status < 300:
        return FetchError(ERR_HTTP, status, url)

    if not _is_html(resp.headers.get("Content-Type")):
        return FetchError(ERR_WRONG_CONTENT_TYPE, status, url)

    declared = resp.headers.get("Content-Length")

    if declared and declared.isdigit() and int(declared) > config.max_bytes:
        return FetchError(ERR_OVERSIZED, status, url)

    try:
        data, oversized = _read_capped(resp, config.max_bytes)
    except requests.exceptions.RequestException:
        return FetchError(ERR_CONN, status, url)

    if oversized:
        return FetchError(ERR_OVERSIZED, status, url)

    return FetchSuccess(status, _decode(data, resp), url)


def _read_capped(resp: requests.Response, max_bytes: int) -> tuple[bytes, bool]:
    buf = bytearray()

    for chunk in resp.iter_content(CHUNK_SIZE):
        if not chunk:
            continue
        if len(buf) + len(chunk) > max_bytes:
            return bytes(buf), True

        buf.extend(chunk)

    return bytes(buf), False


def _decode(data: bytes, resp: requests.Response) -> str:
    declared = resp.encoding

    if declared and declared.lower() != "iso-8859-1":
        try:
            return data.decode(declared, errors="replace")
        except LookupError:
            pass

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("iso-8859-1", errors="replace")


def _is_html(content_type: str | None) -> bool:
    if not content_type:
        return False

    content_type = content_type.lower()

    return "text/html" in content_type or "application/xhtml" in content_type


def _retry_delay(resp: requests.Response) -> float:
    value = resp.headers.get("Retry-After")

    if value:
        try:
            return min(max(0.0, float(value)), MAX_RETRY_DELAY)
        except ValueError:
            pass
        try:
            when = parsedate_to_datetime(value)

            return min(
                max(0.0, (when - datetime.now(UTC)).total_seconds()),
                MAX_RETRY_DELAY,
            )
        except TypeError, ValueError:
            pass

    return DEFAULT_RETRY_DELAY
