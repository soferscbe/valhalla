# ProductLens AI

An MBA-Tech research application for explainable, evidence-based SaaS feature prioritisation.

**Current status (9 November 2026):** upload, validation, seeded synthetic datasets and local semantic grouping work. The app shows broader opportunities, stricter candidate duplicates, source feedback and distinct-customer counts. Initial held-out semantic results are saved with a frozen configuration. Transparent scoring, ranking baselines, stored human decisions and cloud deployment are **not implemented**. The full approved project is not complete. See `docs/SEMANTIC_RESULTS.md` for measured limitations and `docs/PROFESSOR_UPDATE_2026-11-10.md` for the discussion brief.

Read `AGENTS.md`, `PROJECT_CONTEXT.md`, `PROGRESS.md` and `DECISIONS.md` before continuing development.

## Setup and run

Use Python 3.12. From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Open the local address printed by Streamlit, normally http://127.0.0.1:8501. No API key is needed. Use **Try synthetic sample**, or upload the generated feedback CSV, then click **Group related feedback**. Select an opportunity to inspect original feedback and stricter candidate duplicate groups. Stop the server with Ctrl+C.

On this workstation, the environment was created with the bundled Python 3.12.14 at `/Users/sofers-4887/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`; system Python is 3.9.6. The existing `.venv` is local and not portable. Recreate it with Python 3.12 on another machine.

`requirements.txt` pins the validated environment, including test dependencies. Main packages: Streamlit 1.66.1, pandas 2.2.3, NumPy 2.3.5, openpyxl 3.1.5, pytest 9.2.0, sentence-transformers 6.2.0, scikit-learn 1.9.1, transformers 5.22.1 and Torch 2.15.0. A fresh installation on Linux/cloud has not yet been verified.

Prepare the model before a demonstration:

```bash
python -m productlens.embeddings
PRODUCTLENS_OFFLINE=1 python -m streamlit run app.py --server.address 127.0.0.1
```

The first command downloads the public pinned MiniLM model into `.cache/models/` if needed; subsequent inference is local. Keep the cache for an offline demo. The model assets are approximately 87.3 MiB, in addition to Python dependencies. No feedback is transmitted to a model API. Failures are displayed explicitly, with no lexical fallback.

Grouping supports at most 2,000 rows (ingestion supports 10,000). The 256-token model window may truncate long text; the app flags affected rows and retains their original text. Every row receives one group, so overlapping intents and vague feedback require review. Grouping is an input to the future decision engine, not a priority ranking or validated feature specification.

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

Store Excel IDs as **text**: numeric cells with zero-padding formats do not preserve those leading zeros as identifier values. Literal text such as `NA` remains text, not an automatically missing value. Keep one currency and effort unit per dataset; scoring/aggregation conventions will be defined in the decision-engine milestone.

Missing optional values remain missing with a warning. Unknown columns, including any truth labels, are excluded from the validated output and reported. This is not sufficient by itself to guarantee future model leakage prevention: model inputs must explicitly select feedback text, and research labels must live separately. Invalid rows are reported with spreadsheet row numbers (header = row 1); rows are never silently dropped. Validation success is required before showing the validated preview.

Uploads are processed in session memory; this application does not write them to disk. There is no durable storage, authentication or cross-session decision history yet. Use only synthetic/nonconfidential data.

## Tests and smoke check

```bash
source .venv/bin/activate
python -m pytest -q
python -m pip check
PRODUCTLENS_OFFLINE=1 PRODUCTLENS_TEST_REAL_MODEL=1 python -m pytest -q
```

Core tests cover file validation, deterministic data generation, leakage guards, grouping/count traceability, metric arithmetic, frozen experiment checks and UI state. UI tests use [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest). The default suite skips two real-model tests; the final command enables them after model download, including the generated 500-row upload-to-grouping journey. AppTest simulates interaction. The six-row workflow was also exercised in a local browser on 9 November; no hosted journey has been verified. See `PROGRESS.md` for final test counts and results.

After starting Streamlit, `http://127.0.0.1:8501/_stcore/health` should return `ok`. Both this endpoint and the root page returned HTTP 200 during local verification. A healthy server alone does not validate the user journey; retain the UI tests and later verify the hosted workflow in a real browser.

## Generate synthetic evidence

```bash
source .venv/bin/activate
python -m productlens.synthetic --rows 500 --seed 42
python -m productlens.synthetic --rows 1500 --seed 42
```

Upload `data/generated/v1.0.0_seed42_n500/inputs/feedback.csv` into the existing app. The generated folder also contains separate tuning/evaluation inputs, text-only model-input files, truth labels/account registry and a version/configuration/hash manifest. It is ignored by Git and reproducible from source. The CLI refuses to overwrite existing folders; use `--output` with a new destination to reproduce or compare a run.

Use only `feedback_text` for semantic features; IDs are join keys. Do not tune on the combined demonstration file or held-out evaluation labels. See [the synthetic dataset specification](docs/SYNTHETIC_DATA.md) for units, split/label policies, scenario assumptions and limitations. The dataset contains designed prioritisation conflicts and a finite authored phrase catalog; it does not establish real-world model accuracy or business impact.

## Structure

```text
app.py                    Streamlit upload and preview UI
productlens/ingestion.py   File reader and validation contract
productlens/synthetic.py   Seeded generator, integrity checks and bundle CLI
productlens/synthetic_catalog.py  Authored request families and paraphrases
productlens/embeddings.py  Pinned local CPU model loading and encoding
productlens/grouping.py    Evidence-linked opportunity/duplicate groups
productlens/ui_semantics.py  Group and source-evidence review UI
productlens/grouping_metrics.py  Offline research metrics
productlens/semantic_experiment.py  Separate tuning and evaluation commands
config/semantic.json      Frozen tuning-selected settings used by the app
experiments/semantic_v1/   Actual configurations, predictions and measurements
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

## Deployment plan — not executed

Preferred candidate is Streamlit Community Cloud, as specified in the handoff. Prepare a source repository with `app.py`, `productlens/`, sample data, configuration and pinned requirements; exclude the virtual environment, secrets and uploaded data. Configure a Python 3.12 deployment with `app.py` as entry point. Resolve Linux dependency/model resource compatibility before calling hosting complete.

Include `config/semantic.json`. The deployment needs writable model-cache space and an initial model download (or a prepared model cache). Local held-out inference used approximately 567 MiB peak process memory; a Streamlit process and concurrent sessions may need more. PyTorch platform dependencies and cloud resource limits require actual deployment validation. Do not assume this local measurement guarantees cloud feasibility.

Before publishing a complete MVP, determine durable storage for decision history; local filesystem persistence must not be assumed to survive cloud restarts. After deployment, record the actual URL and verify sample mode, valid CSV/XLSX uploads, malformed inputs, semantic grouping, score explanations and persistence of human decisions. No hosting account, deployment or hosted journey has been verified yet.

## Research boundaries

The accepted proposal remains authoritative. Planned evaluation compares semantic grouping and transparent ranking with vote-based, weighted and RICE-style baselines. Synthetic data, model/split configuration and measured outcomes must be documented. Ranking agreement is not proof of a universally correct business priority. Do not fabricate business impact, participant reviews, experiments or references.
