# ProductLens AI

An MBA-Tech research application for explainable, evidence-based SaaS feature prioritisation.

**Current status (9 November 2026):** upload, validation, seeded synthetic datasets, local semantic grouping and transparent scoring work. The app supports strategy weights, score contributions, vote/fixed-weight/RICE-style comparisons, segment coverage and exports. The full suite passes **132 tests** (one PostgreSQL integration test remains skipped locally), and an actual 1,500-record ranking comparison is saved. Local accept/defer/override history with evidence snapshots is implemented and tested; cloud deployment is **not yet verified**; the full approved project remains incomplete. See `docs/SEMANTIC_RESULTS.md`, `docs/SCORING_RESULTS.md` and the updated `docs/PROFESSOR_UPDATE_2026-11-10.md`.

Read `AGENTS.md`, `PROJECT_CONTEXT.md`, `PROGRESS.md` and `DECISIONS.md` before continuing development.

## Setup and run

Use Python 3.12. From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Open the local address printed by Streamlit, normally http://127.0.0.1:8501. No API key is needed. Use **Try synthetic sample**, or upload the generated feedback CSV, then click **Group related feedback**. Select an opportunity to inspect original feedback and stricter candidate duplicate groups. Scroll to **Prioritise with evidence**, adjust weights, inspect contributions and compare baselines. Download scores and the accompanying scoring-assumptions JSON to retain a strategy view. Stop the server with Ctrl+C.

On this workstation, the environment was created with the bundled Python 3.12.14 at `/Users/sofers-4887/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`; system Python is 3.9.6. The existing `.venv` is local and not portable. Recreate it with Python 3.12 on another machine.

`requirements.txt` pins the validated environment, including test dependencies. Main packages: Streamlit 1.66.1, pandas 2.2.3, NumPy 2.3.5, openpyxl 3.1.5, pytest 9.2.0, sentence-transformers 6.2.0, scikit-learn 1.9.1, transformers 5.22.1 and Torch 2.15.0. A fresh installation on Linux/cloud has not yet been verified.

Prepare the model before a demonstration:

```bash
python -m productlens.embeddings
PRODUCTLENS_OFFLINE=1 python -m streamlit run app.py --server.address 127.0.0.1
```

The first command downloads the public pinned MiniLM model into `.cache/models/` if needed; subsequent inference is local. Keep the cache for an offline demo. The model assets are approximately 87.3 MiB, in addition to Python dependencies. No feedback is transmitted to a model API. Failures are displayed explicitly, with no lexical fallback.

Grouping supports at most 2,000 rows (ingestion supports 10,000). The 256-token model window may truncate long text; the app flags affected rows and retains their original text. Every row receives one group, so overlapping intents and vague feedback require review. Grouping feeds the deterministic scoring engine; it is not a validated feature specification. Scores remain provisional when groups or effort need review.

## Feedback input

UTF-8 CSV (BOM accepted) or `.xlsx`; first Excel worksheet only. Limit: 10 MiB and 10,000 data rows. Legacy `.xls` is not supported. CSV columns must have consistent widths; duplicate/blank column headers are rejected. Headers and surrounding field whitespace are trimmed; header names are case-sensitive.

| Column | Rule |
| --- | --- |
| `feedback_id` | Required, nonblank, unique string |
| `customer_id` | Required, nonblank string; repeats allowed |
| `feedback_text` | Required, nonblank text |
| `segment` | Optional text |
| `request_date` | Optional valid YYYY-MM-DD date or native Excel date |
| `account_value` | Optional finite number ≥ 0 |
| `votes` | Optional finite whole number ≥ 0 |
| `urgency` | Optional finite number between 1 and 5 |
| `strategic_alignment` | Optional finite number between 1 and 5 |
| `effort` | Optional finite number > 0 |

Store Excel IDs as **text**: numeric cells with zero-padding formats do not preserve those leading zeros as identifier values. Literal text such as `NA` remains text, not an automatically missing value. Keep one currency and effort unit per dataset; see `docs/SCORING_PROTOCOL.md` for the exact scoring/aggregation conventions. Synthetic account value is USD ARR and effort is person-days. Conflicting account values are unresolved rather than summed; candidate duplicate groups each contribute one provisional effort estimate.

