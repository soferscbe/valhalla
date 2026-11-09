# ProductLens AI progress

**Current verified status — 9 November 2026:** local upload → validation → real semantic grouping → deterministic scoring → saved human review works. Latest full suite: **132 passed, 1 skipped** (real PostgreSQL integration requires a configured test database). Local persistence/recovery and browser review save are verified. Linux CPU dependency resolution and cloud entrypoint are prepared; actual hosted operation, PostgreSQL persistence, broader data robustness and final report remain incomplete. Deadline is 15 November.

## 5 November 2026 — project memory established before implementation

Verified starting state: repository contains `AGENTS.md` and three academic source documents; no application, tests, environment or existing memory files. Git is on `master` with no commits. Source documents and handoff have been read. No application smoke test was possible at this point.

Created `PROJECT_CONTEXT.md`, `PROGRESS.md` and `DECISIONS.md` before application code. Recorded approved scope, source locations, report requirements, deadline, risks, architecture and milestone order. No source documents changed.

Checks performed:

- `rg --files`, `ls -la`, `git status --short`: only the four initial source files, all untracked.
- `git log -1 --oneline`: reports no commits (expected for an uninitialised history).
- Source extraction: pypdf read both PDF files (2-page proposal, 1-page guidelines); python-docx read Annexure paragraphs and tables.
- Runtime inventory: system Python 3.9.6; bundled Python 3.12.14, pandas 2.2.3, NumPy 2.3.5 and openpyxl 3.1.5 available. Streamlit and pytest missing in bundled runtime. Application dependency validation is pending.

Status: project memory complete; foundation planned; semantic grouping, scoring, synthetic generator, experiments, report and deployment not implemented. No deployed URL or commits.

## Day-1 acceptance criteria

1. Documented isolated environment can start Streamlit locally without an API key.
2. CSV and XLSX feedback can be parsed, validated and displayed; malformed files and invalid required/optional fields produce actionable errors.
3. Tests exercise empty input, missing/duplicate IDs, repeated customers, missing text and invalid optional signals; valid data preserves string IDs and does not mutate source frames.
4. Run core tests, Streamlit app smoke tests and a local HTTP health check; record actual results and any unverified browser/deployment behaviour.

## 5 November 2026 — foundation implemented and tested locally

**Works:** Streamlit CSV/XLSX upload, format/size/row-limit checks, required identity/text validation, optional business-signal validation, explicit errors/warnings, synthetic sample, preview and distinct customer versus record counts. Leading-zero text IDs are preserved; repeated customers retained; duplicate feedback IDs rejected. Unknown columns excluded; missing optional signals not imputed. Invalid replacement uploads clear the successful preview. No uploads saved to disk.

**Files added:** `app.py`, `productlens/__init__.py`, `productlens/ingestion.py`, `tests/test_ingestion.py`, `tests/test_app.py`, `data/sample_feedback.csv`, `.gitignore`, `.python-version`, `.streamlit/config.toml`, `pyproject.toml`, `requirements.txt`, `README.md`. Updated context and progress after implementation. Existing academic source documents and `AGENTS.md` unchanged.

**Commands and observed results:**

- Bundled Python 3.12.14 `-m venv .venv`: succeeded. Initial sandboxed pip install failed because network access was denied; an approved elevated install succeeded. No global Python environment modified.
- `.venv/bin/python -m pip install --no-cache-dir --disable-pip-version-check streamlit pandas==2.2.3 numpy==2.3.5 openpyxl==3.1.5 pytest`: succeeded; Streamlit 1.66.1 and pytest 9.2.0 installed.
- `.venv/bin/python -m pytest -q`: **39 passed in 10.41s**, exit 0. Test evidence resides in `tests/test_ingestion.py` and `tests/test_app.py`; output observed in this session. Includes actual AppTest upload-widget interactions for CSV/XLSX and invalid-data handling, not just parser unit tests.
- `.venv/bin/python -m pip check`: **No broken requirements found**, exit 0.
- `.venv/bin/python -m pip freeze > requirements.txt`: captured validated direct/transitive package versions.
- `.venv/bin/python -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8501`: sandbox initially denied socket binding; approved elevated launch succeeded on loopback. Server left running at `http://127.0.0.1:8501` at session end; availability depends on process lifetime.
- Local HTTP checks using `urllib.request.urlopen`: sandbox initially denied socket connection; approved elevated check returned `/_stcore/health` **200 `ok`** and `/` **200**, 6,467 bytes HTML.

