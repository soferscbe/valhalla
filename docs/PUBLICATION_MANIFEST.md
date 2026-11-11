# Approved GitHub publication

Destination: `https://github.com/soferscbe/valhalla`, public. The approved checkpoint was published on 9 November 2026 as main commit `0a0b418853d733af4b560b69f15f8e6b54b5a7b0`, preserving the original project history and the student's initial README commit. All 75 file paths, modes and blob hashes were verified against local checkpoint `e4211a46ffcc04b5084418b82333a3cfedb063e1`.

The approved publication includes the complete tested local Git history and the files below. It contains the student name, roll number, mentor, project title, local development paths and the supplied Git author name/email in commit history. Source code, synthetic examples and experiment records, test results, implementation instructions, draft professor briefing and screenshots are publicly readable. The private reviewer database, recovery keys, real credentials, Python environment, model cache and supplied academic PDF/DOCX documents are excluded. The CI password is only for an ephemeral test database; the secrets example contains placeholders.

Review `README.md`, `PROGRESS.md`, `PROJECT_CONTEXT.md`, and `docs/PROFESSOR_UPDATE_2026-11-10.md` for the main student/project details. This manifest describes the source checkpoint, not an already deployed app. The student explicitly approved this public publication on 9 November 2026. Subsequent documentation updates record actual publication and verification results.

## Approved checkpoint files

- `.github/workflows/tests.yml`
- `.gitignore`
- `.python-version`
- `.streamlit/config.toml`
- `.streamlit/secrets.toml.example`
- `AGENTS.md`
- `DECISIONS.md`
- `PROGRESS.md`
- `PROJECT_CONTEXT.md`
- `README.md`
- `app.py`
- `config/semantic.json`
- `data/sample_feedback.csv`
- `deployment/linux_dependency_receipt.json`
- `deployment/requirements.txt`
- `deployment/streamlit_app.py`
- `docs/DEPLOYMENT.md`
- `docs/PROFESSOR_UPDATE_2026-11-10.md`
- `docs/PUBLICATION_MANIFEST.md`
- `docs/REVIEW_WORKFLOW.md`
- `docs/SCORING_PROTOCOL.md`
- `docs/SCORING_RESULTS.md`
- `docs/SEMANTIC_PROTOCOL.md`
- `docs/SEMANTIC_RESULTS.md`
- `docs/SYNTHETIC_DATA.md`
- `docs/review-demo.png`
- `docs/scoring-demo.png`
- `docs/semantic-demo.png`
- `experiments/ranking_v1/accounts.csv`
- `experiments/ranking_v1/assignments.csv`
- `experiments/ranking_v1/grouping_config.json`
- `experiments/ranking_v1/opportunities.csv`
- `experiments/ranking_v1/report.json`
- `experiments/ranking_v1/scores_balanced.csv`
- `experiments/ranking_v1/scores_enterprise.csv`
- `experiments/ranking_v1/scores_reach.csv`
- `experiments/ranking_v1/subgroup_effort.csv`
- `experiments/semantic_v1/heldout/assignments.csv`
- `experiments/semantic_v1/heldout/challenge_review.csv`
- `experiments/semantic_v1/heldout/duplicate_errors.csv`
- `experiments/semantic_v1/heldout/evaluation.json`
- `experiments/semantic_v1/heldout/opportunities.csv`
- `experiments/semantic_v1/model_assets.json`
- `experiments/semantic_v1/scale_check.json`
- `experiments/semantic_v1/tuning/assignments.csv`
- `experiments/semantic_v1/tuning/frozen_config.json`
- `experiments/semantic_v1/tuning/tuning_metrics.json`
- `productlens/__init__.py`
- `productlens/embeddings.py`
- `productlens/grouping.py`
- `productlens/grouping_metrics.py`
- `productlens/ingestion.py`
- `productlens/ranking_experiment.py`
- `productlens/reviews.py`
- `productlens/scoring.py`
- `productlens/semantic_experiment.py`
- `productlens/synthetic.py`
- `productlens/synthetic_catalog.py`
- `productlens/ui_reviews.py`
- `productlens/ui_scoring.py`
- `productlens/ui_semantics.py`
- `pyproject.toml`
- `requirements.txt`
- `tests/test_app.py`
- `tests/test_grouping.py`
- `tests/test_ingestion.py`
- `tests/test_ranking_experiment.py`
- `tests/test_reviews.py`
- `tests/test_reviews_app.py`
- `tests/test_scoring.py`
- `tests/test_scoring_app.py`
- `tests/test_semantic_app.py`
- `tests/test_semantic_experiment.py`
- `tests/test_semantic_integration.py`
- `tests/test_synthetic.py`

## Subsequent hosted verification evidence — 10 November 2026

Added `docs/hosted-scoring-2026-11-10.jpg`, `docs/hosted-review-2026-11-10.jpg` and `docs/hosted-recovery-2026-11-10.jpg` alongside updated project/deployment/professor documentation. Screenshots contain synthetic feedback/results and an explicitly labelled automated test review. They contain no database credentials or recovery keys. The original 75-file checkpoint remains unchanged in history.

## 11 November research and preparation checkpoint

Adds reproducible synthetic robustness outputs, runner/tests, generic demo/reference notes and report-builder source. Generated report documents, student reflection, academic source attachments and transformed synthetic input copies are excluded. No credentials or recovery keys are included.

- `.gitignore`
- `DECISIONS.md`
- `PROGRESS.md`
- `PROJECT_CONTEXT.md`
- `README.md`
- `docs/DEMO_AND_VIVA.md`
- `docs/DEPLOYMENT.md`
- `docs/PROFESSOR_UPDATE_2026-11-10.md`
- `docs/ROBUSTNESS_PROTOCOL.md`
- `docs/ROBUSTNESS_RESULTS.md`
- `docs/VERIFIED_REFERENCES.md`
- `experiments/robustness_v1/arr_missing/assignments.csv`
- `experiments/robustness_v1/arr_missing/scores.csv`
- `experiments/robustness_v1/arr_uncertainty/assignments.csv`
- `experiments/robustness_v1/arr_uncertainty/scores.csv`
- `experiments/robustness_v1/base_scores.csv`
- `experiments/robustness_v1/effort_uncertainty/assignments.csv`
- `experiments/robustness_v1/effort_uncertainty/scores.csv`
- `experiments/robustness_v1/permuted/assignments.csv`
- `experiments/robustness_v1/permuted/scores.csv`
- `experiments/robustness_v1/repeated_account/assignments.csv`
- `experiments/robustness_v1/repeated_account/scores.csv`
- `experiments/robustness_v1/report.json`
- `experiments/robustness_v1/runtime.json`
- `productlens/robustness_experiment.py`
- `report/README.md`
- `tests/test_robustness_experiment.py`
- `tools/build_report_template.py`
