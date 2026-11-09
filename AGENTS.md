# ProductLens AI — Standing Instructions for Codex / Astra

> **Start here.** These instructions apply to all work in the ProductLens AI repository. The student will supply the accepted proposal, IIT Jodhpur MBA-Tech Project Guidelines, Annexure I report-format guidelines, and a detailed project handoff in the Codex conversation. Read those sources **before making project or research decisions**. They take precedence over summaries in this file.

## 1. Project and constraints

- **Student:** Sofers Paul Durai Alexander | **Roll number:** M24SME2042
- **Programme:** Tech MBA, IIT Jodhpur | **Faculty mentor:** Prof. Deepak Saxena
- **Approved title:** *Design and Evaluation of an Explainable AI-Assisted Product Intelligence System for Evidence-Based SaaS Feature Prioritisation*
- **Application working name:** ProductLens AI
- **Submission deadline stated in the guidelines:** **15 November 2026**. Confirm any changed deadline with the student; do not infer an extension.
- **Starting status:** Proposal approved; **no application implementation completed yet**, unless the repository shows otherwise.
- **Critical expectation:** An end-to-end **working, tested, deployed** application, plus a defensible research evaluation and final report. Synthetic data is permitted. Do not use confidential Zoho/customer data.

## 2. First action: establish persistent project memory

**Before substantial implementation**, inspect the repository and attached source documents. If missing, create and maintain:

1. **`PROJECT_CONTEXT.md`** — concise, stable source of truth:
   - project objective, approved research question and scope;
   - authoritative document names/locations and key academic requirements;
   - architecture, tools, data model and why chosen;
   - core MVP acceptance criteria, out-of-scope/stretch features;
   - methodological decisions, evaluation metrics and their limitations;
   - confirmed constraints, risks and significant open questions.
2. **`PROGRESS.md`** — dated running status, updated **at the end of every meaningful milestone and session**:
   - current milestone and what actually works;
   - commands run, tests performed and results (pass/fail, with evidence or paths);
   - files added/changed, commits if made, deployment URL/status if verified;
   - bugs, blockers, risks and what has **not** been verified;
   - exactly **one recommended next task**, with 2–4 acceptance checks.
3. **`DECISIONS.md`** — short dated architecture/research decision log: decision, options considered, rationale and trade-offs. Create it when the first non-trivial decision arises.

Do not dump entire chats into these files. Keep them useful, factual and current. Never label a planned feature as complete. Never invent run results, deployment links, data, interviews, citations, experiment numbers or Git commits.

### Every new session

1. Read `AGENTS.md`, `PROJECT_CONTEXT.md`, `PROGRESS.md`, and relevant recent code/test files.
2. Inspect the repository state and run a minimal smoke test where feasible.
3. Summarise **verified status**, blockers and the next milestone in a few sentences.
4. Continue from the recorded next task; do not restart planning unless a blocker warrants it.
5. After work, update `PROGRESS.md` (and `PROJECT_CONTEXT.md`/`DECISIONS.md` if decisions changed).

## 3. Implementation scope and order

**Prioritise a reliable MVP over feature accumulation.** Aim for early deployment, then evaluation and report writing.

**Core milestones:**

1. **Foundation:** Python environment, repository structure, reproducible dependencies, locally runnable Streamlit app; upload/preview CSV or Excel; data validation.
2. **Synthetic evidence:** seeded generator with realistic SaaS feedback, customer and account signals; known theme labels stored separately from model input; tests for data integrity.
3. **AI understanding:** semantic embeddings; duplicate/related-request grouping; theme and underlying-opportunity extraction; evaluation against held-out or independently defined labels where applicable.
4. **Decision engine:** aggregate distinct customers and request volume separately; transparent configurable multi-factor scoring, documented normalisation and effort handling; evidence-linked explanations; vote-based, weighted and RICE-style baselines.
5. **User workflow:** ranked opportunities, segment/trend analyses, strategy/what-if weights, accept/override decisions and stored reasons; export where feasible.
6. **Delivery and research:** cloud deployment, automated tests, repeatable comparative experiments, robustness/sensitivity checks, properly documented outcomes, final report and live demonstration.