**Status:** Day-1 foundation acceptance checks passed locally. No known failing tests. AppTest is a simulated Streamlit interaction test; visual browser QA and hosted end-to-end testing have **not** been performed. No cloud URL, fresh-machine/Linux installation, semantic model, clustering, prioritisation, persistence, generator or research evaluation verified. The six hand-written sample rows are not the seeded research dataset. No commits made; source files remain untracked.

**Risks:** dependency installation and local socket operations required environment approval; subsequent sessions may need the same. Cloud compatibility remains unverified. Deadline remains 15 November 2026. Planned semantics, scoring and research work must be kept small enough to protect deployment and evaluation time.

## 5 November 2026 — synthetic-evidence milestone completed locally

**Baseline:** Reread repository instructions, context, progress, decisions and relevant code; prior source documents/handoff remain the accepted sources read earlier in this session. Before changes, `.venv/bin/python -m pytest -q` returned **39 passed in 0.82s**. No application regressions or new blockers found.

**Implemented:** Seeded generator v1.0.0 with configurable row count (200–10,000), default seed 42/500 rows; 32 authored specific-request families, 96 base phrasings, six clear themes and explicit overlapping/vague examples. Stable customer signals, repeated vocal accounts, business-value/volume conflicts and a fixed-window emerging usage-alert trend. Full feedback, tuning/evaluation subsets, minimal text-only model inputs, truth labels/account registry and deterministic source/file-hash manifest are separate outputs. Whole families and accounts remain isolated between approximately equal splits. No labels or generation metadata enter feedback/model inputs. The CLI refuses to overwrite existing output directories.

**Files added:** `productlens/synthetic.py`, `productlens/synthetic_catalog.py`, `tests/test_synthetic.py`, `docs/SYNTHETIC_DATA.md`.

**Files updated:** `tests/test_app.py` (generated-file upload journey), `.gitignore` (generated bundles), `README.md`, `PROJECT_CONTEXT.md`, `DECISIONS.md`, `PROGRESS.md`. No dependencies added; existing application and ingestion code unchanged.

**Generated outputs:**

- `data/generated/v1.0.0_seed42_n500/`: **500 records**, 250 tuning / 250 evaluation; 98 distinct submitting customers; 425 clear, 50 overlapping, 25 vague records. Full app upload file: `inputs/feedback.csv`; reproducibility evidence: `manifest.json`. Content SHA-256: `d05cba31a08bd3f2f00707d5f81d045b973e0aea4f8119b06d4b54ff484d7e37`.
- `data/generated/v1.0.0_seed42_n1500/`: **1,500 records**, 748 tuning / 752 evaluation; 293 distinct submitting customers. This verifies proposal-scale generation, not independent additional research evidence. Content SHA-256: `e6b0dc3e3af37059b6f7f127f3f1e98071f99496fefc93d69c659d6b1b362749`.
- These bundles are local and Git-ignored; regenerate from the documented command. They are not uploaded to any external service.

**Commands/checks and actual results:**

- `.venv/bin/python -m productlens.synthetic --rows 500 --seed 42` and `--rows 1500 --seed 42`: **passed**, wrote the bundles above.
- Initial expanded suite: **62 passed in 1.76s**. Added truth-annotation corruption detection and case/whitespace-normalised split checks, then final `.venv/bin/python -m pytest -q`: **63 passed in 1.79s**, exit 0.
- Tests cover 200/500/1,000/1,500 rows, fixed-seed frame/file equality, different seeds, one-to-one labels, account consistency, input allowlists, whole-family/duplicate/customer/text split isolation, valid dates/signals, business conflicts, emerging trend, challenge eligibility, label/account corruption, bad configuration, manifest hashes, CLI output and refusal to overwrite.
- Generated 500-row CSV successfully uploaded through Streamlit AppTest: no exception/error, validation success, 500 preview rows and correct distinct-customer count; missing effort/other uncertain signals displayed as warnings. This is simulated UI verification, not browser visual QA.
- Independently regenerated both bundles into temporary directories after final integrity changes: **all seven CSV files in each bundle reproduced byte-for-byte**. Refreshed manifests from the regenerated bundles to capture final source hashes; content hashes unchanged.
- Direct descriptive inspection of the 500-row fixture: dashboard customisation = 128 requests / six customers / 793 synthetic votes; audit and identity = 34 requests each; 52 of 68 usage-alert requests in the latest 30 days. These verify constructed scenarios, not model findings.
- `git check-ignore data/generated/v1.0.0_seed42_n500/inputs/feedback.csv`: confirms generated output ignored. `git status --short`: source files remain untracked, no commits made. `git diff --check` exited 0 but has no tracked diff to inspect in this initial repository.

