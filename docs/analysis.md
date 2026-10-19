# Stage two: analysis numbers

- pages: 50 in pages.jsonl, 50 in stats.json
- URLs seen: 1287
- wall clock: 137.8 s
- logged decisions: 1699

## Q1: URL patterns by budget

50 pages across 50 patterns; top 15 by pages:

| rank | pattern | pages | distinct hashes |
| --- | --- | --- | --- |
| 1 | `azindex.kennesaw.edu/` | 1 | 1 |
| 2 | `campus.kennesaw.edu/` | 1 | 1 |
| 3 | `campus.kennesaw.edu/colleges-departments/arts/` | 1 | 1 |
| 4 | `campus.kennesaw.edu/colleges-departments/bagwell/` | 1 | 1 |
| 5 | `campus.kennesaw.edu/colleges-departments/cacm/` | 1 | 1 |
| 6 | `campus.kennesaw.edu/colleges-departments/ccse/` | 1 | 1 |
| 7 | `campus.kennesaw.edu/colleges-departments/coles/` | 1 | 1 |
| 8 | `campus.kennesaw.edu/colleges-departments/csm/` | 1 | 1 |
| 9 | `campus.kennesaw.edu/colleges-departments/graduate/` | 1 | 1 |
| 10 | `campus.kennesaw.edu/colleges-departments/honors/` | 1 | 1 |
| 11 | `campus.kennesaw.edu/colleges-departments/honors/admission/` | 1 | 1 |
| 12 | `campus.kennesaw.edu/colleges-departments/radow/` | 1 | 1 |
| 13 | `campus.kennesaw.edu/colleges-departments/spceet/` | 1 | 1 |
| 14 | `campus.kennesaw.edu/colleges-departments/wellstar/` | 1 | 1 |
| 15 | `campus.kennesaw.edu/current-students/` | 1 | 1 |

## Q2: duplicate content

Near-duplicate threshold: 0.80 (5-gram word shingles, Jaccard).

- byte-identical: 0 pages (0.0%), 0 duplicate groups
- near-duplicate: 0 pages (0.0%), 0 pairs at Jaccard >= 0.80
- self-declared canonical: 41 pages (82.0%)

Non-identical pairs by similarity band:

| Jaccard >= | pairs |
| --- | --- |
| 0.90 | 0 |
| 0.80 | 0 |
| 0.70 | 0 |
| 0.50 | 5 |

Examples:
- near: https://www.kennesaw.edu/alumni/ ~ https://www.kennesaw.edu/degrees-programs/ (Jaccard 0.61)
- self-declared: https://www.kennesaw.edu/ -> https://www.kennesaw.edu/index.php

## Q3: most common fetch failures

| rank | failure_reason | count |
| --- | --- | --- |

Total: 0 errors.

## Q4: top pages by links

Top 5 by incoming links (from crawled pages):

| rank | url | in-links |
| --- | --- | --- |
| 1 | https://campus.kennesaw.edu/ | 50 |
| 2 | https://www.kennesaw.edu/news/ | 50 |
| 3 | https://azindex.kennesaw.edu/ | 49 |
| 4 | https://campus.kennesaw.edu/colleges-departments/arts/ | 49 |
| 5 | https://campus.kennesaw.edu/colleges-departments/bagwell/ | 49 |

Top 5 by outgoing links:

| rank | url | out-links |
| --- | --- | --- |
| 1 | https://azindex.kennesaw.edu/ | 279 |
| 2 | https://www.kennesaw.edu/academics/ | 166 |
| 3 | https://campus.kennesaw.edu/current-students/ | 156 |
| 4 | https://campus.kennesaw.edu/colleges-departments/ccse/ | 145 |
| 5 | https://campus.kennesaw.edu/faculty-staff/ | 143 |

## Q5: boilerplate removal

Strategy: trafilatura main-content extraction over the cached HTML.

- pages: 50 of 50 with cached HTML
- mean words before: 991.6
- mean words after: 310.3 (68.7% removed)

Top 5 longest by raw text:

| rank | url | words |
| --- | --- | --- |
| 1 | https://campus.kennesaw.edu/current-students/registrar/academic-calendars.php | 6459 |
| 2 | https://campus.kennesaw.edu/offices-services/fiscal-services/bursar/tuition-fees/ | 2610 |
| 3 | https://campus.kennesaw.edu/colleges-departments/honors/admission/ | 2348 |
| 4 | https://www.kennesaw.edu/academics/ | 1724 |
| 5 | https://campus.kennesaw.edu/current-students/ | 1507 |

Top 5 longest after removal:

| rank | url | words |
| --- | --- | --- |
| 1 | https://campus.kennesaw.edu/colleges-departments/honors/admission/ | 1671 |
| 2 | https://azindex.kennesaw.edu/ | 1286 |
| 3 | https://campus.kennesaw.edu/offices-services/fiscal-services/bursar/tuition-fees/ | 948 |
| 4 | https://www.kennesaw.edu/academics/ | 831 |
| 5 | https://campus.kennesaw.edu/current-students/registrar/academic-calendars.php | 780 |

