# Data robustness results — 11 November 2026

Protocol: ROBUSTNESS_PROTOCOL.md, declared before execution. Evidence: experiments/robustness_v1/report.json and per-scenario input, assignments and score CSVs. Model/thresholds/weights unchanged. The baseline reproduced ranking_v1 assignment IDs exactly and all four numeric score columns within absolute tolerance 1e-10. Input order, text and model provenance remain traceable.

| Scenario | Rows | Scored / 27 | Common Spearman | Common Top-K agreement | Original Top-5 retained |
| --- | ---: | ---: | ---: | ---: | ---: |
| Permuted rows | 1500 | 14 | 1.0000 | 5/5 | 5/5 |
| Repeated first account | 1520 | 14 | 1.0000 | 5/5 | 5/5 |
| ARR uncertainty ±20% | 1500 | 14 | 1.0000 | 5/5 | 5/5 |
| Subgroup effort uncertainty ±20% | 1500 | 14 | 0.9912 | 4/5 | 4/5 |
| ARR missing for 30 of 293 accounts | 1500 | 1 | Undefined | 1/1 | 0/5 |

Every scenario retained exact source-ID coverage. Repetition added ten copies of each of the selected account's two records. Its request volume/endorsements can rise, but distinct reach, ARR, customer-balanced ratings, effort, strategy, RICE-style and fixed weighted scores remained unchanged. Full assignments on original rows were also unchanged within 1e-10 for numeric similarity.

ARR uncertainty preserved the full ranking, despite changed scores. Effort uncertainty replaced one Top-5 candidate. These are single, reproducibly seeded scenarios; they do not estimate the probability of stability under arbitrary uncertainty.

Missingness exposes a material design limitation: the conservative requirement for complete customer ARR prevented 13 of the originally 14 scorable opportunities from receiving a score. None of the original Top-5 survived. The common-intersection agreement of 1/1 must NOT be described as robust ranking: only one candidate remained and Spearman is undefined. An operator needs better evidence or an explicitly justified strategy excluding ARR; this experiment does not silently impute or change strategy after seeing results. Any alternative missing-data treatment would require a separately declared evaluation.

No new language, typos, adversarial feedback, independent real data, participant utility or business outcomes were tested. Semantic accuracy is still limited to the original held-out synthetic result. Grouping remained fixed for business-signal changes to isolate their effect. Local runtime is the existing pinned environment; no fresh cloud performance benchmark was taken.

Verification: three new tests passed, covering seeded customer/subgroup consistency, invariance to input order, coverage-loss disclosure, exact repeatable output and overwrite refusal. Full suite including real-model inference: 135 passed, one disposable-PostgreSQL test skipped, 9.40 seconds. Previous Linux/PG CI passed 133 tests before these three experiment tests were added. Initial execution stopped before creating output because CSV deserialisation used object rather than pandas string dtype; fixed the reference comparison to compare values without requiring identical string storage dtype. No result-driven scenario or parameter change followed.

Reproduce from the repository root, with the existing generated dataset and prepared model:

```bash
PRODUCTLENS_OFFLINE=1 python -m productlens.robustness_experiment \
  --input data/generated/v1.0.0_seed42_n1500/inputs/feedback.csv \
  --reference experiments/ranking_v1 \
  --output experiments/robustness_reproduction
```

Use a new destination. The saved input hashes and multipliers in report.json identify each transformation exactly.
