from html import escape

import pytest

from parse import ParseResult, parse

BASE = "http://kennesaw.edu/page.html"


def title(html: str, base: str = BASE) -> str:
    return parse(html, base).title


def text(html: str, base: str = BASE) -> str:
    return parse(html, base).text


def links(html: str, base: str = BASE) -> list[str]:
    return parse(html, base).out_links


def canonical(html: str, base: str = BASE) -> str | None:
    return parse(html, base).canonical_link


def test_empty_input_returns_empty_result():
    assert parse("", BASE) == ParseResult("", "", [], None)


def test_title_extracted():
    assert title("<title>Hello</title>") == "Hello"


def test_title_whitespace_stripped():
    assert title("<title>  Hello  </title>") == "Hello"


def test_title_entities_decoded():
    assert title("<title>Foo &amp; Bar</title>") == "Foo & Bar"


def test_title_tag_case_insensitive():
    assert title("<TITLE>Hello</TITLE>") == "Hello"


def test_missing_title_is_empty_string():
    assert title("<html><body>hi</body></html>") == ""


def test_empty_title_is_empty_string():
    assert title("<title></title>") == ""


def test_first_title_wins():
    assert title("<title>first</title><title>second</title>") == "first"


def test_text_joins_block_elements():
    assert text("<p>hello</p><p>world</p>") == "hello world"


def test_text_omits_script_and_style():
    assert text("<script>var x=1</script><style>p{}</style><p>real</p>") == "real"


def test_text_omits_comments():
    assert text("<p>visible<!-- secret --></p>") == "visible"


def test_text_empty_when_no_content():
    assert text("<html><body></body></html>") == ""


def test_text_excludes_head_and_title():
    assert text("<title>Hello</title><p>body</p>") == "body"


def test_text_does_not_split_words_at_inline_boundaries():
    assert text("<p>state<b>ment</b></p>") == "statement"


def test_text_collapses_internal_whitespace():
    assert text("<p>a   b\n\tc</p>") == "a b c"


def test_text_inserts_space_for_br():
    assert text("<div>a<br>b</div>") == "a b"


def test_text_separates_list_items():
    assert text("<ul><li>one</li><li>two</li></ul>") == "one two"


@pytest.mark.parametrize(
    "href, expected",
    [
        ("/a", "http://kennesaw.edu/a"),
        ("a", "http://kennesaw.edu/a"),
        ("../up", "http://kennesaw.edu/up"),
        ("//cs.kennesaw.edu/z", "http://cs.kennesaw.edu/z"),
        ("http://cs.kennesaw.edu/abs", "http://cs.kennesaw.edu/abs"),
        ("/a?utm_source=n&id=2", "http://kennesaw.edu/a?id=2"),
        ("http://kennesaw.edu:80/p", "http://kennesaw.edu/p"),
        ("/a?b=2#frag", "http://kennesaw.edu/a?b=2"),
    ],
)
def test_link_resolved_and_canonicalized(href, expected):
    assert links(f"<a href='{href}'>x</a>") == [expected]


@pytest.mark.parametrize(
    "href",
    [
        "",
        "mailto:a@b.com",
        "javascript:void(0)",
        "tel:+15551234",
        "ftp://kennesaw.edu/f",
        "http://example.com/x",
        "http://notkennesaw.edu/x",
    ],
)
def test_non_crawlable_links_dropped(href):
    assert links(f"<a href='{href}'>x</a>") == []


def test_anchor_without_href_ignored():
    assert links("<a name='x'>x</a>") == []


def test_fragment_link_does_not_stop_later_links():
    assert links("<a href='#top'>a</a><a href='/b'>b</a>") == ["http://kennesaw.edu/b"]


def test_query_only_link_resolves_against_page():
    assert links("<a href='?q=1'>x</a>") == ["http://kennesaw.edu/page.html?q=1"]


def test_uppercase_scheme_and_host_normalized_path_preserved():
    assert links("<a href='HTTP://CS.Kennesaw.EDU/P'>x</a>") == [
        "http://cs.kennesaw.edu/P"
    ]


def test_internal_whitespace_removed_from_href():
    assert links("<a href='/a\nb'>x</a>") == ["http://kennesaw.edu/ab"]


def test_duplicate_links_deduped_after_canonicalization():
    html = "<a href='/a'>1</a><a href='/a/'>2</a><a href='/a#f'>3</a>"
    assert links(html) == ["http://kennesaw.edu/a"]


def test_fragment_only_links_skipped():
    assert links("<a href='#top'>x</a>") == []


def test_links_preserve_document_order():
    html = "<a href='/b'>b</a><a href='/a'>a</a>"
    assert links(html) == ["http://kennesaw.edu/b", "http://kennesaw.edu/a"]


def test_no_links_returns_empty_list():
    assert links("<p>nothing here</p>") == []


def test_base_href_changes_link_resolution():
    html = "<base href='/sub/'><a href='x'>x</a>"
    assert links(html) == ["http://kennesaw.edu/sub/x"]


def test_relative_base_resolved_against_page():
    html = "<base href='sub/'><a href='x'>x</a>"
    assert links(html) == ["http://kennesaw.edu/sub/x"]


def test_absolute_base_to_subdomain():
    html = "<base href='http://cs.kennesaw.edu/d/'><a href='x'>x</a>"
    assert links(html) == ["http://cs.kennesaw.edu/d/x"]


def test_out_of_scope_base_ignored():
    html = "<base href='http://example.com/'><a href='x'>x</a>"
    assert links(html) == ["http://kennesaw.edu/x"]


