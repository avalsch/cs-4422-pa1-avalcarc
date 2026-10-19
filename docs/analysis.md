# CS 4422 PA1 Analysis

Written answers to Q1–Q8. The generated numbers behind them are in the appendix.

## Q1: URL patterns that ate the budget

## Q2: Duplicate-content census

## Q3: Error taxonomy

## Q4: Top pages by in- and out-links

## Q5: Boilerplate removal

## Q6: Text statistics and Zipf

## Q7: TF-IDF keywords

## Q8: Politeness evidence

---

# Appendix: Generated output

- pages: 500 in pages.jsonl, 500 in stats.json
- URLs seen: 6663
- wall clock: 1011.5 s
- logged decisions: 9493

## Q1: URL patterns by budget

Grouped by host + first 2 path segments; 500 pages across 185 patterns, top 15 by pages:

| rank | pattern | pages | distinct hashes |
| --- | --- | --- | --- |
| 1 | `campus.kennesaw.edu/colleges-departments/ccse` | 55 | 49 |
| 2 | `campus.kennesaw.edu/current-students/student-affairs` | 47 | 39 |
| 3 | `campus.kennesaw.edu/colleges-departments/coles` | 23 | 23 |
| 4 | `campus.kennesaw.edu/colleges-departments/radow` | 18 | 18 |
| 5 | `campus.kennesaw.edu/faculty-staff/academic-affairs` | 17 | 16 |
| 6 | `campus.kennesaw.edu/current-students/academics` | 15 | 14 |
| 7 | `campus.kennesaw.edu/offices-services/fiscal-services` | 13 | 12 |
| 8 | `campus.kennesaw.edu/offices-services/research` | 13 | 13 |
| 9 | `campus.kennesaw.edu/colleges-departments/bagwell` | 12 | 12 |
| 10 | `www.kennesaw.edu/news/stories` | 10 | 10 |
| 11 | `campus.kennesaw.edu/colleges-departments/spceet` | 9 | 9 |
| 12 | `campus.kennesaw.edu/faculty-staff/human-resources` | 9 | 9 |
| 13 | `campus.kennesaw.edu/colleges-departments/arts` | 8 | 8 |
| 14 | `campus.kennesaw.edu/colleges-departments/wellstar` | 8 | 8 |
| 15 | `campus.kennesaw.edu/offices-services/campus-operations` | 7 | 5 |

## Q2: duplicate content

Near-duplicate threshold: 0.80 (5-gram word shingles, Jaccard).

- byte-identical: 88 pages (17.6%), 42 duplicate groups
- near-duplicate: 11 pages (2.2%), 19 pairs at Jaccard >= 0.80
- self-declared canonical: 297 pages (59.4%)

Non-identical pairs by similarity band:

| Jaccard >= | pairs |
| --- | --- |
| 0.90 | 17 |
| 0.80 | 19 |
| 0.70 | 21 |
| 0.50 | 22 |

Examples:
- identical: https://campus.kennesaw.edu/current-students/academics/writing-center/ == https://campus.kennesaw.edu/current-students/academics/writing-center/index.php
- near: https://www.kennesaw.edu/degrees-programs/ ~ https://www.kennesaw.edu/degrees-programs/certificates/index.php (Jaccard 1.00)
- self-declared: https://www.kennesaw.edu/ -> https://www.kennesaw.edu/index.php

## Q3: most common fetch failures

| rank | failure_reason | count |
| --- | --- | --- |
| 1 | robots_unreachable | 50 |
| 2 | http_error (404) | 7 |
| 3 | out_of_scope | 7 |
| 4 | http_error (403) | 2 |
| 5 | wrong_content_type | 1 |

Total: 67 errors.

## Q4: top pages by links

Top 5 by incoming links (from crawled pages):

| rank | url | in-links |
| --- | --- | --- |
| 1 | https://www.kennesaw.edu/ | 491 |
| 2 | https://www.kennesaw.edu/accreditation.php | 490 |
| 3 | https://www.kennesaw.edu/feedback.php | 489 |
| 4 | https://campus.kennesaw.edu/ | 487 |
| 5 | https://maps.kennesaw.edu/ | 487 |

Top 5 by outgoing links:

