# ProductLens AI progress discussion

Updated on 10 November 2026 for discussion on **10 November 2026**. Review and adapt these speaking notes before using them. They are a factual progress briefing, not the final academic report.

**Student:** Sofers Paul Durai Alexander · **Roll:** M24SME2042 · **Mentor:** Prof. Deepak Saxena

**Approved title:** Design and Evaluation of an Explainable AI-Assisted Product Intelligence System for Evidence-Based SaaS Feature Prioritisation

**10 November deployment update:** [Live app](https://valhalla-arkjg4bdxtfmm3d9z55dwu.streamlit.app/) now validates a 500-record CSV, groups it into 21 candidate opportunities and scores the 10 with sufficient inputs. An explicitly synthetic Defer review was saved to PostgreSQL and reread after reruns; a second workspace could not see it. A separate synthetic test review was recovered in a fresh browser session and after an owner-reported host reboot; its review/evidence JSON export was inspected.

## Suggested opening

“The project now has a working hosted prototype that uploads and validates feedback, groups related requests using a pinned sentence-embedding model, and lets me inspect the original evidence and distinct customers behind each group. It now also calculates transparent priorities, shows score contributions, and lets me change strategy weights and compare baselines. I have reproducible synthetic datasets with 500 and 1,500 records. I have also completed an initial held-out evaluation of the semantic grouping component, with settings selected only on tuning data.

“The results show both useful matches and clear limitations: duplicate links have high precision in this synthetic test, but many paraphrases are missed and broad groups sometimes combine different needs. I have retained the errors and source evidence rather than treating the AI output as authoritative. The scoring engine and an initial 1,500-record ranking comparison now work locally. Some candidates remain unranked because their inputs are incomplete. Stored human decisions now work in the hosted PostgreSQL backend with reasons and exact evidence snapshots. The source is published on GitHub and all 133 tests pass on Linux with PostgreSQL. My immediate priority is the remaining hosted input/export checks, further robustness evaluation and the report.”

## What can be demonstrated now

| Area | Verified status |
| --- | --- |
| CSV/Excel intake | Both tested locally; actual 500-row CSV upload and validation also verified in the hosted browser |
| Synthetic evidence | Seeded 500- and 1,500-record bundles; stable account signals and separate truth labels |
| Semantic grouping | Real MiniLM embeddings verified locally and hosted; 500-row hosted journey produced 21 candidate opportunities |
| Explainability at grouping stage | Original requests, representative source sentence, extracted terms, request counts and distinct customers |
| Research controls | Whole request families and customer accounts separated between tuning and evaluation; frozen configuration and source/model hashes |
| Automated verification | All 133 tests passed on Linux with real-model inference and PostgreSQL on 9 November; locally 132 passed and the PostgreSQL test is skipped |
| Published source | [GitHub repository](https://github.com/soferscbe/valhalla), original history preserved; [successful CI](https://github.com/soferscbe/valhalla/actions/runs/42658653667) |
| Scoring and strategy simulation | Working locally: account deduplication, provisional effort, configurable weights, factor contributions and exports |
| Vote/weighted/RICE-style ranking comparison | Initial 1,500-record descriptive run saved, with defined denominators and weight sensitivity |
| Accept/defer/override history | Local workflow tested; hosted Defer save/read, strategy-context separation and two-workspace isolation verified; a separate recovery test also passed after an owner-reported host reboot |
| Cloud deployment and full report | Hosted upload → grouping → scoring → saved review works; final acceptance checks and academic report remain incomplete |

The core workflow is deployed and demonstrable, including a saved PostgreSQL review. Fresh-session and post-reboot recovery have also been checked. Remaining hosted edge cases, further evaluation and the final report are unfinished.

## Initial results to explain accurately

The initial semantic experiment uses the **500-record** dataset: 250 tuning and 250 held-out records. The held-out set has 212 clear records and 38 challenge records. The main repetition-reduced results below use **56 unique normalised clear texts**.

| Metric | Result | Meaning |
| --- | ---: | --- |
| Theme adjusted Rand index | 0.606 | Chance-adjusted agreement with the designed theme partition; not 60.6% accuracy |
| Duplicate precision | 0.962 | Most predicted duplicate links in this particular synthetic test were correct |
| Duplicate recall | 0.472 | More than half of the reference duplicate links were missed |
| Duplicate F1 | 0.633 | Combined precision/recall summary |

Do not present this as “96% application accuracy.” It is one component, one synthetic design, and a particular pairwise metric. The 1,500-row dataset now supports an initial ranking comparison as well as the execution scale check. It is not an independent generalisation result.

Two useful failure examples: quota-alert recipient configuration can be confused with quota-threshold alerts; paraphrases about dashboard icons can be split apart. Multi-intent feedback is currently assigned to one group, so another need can be missed. The six-row sample can also over-merge unrelated needs into a broad group. Show the original feedback and stricter subgroups to explain why human review is needed.

## New scoring results to explain

The 1,500 synthetic records produced 27 candidate groups. Fourteen have enough inputs for effort-adjusted scoring; thirteen need effort clarification, and seven of those also lack complete urgency/alignment. All 27 remain visible. Do not describe the unranked candidates as low priority.

On the **14 candidates scored by both methods**, the balanced strategy's Top-5 has no overlap with vote or fixed-benefit Top-5, and four of five overlap with the RICE-style proxy. This demonstrates the consequence of business assumptions and an effort denominator; it does **not** prove the system is better. Both effort-adjusted methods share the same provisional cost proxy. Eight ±20% weight changes retained the Top-5; larger enterprise/reach scenarios each changed one member. This is local sensitivity on one synthetic fixture, not general robustness.

The formula is straightforward: normalise reach, resolved ARR, urgency and alignment; combine with explicit weights; divide by provisional effort. Repeated customers do not multiply account value. Effort counts each candidate duplicate subgroup once. Missing active factors prevent a score. Confidence in the RICE-style comparison is a declared common assumption, not an AI probability. See `docs/SCORING_PROTOCOL.md` and `docs/SCORING_RESULTS.md` for precise definitions.

## Five-minute demonstration

For the hosted demonstration, open https://valhalla-arkjg4bdxtfmm3d9z55dwu.streamlit.app/. Use the local setup below as a fallback. From the project directory:

```bash
source .venv/bin/activate
python -m productlens.embeddings
PRODUCTLENS_OFFLINE=1 python -m streamlit run app.py --server.address 127.0.0.1
```

Open `http://127.0.0.1:8501` on this laptop. This is a local address and cannot be sent to the professor as a hosted link. Keep the laptop awake and the terminal running. Prepare the model cache beforehand so the demonstration does not depend on the meeting's internet connection.

1. Upload `data/generated/v1.0.0_seed42_n500/inputs/feedback.csv`. Explain that every row is synthetic and missing uncertain signals are shown as warnings.
2. Show 500 feedback records versus 98 distinct customers. Explain why repeated requests are not equivalent to additional customer reach.
3. Click **Group related feedback**. Select an opportunity, inspect its representative request and source rows, then show its stricter candidate duplicate groups.
4. Point out one plausible grouping and one limitation. Scroll to **Prioritise with evidence**. Show the coverage message, a score contribution table, original inputs and a candidate needing missing-input review.
5. Change the account-value weight and explain the changed score/order. Show that the fixed baseline remains unchanged. Export scores and assumptions if useful.
6. Start a private review workspace, retain its recovery key, and save a clearly marked demonstration decision with a reason. Change a weight to show that the older decision remains historical. Automated demonstration records are not participant-study evidence.
7. Open `docs/SEMANTIC_RESULTS.md` and `docs/SCORING_RESULTS.md` to show measured findings and their limits. These are provisional candidate priorities, not approved roadmap decisions.

The built-in six-row sample is useful to explain the controls quickly, but is not the research dataset. For a demo fallback, keep the saved experiment results and this briefing available; do not substitute a static result while claiming live inference.

## Methodology and likely questions

**Where does Design Science Research fit?** Problem definition is approved; artefact design, implementation and a local component demonstration are underway; semantic evaluation and initial ranking comparisons are measured. The hosted core workflow is demonstrated; remaining hosted edge cases, broader evaluation and communication in the final report remain incomplete.

**What exactly does AI decide?** It represents feedback text and groups related requests. The separate deterministic engine calculates provisional rankings from explicit business factors and weights. AI does not select those weights or the final roadmap. Human accept/defer/override actions are stored separately with reasons and exact evidence snapshots.

**How is leakage reduced?** Known labels are separate from model inputs. The model sees only feedback text. Complete request families, including all paraphrases, stay in one split; customer accounts also do not cross splits. Common vocabulary, finite templates and the same authoring process remain limitations.

**Has the research question been answered?** No. The current work measures semantic grouping and demonstrates ranking disagreement, traceability and local weight sensitivity. That is partial evidence, not yet an answer about improved consistency, efficiency and evidence use in practice. There is no measured manual-workflow time saving, user study or real business impact.

**How much was AI-assisted?** Development, synthetic wording/labels and these draft notes have used AI assistance. Review and understand the implementation and comply with the institute's academic-integrity requirements. Do not present generated prose as independent student-authored research or invent participants/results.

## Questions to resolve with the mentor

- Is the planned quantitative synthetic evaluation acceptable for the core submission, with PM review included only if genuinely conducted?
- Are the proposed ranking comparisons and candid semantic limitations sufficient, or is a specific additional evaluation essential?
- Which baseline assumptions and business strategy should be emphasised when interpreting ranking changes?
- Confirm the MBA-specific declaration wording and current cover date, because the Annexure sample contains older degree/date placeholders.

## Remaining delivery plan and deadline risk

The stated deadline remains **15 November 2026**. The remaining scope is substantial; the following is a target sequence, not a completed schedule or a promise of an extension.

| Target | Work |
| --- | --- |
| Completed locally on 9 November | Transparent scoring, distinct-account aggregation, contributions and initial baseline/weight comparisons |
| Completed on 10 November | Core cloud deployment, PostgreSQL save, workspace isolation and recovery after an owner-reported reboot |
| 11–12 November | Hosted journey checks, data robustness and further evaluation/interpretation |
| 12–14 November | Student-reviewed results/limitations, report assembly, IEEE citations, Annexure formatting and demo rehearsal |
| 15 November | Final verification and submission by the prescribed deadline |

Protect deployment, evaluation and report time. Defer roadmap optimisation, conversational copilot, integrations and other stretch work. If progress slips, discuss the risk and essential evidence with the mentor rather than claiming incomplete work is finished.

## Evidence locations

- `PROGRESS.md`: dated executed checks, limitations and the next task.
- `docs/SEMANTIC_PROTOCOL.md`: predeclared procedure and metrics.
- `docs/SEMANTIC_RESULTS.md`: measured results and error interpretation.
- `experiments/semantic_v1/tuning/frozen_config.json`: selected parameters and provenance.
- `experiments/semantic_v1/heldout/`: predictions, metrics, challenge rows and duplicate errors.
- `experiments/semantic_v1/scale_check.json`: 1,500-row execution evidence.

- `docs/SCORING_PROTOCOL.md` and `docs/SCORING_RESULTS.md`: exact scoring assumptions and measured findings.
- `experiments/ranking_v1/`: input/config hashes, account/subgroup evidence, score tables, comparisons and sensitivity.
- `docs/scoring-demo.png`: verified local score explanation.

- `docs/REVIEW_WORKFLOW.md` and `docs/DEPLOYMENT.md`: local review behavior, exact cloud setup and remaining verification.

- `docs/hosted-scoring-2026-11-10.jpg` and `docs/hosted-review-2026-11-10.jpg`: actual hosted browser evidence, using synthetic data only.

- `docs/hosted-recovery-2026-11-10.jpg`: original saved test event restored after an owner-reported app reboot.

## Update on 11 November

No mentor discussion has occurred yet, according to the student. The hosted workflow remains demonstrated; owner confirms Data API disabled. XLSX and score export passed. Five new data robustness scenarios are complete: repeated-account invariance passed; effort uncertainty retained 4/5 Top-5; masking ARR for 30 accounts reduced score coverage from 14 candidates to one. This limitation should be discussed explicitly. Local tests: 135 passed/one PostgreSQL skip. Report template and demo/viva preparation are available locally; student interpretation, critical literature synthesis, abstract and declaration remain unfinished.