def test_base_applies_to_relative_link_and_is_scope_checked():
    html = "<base href='/sub/'><a href='../x'>x</a><a href='http://example.com/y'>y</a>"
    assert links(html) == ["http://kennesaw.edu/x"]


def test_base_in_body_ignored():
    html = "<head></head><body><base href='/sub/'><a href='x'>x</a></body>"
    assert links(html) == ["http://kennesaw.edu/x"]


def test_empty_base_href_falls_back_to_page():
    html = "<base href=''><a href='x'>x</a>"
    assert links(html) == ["http://kennesaw.edu/x"]


def test_first_base_wins():
    html = "<base href='/a/'><base href='/b/'><a href='x'>x</a>"
    assert links(html) == ["http://kennesaw.edu/a/x"]


@pytest.mark.parametrize(
    "content, expected",
    [
        ("0; url=/target", "http://kennesaw.edu/target"),
        ("5; URL='/t2'", "http://kennesaw.edu/t2"),
        ("0;url=/t3", "http://kennesaw.edu/t3"),
        ("url=/t5", "http://kennesaw.edu/t5"),
        ("0; url=rel", "http://kennesaw.edu/rel"),
        ('0; url="/t6"', "http://kennesaw.edu/t6"),
        ('0; url=" /t7 "', "http://kennesaw.edu/t7"),
    ],
)
def test_meta_refresh_target(content, expected):
    html = f"""<meta http-equiv="refresh" content="{escape(content)}">"""
    assert links(html) == [expected]


@pytest.mark.parametrize("content", ["0; noturl=/x", "0; dataurl=/x"])
def test_meta_refresh_ignores_url_like_params(content):
    html = f"""<meta http-equiv="refresh" content="{escape(content)}">"""
    assert links(html) == []


def test_meta_refresh_without_content_ignored():
    assert links("<meta http-equiv='refresh'>") == []


def test_meta_refresh_empty_url_ignored():
    assert links("<meta http-equiv='refresh' content='0; url='>") == []


def test_meta_refresh_fragment_only_ignored():
    assert links("<meta http-equiv='refresh' content='0; url=#section'>") == []


def test_meta_refresh_http_equiv_case_insensitive():
    html = "<meta http-equiv='REFRESH' content='0; url=/t'>"
    assert links(html) == ["http://kennesaw.edu/t"]


def test_meta_refresh_without_url_ignored():
    assert links("<meta http-equiv='refresh' content='5'>") == []


def test_meta_refresh_stops_at_semicolon():
    html = "<meta http-equiv='refresh' content='0; url=/t4; x=1'>"
    assert links(html) == ["http://kennesaw.edu/t4"]


def test_meta_refresh_out_of_scope_dropped():
    html = "<meta http-equiv='refresh' content='0; url=http://example.com/x'>"
    assert links(html) == []


def test_meta_refresh_deduped_with_anchor():
    html = "<a href='/t'>a</a><meta http-equiv='refresh' content='0; url=/t'>"
    assert links(html) == ["http://kennesaw.edu/t"]


def test_canonical_link_extracted():
    assert canonical("<link rel='canonical' href='/c'>") == "http://kennesaw.edu/c"


def test_canonical_link_resolved_against_base():
    html = "<base href='/sub/'><link rel='canonical' href='c'>"
    assert canonical(html) == "http://kennesaw.edu/sub/c"


def test_canonical_rel_case_insensitive():
    assert canonical("<link rel='Canonical' href='/c'>") == "http://kennesaw.edu/c"


def test_canonical_rel_multi_token_matched():
    assert (
        canonical("<link rel='alternate canonical' href='/c'>")
        == "http://kennesaw.edu/c"
    )


def test_canonical_rel_partial_token_not_matched():
    assert canonical("<link rel='canonicalx' href='/c'>") is None


def test_missing_canonical_is_none():
    assert canonical("<p>no canonical here</p>") is None


def test_empty_canonical_href_is_none():
    assert canonical("<link rel='canonical' href=''>") is None


def test_canonical_without_href_is_none():
    assert canonical("<link rel='canonical'>") is None


def test_fragment_only_canonical_is_none():
    assert canonical("<link rel='canonical' href='#section'>") is None


def test_out_of_scope_canonical_dropped():
    assert canonical("<link rel='canonical' href='http://example.com/c'>") is None


def test_out_of_scope_canonical_skipped_for_later_valid_one():
    html = (
        "<link rel='canonical' href='http://example.com/c'>"
        "<link rel='canonical' href='/c'>"
    )
    assert canonical(html) == "http://kennesaw.edu/c"


def test_first_canonical_wins():
    html = "<link rel='canonical' href='/first'><link rel='canonical' href='/second'>"
    assert canonical(html) == "http://kennesaw.edu/first"


def test_full_page():
    html = """<html><head>
        <title>Dept Page</title>
        <base href="/dept/">
        <link rel="canonical" href="/dept/index">
        <meta http-equiv="refresh" content="0; url=/dept/new">
      </head><body>
        <p>Hello world</p>
        <a href="faculty">Faculty</a>
        <a href="http://example.com/x">External</a>
      </body></html>"""

    result = parse(html, "http://kennesaw.edu/")

    assert result.title == "Dept Page"
    assert result.canonical_link == "http://kennesaw.edu/dept/index"
    assert "Hello world" in result.text
    assert result.out_links == [
        "http://kennesaw.edu/dept/faculty",
        "http://kennesaw.edu/dept/new",
    ]


def test_malformed_html_still_parses():
    result = parse("unclosed<div>text<a href='/x'>link", BASE)
    assert "unclosed" in result.text
    assert "text" in result.text
    assert result.out_links == ["http://kennesaw.edu/x"]
