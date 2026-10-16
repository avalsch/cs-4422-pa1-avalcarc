# PA1 — A Web Crawler From Scratch

**Due:** October 11, 11:59 PM
**Weight:** 25% of course grade

---

## 0. What is allowed and what is not

This is a **group assignment**, with up to **three members** per group. You may also work alone if you prefer. One repository per group, one submission per group, and one grade shared by the whole group — see §8 and §9.

Groups are responsible for their own division of labour, but every member is answerable for the whole submission. Splitting the work so that only one person understands the frontier and only one person understands the analysis is a bad strategy: every member speaks in the §8 presentation, and the questions afterwards can come from anywhere in the repository.

You may discuss the assignment across groups, but the code and the written analysis must be your group's own.

You may use an AI coding assistant, but every member must understand and be able to explain all code the group submits. In `docs/ai_log.md` your group must write about how you used the assistant: what parts of the code it generated, how you used it to obtain information, and how you verified that the code was correct. One file per group is fine; say which member each entry came from. You may write any important conversation with the assistant while making design decisions.

## 1. Goal

### Implementation

You are tasked with developing a web crawler that retrieves pages within the **Kennesaw State University** domain, processing the pages into a document store. The objective is to scrape 500 web pages, beginning with a selection of seed URLs of your choosing.

### Analytical tasks

Following this, you will conduct an analysis of the corpus to address inquiries pertaining to the KSU webpages. With the information collected during crawling, you will be able to answer the following questions:

- Q1. URL pattern identification
    - Q1.a Which URL patterns consumed the most of your crawl budget?
    - Q1.b Could any of them be unlimited?
    - Q1.c What did you do about it, and why?
- Q2. Duplicate-content census
    - Q2.a How much of what you fetched was duplicate content: byte-identical, near-duplicate, or self-declared duplicate via `<link rel="canonical">`?
    - Q2.b Give three concrete example URL pairs from your crawl, one per category, and say what caused each duplication.
- Q3. What were the five most common ways your fetches failed, ranked by count?
- Q4. Which are the top 5 pages by incoming links and the top 5 by outgoing links?
- Q5. Boilerplate identification and removal
    - Q5.a How much of each page is boilerplate? Report mean words per page before and after removal, and the top 5 longest pages under each.
- Q6. Text statistics
    - Q6.a What are the 30 most frequent words before/after stopwords are removed? Describe the difference.
    - Q6.b Does the word-frequency distribution follow Zipf's law? What is the fitted exponent, and where does the distribution depart from it?
- Q7. For 5 randomly sampled pages, what are the top 5 TF-IDF keywords each — and where they come out badly, why, and what fixes it?
- Q8. Politeness evidence
    - Q8.a Did your delay constraint actually hold across the run, on every host?
    - Q8.b How many URLs did `robots.txt` stop you from fetching, and on which hosts? Pick two of them and quote the rule line that blocked each.
    - Q8.c What was your overall request rate and total wall-clock time?

All answers go in `docs/analysis.md`, grounded in your own crawl data with specific URLs and specific counts. You can find more details in §7.

### Group presentation

In the class session following the submission deadline, your group presents its crawl to the class — what you found and what fought back — scored against a rubric. Because this assignment permits AI assistance, presenting your own findings and your own dead ends is how the course distinguishes a group that directed the work from one that passed it along. Everything you present is work you have already done, so there is nothing separate to prepare. Details are in §8.

---

## 2. Setup: GitHub repository

We'll utilize GitHub to track your work. You don't need to submit anything to D2L; the instructor will visit your group's repository to check your work. The repository is also where you will store your artifacts, so it must be private until after grades are posted.

1. Pick one member to own the repository. Create a single **private** repository named `cs4422-pa1-<owner-netid>` or `cs7263-pa1-<owner-netid>`, using that member's netid. One repository per group — do not create one each.
2. Add every other member as a collaborator, and add `Jiho-YesNLP` as a collaborator **on day one**, not on the due date. We want to see the history accumulate. The instructor's AI agent will collect the incremental history of commits, not just the final state.
3. **Every member commits under their own GitHub account.** Do not pair on one laptop all semester and push everything from one login — the history is how the division of labour is visible, and a repository where one account made every commit will be asked about after your §8 presentation.
4. Commit early and often from the very first hour.
5. Email the instructor your group's members and repository URL by the end of the first week.

