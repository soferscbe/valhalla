# ProductLens AI demonstration and viva guide

Prepared 11 November 2026. A preparation aid, not a script claiming personal work or participant outcomes. Rehearse the explanation in your own words.

## Eight-minute demonstration

1. **Purpose (one minute).** Explain the approved question: whether explainable AI assistance can support consistency, efficiency and customer evidence in SaaS prioritisation. Say the records are synthetic and that business superiority is not established.
2. **Input (one minute).** Open https://valhalla-arkjg4bdxtfmm3d9z55dwu.streamlit.app/ and select Try synthetic sample. Point to six records but five distinct customers. Explain that repeated accounts remain evidence, but must not inflate ARR/reach.
3. **Grouping (one minute).** Click Group related feedback. Inspect the two candidate opportunities and stricter duplicate subgroups. Show one mixed group as a limitation. Text embeddings propose interpretations; groups are not approved feature specifications.
4. **Scoring (two minutes).** Explain benefit divided by provisional effort. Open calculation inputs and trace a score to source rows. State ARR/person-day units, default 30/30/20/20 weights, customer deduplication, and unknown-score handling. Increase Account value from 30 to 100 to demonstrate a sample priority-order change, then restore 30. Fixed weighted baseline remains fixed.
5. **Human control (one minute).** Open a private review workspace and keep its key private. Record an explicitly labelled demo decision and reason. Show the computed score remains unchanged. Change a weight to show historical versus applicable decisions, then restore it. Avoid projecting a recovery key.
6. **Evidence (two minutes).** Explain 1,500 rows/293 customers/27 candidates/14 scorable. Compare votes, weighted and RICE-style methods on the same 14 candidates. Explain effort uncertainty (4/5 retention) and missing ARR (14 to 1 scored); these are useful limitations, not failures to conceal. End with the next validation needed: independently collected language and genuine PM evaluation.

## Before presenting

Open the app early to allow a sleeping host/model to start. Test internet and your private key. Keep the six-row CSV and 500-row generated CSV available. Keep docs/hosted-scoring-2026-11-10.jpg, hosted-review-2026-11-10.jpg and hosted-recovery-2026-11-10.jpg as explicitly dated fallback evidence. If hosting is unavailable, show the recorded evidence and local run; do not call screenshots a live demonstration. The local command is `.venv/bin/streamlit run app.py` from the repository root.

## Questions to practise

**Where is the AI?** The pinned MiniLM encoder maps normalized unique feedback wording into vectors. Complete-linkage cosine clustering proposes broad and stricter groups. The ranking formula is deterministic and independently auditable; no LLM decides priorities.

**Why this is Design Science Research?** The artefact addresses the proposal's problem and is designed, demonstrated and evaluated. The contribution currently consists of a working integrated decision aid and bounded synthetic evidence. Useful effects on real PM decisions remain unmeasured.

**Are the labels leaked?** The model reads feedback text only. The generator stores labels separately. Whole request families and customers are separated for tuning/holdout, but shared vocabulary and a small authored catalog still limit independence.

**Is 0.6065 accuracy?** No. It is adjusted Rand index for held-out unique-text theme partition agreement. NMI is 0.8282. Duplicate-pair precision/recall are 0.9615/0.4717, so missed paraphrases remain substantial. Neither metric establishes correct roadmap choices.

**Why is RICE agreement high?** Both formulas share the same effort denominator. RICE here is a proxy using submitting customers, urgency/5, common confidence 0.5 and person-days. High agreement is not independent proof of correctness.

**Why does missing ARR matter so much?** One unresolved customer can make an opportunity's aggregate ARR unknown. With ARR active, the system refuses to produce a misleading score. Thirty masked accounts affected thirteen previously scorable opportunities in the declared stress test.

**Can more feedback change an unchanged opportunity's score?** Yes. Reach and ARR normalize by maxima across the current candidate set. Different maxima change relative contributions. IDs also depend on grouped wording, so they are not permanent product feature identifiers.

**What does explainable mean here?** Source rows, resolved accounts, subgroup effort, normalized factors, weights and contributions are inspectable. This is evidence and calculation transparency; no human comprehension study has validated perceived explainability.

**Did it save time?** Local grouping and scoring were timed. There was no measured manual comparison, no participant study, and no established time saving or business benefit.

**Is it production-ready?** It is a deployed research demonstrator. Recovery after an owner-reported reboot and workspace isolation passed. Reviewer labels are self-reported, access is by bearer key, and load, production authentication and operational availability are not established.

## Mentor discussion points

Demonstrate the current system. Discuss synthetic validity, conservative missingness, proxy effort/impact, and the limited answer to the research question. Confirm the permitted scope and disclosure of AI assistance, declaration wording, and final PDF expectations. No mentor feedback has yet been received as of 11 November. The submission deadline remains 15 November 2026.