Missing optional values remain missing with a warning. Unknown columns, including any truth labels, are excluded from the validated output and reported. This is not sufficient by itself to guarantee future model leakage prevention: model inputs must explicitly select feedback text, and research labels must live separately. Invalid rows are reported with spreadsheet row numbers (header = row 1); rows are never silently dropped. Validation success is required before showing the validated preview.

Uploads remain in session memory until you explicitly save a review. Saving stores a full evidence/strategy snapshot and a reason in the configured database. Local SQLite history survives restarts when its file is retained; a private recovery key restores the workspace in another browser session. This is lightweight bearer-key isolation, not authenticated user accounts. Use only synthetic/nonconfidential data. See `docs/REVIEW_WORKFLOW.md`.

## Tests and smoke check

```bash
source .venv/bin/activate
python -m pytest -q
python -m pip check
PRODUCTLENS_OFFLINE=1 PRODUCTLENS_TEST_REAL_MODEL=1 python -m pytest -q
```

Core tests cover file validation, deterministic data generation, leakage guards, grouping/count traceability, metric arithmetic, frozen experiment checks, customer/effort aggregation, missing signals, strategy changes, baseline comparisons and UI state. UI tests use [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest). The default suite skips two real-model tests and the PostgreSQL integration test unless its test database is configured; the final command enables them after model download, including the generated 500-row upload → grouping → scoring → saved-review journey. The PostgreSQL integration test still requires a separately configured test database. AppTest simulates interaction. The six-row workflow, live strategy changes and score explanations were also exercised in a local browser on 9 November; no hosted journey has been verified. See `PROGRESS.md` for final test counts and results.

After starting Streamlit, `http://127.0.0.1:8501/_stcore/health` should return `ok`. Both this endpoint and the root page returned HTTP 200 during local verification. A healthy server alone does not validate the user journey; retain the UI tests and later verify the hosted workflow in a real browser.

## Generate synthetic evidence

```bash
source .venv/bin/activate
python -m productlens.synthetic --rows 500 --seed 42
python -m productlens.synthetic --rows 1500 --seed 42
```

Upload `data/generated/v1.0.0_seed42_n500/inputs/feedback.csv` into the existing app. The generated folder also contains separate tuning/evaluation inputs, text-only model-input files, truth labels/account registry and a version/configuration/hash manifest. It is ignored by Git and reproducible from source. The CLI refuses to overwrite existing folders; use `--output` with a new destination to reproduce or compare a run.

Use only `feedback_text` for semantic features; IDs are join keys. Do not tune on the combined demonstration file or held-out evaluation labels. See [the synthetic dataset specification](docs/SYNTHETIC_DATA.md) for units, split/label policies, scenario assumptions and limitations. The dataset contains designed prioritisation conflicts and a finite authored phrase catalog; it does not establish real-world model accuracy or business impact.

## Transparent scoring and ranking experiments

The default strategy combines normalised customer reach, resolved account ARR, customer-balanced urgency and alignment with weights 30/30/20/20, then divides the weighted benefit by provisional effort. Each factor, weight and contribution is visible. Unknown positive-weight factors or unknown effort leave a candidate unranked; zero-weight factors can be omitted explicitly. Default weights are illustrative, not calibrated business truth.

Effort sums the maximum known estimate within each candidate duplicate subgroup once. Grouping mistakes and incomplete estimates can distort scope; engineering review is required. Votes count record endorsements. The fixed weighted baseline omits effort. The RICE-style proxy uses submitting customers, urgency as an impact proxy, a common confidence assumption and effort; it is explicitly an adaptation. Ties share average rank, with ID ordering only for display and Top-K selection.

```bash
PRODUCTLENS_OFFLINE=1 python -m productlens.ranking_experiment \
  --input data/generated/v1.0.0_seed42_n1500/inputs/feedback.csv \
  --output experiments/ranking_v1_reproduction
```