| rank | url | out-links |
| --- | --- | --- |
| 1 | https://facultyweb.kennesaw.edu/ | 1380 |
| 2 | https://azindex.kennesaw.edu/ | 279 |
| 3 | https://campus.kennesaw.edu/colleges-departments/ | 201 |
| 4 | https://www.kennesaw.edu/degrees-programs/minors/index.php | 191 |
| 5 | https://campus.kennesaw.edu/current-students/academics/academic-advising/get-academic-advising/find-your-advisor.php | 188 |

## Q5: boilerplate removal

Strategy: trafilatura main-content extraction over the cached HTML.

- pages: 500 of 500 with cached HTML
- mean words before: 1089.8
- mean words after: 398.5 (63.4% removed)

Top 5 longest by raw text:

| rank | url | words |
| --- | --- | --- |
| 1 | https://www.kennesaw.edu/visit/campus-tours/ | 18879 |
| 2 | https://www.kennesaw.edu/visit/campus-tours/index.php | 18879 |
| 3 | https://www.kennesaw.edu/event-venue-management/ | 17822 |
| 4 | https://campus.kennesaw.edu/current-students/registrar/academic-calendars.php | 6459 |
| 5 | https://campus.kennesaw.edu/current-students/student-affairs/public-forum.php | 4495 |

Top 5 longest after removal:

| rank | url | words |
| --- | --- | --- |
| 1 | https://facultyweb.kennesaw.edu/ | 4065 |
| 2 | https://campus.kennesaw.edu/offices-services/fiscal-services/supplier-vendor-involvement.php | 3653 |
| 3 | https://campus.kennesaw.edu/current-students/student-affairs/public-forum.php | 2918 |
| 4 | https://www.kennesaw.edu/visit/campus-tours/ | 2076 |
| 5 | https://www.kennesaw.edu/visit/campus-tours/index.php | 2076 |

## Q6: word frequencies and Zipf

Corpus: 500 boilerplate-removed pages, 199261 tokens.

Top 30 words (all):

| rank | word | count |
| --- | --- | --- |
| 1 | the | 8144 |
| 2 | and | 7973 |
| 3 | to | 5697 |
| 4 | of | 4737 |
| 5 | in | 2991 |
| 6 | for | 2569 |
| 7 | is | 1711 |
| 8 | ksu | 1655 |
| 9 | you | 1589 |
| 10 | with | 1560 |
| 11 | students | 1502 |
| 12 | your | 1335 |
| 13 | kennesaw | 1296 |
| 14 | resources | 1233 |
| 15 | on | 1219 |
| 16 | or | 1210 |
| 17 | campus | 1128 |
| 18 | student | 1126 |
| 19 | university | 1112 |
| 20 | are | 1096 |
| 21 | our | 1074 |
| 22 | that | 1057 |
| 23 | at | 981 |
| 24 | as | 960 |
| 25 | state | 959 |
| 26 | an | 895 |
| 27 | be | 892 |
| 28 | by | 888 |
| 29 | we | 808 |
| 30 | services | 747 |

Top 30 words (stopwords removed):

| rank | word | count |
| --- | --- | --- |
| 1 | ksu | 1655 |
| 2 | students | 1502 |
| 3 | kennesaw | 1296 |
| 4 | resources | 1233 |
| 5 | campus | 1128 |
| 6 | student | 1126 |
| 7 | university | 1112 |
| 8 | state | 959 |
| 9 | services | 747 |
| 10 | academic | 745 |
| 11 | information | 729 |
| 12 | sign | 617 |
| 13 | research | 602 |
| 14 | faculty | 579 |
| 15 | program | 550 |
| 16 | college | 521 |
| 17 | programs | 486 |
| 18 | community | 452 |
| 19 | education | 425 |
| 20 | support | 391 |
| 21 | center | 389 |
| 22 | learning | 388 |
| 23 | science | 377 |
| 24 | engineering | 362 |
| 25 | 000 | 361 |
| 26 | department | 350 |
| 27 | data | 332 |
| 28 | technology | 316 |
| 29 | graduate | 315 |
| 30 | help | 304 |

Zipf fit on the stopword-removed distribution: exponent s = 1.25, R^2 = 0.96, 11818 terms, 4993 occurring once.

## Q7: TF-IDF keywords

Sampled 5 pages with random_seed = 42.