**Status and limits:** Synthetic-evidence acceptance checks passed locally. No known failing tests. Labels are authored synthetic references, not independent human annotation. Finite wording, repeated text and shared generator vocabulary can inflate results despite the family holdout; documented unique-text/family-weighted diagnostics are required alongside future row-based metrics. Overlapping/vague requests remain in inputs but are ineligible for initial single-label/duplicate metrics. No model quality, ranking benefit or real-world performance measured. No browser visual QA, cloud deployment or Linux compatibility verified; local HTTP availability was not rechecked in this milestone. Deadline remains 15 November 2026.

## 5–9 November 2026 — semantic grouping and measured evaluation

**Implemented and verified locally:** pinned MiniLM embeddings on CPU; normalised distinct-text encoding; complete-linkage cosine grouping at broad-opportunity and stricter duplicate levels; medoid source sentence and extractive terms; source IDs, request counts and distinct customers; long-input flags, 2,000-row grouping cap, explicit model errors, no fake semantic fallback. Streamlit exposes group evidence and, in the final 9 November UI update, candidate duplicate groups within each opportunity. Results persist across inspection reruns and clear when inputs change. No final priority ranking or stored review decisions exist yet.

**Files added:** `productlens/embeddings.py`, `grouping.py`, `grouping_metrics.py`, `semantic_experiment.py`, `ui_semantics.py`; `tests/test_grouping.py`, `test_semantic_app.py`, `test_semantic_experiment.py`, `test_semantic_integration.py`; `config/semantic.json`; `docs/SEMANTIC_PROTOCOL.md`, `docs/SEMANTIC_RESULTS.md`; `experiments/semantic_v1/` configurations, asset receipts, predictions, metrics, challenge/error evidence and scale check.

**Files updated:** `app.py`, `.gitignore`, `pyproject.toml`, `requirements.txt`, `README.md`, context/decision/progress files. Model cache and temporary wheel/download diagnostics remain ignored; generated synthetic data unchanged.

**Installation and failures:** ordinary pip downloads were extremely slow (roughly 16–22 kB/s). Stopped that task-owned installer and used concurrent public downloads verified against PyPI SHA-256 values, then installed from `tmp/wheels` with `--no-index`. Pinned public model assets were verified against Hugging Face content hashes and cached locally. Temporary scripts are in ignored `tmp/`; final setup uses normal pip and the model loader, not those diagnostics. `pip check` passed; the environment was frozen to `requirements.txt`. No feedback was sent to a model API. CPU packages include sentence-transformers 6.2.0, scikit-learn 1.9.1, transformers 5.22.1 and Torch 2.15.0.

**Commands and actual checks:**

- Before semantic work: existing **63 tests passed in 2.08s**.
- `PRODUCTLENS_OFFLINE=1 .venv/bin/python -m productlens.embeddings`: loaded the pinned revision locally, CPU, 384 dimensions.
- First expanded default test run: **3 failed, 82 passed, 2 skipped**. All failures were relative paths in the newly added AppTest tests resolving to `tests/app.py`; corrected to absolute entrypoint paths. Subsequent default run: **85 passed, 2 skipped in 3.78s** (only real-model opt-ins skipped).
- `.venv/bin/python -m productlens.semantic_experiment tune --dataset data/generated/v1.0.0_seed42_n500 --output experiments/semantic_v1/tuning` with offline cache: succeeded; froze thresholds **0.20 / 0.55** using tuning only.
- Separate `semantic_experiment evaluate` with that frozen file and `--output experiments/semantic_v1/heldout`: succeeded without any held-out threshold adjustment. Retained all 250 predictions, including 38 challenge records.
- First real-model full suite: **87 passed in 5.32s**. On resuming 9 November, **87 passed in 8.70s**. Final run after duplicate-subgroup UI/test changes: `PRODUCTLENS_OFFLINE=1 PRODUCTLENS_TEST_REAL_MODEL=1 .venv/bin/python -m pytest -q` → **87 passed in 6.35s**, exit 0.
- Tests include actual-model repeatability/text sensitivity, truncation, generated 500-row upload-to-grouping, source/count traceability, deterministic input ordering, complete-linkage anti-chaining, empty/small/invalid data, exact/unique-text pair metrics, frozen evaluation safeguards, failure messages and stale state clearing.
- 9 November 1,500-row execution check with frozen settings: **1,500 assignments retained**, 27 broad groups, no truncated rows, approximately **2.45s** including model loading. Saved `experiments/semantic_v1/scale_check.json`; no new accuracy claim.
- Verified app config is byte-identical to the frozen tuning config, source/runtime hashes still match, and the held-out report's frozen-config digest matches. Model asset receipt totals **91,567,913 bytes** (about 87.3 MiB).