---

## 3. The Crawler

Write it from scratch in Python. **Do not use a crawling framework** (Scrapy, Frontera, Heritrix, crawl4ai, etc.). Libraries for HTTP transport, HTML parsing, and text processing are fine — the crawl loop, frontier, URL handling, politeness, and storage are yours.

I will not provide any skeleton code or starter files because I want to allow maximum freedom in your design. As long as the requirements in §4 are met, you are free to structure your code as you see fit. Certain files will be examined for grading, so please use the exact file names and paths below.

### 3.1 Pipeline

The system is two stages joined by one file:

```
seed URLs ──► crawl ──► artifacts/pages.jsonl ──► analyze ──► docs/analysis.md
                 ├──► artifacts/crawl.log
                 └──► artifacts/stats.json
```

Stage one fetches and stores. Stage two reads what stage one wrote and computes every number in §7. The two must be separately runnable.

Keeping them apart is what makes the analysis tractable: `pages.jsonl` holds **raw** text, so you can change your boilerplate strategy, your tokenizer, or your duplicate threshold and recompute every number in seconds — without re-crawling a single page. 

*Optional:* you may checkpoint the frontier, visited set, and counters so an interrupted crawl can resume without re-fetching. Not required, but a 500-page crawl at one request per second takes a while, and losing it to a closed laptop is unpleasant.

### 3.2 File structure

✅ = commit this &nbsp;&nbsp; ❌ = do **not** commit; add it to `.gitignore`

```text
✅ README.md                     how to reproduce your run (Req A.1)
✅ requirements.txt              pinned versions
✅ .gitignore                    must exclude everything marked ❌ below
   src/
✅     crawler.py                stage one: seeds -> pages.jsonl + logs
✅     analyze.py                stage two: pages.jsonl -> the numbers in analysis.md
✅     ...                       split into further modules as you see fit
   docs/
✅     analysis.md               your answers to Q1-Q8
✅     ai_log.md                 how you used an AI assistant (§0)
   artifacts/
❌     pages.jsonl               the corpus; produced by the crawl, not committed
✅     crawl.log                 every URL considered
✅     stats.json
❌ cache/                        raw HTML, if you keep any
❌ .venv/                        your virtual environment
```


---

## 4. Requirements


- **Req 1**: Clearly describe how to run your crawler and replicate your crawl in `README.md`: Python version, install steps, the exact commands you ran for both stages, your seed URLs, page budget, and wall-clock runtime.
- **Req 1b**: List every group member in `README.md` — name, netid, and GitHub username — followed by a short paragraph on who did what. Two or three sentences is enough; it is context for §8, not a contract.
- **Req 2**: Both stages must be runnable from the command line, with the seed URLs and the page budget configurable as arguments rather than edited into the source.
- **Req 3**: Your crawler will begin with one or more seed URLs, and the seed URLs and follow-on links must be within the Kennesaw State University domain — `kennesaw.edu` and any of its subdomains. 
- **Req 4**: Your corpus must contain at least 500 pages.
- **Req 5**: Write the crawler from scratch in plain Python code. **Don't use Jupyter Notebook**.
- **Req 6**: Do not use a full-featured crawling framework (Scrapy, Frontera, Heritrix, crawl4ai, etc.). Libraries for HTTP transport, HTML parsing, and text processing are fine (e.g., `requests`, `beautifulsoup4`, `lxml`, `protego`, `nltk`, `scikit-learn`).
- **Req 7**: Canonicalize every URL before it enters the frontier, and canonicalization must determine whether a URL has been seen before. You can use `w3lib.url` or `urllib.parse` for URL parsing.
- **Req 8**: Your canonicalization must at minimum lowercase the scheme and host, remove default ports, remove fragments, normalize percent-encoding, and resolve `.` and `..` path segments. RFC 3986 §6 is the reference.
- **Req 9**: State your query-parameter policy and your trailing-slash policy in `README.md`, as part of the architecture overview.
- **Req 10**: Your HTTP requests must include a descriptive User-Agent that identifies the crawler as coursework (e.g., `KSU CS4422-Crawler/1.0`).
- **Req 11**: Wait at least 1 second between consecutive requests to the same host, and keep at most one request in flight per host. That means, if you crawl one host at a time, 500 pages takes at least 8 minutes; interleaving across hosts is faster, since the delay is per host.
- **Req 12**: Fetch each host's `robots.txt` once, cache it, and obey it. Use [`protego`](https://pypi.org/project/protego/). Honor `Crawl-delay` when the host declares one longer than your `--delay`, and log every URL you skipped because `robots.txt` disallowed it.
- **Req 13**: Handle, without crashing, at minimum: non-2xx statuses, connection failures, timeouts, TLS errors, redirect chains (capped in length, with loop detection), non-HTML content types, and oversized responses (with a byte cap).
- **Req 14**: Record every one of those failures rather than silently discarding them.
- **Req 15**: Store raw extracted text in `pages.jsonl`, with no boilerplate removal at crawl time.
- **Req 16**: Perform boilerplate removal at analysis time, over `pages.jsonl`, in a separate stage.

