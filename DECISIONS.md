# ProductLens AI decisions

## 5 November 2026 — foundation architecture and input contract

**Decision:** Retain the proposed Python/Streamlit architecture with modular ingestion and validation; use Python 3.12 in a local virtual environment. Foundation supports CSV and `.xlsx`, with three required identity/text fields and validated optional business signals. Treat repeated customer IDs as valid while rejecting repeated feedback IDs. No automatic record deletion or optional-signal imputation.

**Options:** Streamlit versus a separate frontend/API; minimal required identity/text schema versus requiring every scoring signal immediately; legacy `.xls` versus modern `.xlsx` support.

**Rationale/trade-offs:** Matches approved direction, reduces infrastructure and allows early working delivery. Explicit fields make later distinct-customer aggregation auditable. Optional signals keep intake usable but require later missing-data/scoring policy. `.xlsx` uses openpyxl; legacy `.xls` is excluded and must be converted by the user. No semantic capabilities are implied by the foundation.

## 5 November 2026 — dataset and report source precedence

**Decision:** Treat approximately 500 records as the initial generator step, retaining the proposal's 1,000–1,500 target for evaluation. Preserve Annexure formatting requirements and flag its dated cover/degree sample wording for clarification rather than copying it literally into a final report.

**Options:** Treat the handoff's initial dataset size as final, or preserve the accepted proposal's target; copy template placeholders or explicitly resolve them before submission.

**Rationale/trade-offs:** Maintains accepted research scope and accurate academic front matter. No evaluation results or final report wording are approved by this decision.

## 5 November 2026 — reproducible synthetic evidence and grouped holdout

**Decision:** Implement v1.0.0 as a seeded, authored catalog of 32 specific-request families with three base phrasings each; default 500 records, scalable to the proposal's 1,000–1,500 target. Fixed 8 July–4 November 2026 dates and stable account registries avoid time-dependent data. Store truth/provenance separately; model input explicitly allows only feedback text plus an ID join key. Label 85% clear, 10% overlapping and 5% vague records. Only clear records are eligible for initial single-theme and semantic-duplicate metrics; retain all records for challenge analysis and app processing.

**Options:** Random row split versus holding out phrasing variants versus holding out whole specific-request intents; externally generated wording versus a versioned authored catalog; forcing overlapping requests into one label versus separate challenge eligibility.

**Rationale/trade-offs:** Whole request families (two of four per theme per split) keep exact and semantic duplicates together; accounts are also disjoint. Approximately 50/50 tuning/evaluation leaves adequate examples in the small fixture. Broad themes remain shared. A finite catalog is fast, inspectable and reproducible without an API, but repeated language can inflate metrics and is not independent annotation. More rows do not add independent semantic diversity. Shared vocabulary/authoring process still limit generalisation. Freeze model/settings using tuning only and report unique-text/family-weighted diagnostics with row-based results. The source specification documents these limits; no accuracy claims are made.

**Business assumptions:** `account_value` is synthetic USD ARR per account; `effort` is hypothetical person-days per specific intent, not additive across duplicate requests. Votes are record-level simulated endorsements, distinct from customer counts. Alignment reflects an illustrative enterprise/retention strategy. Vague records omit urgency/alignment/effort; overlapping records omit effort. Final opportunity-level aggregation, missing-data handling and strategy-specific scoring remain pending.

**Reproducibility:** Persist seed, dataset version, Python/pandas versions, source/file hashes and counts in a deterministic manifest. Refuse overwrite of existing output directories. Generated bundles are Git-ignored and rebuilt from source; never combine different-size/seed bundles as independent samples.

## 5 November 2026 — semantic representation and predeclared evaluation

**Decision:** Use local CPU `sentence-transformers/all-MiniLM-L6-v2`, immutable revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, for normalised distinct-text embeddings. Apply complete-linkage cosine clustering at a broader opportunity threshold and a stricter candidate-duplicate threshold. Retain every source row and distinct customer counts; derive titles from representative source sentences and extractive terms. Cap grouping at 2,000 rows and flag model-window truncation. Model failures are explicit with no lexical fallback.

**Options:** Fixed-K clustering, density-based grouping, cosine connected components, or complete linkage; cloud/LLM summaries versus local extractive descriptions; clustering repeated rows versus distinct wordings.

**Rationale/trade-offs:** No fixed number of product needs is assumed. Complete linkage avoids similarity chains joining distant requests and supports nested stricter groups, but can fragment broad themes. Unique wording avoids volume-driven clustering. Local inference avoids sending feedback to an external AI service and requires no API key. CPU/model dependencies add download, disk and memory costs. All rows receive one group; ambiguous or multi-intent requests are not reliably detected, and extractive summaries are not verified customer-problem statements. Group membership hashes are dataset-specific, not durable opportunity identities for future review persistence.

**Evaluation decision made before the first run:** `docs/SEMANTIC_PROTOCOL.md` declares grids and selection objectives: unique-normalised-text theme ARI followed by unique-text duplicate-pair F1; ties choose higher similarity. Freeze selected settings, code/runtime/model/dataset hashes before a separate held-out invocation. Report row and unique-text metrics, exact-pair exclusions, challenge evidence and actual local timings. No holdout-driven threshold adjustments are permitted within this declared run. No result is assumed by this decision.

## 9 November 2026 — preserve measured limitations and expose subgroup evidence

**Decision:** Keep the tuning-selected 0.20 opportunity / 0.55 duplicate thresholds unchanged after evaluation. Expose the stricter subgroup counts and source examples in the app, and document broad over-merging, missed paraphrases and multi-intent limitations in the professor brief and results note.

**Options:** Adjust settings after seeing held-out/demo weaknesses, hide poor examples, or preserve the experiment and make review limitations explicit.

**Rationale/trade-offs:** Preserves the meaning of the saved holdout. The UI addition changes evidence presentation only; frozen grouping/model/metric source hashes still match. Current groups are candidate interpretations, not validated features. The next scoring stage must expose uncertainty and require human scrutiny. Any future algorithm/settings revision needs a separately documented experiment and must disclose evaluation reuse.
