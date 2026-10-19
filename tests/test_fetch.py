import io
from pathlib import Path

import pytest
import requests
from requests.structures import CaseInsensitiveDict

from crawl_config import Config
from fetch import (
    ERR_CONN,
    ERR_HTTP,
    ERR_OUT_OF_SCOPE,
    ERR_OVERSIZED,
    ERR_REDIRECT_LOOP,
    ERR_ROBOTS,
    ERR_TIMEOUT,
    ERR_TLS,
    ERR_TOO_MANY_REDIRECTS,
    ERR_WRONG_CONTENT_TYPE,
    FetchError,
    FetchSuccess,
)
from fetch import (
    fetch as _fetch,
)


def fetch(url, config, session, permit=None, wait=None) -> FetchSuccess | FetchError:
    return _fetch(url, config, session, permit, wait)


URL = "http://kennesaw.edu/"


def make_response(status=200, headers=None, body=b"", encoding="utf-8"):
    r = requests.Response()
    r.status_code = status
    r.headers = CaseInsensitiveDict(headers or {})
    r.raw = io.BytesIO(body)
    r.encoding = encoding
    r.url = URL
    return r


class FakeSession:
    def __init__(self, *items):
        self._items = list(items)
        self.calls = []

    def get(self, url, **_kwargs):
        self.calls.append(url)

        item = self._items.pop(0)

        if isinstance(item, Exception):
            raise item

        item.url = url

        return item


def config(**overrides):
    opts = {
        "seeds": [URL],
        "budget": 1,
        "delay": 0.0,
        "output_dir": Path("out"),
        "max_bytes": 1024,
        "max_redirects": 5,
    }
    opts.update(overrides)

    return Config(**opts)  # ty: ignore[invalid-argument-type]


def redirect(to, status=301):
    return make_response(status, {"Location": to})


def html(body=b"<html><body>hi</body></html>"):
    return make_response(200, {"Content-Type": "text/html; charset=utf-8"}, body)


def test_success():
    session = FakeSession(html(b"<html>ok</html>"))
    result = fetch(URL, config(), session)

    assert result == FetchSuccess(200, "<html>ok</html>", URL)
    assert session.calls == [URL]


def test_empty_body_is_success():
    result = fetch(URL, config(), FakeSession(html(b"")))

    assert isinstance(result, FetchSuccess) and result.html == ""


def test_xhtml_content_type_allowed():
    resp = make_response(200, {"Content-Type": "application/xhtml+xml"}, b"<html/>")

    assert isinstance(fetch(URL, config(), FakeSession(resp)), FetchSuccess)


def test_non_2xx_is_http_error():
    resp = make_response(404, {"Content-Type": "text/html"}, b"nope")
    result = fetch(URL, config(), FakeSession(resp))

    assert result == FetchError(ERR_HTTP, status=404, url=URL)


def test_wrong_content_type():
    resp = make_response(200, {"Content-Type": "application/pdf"}, b"%PDF-1.4")
    result = fetch(URL, config(), FakeSession(resp))

    assert isinstance(result, FetchError)
    assert result.error == ERR_WRONG_CONTENT_TYPE
    assert result.status == 200


def test_missing_content_type_rejected():
    result = fetch(URL, config(), FakeSession(make_response(200, {}, b"hello")))

    assert isinstance(result, FetchError)
    assert result.error == ERR_WRONG_CONTENT_TYPE


def test_oversized_by_content_length():
    resp = make_response(
        200, {"Content-Type": "text/html", "Content-Length": "999999"}, b"<html>"
    )
    result = fetch(URL, config(max_bytes=1024), FakeSession(resp))

    assert isinstance(result, FetchError)
    assert result.error == ERR_OVERSIZED


def test_oversized_by_bytes_read():
    resp = make_response(200, {"Content-Type": "text/html"}, b"<html>" + b"x" * 5000)
    result = fetch(URL, config(max_bytes=1024), FakeSession(resp))

    assert isinstance(result, FetchError)
    assert result.error == ERR_OVERSIZED


def test_redirect_followed_and_canonicalized():
    session = FakeSession(redirect("/b/?utm_source=x"), html(b"<html>b</html>"))
    result = fetch(URL, config(), session)

    assert isinstance(result, FetchSuccess)
    assert result.final_url == "http://kennesaw.edu/b/"
    assert session.calls == [URL, "http://kennesaw.edu/b/"]


def test_redirect_loop_detected():
    result = fetch(URL, config(), FakeSession(redirect(URL)))

    assert isinstance(result, FetchError)
    assert result.error == ERR_REDIRECT_LOOP