---

## 5. Artifacts

Three files, all written by the crawler and analysis stages, go into `artifacts/`. Each is graded on being present, conforming to its schema, and agreeing with the others. Everything else your analysis produces belongs in `docs/analysis.md`, not in separate files.

`crawl.log` and `stats.json` are committed; commit and push the files to GitHub when they are updated. `pages.jsonl` is **not** committed — `.gitignore` it along with any raw HTML cache. It still has a required schema: your analysis is graded against numbers that only it can produce.

### 5.1 `artifacts/pages.jsonl` — one JSON object per line

One record per successfully fetched page. Suggested schema:

| Field            | Type         | Notes                                                                                         |
|------------------|--------------|-----------------------------------------------------------------------------------------------|
| `url_canonical`  | string       | after canonicalization                                                                        |
| `status`         | int          | final HTTP status                                                                             |
| `fetched_at`     | string       | ISO-8601 UTC                                                                                  |
| `title`          | string       |                                                                                               |
| `text`           | string       | **raw** extracted text — visible text as the page served it, *before* any boilerplate removal |
| `word_count`     | int          | of raw `text`                                                                                 |
| `out_links`      | list[string] | canonicalized, deduplicated                                                                   |
| `content_hash`   | string       | SHA-256 of normalized raw `text`, for Q2                                                      |
| `canonical_link` | string\|null | the `<link rel="canonical">` target, if the page declares one, for Q2                         |

### 5.2 `artifacts/crawl.log` — JSONL, one line per decision

Every URL your crawler *considered*, not just the ones it fetched. Suggested schema:

| Field            | Notes                                                             |
|------------------|-------------------------------------------------------------------|
| `ts`             | ISO-8601 UTC                                                      |
| `event`          | one of `enqueue`, `fetch`, `skip`, `error`                        |
| `url`            | canonical                                                         |
| `failure_reason` | why it was skipped or why it failed; free text, but be consistent |
| `status`         | HTTP status, where there was one                                  |

**Design this file before you write the crawl loop, not after.** It is the only evidence behind many analytical questions — a decision you fail to log here is a question you cannot answer later without re-crawling.

### 5.3 `artifacts/stats.json`

Single JSON object covering the full crawl. Consider adding the fields below:

`pages_fetched`, `urls_seen`, `wall_clock_seconds`, `robots_skips`, `random_seed`, etc.

## 6. Implementation tips and useful resources

Questions you might have. Useful tips and resources for mostly Python programming. These are starting points, not requirements — deviate freely. `design-points.md` discusses the decision behind each of these in more depth.

