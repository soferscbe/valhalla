# Semantic grouping results

Status reviewed on 9 November 2026. These are initial synthetic-data results, not evidence that the full prioritisation system improves real business decisions.

## Experiment and evidence

The `semantic-v1` run used the 500-record, seed-42 synthetic bundle: 250 tuning and 250 held-out records, with disjoint request families and customer accounts. Settings were selected on tuning data and frozen before held-out evaluation. No threshold was changed after examining held-out results.

The model is `sentence-transformers/all-MiniLM-L6-v2` at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Complete-linkage cosine similarity thresholds selected from the predeclared grid were **0.20 for broad opportunities** and **0.55 for candidate duplicates**. Both are the lowest values in their grids; they are the best tested tuning settings under the declared objectives, not demonstrated global optima.

The frozen configuration is in `config/semantic.json` and `experiments/semantic_v1/tuning/frozen_config.json`. Raw results and supporting evidence are in `experiments/semantic_v1/heldout/`. The protocol and metric definitions are in `docs/SEMANTIC_PROTOCOL.md`.

## Measured held-out results

All 250 held-out rows were processed. The clear-label metrics use 212 rows, representing **56 unique case/whitespace-normalised texts**. The other 38 rows (25 overlapping, 13 vague) remain in predictions and are analysed separately.

| Metric | All 212 eligible rows | 56 unique normalised texts |
| --- | ---: | ---: |
| Theme adjusted Rand index | 0.5991 | 0.6065 |
| Theme normalised mutual information | 0.8090 | 0.8282 |
| Duplicate precision | 0.9682 | 0.9615 |
| Duplicate recall | 0.5053 | 0.4717 |
| Duplicate F1 | 0.6640 | 0.6329 |

The unique-text duplicate calculation includes 1,540 unordered pairs: 50 true-positive links, two false-positive links and 56 missed true links. Excluding identical-normalised-text pairs from the row-based calculation reduces duplicate F1 to **0.5040**. Repetition therefore materially affects the apparent result.

There were 12 predicted opportunity groups across all held-out rows. Clear requests occupied ten of those groups, versus six reference themes. No input was truncated in this run. The reference theme and specific-request duplicate labels represent different levels of granularity.

ARI is an agreement statistic, not percentage accuracy. Duplicate precision of 0.9615 does not mean the overall application is “96% accurate”: recall is much lower, labels are synthetic, and the ranking component does not exist yet.

## Errors and interpretation

The two unique-text false duplicate links connect configurable quota-alert recipients with early quota-threshold warnings. These requests share terminology but ask for different capabilities. Missed links include paraphrases of dashboard-icon customisation and quota-threshold warnings. Detailed evidence is in `duplicate_errors.csv`.

Overlapping dashboard/bulk-editing requests joined groups containing clear bulk-editing requests; their dashboard intent was not separately represented. Overlapping security requests joined clear identity/access groups without separately retaining their audit-history intent. Some vague requests formed separate groups, while “Could you improve this in the next update?” joined dashboard customisation. There is no automatic ambiguity detector, and an extractive representative sentence does not establish that every member has the same underlying need.

The six-row browser demonstration also grouped reports, audit changes and usage alerts into one broad group. This illustrates broad-group over-merging on a small input batch; the stricter duplicate subgroups are exposed for inspection. The frozen settings have been preserved, and this limitation must be disclosed. Clustering is recomputed per input batch, so group membership can change when the batch changes.

The initial result supports a working, inspectable grouping prototype with known errors. It does not yet establish better prioritisation, PM productivity, or universally correct feature choices. Group review is necessary before using aggregated evidence for a score. Finite authored templates, shared vocabulary and non-independent labels limit external validity. More synthetic rows do not solve those limitations.

## Runtime and verification

The held-out command recorded 1.744 seconds for cached model loading plus encoding and 0.029 seconds for grouping/summarisation on the local Mac ARM CPU, with two Torch threads. Process peak RSS was approximately 566.9 MiB. This is one local observation, not a cloud memory guarantee or an efficiency comparison with human work. Model assets total about 87.3 MiB; Python/Torch dependencies require additional disk and memory.

The final test suite with real-model integration enabled passed **87 tests in 6.35 seconds on 9 November 2026**, after the UI addition exposing duplicate subgroups. Tests verify source traceability, repeated-customer counts, input-order stability, complete-linkage behaviour, invalid/empty inputs, truncation flags, metric arithmetic, tuning/evaluation separation and failure handling. Default tests use controlled embeddings where appropriate; two opt-in tests run the actual pinned model, including a 500-row upload-to-grouping journey.

The 1,500-record execution scale check retained all 1,500 assignments in 27 opportunity groups, taking about 2.45 seconds including model loading, with zero truncated rows. Results are saved separately in `experiments/semantic_v1/scale_check.json`. It is not an independent holdout. Linux/cloud installation, hosted user journeys and durable review storage remain unverified.

## Reproduce

Use the pinned environment and a new output path. Existing experiment folders are never overwritten.

```bash
python -m productlens.embeddings
PRODUCTLENS_OFFLINE=1 python -m productlens.semantic_experiment tune \
  --dataset data/generated/v1.0.0_seed42_n500 \
  --output /tmp/productlens-semantic-reproduction/tuning
PRODUCTLENS_OFFLINE=1 python -m productlens.semantic_experiment evaluate \
  --dataset data/generated/v1.0.0_seed42_n500 \
  --frozen /tmp/productlens-semantic-reproduction/tuning/frozen_config.json \
  --output /tmp/productlens-semantic-reproduction/heldout
```

The runner verifies dataset file hashes and frozen source/runtime/model identity. Future implementation changes need a separately documented experiment; do not overwrite this run or describe reused evaluation feedback as an untouched holdout.
