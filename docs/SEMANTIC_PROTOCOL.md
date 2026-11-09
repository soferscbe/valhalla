# Semantic grouping protocol v1

This protocol is specified before the first tuning/evaluation run. No numerical result is assumed. The task is unsupervised, evidence-linked grouping, not final feature prioritisation.

## Representation and grouping

Use `sentence-transformers/all-MiniLM-L6-v2` at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, CPU execution with two Torch threads. The [model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) describes 384-dimensional embeddings and a 256-wordpiece limit. Long inputs are flagged when truncated; retained original feedback remains visible. No feedback is sent to a model service. The first use downloads public model assets; inference is local. There is no lexical fallback on model failure.

Case-fold and collapse whitespace, then embed sorted distinct text strings. This prevents repeated records from reweighting clustering. IDs, business signals and truth annotations are never embedding features. Apply complete-linkage agglomerative clustering on cosine distance, with no prescribed number of groups. A cluster merges only below distance `1 - similarity_threshold`; the strict boundary is inherited from the library. Complete linkage limits chaining at the cost of splitting loosely related requests. The [scikit-learn implementation](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html) is version-pinned after validation.

Two cuts on the same representation separate broader candidate opportunities and stricter candidate semantic duplicates. Exact normalised repeats map back to the same groups. Every input has an assignment, including singletons; there is no noise class or automatic ambiguity detector. One cluster per record cannot represent multiple intents. All groups need human review. Up to 2,000 rows can be grouped in this MVP; the quadratic pairwise distance calculation makes larger uploads unsuitable without an explicit scalability change.

Each opportunity retains a medoid source sentence (greatest mean similarity across unique wordings), three extractive TF-IDF terms, source IDs, request count, distinct customers and similarity to its representative. These are extractive descriptions, not verified problem statements or confidence probabilities. No synthetic label lookup or LLM assigns names. Group IDs hash membership and change when membership changes. Counts describe evidence volume and do not constitute prioritisation.

## Predeclared tuning and holdout

Use the initial 500-row v1.0.0 seed-42 bundle. Load only the tuning input for selection. Join its labels solely in the metric stage. All challenge rows participate in clustering, but only eligible clear rows enter the initial theme/duplicate metrics.

1. Opportunity similarity grid: 0.20, 0.30, 0.40, 0.50, 0.60. Select maximum theme adjusted Rand index (ARI) on unique normalised clear texts. Ties select the higher similarity threshold.
2. Duplicate similarity grid: 0.55, 0.65, 0.75, 0.85, restricted to values at least the selected opportunity threshold. Select maximum duplicate-pair F1 on unique normalised clear texts. Ties select the higher threshold.
3. Save all candidate scores, chosen configuration, dataset/input hashes, immutable model revision, source hashes and runtime versions to `frozen_config.json` **before evaluation**.
4. In a separate invocation, evaluate once on the held-out split with the frozen configuration. Refuse changed code/runtime/model/dataset identity. Retain all predictions, opportunities, challenge records and duplicate errors. Do not adjust thresholds after inspecting holdout results.

The catalog and split were authored by the implementation team. This is held-out request-family evaluation within one synthetic design, not an independent external test. The 1,500-row bundle is a scale check using the same catalog and must not be treated as a second independent generalisation study.

## Metric definitions

- **Theme ARI:** chance-adjusted agreement between pairs induced by reference clear-theme labels and predicted opportunity membership. 1 means matching partitions; values near 0 reflect chance-adjusted agreement. It is not classification accuracy.
- **Theme NMI:** mutual information normalised by the arithmetic mean of the two partition entropies, as implemented by scikit-learn. Range 0–1. Report with ARI because fragmentation can affect them differently.
- **Duplicate precision/recall/F1:** universe = all unordered pairs of eligible clear rows. A true pair shares a specific-request `duplicate_group`; a predicted pair shares the stricter predicted group. Precision = TP/(TP+FP); recall = TP/(TP+FN); F1 = 2TP/(2TP+FP+FN). Return null for a zero denominator, report counts, and do not silently call undefined precision perfect.
- Report the metrics on all eligible rows and once per unique case/whitespace-normalised text. Also report duplicate-pair metrics after excluding identical normalised strings. The unique-text variant is the tuning objective to reduce repetition bias; it is not independent-family sampling and noisy variants can still be correlated.
- Report total/eligible/excluded counts. Singleton predicted groups are ordinary distinct clusters, not a shared noise class. For fewer than two eligible observations, ARI/NMI are null.
- Challenge rows are retained in `challenge_review.csv` with expected theme sets and clear themes sharing their predicted group. Inspect them separately; do not calculate forced single-label accuracy or silently remove them from the actual pipeline.
- Record one local load/encode time, grouping/summarisation time, and process peak RSS. Cached downloads, hardware and runtime affect these values. No PM productivity or cloud capacity claim follows from a single run.

References for metric semantics: [scikit-learn clustering evaluation](https://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation). Source links are implementation references, not a completed IEEE literature review.