## Q6: word frequencies and Zipf

Corpus: 50 boilerplate-removed pages, 15517 tokens.

Top 30 words (all):

| rank | word | count |
| --- | --- | --- |
| 1 | and | 697 |
| 2 | the | 503 |
| 3 | to | 447 |
| 4 | of | 347 |
| 5 | ksu | 213 |
| 6 | in | 212 |
| 7 | you | 192 |
| 8 | for | 164 |
| 9 | your | 151 |
| 10 | our | 150 |
| 11 | students | 148 |
| 12 | kennesaw | 127 |
| 13 | we | 125 |
| 14 | resources | 124 |
| 15 | university | 124 |
| 16 | state | 114 |
| 17 | academic | 111 |
| 18 | with | 111 |
| 19 | student | 107 |
| 20 | is | 102 |
| 21 | are | 99 |
| 22 | or | 92 |
| 23 | at | 91 |
| 24 | campus | 88 |
| 25 | college | 83 |
| 26 | that | 80 |
| 27 | on | 79 |
| 28 | services | 67 |
| 29 | as | 65 |
| 30 | research | 64 |

Top 30 words (stopwords removed):

| rank | word | count |
| --- | --- | --- |
| 1 | ksu | 213 |
| 2 | students | 148 |
| 3 | kennesaw | 127 |
| 4 | resources | 124 |
| 5 | university | 124 |
| 6 | state | 114 |
| 7 | academic | 111 |
| 8 | student | 107 |
| 9 | campus | 88 |
| 10 | college | 83 |
| 11 | services | 67 |
| 12 | research | 64 |
| 13 | honors | 60 |
| 14 | programs | 57 |
| 15 | community | 56 |
| 16 | graduate | 56 |
| 17 | faculty | 51 |
| 18 | education | 50 |
| 19 | success | 45 |
| 20 | apply | 42 |
| 21 | learning | 42 |
| 22 | information | 39 |
| 23 | application | 38 |
| 24 | health | 38 |
| 25 | business | 37 |
| 26 | courses | 37 |
| 27 | program | 37 |
| 28 | center | 35 |
| 29 | help | 35 |
| 30 | office | 34 |

Zipf fit on the stopword-removed distribution: exponent s = 0.91, R^2 = 0.96, 2380 terms, 1146 occurring once.

## Q7: TF-IDF keywords

Sampled 5 pages with random_seed = 42.

| # | words | url | top 5 keywords |
| --- | --- | --- | --- |
| 1 | 239 | https://campus.kennesaw.edu/colleges-departments/ccse/ | major (0.30), declare (0.28), computing (0.28), cse (0.21), fye (0.21) |
| 2 | 384 | https://campus.kennesaw.edu/current-students/ | you (0.23), to (0.22), core (0.21), do (0.20), advisor (0.18) |
| 3 | 243 | https://campus.kennesaw.edu/offices-services/research/university-initiatives/ | initiatives (0.42), research (0.24), and (0.22), efforts (0.18), these (0.17) |
| 4 | 268 | https://campus.kennesaw.edu/colleges-departments/graduate/ | graduate (0.30), and (0.28), to (0.21), resources (0.20), college (0.18) |
| 5 | 255 | https://www.kennesaw.edu/admissions/undergraduate/admission-requirements/transfer.php | 2027 (0.40), transfer (0.38), sent (0.24), 2026 (0.22), application (0.20) |

Worst sampled page: https://campus.kennesaw.edu/current-students/ (384 words, 3 of 5 keywords are stopwords or numbers).
- before: you (0.23), to (0.22), core (0.21), do (0.20), advisor (0.18)
- after min_df=2 + sublinear_tf: core (0.19), impacts (0.17), advisor (0.16), my (0.16), do (0.14)

0 of 50 pages are shorter than 50 words.

## Q8: politeness evidence

**Q8.a delay compliance.** 11 hosts, minimum gap 1.00 s, 0 below the 1.00 s floor.

| host | min gap (s) |
| --- | --- |
| www.kennesaw.edu | 1.00 |
| campus.kennesaw.edu | 1.00 |
| ccse.kennesaw.edu | 2.83 |
| azindex.kennesaw.edu | 6.63 |
| bookstore.kennesaw.edu | 10.00 |
| libanswers.kennesaw.edu | 10.00 |
| ksumail.kennesaw.edu | 14.12 |
| service.kennesaw.edu | 14.62 |
| libguides.kennesaw.edu | 44.51 |
| catalog.kennesaw.edu | 60.00 |
| advising.kennesaw.edu | 100.42 |

**Q8.b robots.txt.**

| host | blocked |
| --- | --- |
| programfinder.kennesaw.edu | 5 |
| libguides.kennesaw.edu | 5 |
| catalog.kennesaw.edu | 2 |
| ksuconnect.kennesaw.edu | 1 |
| mysportsrec.kennesaw.edu | 1 |
| calendar.kennesaw.edu | 1 |

**Q8.c request rate.** 50 pages / 137.8 s = 0.36 pages/s; 137 requests / 137.8 s = 0.99 requests/s.
