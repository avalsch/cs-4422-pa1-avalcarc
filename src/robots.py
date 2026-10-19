from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

import requests
from protego import Protego

from crawl_config import Config

ROBOTS_PATH = "/robots.txt"
ROBOTS_MAX_BYTES = 512 * 1024
CHUNK_SIZE = 8192
MAX_CRAWL_DELAY = 60.0
ROBOTS_UNREACHABLE = "robots_unreachable"

_ALLOW_ALL_RULES = "User-agent: *\nAllow: /\n"
_DISALLOW_ALL_RULES = "User-agent: *\nDisallow: /\n"


class RobotsPolicy(Protocol):
    def can_fetch(self, url: str) -> bool: ...


@dataclass(frozen=True)
class RobotsRules:
    parser: Protego
    user_agent: str
    crawl_delay: float | None = None

    def can_fetch(self, url: str) -> bool:
        return self.parser.can_fetch(url, self.user_agent)


def _allow_all(user_agent: str) -> RobotsRules:
    return RobotsRules(Protego.parse(_ALLOW_ALL_RULES), user_agent)


def _disallow_all(user_agent: str) -> RobotsRules:
    return RobotsRules(Protego.parse(_DISALLOW_ALL_RULES), user_agent)


def _parse(text: str, user_agent: str) -> RobotsRules:
    try:
        parser = Protego.parse(text)
        delay = parser.crawl_delay(user_agent)
    except Exception:  # noqa: BLE001
        return _disallow_all(user_agent)

    if delay is not None:
        delay = min(delay, MAX_CRAWL_DELAY)

    return RobotsRules(parser, user_agent, delay)


class RobotsCache:
    def __init__(
        self,
        config: Config,
        session: requests.Session,
        wait: Callable[[str], None] | None = None,
        delays: dict[str, float] | None = None,
        on_error: Callable[[str, int | None], None] | None = None,
    ) -> None:
        self._config = config
        self._session = session
        self._wait = wait
        self._delays = delays if delays is not None else {}
        self._on_error = on_error
        self._rules: dict[str, RobotsRules] = {}

    def rules_for(self, url: str) -> RobotsRules:
        origin = _origin(url)
        cached = self._rules.get(origin)

        if cached is not None:
            return cached

        rules = self._fetch(origin)
        self._rules[origin] = rules

        if rules.crawl_delay is not None:
            self._delays[urlsplit(url).hostname or ""] = rules.crawl_delay

        return rules

    def can_fetch(self, url: str) -> bool:
        return self.rules_for(url).can_fetch(url)

    def _fetch(self, origin: str) -> RobotsRules:
        url = origin + ROBOTS_PATH

        if self._wait is not None:
            self._wait(url)

        try:
            with self._session.get(
                url,
                headers={"User-Agent": self._config.user_agent},
                timeout=self._config.timeout,
                stream=True,
                allow_redirects=True,
            ) as resp:
                status = resp.status_code

                if 200 <= status < 300:
                    return _parse(_read_text(resp), self._config.user_agent)

                if status == 429 or 500 <= status < 600:
                    self._report(url, status)
                    return _disallow_all(self._config.user_agent)

                return _allow_all(self._config.user_agent)
        except requests.exceptions.RequestException:
            self._report(url, None)
            return _disallow_all(self._config.user_agent)

    def _report(self, url: str, status: int | None) -> None:
        if self._on_error is not None:
            self._on_error(url, status)


def _origin(url: str) -> str:
    parts = urlsplit(url)

    return f"{parts.scheme}://{parts.netloc}"


def _read_text(resp: requests.Response) -> str:
    buf = bytearray()

    for chunk in resp.iter_content(CHUNK_SIZE):
        if not chunk:
            continue

        buf.extend(chunk)

        if len(buf) >= ROBOTS_MAX_BYTES:
            del buf[ROBOTS_MAX_BYTES:]
            break

    return buf.decode("utf-8", errors="replace")
