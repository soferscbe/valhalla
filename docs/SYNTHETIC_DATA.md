# Synthetic evidence dataset v1.0.0

This dataset is a controlled development and evaluation fixture for ProductLens AI. All customer accounts, feedback, business signals and annotations are synthetic. The request wording and labels were authored with AI assistance during implementation and have not been independently validated by Product Managers. No Zoho or customer records were used.

## Generate and reproduce

From the repository root, using the pinned Python 3.12 environment:

```bash
source .venv/bin/activate
python -m productlens.synthetic --rows 500 --seed 42
python -m productlens.synthetic --rows 1500 --seed 42
```

Defaults: 500 rows, seed 42. Supported range: 200–10,000 rows. The lower bound retains adequate family representation. The approved proposal's target remains 1,000–1,500; the 500-row bundle is the initial development fixture. A 1,500-row bundle has also been generated to verify scaling, not to claim additional independent research evidence.

Outputs default to `data/generated/v1.0.0_seed42_n500/` (or `n1500/`). The CLI refuses existing destination directories. Reproduce into a new directory with `--output /tmp/productlens-reproduction`; compare file hashes in the manifests. Reusing the same seed, row count, source and pinned environment produces identical bundle bytes. There is no wall-clock timestamp in the manifest. Source hashes and runtime versions record the generation conditions. Do not manually edit generated files.

Generated bundles are ignored by Git. Their source catalog, generator, tests and this specification remain source-controlled candidates. No new dependency or external API is required.

## Bundle contract

| File | Purpose |
| --- | --- |
| `inputs/feedback.csv` | Full input dataset for upload/demonstration; existing validated schema only |
| `inputs/tuning.csv` | Feedback and business signals from tuning families/accounts |
| `inputs/evaluation.csv` | Feedback and business signals from held-out families/accounts |
| `model_inputs/tuning.csv` | Only `feedback_id` and `feedback_text` |
| `model_inputs/evaluation.csv` | Only `feedback_id` and `feedback_text` |
| `truth/labels.csv` | ID join key, split, family provenance, theme and duplicate labels, eligibility flags |
| `truth/customers.csv` | Synthetic account registry with stable segment, annual account value and split |
| `manifest.json` | Version, seed, size, units, policies, runtime/source hashes, per-file hashes, summary and limitations |

For app preview, upload **`inputs/feedback.csv`**. For semantic processing, embed **only `feedback_text`** from the appropriate model-input file. `feedback_id` is a join key, never a feature. Customer IDs, business signals, labels, family names and manifest summaries must not be supplied to embeddings or clustering. The existing app does not import the generator or load truth files. `inputs/feedback.csv` mixes both splits for demonstration and must not be used to tune a model intended for held-out evaluation.

## Composition and business signals

The generator allocates 85% clear requests, 10% overlapping requests and 5% vague/ambiguous requests, using largest-remainder rounding. Clear themes have relative weights: dashboard customisation 30, bulk editing 20, reporting 18, usage alerts 16, audit history 8 and identity/access 8. These are design assumptions, not population estimates.

The catalog contains 32 specific request families with three base phrasings each: 24 clear families across six themes, four overlapping families and four vague families. A clear family denotes one specific requested capability, such as scheduled report email. Related capabilities, such as CSV report export, share a broader theme but have a different duplicate-group label. Repeated phrasings, lowercase variants and occasional `pls help:` prefixes are deliberate lightweight noise. They do not provide a comprehensive model of real-world language variation.

Account segments are Startup, SMB and Enterprise. The registry has `2 × clamp(rows // 10, 20, 150)` accounts; some need not submit feedback. Each account's segment and value stay fixed across its records. Customers can make repeated requests or request several different capabilities.

| Signal | Meaning and assumptions |
| --- | --- |
| `account_value` | Simulated USD annual recurring revenue per account, not per request. Startup 120–1,800; SMB 2,400–12,000; Enterprise 24,000–120,000. Do not sum the same account's ARR repeatedly within an opportunity. |
| `votes` | Simulated endorsements attached to a record; not distinct customers and not independently verified voters. |
| `request_date` | Fixed 120-day window, 8 July–4 November 2026 inclusive. Generation does not depend on today's date. |
| `urgency` | Ordinal 1–5. Higher values intentionally assigned to the enterprise security scenarios. |
| `strategic_alignment` | Illustrative enterprise/retention-oriented 1–5 assessment. Not an objective or universal alignment score. Future strategy presets must make changed assumptions explicit. |
| `effort` | Hypothetical person-days, stable within a clear request family. Do not sum effort across duplicate records. Opportunity-level estimation/aggregation is still a decision-engine task. |