**Q. How do I collect user input for configuration settings?**
A. Use [`argparse`](https://docs.python.org/3/library/argparse.html). E.g., Seeds, page budget, delay, and output paths are flags.

**Q. How do I canonicalize a URL?**
A. [`urllib.parse`](https://docs.python.org/3/library/urllib.parse.html) — `urlsplit`/`urlunsplit` for the mechanical parts (lowercase scheme and host, drop default port and fragment, normalize percent-encoding, resolve `.` and `..`), `urljoin` to resolve relative links. [`w3lib.url.canonicalize_url`](https://w3lib.readthedocs.io/en/latest/w3lib.html#w3lib.url.canonicalize_url) does most of it in one call. The normative rules are [RFC 3986 §5 (reference resolution)](https://www.rfc-editor.org/rfc/rfc3986#section-5) and [§6 (equivalence and normalization)](https://www.rfc-editor.org/rfc/rfc3986#section-6).

**Q. Are `/about` and `/about/` the same URL? What about `?utm_source=...`?**
A. Your call — [RFC 3986 §6.2.3](https://www.rfc-editor.org/rfc/rfc3986#section-6.2.3) explicitly leaves this to scheme-based and site-specific judgment. Pick a rule, apply it everywhere, and state both policies in `README.md` (Req 9). Write a few unit tests for canonicalization before you build anything on top of it.

**Q. What data structure should the frontier be?**
A. Start with [`collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque) as a FIFO (breadth-first) plus a `set` of seen canonical URLs. Move to [`heapq`](https://docs.python.org/3/library/heapq.html) or per-host queues only when you have measured a reason to. Background: Manning et al., [*Introduction to Information Retrieval*, ch. 20 — Web crawling and indexes](https://nlp.stanford.edu/IR-book/html/htmledition/web-crawling-and-indexes-1.html).

**Q. My crawler is slow because it waits 1 second on the same host.**
A. That is the politeness floor working (Req 11). To go faster, keep one queue per host and a scheduler that picks the next host whose delay has elapsed — the delay is per host, not global. See [IIR §20.2.3, the URL frontier](https://nlp.stanford.edu/IR-book/html/htmledition/the-url-frontier-1.html).

**Q. How do I read `robots.txt`?**
A. Use [`protego`](https://pypi.org/project/protego/) — `Protego.parse(text)`, then `can_fetch(url, user_agent)` and `crawl_delay(user_agent)`. It is the parser Scrapy uses, it implements [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309) correctly, and it is about ten lines to wire in. Fetch each host's `robots.txt` once and cache the parsed object.

**Q. Q8.b asks which rule blocked a URL. How do I get that out of the parser?**
A. You don't — no off-the-shelf parser reports the matching rule, and writing one that does is out of scope here. Log the host and the blocked URL at crawl time; then, for the two examples Q8.b asks for, open that host's `robots.txt` in a browser and find the line yourself. Quote it, and say why it matches. Two URLs by hand is the whole ask.

**Q. How do I enforce the per-host delay?**
A. A `dict` of host → earliest-next-request-time. Before fetching, sleep until that host's time, then set it to now + your delay (or the host's `Crawl-delay`, whichever is longer).

**Q. What if a host starts returning 429 or 503?**
A. Sleep for [`Retry-After`](https://www.rfc-editor.org/rfc/rfc9110#field.retry-after) if the response carries one, otherwise 10 seconds; retry the URL once; if it fails again, log it and move on. 

**Q. Should I let `requests` follow redirects?**
A. No — pass `allow_redirects=False` and follow them yourself ([requests: redirection and history](https://requests.readthedocs.io/en/latest/user/quickstart/#redirection-and-history)). Each hop is a URL you must canonicalize, scope-check, and re-check against `robots.txt`. 

**Q. How do I extract text and links?**
A. [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) with the [`lxml`](https://lxml.de/) parser. [`get_text()`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#get-text) already drops `<script>`, `<style>`, and comments — bs4 treats their contents as string types it excludes by default — so pin `beautifulsoup4>=4.9` in `requirements.txt`. Canonicalize each link at extraction time so only canonical URLs ever exist downstream.

**Q. What is easy to miss in parsing?**
A. Three things: [`<base href>`](https://html.spec.whatwg.org/multipage/semantics.html#the-base-element) changes what relative links resolve against; [`<meta http-equiv="refresh">`](https://html.spec.whatwg.org/multipage/semantics.html#attr-meta-http-equiv-refresh) is a redirect that never touched HTTP; [`<link rel="canonical">`](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls) is the page declaring itself a duplicate, and Q2 asks you to count those.

**Q. Should I clean boilerplate before storing?**
A. No. Store raw text in `pages.jsonl` (Req 15). Q5 requires before/after numbers, which are impossible if you cleaned at crawl time.

**Q. How do I keep the log usable if I hit Ctrl-C?**
A. Write [JSONL](https://jsonlines.org/) one object per line and flush on every write (`f.flush()`, or open with `buffering=1` — see [`open()`](https://docs.python.org/3/library/functions.html#open)). Log the decision as you make it, not in a batch at the end.

**Q. How do I detect exact duplicates?**
A. [`hashlib.sha256`](https://docs.python.org/3/library/hashlib.html) over normalized text (lowercased, whitespace-collapsed), then group by hash.

**Q. How do I detect near-duplicates?**
A. Represent each page as a set of word n-gram shingles (n = 5 is a reasonable start) and compute Jaccard similarity. At 500 pages all-pairs is ~125k comparisons — perfectly tractable and much easier to get right than MinHash. Report the threshold you chose *and what you measured* to choose it. Read [IIR §19.6, near-duplicates and shingling](https://nlp.stanford.edu/IR-book/html/htmledition/near-duplicates-and-shingling-1.html) and, for MinHash, [Leskovec, Rajaraman & Ullman, *Mining of Massive Datasets*, ch. 3 (PDF)](http://infolab.stanford.edu/~ullman/mmds/ch3n.pdf).

**Q. How do I remove boilerplate?**
A. Easiest defensible approach: find shingles that appear on a large fraction of pages (say >50%) and strip them. Alternatives are DOM text-density — see [Kohlschütter et al., "Boilerplate Detection Using Shallow Text Features" (WSDM 2010)](https://doi.org/10.1145/1718487.1718542), whose reference implementation is [boilerpipe](https://github.com/kohlschutter/boilerpipe) — or extracting only from `<main>`/`<article>`. Whichever you pick, eyeball the output of a few pages by hand before you trust the aggregate numbers.

**Q. How do I group URLs into patterns for Q1?**
A. Reduce each URL to a shape key: replace all-digit segments with `<num>`, dates with `<date>`, UUIDs with `<id>`; keep query parameter names and drop their values with [`urllib.parse.parse_qsl`](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.parse_qsl). Rank patterns by distinct URLs, but also count distinct content hashes per pattern — 400 URLs with 6 distinct bodies is a trap, 400 URLs with 390 distinct bodies is a real section of the site.

**Q. How do I compute TF-IDF for Q7?**
A. [`sklearn.feature_extraction.text.TfidfVectorizer`](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html) over your cleaned corpus; note that its smoothing differs from the textbook formula in [IIR §6.2](https://nlp.stanford.edu/IR-book/html/htmledition/tf-idf-weighting-1.html), so say which you used.

**Q. Where do I start?**
A. Small. Get 20 pages working end to end — fetch, parse, canonicalize, store, log — before you touch anything in §7. Then scale up. The interesting failures only appear at scale, and you want a working baseline underneath you when they do.

## 7. Notes on the analytical tasks

Each answer must be grounded in **your own crawl data**, with specific URLs and specific numbers. Generic descriptions of how crawlers work in general earn zero.

### Q1 — URL patterns that eat your budget

Some URL patterns produce far more distinct URLs than distinct content: event calendars with a `?date=` parameter, search results, sort and paging parameters, session IDs. A few produce *unlimited* URLs, which means a crawler that follows them never finishes.

Unlimited does not mean worthless — a calendar might be content people want. The question is whether **you decided** how much of it to crawl, or whether it just happened to you.

To group URLs by pattern, reduce each one to a shape: same path shape, same query parameter names, different values. Rank by distinct URLs, and consider also counting distinct `content_hash` values per pattern — 400 URLs with 390 distinct bodies is a large real section of the site, 400 URLs with 6 distinct bodies is a trap, and the URL count alone cannot tell them apart.

For Q1.b, test your largest pattern with a handful of manual requests: a date far in the future, a page number much higher than anything you crawled. Report what came back. For Q1.c, state your policy — skip it, allow it up to a limit, or allow it all — and say what fraction of your budget it used and what your rule might wrongly exclude.

If you found nothing worth limiting, say so. That is a fine answer, as long as you back it with the census and the probe. "I didn't hit any traps" with no evidence earns nothing. **You do not need to re-crawl for this section.**

### Q3 — Error taxonomy from real data

**At least one of your five must be something not named in Req 13.** Real crawls produce strange things — a WAF that starts returning `403` once you speed up, a `Content-Type: text/html` on a PDF, mojibake from a mislabeled charset, a redirect loop between `www` and bare host, a page that returns `200` with an error message in the body. Find yours and describe it precisely.

### Q5 — Boilerplate removal

Every page on a university site carries a large shared navigation, header, and footer. Naive text extraction treats that chrome as page content and it will poison every downstream number.

Implement **one** strategy of your choice: shared-shingle detection across pages, DOM-density heuristics, tag-based extraction, template diffing. Report the strategy and why you picked it over the alternatives you considered. If the top-5-longest ranking changed, explain what changed it; if it didn't, explain why not.

### Q6 — Zipf's law, with diagnosis

Your distribution **will** deviate from the ideal Zipf line at both the head and the tail. Do not just note that it deviates. **Name the actual head terms** in your corpus and say what they are — stopwords? the university name? a navigation label? a department that dominates your subdomain? Explain the tail in terms of your specific corpus and your specific tokenizer. What is down there? Look at it.

For the 30 most frequent words after stopword removal: does the list actually characterize your crawled subdomain, or is it still dominated by artifacts? "Still dominated by artifacts, here's why" is a full-credit answer if the diagnosis is correct.

### Q7 — TF-IDF keywords, including a failure

TF-IDF breaks on short pages, menu pages, and template-heavy pages, in different ways. For the page whose keywords come out worst: show its URL, its extracted text length, and its keywords; diagnose *why* they are bad, specifically to that page; then propose a fix, implement it, and show before/after.

If you genuinely believe all five sampled pages produced good keywords, argue it — show the pages and defend them. That is a legitimate answer, but the bar is high. Note that filtering very short pages out of your sample removes one common failure mode; if you filter, say what your cutoff was.

### Q8 — Politeness evidence

Q8.a and Q8.c come straight out of `crawl.log`: group fetch timestamps by host, take consecutive differences, and report the minimum per host — one number per host, plus the count of any that fell below your floor. Q8.c is total wall-clock time and pages divided by it.

Q8.b needs no parser work. Report the count of robots-blocked URLs and the hosts they were on from your log; then open the two hosts' `robots.txt` yourself, find the line that blocked your two examples, and quote it. Explain why it matches — the wildcard, the prefix, the `User-agent` group it sits under.

---

## 8. Group presentation

**20 points.** In the class session following the submission deadline. Each group presents its crawl to the class: what you found, and what fought back.

There is nothing separate to study and nothing extra to submit. The presentation is about work you have already done — your crawl, your artifacts, your numbers.

### Format

- **10 minutes per group, plus about 3 minutes of questions** from the instructor and the class.
- **Every member speaks.** Divide it however you like, but a group where one person presents and the others stand there has not presented as a group.
- Slides are optional. What is not optional is showing your actual output — the Zipf plot, the URL-pattern table, a `crawl.log` excerpt. Screenshots of real artifacts beat bullet points describing them.
- Have the repository open. Questions may ask you to show where a number came from.
- **The group receives one shared score.**

### What to cover

Ten minutes is not enough for all of Q1–Q8, so do not try. Pick the interesting parts and go deep on them. A presentation that covers three findings well scores better than one that lists eight.

1. **What you crawled, in 60 seconds.** Seeds, budget, frontier ordering, wall-clock time. Enough context for the rest to make sense — not a tour of your architecture.
2. **Two or three findings, with the evidence on screen.** The URL pattern that ate your budget, the duplicate cluster you did not expect, the shape of your Zipf tail, the TF-IDF keywords that came out wrong. Show the number or the plot, then say what it means about *this site*.
3. **The hardest problem you hit, and how you diagnosed it.** This is the part we most want to hear. What broke, how you noticed, what you tried that did not work, what finally did. A dead end you can explain is worth more than a feature you cannot.
4. **What surprised you.** Something the crawl told you that you did not expect going in.
5. **What you would do differently** with another week, or at ten times the page budget.

Points 3 and 4 are where the marks are. Every group's §3.1 pipeline looks roughly alike; no two groups' *problems* do.

### Scoring

| Band | Points | What it looks like |
|---|---|---|
| Strong | 18–20 | Findings are specific to this corpus and backed by output shown on screen. The challenge is described honestly, including what failed first. The group separates what it measured from what it assumed. Every member contributes substance, and questions are answered from the repository. |
| Solid | 14–17 | Real findings, grounded in their own data, clearly presented. The challenge section is thinner or the diagnosis is less complete. Questions are mostly answered well. |
| Partial | 8–13 | Describes what was built more than what was found. Numbers appear without interpretation, or the "challenge" is generic — *"it was slow"*, *"the site was big"* — rather than a specific problem and its diagnosis. |
| Weak | 0–7 | Generic description of how crawlers work, findings not grounded in the group's own crawl, or one member presenting alone. |

Say what actually happened. A crawl that went sideways, diagnosed clearly and honestly, scores well — better than a tidy narrative that skips the part where you rebuilt the frontier. *"We thought X, the data showed Y, here is what we changed"* is the shape of a strong presentation.

Where the written work and the presentation are far apart, I will raise it with the group and give you the chance to respond, rather than adjusting a grade quietly afterwards.

A member who misses the session without arranging an alternative in advance scores 0 on this component individually; the rest of the group keeps the group score. If a group tells me before the deadline that the work has been split very unevenly, I will look at the commit history and may score this component individually for that group. Neither is the default, and neither happens quietly.

---

## 9. Grading

| Component | Points |
|---|---|
| Crawler implementation (§4) — canonicalization, `robots.txt`, politeness, error handling, reproducibility from README | 25 |
| **Group presentation (§8)** | **20** |
| Crawl investigations — Q1 URL patterns, Q2 duplicates, Q3 errors, Q8 politeness | 22 |
| Corpus analysis — Q4 link structure, Q5 boilerplate, Q6 Zipf, Q7 TF-IDF | 23 |
| Crawl artifacts (§5) — present, schema-conformant, internally consistent | 10 |

All 100 points are shared by the group.

Git history is not scored, but it is looked at, and with groups it is looked at more closely. Commit as you work rather than in one batch at the end, and commit under your own account — a history that shows the system being built, run, and revised by several people is where the §8 challenge story comes from.

80 of these 100 points are earned by what you submit and 20 by how well you present it. The two are not independent — the presentation is drawn entirely from your own crawl, so a submission you understand makes §8 straightforward.


---

## 10. Submission

There is nothing to submit to D2L. Your private GitHub repository *is* the submission, and it is collected at the deadline.

Confirm before the deadline:

- [ ] One repository for the group, **private**, with every member and `Jiho-YesNLP` added as collaborators
- [ ] `README.md` lists every member (name, netid, GitHub username) and who did what
- [ ] Every member has commits under their own account
- [ ] All required files exist at the paths in §3.2
- [ ] No cache and no `pages.jsonl` committed
- [ ] `docs/ai_log.md` is written