**Measured held-out findings:** 212 clear rows / 56 unique normalised clear texts; 25 overlapping and 13 vague rows separately retained. Unique-text theme ARI **0.6065**, NMI **0.8282**; duplicate precision **0.9615**, recall **0.4717**, F1 **0.6329**. Row-based duplicate F1 is **0.6640**, falling to **0.5040** when identical-text pairs are excluded. High precision does not mean 96% overall accuracy; missed paraphrases and repeated templates matter. See `docs/SEMANTIC_RESULTS.md` for errors, denominators, timing and limitations.

**Browser/demo verification on 9 November:** started Streamlit on loopback at `http://127.0.0.1:8501`; exercised the six-row sample, real semantic grouping and original evidence in the in-app browser. After an initial module update was not reflected in the running process, restarted the task-owned server, then verified the final duplicate-subgroup table. The sample produced two broad groups; the five-record group over-merges reports, audit changes and alerts. Some stricter subgroups also need correction. This is documented, not hidden or fixed by retuning the holdout. Screenshot: `docs/semantic-demo.png`. Server left running at session end; restart it if the process has stopped. Generated 500-row upload was tested through AppTest, not through the browser file picker. No hosted journey has been tested.

**Limits/risks:** all-row exclusive assignment misses overlapping intents; vague feedback can join clear groups; broad groups can over-merge and stricter groups miss paraphrases. Review is required before interpreting a group as a feature. The six-day interval to submission makes remaining delivery scope high risk. Local measured peak RSS was about 567 MiB; cloud/Linux compatibility, concurrent usage and durable decisions are still unverified. No prioritisation experiment, PM study, business outcome or final report is complete.

## 9 November 2026 — professor discussion preparation

Created `docs/PROFESSOR_UPDATE_2026-11-10.md` for tomorrow's discussion: suggested opening, factual status table, exact metric interpretation, five-minute offline demo path, methodology questions, mentor clarifications and a target delivery sequence through 15 November. Updated README/context/decisions and semantic results to distinguish completed local work from pending end-to-end work. This is a discussion aid for student review, not an independently student-authored final report. Nothing was sent to the professors or published.

**Git checkpoint:** created branch `codex/semantic-milestone`; the initial commit attempt failed because no author identity was configured. After the student supplied their email, configured the author identity for this repository only, restaged the progress log, and passed `git diff --cached --check`. Successfully saved implementation, documentation, tests and small experimental artefacts in commit `c00669b0cebc45b722cb4ec41d285e9c2e38d5b2` (`Build tested feedback ingestion and semantic grouping prototype`). Nothing was pushed. Supplied academic PDF/DOCX source documents remain untracked. No application code changed during this checkpoint operation; the preceding 87-test verification still applies.

## 9 November 2026 — decision engine and ranking comparison completed locally

Implemented `productlens/scoring.py`, `ui_scoring.py`, and `ranking_experiment.py`, integrated priorities into the existing app, and declared `docs/SCORING_PROTOCOL.md` before the first experiment. Added core, app and experiment tests. Deterministic aggregation separates accounts, requests and endorsements; account conflicts and missing active factors remain visible; provisional effort counts each duplicate subgroup once. Strategy controls expose contributions, fixed/vote/RICE-style comparisons, segment coverage and a CSV export. No stored decisions or cloud delivery are implied.

