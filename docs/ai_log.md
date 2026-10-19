# AI log

Solo project. Every entry is from me (Adrian Valcarcel-Schott).

## How the assistant was used

As a pair programmer: it wrote some/most of the Python, but I set the direction and reviewed every change: URL policy, error taxonomy, analysis methods, log schema, etc. All decided or revised by hand before being committed.

## What the assistant generated

About ~30-40% of the initial crawler implementation (early commits), and ~80% of the later crawler implementation. Includes scaffolding, `argparse`, parts of the initial `canonicalize.py` implementation, schema/storage helpers, `parse.py`, `crawl.py`, `crawler.py`, and so on.

About 95% of the analysis implementation.

About 95% of the test suite.

## How it was used to obtain information

- Assignment rules: interpreting assignment instructions (e.g., artifact schemas, per-question guidance) and checking output against them.

- Standards and library behavior: RFC 9309 robots status handling, `protego` API, `w3lib` parameter sorting, `sklearn`'s `ENGLISH_STOP_WORDS`.

- Diagnosing live behavior : TLS failure investigation, determining the root cause of the `certifi`/OS store mismatch.

## How correctness was verified

- Tests: ~235 unit tests (`uv run pytest`), all reviewed, written alongside the code, covering all core aspects of crawling and analysis. TDD was used liberally.

- Static checks: `uv run ty check`, `uv run ruff check`, `uv run ruff format --check` to ensure code quality, type checking, and linting.

- Live smoke crawls: 3-15 page runs against the real site after each stage-one change, before moving to 500-page budget.

- Manual probes: e.g., `catalog...?catoid=1/9999` and `calendar...?days=1/3650` by hand with body-hash comparison for Q1.b, and eyeballing trafilatura output on two pages for Q5.

## Where the assistant was wrong, and how it was caught

- Trailing-slash redirect loops: the first full run dropped hundreds of directory pages as `redirect_loop`. The log showed the site 301s `/x` -> `/x/`, and the assistant's canonicalization stripped the slash, so the target looked like the current page. Policy changed to preserve trailing slashes.

- Q7 worst-page heuristic: first version flagged the shortest sampled page; changed to flag the page whose top keywords are mostly stopwords or numbers.

- Silent robots failures: robots.txt fetch failures were only visible as downstream skips; added a `robots_unreachable` error so Req 14 holds.

- Out-of-scope targets: errors recorded the redirecting URL, not the target; added a `target` field so the log names where the redirect went.