| # | words | url | top 5 keywords |
| --- | --- | --- | --- |
| 1 | 104 | https://campus.kennesaw.edu/ | services (0.29), find (0.29), index (0.28), tools (0.27), policies (0.25) |
| 2 | 40 | https://campus.kennesaw.edu/current-students/student-affairs/wellbeing/counseling/ | counseling (0.51), psychological (0.34), caps (0.24), 6600 (0.23), emotions (0.22) |
| 3 | 202 | https://campus.kennesaw.edu/policies-governance/staff-senate/ | staff (0.53), senate (0.48), and (0.18), body (0.17), the (0.14) |
| 4 | 455 | https://campus.kennesaw.edu/colleges-departments/bagwell/iteach/ | iteach (0.34), and (0.28), pd (0.24), instructional (0.21), coaches (0.14) |
| 5 | 55 | https://campus.kennesaw.edu/faculty-staff/academic-affairs/student-success/smart-center/ | smart (0.65), tutoring (0.28), students (0.20), 80 (0.19), ksu (0.18) |

Worst sampled page: https://campus.kennesaw.edu/policies-governance/staff-senate/ (202 words, 2 of 5 keywords are stopwords or numbers).
- before: staff (0.53), senate (0.48), and (0.18), body (0.17), the (0.14)
- after stop_words + min_df=2 + sublinear_tf: senate (0.31), body (0.20), staff (0.20), meetings (0.17), updated (0.17)

20 of 500 pages are shorter than 50 words.

## Q8: politeness evidence

**Q8.a delay compliance.** 64 hosts, minimum gap 1.00 s, 0 below the 1.00 s floor.

| host | min gap (s) |
| --- | --- |
| www.kennesaw.edu | 1.00 |
| campus.kennesaw.edu | 1.00 |
| degreeworks.kennesaw.edu | 1.00 |
| service.kennesaw.edu | 1.00 |
| alumni.kennesaw.edu | 1.00 |
| owlexpress.kennesaw.edu | 1.00 |
| vpn.kennesaw.edu | 1.00 |
| sportspark.kennesaw.edu | 1.00 |
| kennesawtower.kennesaw.edu | 1.00 |
| ccse.kennesaw.edu | 2.91 |
| campusservices.kennesaw.edu | 2.94 |
| fiscalservices.kennesaw.edu | 5.53 |
| azindex.kennesaw.edu | 6.82 |
| bookstore.kennesaw.edu | 10.00 |
| libanswers.kennesaw.edu | 10.00 |
| financialaid.kennesaw.edu | 10.99 |
| ksumail.kennesaw.edu | 14.07 |
| registrar.kennesaw.edu | 26.93 |
| diversity.kennesaw.edu | 28.58 |
| sportsrec.kennesaw.edu | 39.53 |
| owllife.kennesaw.edu | 40.56 |
| libguides.kennesaw.edu | 43.71 |
| catalog.kennesaw.edu | 60.00 |
| owltrain.kennesaw.edu | 72.15 |
| digitalcommons.kennesaw.edu | 97.34 |
| advising.kennesaw.edu | 100.67 |
| cpe.kennesaw.edu | 136.88 |
| calendar.kennesaw.edu | 169.37 |
| maps.kennesaw.edu | 171.48 |
| kennesaw.edu | 177.67 |
| experience.kennesaw.edu | 273.93 |
| artspurchase.kennesaw.edu | 277.03 |
| payroll.kennesaw.edu | 302.54 |
| hr.kennesaw.edu | 303.58 |
| epay.kennesaw.edu | 343.48 |
| dga.kennesaw.edu | 386.26 |
| learnonline.kennesaw.edu | 399.28 |
| careers.kennesaw.edu | 411.54 |
| facultyweb.kennesaw.edu | 429.13 |
| ksuhousing.kennesaw.edu | 434.56 |
| studenthealth.kennesaw.edu | 436.97 |
| directory.kennesaw.edu | 640.89 |
| uits.kennesaw.edu | 762.13 |
| orientation.kennesaw.edu | 915.85 |
| commencement.kennesaw.edu | 916.50 |
| police.kennesaw.edu | 917.20 |
| visit.kennesaw.edu | 919.70 |
| handbooks.kennesaw.edu | 923.03 |
| testing.kennesaw.edu | 924.56 |
| writingcenter.kennesaw.edu | 925.22 |
| counseling.kennesaw.edu | 931.37 |
| wellness.kennesaw.edu | 933.74 |
| cyaar.kennesaw.edu | 934.47 |
| care.kennesaw.edu | 936.06 |
| esports.kennesaw.edu | 937.73 |
| livesafe.kennesaw.edu | 937.74 |
| dining.kennesaw.edu | 938.61 |
| events.kennesaw.edu | 941.09 |
| parking.kennesaw.edu | 941.13 |
| taloncard.kennesaw.edu | 941.35 |
| talon.kennesaw.edu | 943.04 |
| stratcomm.kennesaw.edu | 952.63 |
| homecoming.kennesaw.edu | 958.56 |
| giving.kennesaw.edu | 960.16 |