Checks so far: baseline **87 passed in 5.52s**; new scoring core **22 passed in 0.68s**; expanded suite **112 passed in 7.11s**; with experiment tests, `PRODUCTLENS_OFFLINE=1 PRODUCTLENS_TEST_REAL_MODEL=1 .venv/bin/python -m pytest -q` → **114 passed in 6.83s**. Real-model 500-row AppTest now reaches scored priorities. The 1,500-row ranking CLI completed with 27 candidates and exact 1,500/1,500 ID traceability. Coverage: strategy 14, votes 27, fixed weighted 20, RICE-style 14. Results/configuration/provenance saved under `experiments/ranking_v1/`. Thirteen strategy candidates are unrankable due to unknown effort, seven also lacking complete urgency/alignment. Live-browser scoring QA and the final documentation update subsequently completed as recorded below.

**Final verification:** after adding the scoring-assumptions JSON export and readable missing-score display, the full offline real-model suite passed **114 tests in 8.07s**. Ranking report input, grouping-config and source hashes were independently checked against the current files and all matched. `git diff --check` passed. No changes were made to frozen semantic model/grouping/metric code or thresholds. No new dependencies were introduced. Experiment CSV reproduction is tested with controlled embeddings; a second real-model 1,500-row ranking run was not performed.

**Live browser:** restarted the task-owned local server to load imported modules. The sandboxed launch failed to bind its socket (`PermissionError`); an approved local launch succeeded at `http://127.0.0.1:8501`, session 49230. The six-row sample produced two scored candidates. Increasing account-value weight from 30 to 99 changed the priority order: the broad usage/changes/email group moved above the dashboard keyboard group; factor contributions updated and fixed weighted baseline scores stayed unchanged. Browser AX and screenshot checks verified the explanation and retained source-review controls. Screenshot: `docs/scoring-demo.png`; local tab/server left available for demonstration. Browser downloads were not clicked; CSV escaping and content generation are covered by automated tests. Actual 500-row upload/scoring is verified through AppTest, not the browser file picker. No hosted journey is verified.

**Actual comparison findings:** among 14 shared rankable candidates, balanced-vs-votes Spearman −0.3363 / Top-5 agreement 0/5; vs fixed weighted benefit −0.2442 / 0/5; vs RICE-style 0.9385 / 4/5. Enterprise and reach emphasis each changed one Top-5 member. All eight ±20% weight perturbations preserved Top-5; seven preserved all ranks. First-run grouping took 1.8823s including model loading, and aggregation/scoring/comparison took 0.2744s; these exclude process launch, file output and browser rendering. They are not manual-workflow time savings. Full exact values and segment denominators are in `experiments/ranking_v1/report.json` and `docs/SCORING_RESULTS.md`.

**Documentation and limits:** updated README, context, decisions and `docs/PROFESSOR_UPDATE_2026-11-10.md` to include demonstrated scoring and precise limitations. Saved approximately 304 KiB of experiment evidence. Scoring uses provisional scope and urgency-as-impact proxies; effort/grouping errors and missing inputs constrain comparisons. All baselines share the same AI groups; this is not a controlled human-workflow comparison. No claim of ranking correctness, business improvement or participant observations. No known failing tests. Stored accept/override decisions, durable hosted persistence, cloud/Linux verification, broader data robustness and the final report remain pending.

**Saved checkpoint:** commit `7d61d60ef3a8f822c91c89298333af0b445c7b42` (`Add auditable scoring and reproducible ranking comparisons`) succeeded on `codex/semantic-milestone`; staged whitespace checks passed. Nothing was pushed or published. Supplied academic source documents remain untracked and unchanged.

## 9 November 2026 — persistent review workflow (deployment verification in progress)

Implemented immutable evidence/strategy snapshots and append-only accept/defer/manual-priority review events with required reasons. Local SQLite stores snapshots transactionally; an optional PostgreSQL adapter supports hosted durable storage without a local fallback in cloud mode. Workspace recovery keys are generated, stored only as digests, and scope all queries. Different input/strategy versions retain earlier events as historical. Current workflow includes recovery, explicit storage disclosure and JSON evidence/history export.

Initial checks: previous suite **114 passed in 7.35s**; expanded suite **131 passed, 1 skipped in 8.65s**. The skipped test is the real PostgreSQL round trip (no configured test database). SQLite tests exercise a separate Python interpreter, eight concurrent appends, rollback after an injected insert failure, namespace isolation, tampered snapshots, required reasons, overrides and stale-context handling. App tests exercise save/rerun/recovery and missing-cloud-storage errors. PostgreSQL driver psycopg/psycopg-binary **3.3.8** installed from official PyPI; `pip check` reports no broken requirements. Root research requirements remain unchanged.

