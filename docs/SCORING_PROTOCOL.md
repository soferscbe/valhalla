# Scoring protocol v1 — 9 November 2026

Declared before the first ranking experiment. This is a transparent decision aid over candidate groups, not a learned ranking or a claim of correct business priorities. Frozen semantic settings remain unchanged. No synthetic truth labels are used here.

## Evidence aggregation

- Join every validated feedback ID to exactly one opportunity and candidate duplicate group. Reject missing, additional or repeated assignments; reject a duplicate group spanning multiple opportunities.
- Request volume counts rows; reach counts distinct customer IDs per opportunity. Votes sum record-level endorsements only when every row supplies votes; endorsements are not verified unique voters.
- Account value is USD ARR in the synthetic data. Resolve one value per customer across the entire uploaded dataset. Exactly one distinct nonmissing value is usable (missing rows are flagged); conflicting or entirely missing values are unknown. Sum each customer's resolved value once per opportunity. If any member account is unresolved, total ARR is unknown; separately display the known subtotal and coverage. The same account may support several opportunities, so totals across opportunities are not additive revenue forecasts.
- For urgency and alignment, first average distinct known values within each customer/opportunity, then average customers equally. This avoids repeated identical submissions reweighting a customer. A customer with no value makes the group factor unknown. Partial missing rows and conflicting assessments are flagged. Values are assessments, not measured outcomes.
- For each candidate duplicate group use the maximum distinct known effort estimate, then sum those subgroup estimates once per opportunity. This is an explicit provisional scope-cost proxy in person-days. Duplicate rows cannot multiply effort; distinct subgroups can still describe overlapping work, and grouping errors can inflate or deflate scope. A subgroup with no estimate makes the opportunity effort unknown. Partial missing rows and disagreeing estimates are flagged. This proxy requires engineering review before a delivery commitment; it is not a verified total estimate.
- Resolve a customer's segment globally; conflicting or missing segments become `Unknown/conflicting`. Keep customer, subgroup and original-row evidence tables for inspection.

## Formula and missing values

Default weights: reach 0.30, ARR 0.30, urgency 0.20, alignment 0.20. All weights must be finite, nonnegative, and have positive total; normalise by their sum. These are illustrative assumptions, not calibrated research findings.

Factors: reach / maximum opportunity reach; ARR / maximum fully-known opportunity ARR; (urgency − 1) / 4; (alignment − 1) / 4. A known all-zero ARR column normalises to zero. No valid ARR observations leaves it unknown. Dataset-relative maxima are recorded and recomputed when the candidate set changes; this can change scores without changing the opportunity itself. Rating factors use fixed endpoints, so 1 contributes zero and 5 contributes one.

Benefit = 100 × sum(normalised weight × factor). Priority score = benefit / effort proxy (weighted points per person-day). Display every factor and contribution. No semantic similarity is used as confidence. Zero-weight factors contribute zero even if missing. Any unknown positive-weight factor prevents that strategy's score; unknown effort also prevents effort-adjusted scores. Do not impute a missing signal as zero or silently redistribute its weight. Keep unrankable opportunities visible with reasons.

Baselines on the same candidate groups:

1. **Votes:** sum of record-level endorsements, no effort adjustment; incomplete votes → unavailable.
2. **Fixed weighted benefit:** default weights above, no effort division; remains fixed when the strategy sliders change.
3. **RICE-style proxy:** distinct submitting customers × (customer-balanced urgency / 5) × common confidence / effort proxy. Confidence defaults to 0.50 for every candidate and is a declared scenario assumption, not an estimated probability. The UI permits a common 0–1 scenario value. Reach covers this uploaded observation window, not forecast adoption. Urgency is an impact proxy; effort uses person-days. Thus this is an adaptation, not standard RICE or independently assessed product impact.

RICE background: Sean McBride, “RICE: Simple prioritization for product managers,” Intercom, 5 January 2018, [original article](https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/), verified 9 November 2026. The original combines reach, impact and confidence with effort as a divisor; this implementation explicitly changes the operational inputs and units.

Scores sort descending; exact score ties share average statistical rank. Within ties, opportunity ID sorts ascending solely for reproducible display and Top-K selection. Unavailable scores have no rank and appear last. Tied boundary selection is arbitrary and disclosed; it is not a preference.

## Descriptive comparison and sensitivity protocol

Run on the 1,500-row seed-42 synthetic input with the previously frozen semantic configuration. This is an execution and ranking-comparison scenario, not a new semantic holdout or a validation of business value. The finite synthetic catalog deliberately contains trade-offs and shares authoring assumptions with the scoring design.

Save input/config/source SHA-256 hashes, runtime versions, strategy weights, normalisation maxima, subgroup/account evidence, group assignments, all candidate scores/ranks, timings and failures. Refuse overwriting experiment folders. Separately test exact reproducibility of scores and evidence when row order changes.

For each pair of score methods, restrict to candidates with both scores known; disclose that intersection and each method's full coverage. Recompute average ranks within the intersection. Spearman correlation is Pearson correlation of those average ranks; undefined with fewer than two candidates or constant scores. Top-K agreement = intersection size / K where K = min(5, common candidate count); null if zero. Order ties by ID as above. Report each common candidate's change as comparison rank minus reference rank (positive = lower priority under comparison). These measures show agreement, not accuracy or superiority.

Predeclared scenarios: balanced default; enterprise/ARR emphasis (0.10, 0.60, 0.10, 0.20); reach emphasis (0.70, 0.10, 0.10, 0.10). Perturb each balanced weight independently by ±20%, renormalising, while holding groups/signals fixed. Compare each resulting score to balanced. Sensitivity here covers weights only; data perturbation and grouping robustness remain future work.

Segment representation: for each method's Top-5 rankable candidates, union the supporting customer IDs. For every globally resolved segment report selected customers / all uploaded customers in that segment, with numerator and denominator. Customers count once within a segment; segment totals and ratios are not fairness guarantees. Traceability = assigned feedback IDs / uploaded feedback IDs, with exact ID coverage checked before scoring. Timing is local process timing, not a cloud benchmark. No participant study or business outcome is inferred.
