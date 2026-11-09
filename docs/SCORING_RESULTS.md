# Initial ranking comparison — measured 9 November 2026

This is a descriptive experiment on **synthetic data**, following `SCORING_PROTOCOL.md`. It does not establish a correct ranking, improvement over human product managers, or business impact. The frozen semantic settings were not retuned.

## Executed scenario

Input: `data/generated/v1.0.0_seed42_n1500/inputs/feedback.csv`, seed 42, generator v1.0.0. All 1,500 records from 293 customers were grouped into 27 candidates. Exact assignment coverage was **1,500/1,500**; every score can be joined to original feedback through `assignments.csv`. This full generated input is a demonstration/comparison set, not an independent semantic holdout. More rows do not add independent authored phrasing diversity.

Output: `experiments/ranking_v1/`. The JSON report contains input/config/source hashes, runtime versions, weights, maxima, exact metrics, rank changes, segment counts and timings. Grouping configuration is copied verbatim. Account resolution, subgroup effort, candidate descriptions and all three strategy score tables are saved alongside it.

## Coverage before agreement

| Method | Scored candidates / 27 |
| --- | ---: |
| Balanced strategy benefit / effort | 14 / 27 |
| Votes | 27 / 27 |
| Fixed weighted benefit | 20 / 27 |
| RICE-style proxy | 14 / 27 |

Thirteen candidates lack a complete effort proxy; seven of these also lack complete customer-level urgency/alignment. They remain visible and unranked for the balanced strategy. They are not assigned zero value or silently dropped from the app. The missing data reflect intentionally uncertain synthetic records and the way the semantic model groups them.

All comparisons below use **14 common scorable candidates**, recalculating ranks on that intersection. Their Top-5 sets therefore differ in definition from the unrestricted Top-5 of methods with larger coverage. Spearman uses average ranks for ties; ID breaks display/Top-K ties only.

| Balanced strategy compared with | Spearman | Top-5 agreement |
| --- | ---: | ---: |
| Votes | −0.3363 | 0 / 5 |
| Fixed weighted benefit | −0.2442 | 0 / 5 |
| RICE-style proxy | 0.9385 | 4 / 5 |

**Interpretation:** the effort denominator materially changes the order relative to endorsement volume and benefit alone. Both the balanced and RICE-style formulas divide by the same provisional effort, which helps explain their agreement; this is not independent validation. The group definitions, synthetic construction and selected business proxies shape these findings. Low agreement is not evidence that a baseline is wrong or the new system is better.

The balanced Top-5 source terms concern owner reassignment, tagging, archiving, CSV reports and quota warnings. These are candidate grouped requests, not approved feature specifications or roadmap commitments.

## Strategy and local sensitivity

| Scenario compared with balanced | Spearman | Top-5 agreement |
| --- | ---: | ---: |
| Enterprise/ARR emphasis | 0.9692 | 4 / 5 |
| Reach emphasis | 0.9560 | 4 / 5 |

Eight predeclared perturbations changed one balanced weight by ±20% and renormalised. All eight retained the same Top-5. Seven retained the complete ranking; reducing reach weight gave Spearman 0.9956. This shows local weight stability for this fixture only, not robustness to new feedback, grouping errors, missing inputs or larger strategy changes.

Balanced Top-5 customer coverage, using the union of supporting customers:

| Segment | Represented / all uploaded customers in segment |
| --- | ---: |
| Enterprise | 41 / 99 (41.4%) |
| SMB | 71 / 98 (72.4%) |
| Startup | 47 / 96 (49.0%) |

These are descriptive representation rates, not a fairness assessment or predicted adoption. A customer may support several candidate opportunities but counts once in this Top-5 coverage calculation.

## Runtime and verification

Local first run: grouping including model loading **1.8823 seconds**; aggregation, scoring and comparison **0.2744 seconds**. This excludes process start, input parsing, file output and browser rendering. It is not a cloud benchmark or measured time saved versus manual work.

The full suite passed **114 tests**, including the real-model 500-row upload → grouping → scoring journey. Core checks include hand-calculated scores, repetition invariance for reach/ARR/effort, conflicting and missing values, row-order reproducibility, zero weights, ties, undefined metrics, segment counts, safe text export and refusal to overwrite experiment evidence. Controlled-embedding unit runs reproduced all experiment CSV outputs byte-for-byte; real-model full-run reproducibility is checked separately only where recorded in `PROGRESS.md`.

The local six-row browser demo showed two scored candidates and a priority-order change when account-value weight increased from 30 to 99, with revised factor contributions and unchanged fixed baseline scores. This confirms live controls, not grouping validity. The sample's broad group still combines different needs. The scoring screenshot is `docs/scoring-demo.png`.

## Reproduce

After model preparation and dataset generation described in README:

```bash
PRODUCTLENS_OFFLINE=1 python -m productlens.ranking_experiment \
  --input data/generated/v1.0.0_seed42_n1500/inputs/feedback.csv \
  --output experiments/ranking_v1_reproduction
```

Use a new output path. Timings and environment metadata may differ. No ground-truth labels or catalog are read by this command. Review the known semantic grouping errors and the scoring proxy assumptions before interpreting scores. Stored human reviews, data perturbation experiments, a user study, Linux/cloud verification and the final academic report remain incomplete.