Dashboard customisation receives many records and votes from only three Startup accounts in each split. Audit and identity requests come from Enterprise accounts, with lower volume but higher assigned value/alignment. Usage alerts have roughly four of five requests per family in the latest 30 days, versus the other themes' uniform date sampling. These conflicts and trends are intentionally constructed test scenarios; a later ranking that reflects them is not evidence of real business benefit.

Overlapping requests have two theme labels and no single effort estimate. Vague requests have no theme label and no urgency, alignment or effort estimate. The validator exposes these missing values as warnings. No missing values are silently replaced with zero.

## Split and annotation rules

For each clear theme, the seeded split assigns two complete specific-request families to tuning and two to evaluation. It does the same 2/2 assignment for overlapping and vague families. All three paraphrases, casing/prefix variants, exact repetitions and semantic duplicate members of a family stay together. Accounts are separately assigned to one split. Record order is shuffled before generic feedback IDs are assigned.

The split is approximately 50/50 by row count; whole-family allocation takes precedence over exact balance. Both halves intentionally share the six broader themes. Integrity checks prohibit shared family IDs, semantic duplicate-group IDs, customer accounts or case/whitespace-normalised text across splits. Business distributions are synthetic in both halves; common vocabulary and the same design process remain shared.

Truth fields:

- `template_family`: generation provenance and split unit; not a model feature.
- `label_kind`: `clear`, `overlapping` or `ambiguous`.
- `theme_labels`: alphabetically sorted, pipe-separated theme names; two for overlap, empty for vague records.
- `primary_theme`: only populated for clear single-theme records.
- `duplicate_group`: specific-request family for clear records; exact and paraphrased duplicates share it. Separate capabilities within a theme do not.
- `eligible_single_theme` and `eligible_duplicate`: true only for clear records.

Use tuning data/labels for model and threshold choices. Freeze model/version, preprocessing, clustering settings and metric definitions before running held-out evaluation. Use held-out truth only after predictions are produced. If evaluation output is used to revise settings, disclose that contamination and create a genuinely new evaluation design; changing the random seed alone does not create new independently authored language.

Do not combine bundles with different sizes/seeds as independent samples. IDs can recur and family assignments may change with the seed. Record the full dataset hash in every experiment.

## Evaluation limits and planned handling

No semantic or prioritisation performance has been measured in this milestone. Future clustering metrics on clear labels must report the eligible record count and excluded challenge count. Overlapping/vague records stay in the application input and should receive separate analysis of ambiguity/noise handling rather than being silently discarded or forced into an invented class. A row excluded from a single-label metric is not thereby excluded from model processing.

Exact repetitions can inflate clustering and pairwise duplicate performance. Report row-based results alongside unique-normalised-text or family-weighted diagnostics, and distinguish exact from nonidentical duplicate pairs. Define the exact pair universe, treatment of unclustered records and weighting before measuring results. A selected-theme synthetic label is a designed reference, not independently established customer truth.

The finite 96-phrase catalog limits linguistic diversity. Scaling to 1,500 rows changes volume and account coverage, not the number of independently authored request concepts. Holding out specific request families reduces direct paraphrase leakage but does not establish real-world generalisation. A broader independently reviewed dataset or real permitted nonconfidential evidence would be needed for stronger claims.

## Observed fixture checks on 5 November 2026

For seed 42, 500 rows:

- 250 tuning and 250 evaluation records; 98 distinct submitting customers (49 per split).
- 425 clear, 50 overlapping and 25 vague records; 198 distinct literal feedback texts across both splits.
- Dashboard customisation: 128 records from six customers and 793 synthetic votes. Audit and identity: 34 records each, 57 and 52 votes respectively.
- Usage alerts: 52 of 68 requests fall in the last 30 days. This verifies the configured trend, not a discovered market trend.
- Content hash: `d05cba31a08bd3f2f00707d5f81d045b973e0aea4f8119b06d4b54ff484d7e37`.

For seed 42, 1,500 rows: 748 tuning and 752 evaluation records; 293 distinct submitting customers. Content hash: `e6b0dc3e3af37059b6f7f127f3f1e98071f99496fefc93d69c659d6b1b362749`.

Tests exercise deterministic frame/file output, sizes 200/500/1,000/1,500, label/account integrity, split isolation, scenario properties, manifest hashes, invalid configuration, refusal to overwrite, CLI invocation and generated-file upload through Streamlit AppTest. Refer to `PROGRESS.md` for the final executed result. Browser visual QA and cloud deployment remain unverified.
