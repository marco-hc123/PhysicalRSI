# Secondary analysis of published hybrid/direct episodes

This is a local reanalysis of a public result snapshot, not an independent robotics reproduction.
It compares **pi0.5 + GPT-6 Astra (`mix`) with GPT-6 Astra direct (`gpt`)**.
**PhysicalRSI is not an experimental arm. The token reduction is not a measured PhysicalRSI advantage.**

Source: [https://anonymous-report-421.github.io/public-website/source/public_results/data.json](https://anonymous-report-421.github.io/public-website/source/public_results/data.json); report as of 2026-09-13.
Source SHA-256: `0c4be006a2a0dc1ca2559e4421c45680eec94d466f390ea34b2ea055af9bd74e`.

## Validation and denominators

All 100 selected episodes are retained: 50 per method, paired by case_id and the complete seed dictionary.
All 50 pairs match, spanning 10 tasks with five pairs each. Every published aggregate token, step,
correction, chunk, success, and score-denominator total matches the recomputed values.
There are two direct episodes with `native_complete=false` and `score=null`. They remain in the
50-episode success denominator and token totals. Score means use 50 hybrid and 48 direct scored episodes.
The snapshot excludes earlier retries and does not establish total development/search/billing cost.

## Recomputed selected-run totals

| Metric | Hybrid | Direct |
|---|---:|---:|
| Successful / attempted | 24/50 | 13/50 |
| Success rate | 48.0% | 26.0% |
| Total tokens (input + output) | 624,762,828 | 1,132,343,772 |
| Input tokens | 623,457,803 | 1,130,257,208 |
| Cached input tokens (subset) | 607,555,840 | 1,107,349,760 |
| Uncached input tokens | 15,901,963 | 22,907,448 |
| Output tokens | 1,305,025 | 2,086,564 |
| Reasoning output tokens (subset) | 380,541 | 873,464 |
| Action chunks (not model calls) | 3,776 | 7,729 |
| Physical steps | 42,750 | 38,221 |
| Cached share of input | 97.449% | 97.973% |
| Total tokens / chunk (ratio of sums) | 165,456.26 | 146,505.86 |
| All-attempt total tokens / success | 26,031,784.50 | 87,103,367.08 |
| Mean physical-step time (seconds) | 34.2000 | 30.5768 |
| Mean video duration (seconds) | 34.2400 | 30.6168 |

Cache-write input tokens are zero in all rows. Cached input is included in input; reasoning
is included in output. These subsets must not be added to the total again. Token totals are not
dollar costs: pricing, discounts, billed retries, and provider invoices are absent.

## Arithmetic decomposition and heterogeneous pairs

The aggregate total-token reduction is **44.8257%**.
The following identity decomposes the accounting but does not establish a causal mechanism:

```text
Hybrid total / direct total = (hybrid chunks / direct chunks) *
                             (hybrid tokens per chunk / direct tokens per chunk)
0.55174307 = 0.48854962 * 1.12934909
```

Hybrid has 51.15% fewer published chunks, but
12.93% more total tokens per chunk.
An executed chunk can involve zero, one, or multiple model-related operations; these data
cannot convert chunk counts into verified API call counts.

The **ratio of sums** is 0.551743; the **unweighted mean of 50 pair ratios**
is 1.035185; the median pair ratio is 0.485600.
The ratio of sums equals a direct-token-weighted mean of pair ratios. The unweighted mean
gives equal weight to each case, so it answers a different question. Percent savings must
state which aggregation is used. Neither discards failed episodes.

The unweighted mean of pair percentage reductions is -3.52%,
which reverses the sign of the aggregate claim. A large hybrid/direct ratio on a small direct
denominator can dominate this unweighted statistic. For example, the published
`imitate_sorting_sequence__standard__g0__l3` pair uses 27,872,887 versus 1,534,875 tokens
(18.16 times); both episodes fail. Keep these cases rather than removing inconvenient outliers.

Hybrid uses fewer tokens in 42 pairs, the same in 0,
and more in 8. Success pairing is: both succeed 8;
hybrid only 16; direct only 5; both fail 21.

## Task-cluster sensitivity intervals

A deterministic percentile bootstrap uses seed 20261011 and 20,000 resamples.
Each resample draws ten task clusters with replacement and retains all five paired cases within each cluster.
The 95% interval for aggregate token reduction is [22.38%, 58.23%].
The success-rate difference is 22.0%; its 95% interval is
[0.00%, 44.00%].
These are descriptive sensitivity intervals over only ten selected task clusters. They do not
correct selection bias, make the observations independent, identify causality, or establish
performance on unobserved tasks. All additional intervals and valid replicate counts are in JSON.

## Per-task totals

| Task | Hybrid success / 5 | Direct success / 5 | Hybrid total tokens | Direct total tokens | Reduction |
|---|---:|---:|---:|---:|---:|
| arrange_largest_number | 2 | 2 | 80,435,360 | 135,352,225 | 40.57% |
| build_tower | 3 | 0 | 56,495,547 | 141,689,627 | 60.13% |
| classify_objects | 3 | 5 | 55,966,402 | 114,530,904 | 51.13% |
| classify_objects_by_language | 1 | 2 | 72,118,919 | 188,057,301 | 61.65% |
| fold_clothes | 5 | 2 | 17,293,400 | 57,584,839 | 69.97% |
| imitate_sorting_sequence | 2 | 0 | 92,598,216 | 26,151,141 | -254.09% |
| make_kong | 2 | 0 | 37,403,126 | 105,187,285 | 64.44% |
| organize_table | 0 | 0 | 77,778,308 | 113,033,588 | 31.19% |
| pack_objects_into_box | 1 | 1 | 103,010,124 | 155,935,123 | 33.94% |
| put_bottles_into_dustbin | 5 | 1 | 31,663,426 | 94,821,739 | 66.61% |

The JSON retains all per-task token subsets, chunk counts, physical steps, times, and cost-per-success denominators.
A task with zero successes has an undefined (`null`) token-per-success value, not zero cost.

## Time and attribution limits

`steps * dt` measures simulated physical progression. `duration = frames / fps` is video duration;
the initial frame adds 0.04 seconds per episode. Neither includes model waiting or measures wall-clock
latency. No statement that hybrid executes faster in real time follows from this dataset.
Matching seeds and tasks supports a paired descriptive comparison, but method/controller changes,
termination, outcomes, context construction, cache policy, and run selection remain entangled.
This analysis motivates controlled PhysicalRSI measurements; it does not replace them.

## Reproduce

From any machine with Python 3.10 or newer and the copied `result` directory:

```bash
python result/scripts/analyze_published_results.py
# Write a separate reproducibility run instead of replacing the packaged results:
python result/scripts/analyze_published_results.py --output-dir /tmp/published-reanalysis
```

Outputs: `data/published_episodes.csv`, `data/published_pairs.csv`, `data/published_summary.json`,
and `reports/published_results_analysis.md`. CSV files use UTF-8 with BOM for spreadsheet portability.
No network, simulator, GPU, API key, or model request is used.