**Stretch only after core works:** capacity-based roadmap optimisation, dependency constraints, counterfactual explanations, conversational copilot, real integrations, complex authentication. Do not introduce unnecessary infrastructure or switch frameworks without a clear, recorded reason.

**Preferred initial stack:** Python, Streamlit, pandas/NumPy, sentence-transformers, scikit-learn, Plotly, pytest, straightforward persistence. Confirm installed versions and cloud feasibility; pin dependencies after validation. A different stack requires a concrete benefit and a recorded trade-off.

## 4. Engineering and verification rules

- Implement vertically: **working upload → grouping → scoring → review → deployed experience**, rather than disconnected mock screens.
- Use clean, understandable modules, deterministic random seeds, explicit data schemas and reproducible scripts.
- Never hide a hardcoded demo ranking behind an AI label. If AI or an external API is unavailable, make fallback behaviour explicit and test it.
- Keep AI interpretation separate from the **auditable, deterministic ranking formula**. Show input signals, score contributions, weights and source feedback.
- Validate customer-level deduplication, missing values, changing weights, ties, empty datasets and noisy/ambiguous feedback.
- Use pytest for core logic; validate the deployed user journey as well as local behaviour.
- Whenever a milestone is called complete, state **how it was tested**. If a test could not run, say why.
- Do not commit secrets, credentials, proprietary data or large generated artefacts unnecessarily. Maintain `.gitignore` and a documented setup/launch process.
- Prefer small coherent commits. Only record a commit hash after the commit has actually succeeded.
- Maintain `README.md` with setup, configuration, run, test and deployment instructions.

## 5. Research and academic integrity rules

- Follow the **actual accepted proposal** and the two **official IIT Jodhpur guideline files**, not generic MBA templates. The final report is distinct from the short proposal.
- Use **Design Science Research** as the planned framework, with actual artefact demonstration and evaluation.
- Simulated records must be described as **synthetic**, not real business/customer outcomes.
- Ground-truth synthetic theme labels must **not leak into clustering inputs**; separate training/tuning from evaluation as practical.
- Report appropriate clustering quality measures; for ranking comparison use rank changes, Top-K agreement, correlation, stability, segment representation and evidence traceability. Define metrics precisely before interpretation.
- **Do not claim any prioritisation ranking is universally correct.** Business priorities depend on strategy, assumptions and trade-offs.
- Document experiment configuration (seed, dataset version, embedding model/version, thresholds, scoring weights), scripts, outputs and failures. Never fabricate performance numbers or user-study participants.
- Cite **real, verified** literature using the prescribed IEEE style. Never invent bibliographic details, DOIs, URLs or quotations.
- If the university restricts AI-generated academic writing, support the student's research, analysis, organisation, editing and understanding without pretending generated material is independent student-authored work. The student must review and take responsibility for the final report.
- Follow Annexure I's exact report format, including cover/declaration, abstract limit, preliminary numbering, main-section formatting, captions, references and final PDF checks; verify details from the attached document.

## 6. Deadline protection and quality gates

The project begins close to its submission deadline. **Build the smallest complete application first and deploy before writing the final conclusions.** Reserve real time for comparative experiments, analysis, formatting, reproducibility and viva preparation.

Stop adding features if the remaining time risks the following minimum delivery package:
- functioning deployed URL and reproducible local run;
- clean source and README;
- synthetic dataset generator + documented evaluation split/labels;
- tested semantic grouping and transparent prioritisation;
- baseline comparison with actual experimental outputs;
- evidence-backed explanation and human review flow;
- academic report aligned to official formatting and citations;
- screenshots/demo path and candid limitations.

**Always distinguish:** completed / tested locally / deployed and verified / planned / blocked.

## 7. What to do right after receiving this file

1. Read the user's handoff message and three referenced documents.
2. Inspect the repository rather than assuming it is empty.
3. Create `PROJECT_CONTEXT.md` and `PROGRESS.md` with truthful starting status.
4. Write a short implementation plan and explicit Day-1 acceptance criteria.
5. Immediately build and run a minimal Streamlit workflow that uploads, validates and displays feedback data.
6. Run tests, record results in `PROGRESS.md`, and tell the student exactly what works and what comes next.

**Working principle:** Build evidence, not just impressive screens. The student should be able to explain and defend every important product, engineering and research decision.
