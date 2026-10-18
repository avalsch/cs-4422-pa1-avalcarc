from canonicalize import canonicalize


def test_lowercases_scheme_and_host():
    assert (
        canonicalize("HTTP://WWW.Kennesaw.EDU/About") == "http://www.kennesaw.edu/About"
    )


def test_drops_http_default_port():
    assert canonicalize("http://kennesaw.edu:80/x") == "http://kennesaw.edu/x"


def test_drops_https_default_port():
    assert canonicalize("https://kennesaw.edu:443/x") == "https://kennesaw.edu/x"


def test_keeps_nondefault_port():
    assert canonicalize("http://kennesaw.edu:8080/x") == "http://kennesaw.edu:8080/x"


def test_drops_fragment():
    assert canonicalize("http://kennesaw.edu/x#section") == "http://kennesaw.edu/x"


def test_percent_encoding_roundtrip():
    assert canonicalize("http://kennesaw.edu/a%20b") == "http://kennesaw.edu/a%20b"


def test_resolves_dot_segments():
    assert canonicalize("http://kennesaw.edu/a/../b/./c") == "http://kennesaw.edu/b/c"


def test_resolves_relative_with_base():
    assert (
        canonicalize("../about", base="http://kennesaw.edu/dept/page.html")
        == "http://kennesaw.edu/about"
    )


def test_trailing_slash_stripped():
    assert canonicalize("http://kennesaw.edu/about/") == "http://kennesaw.edu/about"


def test_root_path_kept():
    assert canonicalize("http://kennesaw.edu/") == "http://kennesaw.edu/"


def test_drops_tracking_param():
    assert (
        canonicalize("http://kennesaw.edu/x?utm_source=news&id=5")
        == "http://kennesaw.edu/x?id=5"
    )


def test_rejects_foreign_host():
    assert canonicalize("http://example.com/x") is None
    assert canonicalize("http://notkennesaw.edu/x") is None


def test_accepts_subdomain():
    assert canonicalize("http://cs.kennesaw.edu/x") == "http://cs.kennesaw.edu/x"


def test_rejects_non_http_schemes():
    assert canonicalize("mailto:foo@bar.com") is None
    assert canonicalize("javascript:void(0)") is None


def test_invalid_port_returns_none():
    assert canonicalize("http://kennesaw.edu:abc/x") is None


def test_preserves_user_info_when_dropping_default_port():
    assert (
        canonicalize("http://user:pass@kennesaw.edu:80")
        == "http://user:pass@kennesaw.edu/"
    )


def test_empty():
    assert canonicalize("") is None
