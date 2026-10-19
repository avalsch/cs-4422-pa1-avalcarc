# CS 4422 PA1: Two-Stage Web Crawler

A from-scratch crawler for `kennesaw.edu` and its subdomains (stage one), plus an analysis of the resulting corpus (stage two).

Stage one (`src/crawler.py`) writes `artifacts/pages.jsonl`, `artifacts/crawl.log` and `artifacts/stats.json`, and caches the raw HTML in `cache/`. Stage two (`src/analyze.py`) reads those and produces the numbers behind `docs/analysis.md`.

## Team

Solo project.

- Adrian Valcarcel-Schott — netid `avalcarc` — GitHub `@avalsch`

All of it: crawler, analysis, and write-up.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)

```sh
uv sync
```

Pinned versions are in `requirements.txt`.

## Running

### Stage one: crawl

```sh
uv run src/crawler.py       \
  -b 500                    \
  -d 1.0                    \
  -t 10                     \
  --random-seed 42          \
  --cache-dir cache         \
  -o artifacts              \
  https://www.kennesaw.edu/ \
  https://ccse.kennesaw.edu/
```

- Seeds: `https://www.kennesaw.edu/`, `https://ccse.kennesaw.edu/`
- Budget: 500 pages
- Wall-clock runtime: 1011.5 s (0.49 pages/s; 0.90 HTTP requests/s)

Flag notes:

- `-d 1.0` is the per-host delay floor.
- `-t 10` is the request timeout, lowered from the 30 s default: ~50 dead registration/SSO subdomains otherwise spend 30 s each on an unreachable `robots.txt`.
- `--random-seed 42` seeds Q7's page sampling, so the sample is reproducible from `stats.json`.

### Stage two: analysis

```sh
uv run src/analyze.py      \
  -p artifacts/pages.jsonl \
  -l artifacts/crawl.log   \
  -s artifacts/stats.json  \
  --cache-dir cache
```

This prints the Q1–Q8 numbers to stdout. In `docs/analysis.md` those numbers live in the appendix, with the written answers above.

## Artifacts

| Path | Committed | What it is |
| --- | --- | --- |
| `artifacts/pages.jsonl` | no | the corpus: one JSON record per fetched page |
| `artifacts/crawl.log` | yes | one JSON decision per URL considered |
| `artifacts/stats.json` | yes | crawl summary counters |
| `cache/` | no | raw HTML, for stage-two boilerplate removal |

`pages.jsonl` and `cache/` are gitignored.

## Architecture

| File | Role |
| --- | --- |
| `src/crawler.py` | stage-one CLI |
| `src/crawl.py` | crawl loop: frontier, per-host politeness, dedupe, logging |
| `src/canonicalize.py` | URL normalization and `kennesaw.edu` scope check |
| `src/fetch.py` | HTTP transport: retries, manual redirects, byte cap, error taxonomy |
| `src/robots.py` | fetch/cache/enforce `robots.txt`; honor `Crawl-delay` |
| `src/parse.py` | HTML → title, raw text, links, `<link rel="canonical">` |
| `src/crawl_config.py` | stage-one configuration |
| `src/schema.py` | record, stats and log types |
| `src/storage.py` | pages/log/stats writers and the raw-HTML cache |
| `src/analyze.py` | stage-two CLI and the Q1–Q8 computations |

### URL policy

- Query parameters are kept, except the tracking parameters `utm_*`, `gclid` and `fbclid`, which are dropped; the rest are sorted (`w3lib`).
- Trailing slashes are preserved. The site serves directories only with a trailing slash (the slashless form 301s to it), so we keep the server's canonical form; a slashless link follows that redirect and collapses onto the stored page via final-URL dedupe.

Fragments are dropped, default ports removed, scheme and host lowercased, percent-encoding normalized, and `.`/`..` segments resolved.

## Environment notes

### TLS: kennesaw.edu's certificate chain and the OS trust store

`www.kennesaw.edu` serves a chain that terminates in eMudhra's `emSign Root CA - G1`:

```
leaf:         CN=omniwwwprdweb03.kennesaw.edu
intermediate: InCommon Intermediate CA - OVG2C   (issuer: emSign Root TLS CA - G1)
root:         emSign Root CA - G1
```

That root is present in the OS trust store (`/etc/ssl/cert.pem`) but not in `certifi`, the CA bundle `requests` uses by default. With the default store every request to the site failed with:

```
SSLError ... CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate
```

so a crawl would have recorded a `tls_error` on every URL and fetched nothing. `curl` was unaffected because it already uses the system store.

Fixed with [`truststore`](https://pypi.org/project/truststore/):
`src/crawler.py` calls `truststore.inject_into_ssl()` before opening the HTTP session, so TLS verification uses the OS trust store. No `REQUESTS_CA_BUNDLE` override is needed.