GitHub connection verified for `soferscbe`; the initial accessible repository list was empty. The student subsequently supplied `https://github.com/soferscbe/valhalla`, verified public, empty and writable. No hosted application URL exists yet. Linux dependency resolution, cloud-entrypoint tests and browser review QA subsequently completed as recorded below. The initial Linux resolution selected a 539.2 MB generic PyTorch wheel; stopped that check and pinned the official hash-verified CPU wheel for the deployment dependency file. No model/settings or saved research results were retuned.

**Final local checks:** after extending the real-model test through an actual 500-record saved snapshot and adding a cloud-entrypoint guard test, **132 passed, 1 skipped in 8.68s**. After the final candidate-label UI adjustment, the full suite again passed **132 tests with 1 PostgreSQL skip in 8.96s**. The one skipped test is real PostgreSQL, not semantic inference. No local PostgreSQL server or Docker runtime was available. An actual Linux/PG GitHub Actions run is prepared, not yet claimed successful.

**Browser review verification:** local server restarted at session 74108. The six-row sample was grouped/scored and a `Defer` event saved with reviewer `Automated demo` and a reason explicitly marked as synthetic demonstration, not participant evidence. The success message and persisted event table were observed; screenshot `docs/review-demo.png`. Only a synthetic record was written to ignored local SQLite. Recovery keys were not recorded in project files or screenshots. Automated tests verify fresh-session restoration; browser file download and hosted restart tests remain unverified. A final small UI addition explicitly names the candidate being reviewed; AppTest covers that final code while the screenshot shows the preceding save/table view.

**Deployment preparation:** `deployment/streamlit_app.py` runs the same app with cloud storage mode forced; adjacent requirements select official hash-pinned torch 2.15.0+cpu for Linux x86_64/Python 3.12 and psycopg 3.3.8. Cross-platform pip resolution succeeded for **72 packages**, without NVIDIA dependencies. Receipt saved in `deployment/linux_dependency_receipt.json`; logs under ignored `tmp/`. This is not execution on Linux. `.github/workflows/tests.yml` is prepared for real-model tests plus a disposable PostgreSQL 17 service; YAML parsed locally. Real database credentials and service setup remain required for hosting. See `docs/DEPLOYMENT.md` for concrete setup and acceptance checks.

**Access issue:** attempted inspection of the student's GitHub Chrome tab was rejected by automatic approval review because the approval service reported a usage limit (not a manual rejection or unsafe-action finding). Did not retry through another browser or bypass the gate. Used the already-connected, authorised GitHub API to verify the exact repository URL subsequently supplied by the student. Browser deployment actions may remain blocked until that service limit resolves. No changes to account permissions or repository visibility were made.

**Publication approval:** the combined local-commit/remote-push command was rejected before execution by automatic approval review. Reason: the destination is public, and broad publication of the unpublished source/documentation checkpoint on `main` lacked explicit approval of that payload's public disclosure. No commit, remote change or upload occurred from that rejected command. Prepared `docs/PUBLICATION_MANIFEST.md` listing the exact proposed files and noting student details plus Git author identity in history. Continue with local-only checkpointing; obtain explicit public-publication approval or verify the repository has been made private before any upload. Do not bypass the rejection through connector writes.

**Local checkpoint:** `999bad0be79a02176cdc40f3fd6ed5e2992a257e` (`Add persistent review history and cloud deployment configuration`) succeeded with staged whitespace checks passing. This saves the tested review workflow, deployment files, updated professor briefing and the 75-file publication manifest. No source was uploaded and no remote was added. The supplied academic documents remain untracked. Public publication approval is the next required input.

## Recommended next task

Publish the tested checkpoint to the supplied repository, run Linux/PostgreSQL CI and verify the hosted workflow.

Acceptance checks:

1. Preserve existing remote files/history; publish the verified source and record the actual branch/commit. Keep academic source documents, model cache, secrets and local reviews out of the upload.
2. Inspect an actual GitHub Actions result and resolve any Linux/model/PostgreSQL test failures. Dependency resolution alone does not satisfy this check.
3. Configure Streamlit Community Cloud with `deployment/streamlit_app.py`, Python 3.12 and a dedicated TLS PostgreSQL database via private secrets; do not fall back to ephemeral local review files.
4. Record the live URL and verify upload → grouping → scoring → saved review, cross-workspace isolation and restore after hosted restart. If access remains unavailable, record the exact unmet requirement without claiming deployment.
