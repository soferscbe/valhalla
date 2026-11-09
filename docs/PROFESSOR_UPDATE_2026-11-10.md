# ProductLens AI progress discussion

Prepared on 9 November 2026 for discussion on **10 November 2026**. Review and adapt these speaking notes before using them. They are a factual progress briefing, not the final academic report.

**Student:** Sofers Paul Durai Alexander · **Roll:** M24SME2042 · **Mentor:** Prof. Deepak Saxena

**Approved title:** Design and Evaluation of an Explainable AI-Assisted Product Intelligence System for Evidence-Based SaaS Feature Prioritisation

## Suggested opening

“The project now has a working local prototype that uploads and validates feedback, groups related requests using a pinned sentence-embedding model, and lets me inspect the original evidence and distinct customers behind each group. I have reproducible synthetic datasets with 500 and 1,500 records. I have also completed an initial held-out evaluation of the semantic grouping component, with settings selected only on tuning data.

“The results show both useful matches and clear limitations: duplicate links have high precision in this synthetic test, but many paraphrases are missed and broad groups sometimes combine different needs. I have retained the errors and source evidence rather than treating the AI output as authoritative. The transparent scoring engine, baseline ranking comparison, stored human decisions and cloud deployment are still pending. My immediate priority is completing that smallest end-to-end workflow, followed by comparative experiments and the report.”

## What can be demonstrated now

| Area | Verified status |
| --- | --- |
| CSV/Excel intake | Working locally: validation, actionable errors, preview and customer/record counts |
| Synthetic evidence | Seeded 500- and 1,500-record bundles; stable account signals and separate truth labels |
| Semantic grouping | Real MiniLM embeddings running locally, broad opportunities and stricter candidate duplicates |
| Explainability at grouping stage | Original requests, representative source sentence, extracted terms, request counts and distinct customers |
| Research controls | Whole request families and customer accounts separated between tuning and evaluation; frozen configuration and source/model hashes |
| Automated verification | Final run: 87 tests passed on 9 November, including the real-model upload-to-grouping journey and UI state checks |
| Scoring and strategy simulation | Not implemented |
| Vote/weighted/RICE ranking comparison | Not run |
| Accept/override and durable history | Not implemented |
| Cloud deployment and full report | Not completed; there is no verified public URL |

The current local demo is a completed component workflow, not the completed approved project. Viewing grouped evidence is not yet a stored accept/override decision workflow.

## Initial results to explain accurately

The initial semantic experiment uses the **500-record** dataset: 250 tuning and 250 held-out records. The held-out set has 212 clear records and 38 challenge records. The main repetition-reduced results below use **56 unique normalised clear texts**.

| Metric | Result | Meaning |
| --- | ---: | --- |
| Theme adjusted Rand index | 0.606 | Chance-adjusted agreement with the designed theme partition; not 60.6% accuracy |
| Duplicate precision | 0.962 | Most predicted duplicate links in this particular synthetic test were correct |
| Duplicate recall | 0.472 | More than half of the reference duplicate links were missed |
| Duplicate F1 | 0.633 | Combined precision/recall summary |

Do not present this as “96% application accuracy.” It is one component, one synthetic design, and a particular pairwise metric. The 1,500-row dataset has passed an execution scale check; it has not supplied an independent generalisation result or the final ranking comparison.

Two useful failure examples: quota-alert recipient configuration can be confused with quota-threshold alerts; paraphrases about dashboard icons can be split apart. Multi-intent feedback is currently assigned to one group, so another need can be missed. The six-row sample can also over-merge unrelated needs into a broad group. Show the original feedback and stricter subgroups to explain why human review is needed.

## Five-minute demonstration

Before the meeting, from the project directory:

```bash
source .venv/bin/activate
python -m productlens.embeddings
PRODUCTLENS_OFFLINE=1 python -m streamlit run app.py --server.address 127.0.0.1
```

Open `http://127.0.0.1:8501` on this laptop. This is a local address and cannot be sent to the professor as a hosted link. Keep the laptop awake and the terminal running. Prepare the model cache beforehand so the demonstration does not depend on the meeting's internet connection.

1. Upload `data/generated/v1.0.0_seed42_n500/inputs/feedback.csv`. Explain that every row is synthetic and missing uncertain signals are shown as warnings.
2. Show 500 feedback records versus 98 distinct customers. Explain why repeated requests are not equivalent to additional customer reach.
3. Click **Group related feedback**. Select an opportunity, inspect its representative request and source rows, then show its stricter candidate duplicate groups.
4. Point out one plausible grouping and one limitation. Do not describe a broad group as an accepted feature or priority.
5. Open `docs/SEMANTIC_RESULTS.md` or `experiments/semantic_v1/heldout/evaluation.json` to show actual results and the frozen evaluation conditions.

The built-in six-row sample is useful to explain the controls quickly, but is not the research dataset. For a demo fallback, keep the saved experiment results and this briefing available; do not substitute a static result while claiming live inference.

## Methodology and likely questions

**Where does Design Science Research fit?** Problem definition is approved; artefact design, implementation and a local component demonstration are underway; semantic evaluation is measured. End-to-end prioritisation evaluation and communication in the final report remain incomplete.

**What exactly does AI decide?** It represents feedback text and groups related requests. It does not currently produce a final priority ranking. The next engine will use an auditable deterministic formula with explicit weights, source signals and human decisions.

**How is leakage reduced?** Known labels are separate from model inputs. The model sees only feedback text. Complete request families, including all paraphrases, stay in one split; customer accounts also do not cross splits. Common vocabulary, finite templates and the same authoring process remain limitations.

**Has the research question been answered?** No. The current result evaluates semantic grouping only. Claims about consistency, efficiency and use of evidence versus conventional prioritisation require the planned end-to-end baseline comparisons. No user study or real business impact has been observed.

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
| 9–10 November | Transparent scoring, distinct-account aggregation, score contributions and baseline implementations |
| 10–11 November | Minimal strategy/decision workflow and early cloud deployment with durable decisions |
| 11–12 November | Hosted journey checks, actual baseline comparisons and sensitivity experiments |
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