The CLI refuses existing output folders. It saves configurations, hashes, account/subgroup evidence, scores, baseline agreement, segment representation and ±20% weight sensitivity. Read [the protocol](docs/SCORING_PROTOCOL.md) and [measured results](docs/SCORING_RESULTS.md) before interpreting outputs. This first run is a descriptive synthetic comparison, not a finding that the strategy is universally correct. Unsaved strategy controls are session-only; saving a review snapshots its exact settings and evidence. Exported CSV text is escaped for spreadsheet safety.

## Structure

```text
app.py                    Streamlit upload and preview UI
productlens/ingestion.py   File reader and validation contract
productlens/synthetic.py   Seeded generator, integrity checks and bundle CLI
productlens/synthetic_catalog.py  Authored request families and paraphrases
productlens/embeddings.py  Pinned local CPU model loading and encoding
productlens/grouping.py    Evidence-linked opportunity/duplicate groups
productlens/ui_semantics.py  Group and source-evidence review UI
productlens/scoring.py     Auditable aggregation, formulas and comparison metrics
productlens/ui_scoring.py  Strategy controls, ranked view, explanations and exports
productlens/ranking_experiment.py  Reproducible ranking and sensitivity CLI
productlens/reviews.py     Immutable snapshots and isolated append-only review store
productlens/ui_reviews.py  Accept/defer/override, recovery and history export
deployment/               Cloud entrypoint, CPU dependencies and resolution receipt
.github/workflows/tests.yml  Linux/real-model/PostgreSQL CI (awaiting remote run)
productlens/grouping_metrics.py  Offline research metrics
productlens/semantic_experiment.py  Separate tuning and evaluation commands
config/semantic.json      Frozen tuning-selected settings used by the app
experiments/semantic_v1/   Actual semantic configurations, predictions and measurements
experiments/ranking_v1/    Actual scoring configurations, evidence and comparisons
data/sample_feedback.csv  Six explicitly synthetic examples
data/generated/           Reproducible bundles (Git-ignored)
docs/SYNTHETIC_DATA.md     Dataset contract, split protocol and limitations
tests/                    Core and Streamlit interaction tests
requirements.txt          Pinned validated environment
.streamlit/config.toml    Upload limit and telemetry preference
PROJECT_CONTEXT.md        Stable scope, sources, requirements and risks
PROGRESS.md               Verified status, checks and one next task
DECISIONS.md              Dated architecture/research trade-offs
```

## Review history and deployment

After scoring, choose **Explain a priority**, then scroll to **Record a human review**. Start a private workspace and download its recovery key separately. Select accept, defer or override priority; enter a reason and save. An override is a human High/Medium/Low designation and does not rewrite the calculated rank. Changed data or weights create a new context; earlier events remain historical. All review saves are append-only.

Local storage defaults to ignored `data/private/reviews.sqlite3`; `PRODUCTLENS_REVIEW_DB` can select a different local file. Keep the file and recovery key to restore history. JSON export includes evidence and reasons, but no recovery key. Cloud mode instead requires a PostgreSQL URL with TLS, configured only in server-side secrets.

GitHub source destination: [soferscbe/valhalla](https://github.com/soferscbe/valhalla). The repository was initially empty and public; publication/CI status is recorded in `PROGRESS.md`. It is not the application URL.

Cloud entrypoint: **`deployment/streamlit_app.py`**, Python **3.12**, with adjacent `deployment/requirements.txt`. The same application runs with local review-storage fallback disabled. Linux CPU dependency resolution passed, but hosted execution and PostgreSQL persistence remain unverified. No public application URL exists yet. Follow [the concrete deployment handoff](docs/DEPLOYMENT.md) for secrets, checks and the restart test.

## Research boundaries

The accepted proposal remains authoritative. Initial evaluation measures semantic grouping and compares transparent ranking with vote-based, fixed-weight and RICE-style baselines. Further data robustness checks and any participant study remain pending. Synthetic data, model/split configuration and measured outcomes must be documented. Ranking agreement is not proof of a universally correct business priority. Do not fabricate business impact, participant reviews, experiments or references.
