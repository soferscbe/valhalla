# Data robustness protocol v1

Declared 11 November 2026 before execution. This extends, without replacing or retuning, the frozen semantic and scoring experiments. It is a synthetic diagnostic, not independent semantic accuracy or a user study.

Use the existing 1,500-row seed-42 bundle and frozen semantic configuration. Recompute the base pipeline and verify its assignments and numeric scores against ranking_v1. All grouping settings, weights and model revision remain fixed. No truth labels are read.

Scenarios, selected before results:

1. Row permutation, seed 20261111: rerun grouping and scoring; require identical assignments and scores within 1e-10.
2. Vocal-account repetition: choose the lexicographically first customer with records; append ten copies of each of its records with new IDs (subject to the 2,000-row cap). Rerun grouping. Expect reach, ARR, urgency, alignment, effort and strategy scores to remain unchanged; counts and votes may grow.
3. Account-value uncertainty: multiply every record of each customer by the same independently drawn uniform factor in [0.8,1.2], seed 20261111. Hold group assignments fixed. Report ranking changes.
4. Effort uncertainty: multiply every record within each duplicate subgroup by the same independently drawn uniform factor in [0.8,1.2], seed 20261112. Hold group assignments fixed. Report ranking changes.
5. Account-value missingness: remove all ARR observations for 10% of distinct customers (ceil, seeded sample 20261113), so repeated rows cannot accidentally restore a masked value. Hold grouping fixed. Disclose score coverage before calculating agreement.

For each scenario save transformed-input hash, assignments, scores, exact traceability, coverage and comparison to base. Spearman and Top-5 agreement use only common scorable candidates, with the conventions in SCORING_PROTOCOL.md. Also report retention of the original unrestricted base Top-5 in the scenario Top-5, dividing by the original base K, and the number of originally scored candidates that become unranked. These prevent common-intersection agreement hiding missingness losses. Save selected customer/subgroup changes for audit. These are single seeded stress scenarios, not a sampling distribution, confidence interval or population guarantee. No new wording or semantic-noise stress is assessed.
