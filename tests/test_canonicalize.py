from canonicalize import canonicalize


def test_empty():
    assert canonicalize("") is None


def test_rejects_non_http_schemes():
    assert canonicalize("mailto:foo@bar.com") is None
    assert canonicalize("javascript:void(0)") is None


def test_protocol_relative_without_base_rejected():
    assert canonicalize("//kennesaw.edu/x") is None


def test_rejects_foreign_host():
    assert canonicalize("http://example.com/x") is None
    assert canonicalize("http://notkennesaw.edu/x") is None


def test_accepts_subdomain():
    assert canonicalize("http://cs.kennesaw.edu/x") == "http://cs.kennesaw.edu/x"


def test_foreign_host_rejected_as_substring():
    assert canonicalize("http://example.com/x") is None
    assert canonicalize("http://notkennesaw.edu/x") is None
    assert canonicalize("http://kennesaw.edu.not.co") is None


def test_lowercases_scheme_and_host():
    assert (
        canonicalize("HTTP://WWW.Kennesaw.EDU/About") == "http://www.kennesaw.edu/About"
    )


def test_drops_default_port():
    assert canonicalize("http://kennesaw.edu:80/x") == "http://kennesaw.edu/x"
    assert canonicalize("https://kennesaw.edu:443/x") == "https://kennesaw.edu/x"


def test_keeps_nondefault_port():
    assert canonicalize("http://kennesaw.edu:8080/x") == "http://kennesaw.edu:8080/x"
    assert canonicalize("https://kennesaw.edu:80/x") == "https://kennesaw.edu:80/x"


def test_invalid_port_returns_none():
    assert canonicalize("http://kennesaw.edu:abc/x") is None


def test_preserves_user_info_when_dropping_default_port():
    assert (
        canonicalize("http://user:pass@kennesaw.edu:80")
        == "http://user:pass@kennesaw.edu/"
    )


def test_default_port_dropped_https_with_userinfo():
    assert (
        canonicalize("https://user:pass@kennesaw.edu:443/")
        == "https://user:pass@kennesaw.edu/"
    )


def test_resolves_dot_segments():
    assert canonicalize("http://kennesaw.edu/a/../b/./c") == "http://kennesaw.edu/b/c"


def test_trailing_slash_stripped():
    assert canonicalize("http://kennesaw.edu/about/") == "http://kennesaw.edu/about"


def test_root_path_kept():
    assert canonicalize("http://kennesaw.edu/") == "http://kennesaw.edu/"


def test_no_path_defaults_to_root():
    assert canonicalize("http://kennesaw.edu") == "http://kennesaw.edu/"


def test_resolves_relative_with_base():
    assert (
        canonicalize("../about", base="http://kennesaw.edu/dept/page.html")
        == "http://kennesaw.edu/about"
    )
    assert (
        canonicalize("../about", base="http://cs.kennesaw.edu/dept/page.html")
        == "http://cs.kennesaw.edu/about"
    )


def test_drops_fragment():
    assert canonicalize("http://kennesaw.edu/x#section") == "http://kennesaw.edu/x"


def test_fragment_dropped_with_query():
    assert canonicalize("http://kennesaw.edu/x?a=1#fra") == "http://kennesaw.edu/x?a=1"


def test_drops_tracking_param():
    assert (
        canonicalize("http://kennesaw.edu/x?utm_source=news&id=5")
        == "http://kennesaw.edu/x?id=5"
    )
    assert (
        canonicalize("http://kennesaw.edu/x?gclid=abc&id=5")
        == "http://kennesaw.edu/x?id=5"
    )
    assert canonicalize("http://kennesaw.edu/x?fbclid=abc") == "http://kennesaw.edu/x"
    assert (
        canonicalize("http://kennesaw.edu/x?utm_source=news") == "http://kennesaw.edu/x"
    )


def test_tracking_param_case_insensitive_key():
    assert (
        canonicalize("http://kennesaw.edu/x?UTM_Source=news&id=5")
        == "http://kennesaw.edu/x?id=5"
    )


def test_blank_query_value_preserved():
    assert (
        canonicalize("http://kennesaw.edu/x?empty=&other=2")
        == "http://kennesaw.edu/x?empty=&other=2"
    )


def test_duplicate_query_params_preserved():
    assert (
        canonicalize("http://kennesaw.edu/x?id=1&id=2")
        == "http://kennesaw.edu/x?id=1&id=2"
    )


def test_percent_encoding_roundtrip():
    assert canonicalize("http://kennesaw.edu/a%20b") == "http://kennesaw.edu/a%20b"


def test_percent_encoded_reserved_char_preserved():
    assert canonicalize("http://kennesaw.edu/a%2Fb") == "http://kennesaw.edu/a%2Fb"


def test_percent_encoding_hex_normalized_upper():
    assert canonicalize("http://kennesaw.edu/a%2fb") == "http://kennesaw.edu/a%2Fb"