**Q8.b robots.txt.**

Hosts with explicit rules (robots.txt reachable):

| host | blocked | pages |
| --- | --- | --- |
| calendar.kennesaw.edu | 23 | 2 |
| libguides.kennesaw.edu | 19 | 0 |
| programfinder.kennesaw.edu | 5 | 0 |
| digitalcommons.kennesaw.edu | 3 | 1 |
| mysportsrec.kennesaw.edu | 2 | 0 |
| catalog.kennesaw.edu | 2 | 3 |
| opensource.kennesaw.edu | 1 | 0 |
| istart.kennesaw.edu | 1 | 0 |
| go.kennesaw.edu | 1 | 0 |
| ksuweb.kennesaw.edu | 1 | 0 |

Hosts with robots.txt unreachable (disallow-all policy):

| host | blocked |
| --- | --- |
| owlexpresstest.kennesaw.edu | 6 |
| bandir.kennesaw.edu | 4 |
| banssb8preweb01.kennesaw.edu | 4 |
| ksuconnect.kennesaw.edu | 2 |
| gss-patchban.kennesaw.edu | 2 |
| banssb8btaweb01.kennesaw.edu | 2 |
| ksutv.kennesaw.edu | 1 |
| onbaseappforms.kennesaw.edu | 1 |
| ccsenetlab2.kennesaw.edu | 1 |
| banner.kennesaw.edu | 1 |
| onbase.kennesaw.edu | 1 |
| bannavdevweb.kennesaw.edu | 1 |
| bantstora.kennesaw.edu | 1 |
| collie.kennesaw.edu | 1 |
| bannavtstweb.kennesaw.edu | 1 |
| ksuconnecttest.kennesaw.edu | 1 |
| bannavpatweb.kennesaw.edu | 1 |
| banstgora.kennesaw.edu | 1 |
| srs-patchban.kennesaw.edu | 1 |
| sss-patchban.kennesaw.edu | 1 |
| fss-patchban.kennesaw.edu | 1 |
| bcm-patchban.kennesaw.edu | 1 |
| bes-patchban.kennesaw.edu | 1 |
| degreeworkstest.kennesaw.edu | 1 |
| bannavstgweb.kennesaw.edu | 1 |
| degreeworkspatch.kennesaw.edu | 1 |
| bannavbtaweb.kennesaw.edu | 1 |
| banbtaora01.kennesaw.edu | 1 |
| srs-betaban.kennesaw.edu | 1 |
| sss-betaban.kennesaw.edu | 1 |
| fss-betaban.kennesaw.edu | 1 |
| gss-betaban.kennesaw.edu | 1 |
| bcm-betaban.kennesaw.edu | 1 |
| bes-betaban.kennesaw.edu | 1 |
| banenvpreweb01.kennesaw.edu | 1 |
| banpreora01.kennesaw.edu | 1 |
| srs-preban.kennesaw.edu | 1 |
| sss-preban.kennesaw.edu | 1 |
| fss-preban.kennesaw.edu | 1 |
| gss-preban.kennesaw.edu | 1 |
| bcm-preban.kennesaw.edu | 1 |
| bes-preban.kennesaw.edu | 1 |
| banenvpltweb01.kennesaw.edu | 1 |
| aimweb.kennesaw.edu | 1 |
| ccpe.kennesaw.edu | 1 |
| sasprdweb01.kennesaw.edu | 1 |
| boreas.win.kennesaw.edu | 1 |
| enteliprdweb01.kennesaw.edu | 1 |
| niagaraprdweb01.win.kennesaw.edu | 1 |
| sasreports.kennesaw.edu | 1 |

**Q8.c request rate.** 500 pages / 1011.5 s = 0.49 pages/s; 907 requests / 1011.5 s = 0.90 requests/s.