def test_too_many_redirects():
    session = FakeSession(redirect("/a"), redirect("/b"), html())
    result = fetch(URL, config(max_redirects=1), session)

    assert isinstance(result, FetchError)
    assert result.error == ERR_TOO_MANY_REDIRECTS
    assert session.calls == [URL, "http://kennesaw.edu/a"]


def test_redirect_out_of_scope():
    result = fetch(URL, config(), FakeSession(redirect("http://example.com/x")))

    assert isinstance(result, FetchError)
    assert result.error == ERR_OUT_OF_SCOPE
    assert result.target == "http://example.com/x"


def test_redirect_3xx_without_location():
    result = fetch(URL, config(), FakeSession(make_response(304)))

    assert isinstance(result, FetchError)
    assert result.error == ERR_HTTP


def test_permit_callback_gates_hops():
    seen = []
    session = FakeSession(redirect("/blocked"), html())
    result = fetch(URL, config(), session, permit=lambda t: seen.append(t) or False)

    assert isinstance(result, FetchError)
    assert result.error == ERR_ROBOTS
    assert seen == ["http://kennesaw.edu/blocked"]
    assert session.calls == [URL]


def test_wait_called_before_each_request_including_hops():
    waits = []
    session = FakeSession(redirect("/a"), redirect("/b"), html())
    fetch(URL, config(), session, wait=waits.append)

    assert waits == [URL, "http://kennesaw.edu/a", "http://kennesaw.edu/b"]
    assert session.calls == waits


def test_retries_once_on_503():
    throttled = make_response(503, {"Retry-After": "0"})
    session = FakeSession(throttled, html(b"<html>late</html>"))
    result = fetch(URL, config(), session)

    assert isinstance(result, FetchSuccess)
    assert session.calls == [URL, URL]


def test_gives_up_after_one_retry():
    a = make_response(503, {"Retry-After": "0"})
    b = make_response(503, {"Retry-After": "0"})
    result = fetch(URL, config(), FakeSession(a, b))
    assert result == FetchError(ERR_HTTP, status=503, url=URL)


@pytest.mark.parametrize(
    "exc, expected",
    [
        (requests.exceptions.Timeout, ERR_TIMEOUT),
        (requests.exceptions.ConnectTimeout, ERR_TIMEOUT),
        (requests.exceptions.ReadTimeout, ERR_TIMEOUT),
        (requests.exceptions.SSLError, ERR_TLS),
        (requests.exceptions.ConnectionError, ERR_CONN),
        (requests.exceptions.RequestException, ERR_CONN),
    ],
)
def test_transport_errors_are_mapped(exc, expected):
    result = fetch(URL, config(), FakeSession(exc()))

    assert isinstance(result, FetchError) and result.error == expected


class ExplodingRaw:
    def __init__(self):
        self._sent = False

    def read(self, _size=-1):
        if not self._sent:
            self._sent = True
            return b"<html>partial"
        raise requests.exceptions.ChunkedEncodingError("connection dropped")

    def close(self):
        pass


def test_disconnected_mid_body_does_not_raise():
    resp = html()
    resp.raw = ExplodingRaw()
    result = fetch(URL, config(), FakeSession(resp))

    assert isinstance(result, FetchError) and result.error == ERR_CONN


def test_seed_out_of_scope_short_circuits():
    session = FakeSession()
    result = fetch("http://example.com/", config(), session)

    assert isinstance(result, FetchError) and result.error == ERR_OUT_OF_SCOPE
    assert session.calls == []


def test_utf8_mislabled_as_latin1_decodes_as_utf8():
    body = "café — naïve".encode()
    resp = make_response(
        200, {"Content-Type": "text/html"}, body, encoding="iso-8859-1"
    )
    result = fetch(URL, config(), FakeSession(resp))

    assert isinstance(result, FetchSuccess) and result.html == "café — naïve"


def test_declared_charset_wins():
    resp = make_response(
        200,
        {"Content-Type": "text/html; charset=iso-8859-1"},
        "café".encode("iso-8859-1"),
        encoding="iso-8859-1",
    )
    result = fetch(URL, config(), FakeSession(resp))

    assert isinstance(result, FetchSuccess) and result.html == "café"


def test_unknown_charset_falls_back_to_utf8():
    resp = make_response(
        200, {"Content-Type": "text/html"}, "café".encode(), encoding="x-nonsense"
    )
    result = fetch(URL, config(), FakeSession(resp))

    assert isinstance(result, FetchSuccess) and result.html == "café"
