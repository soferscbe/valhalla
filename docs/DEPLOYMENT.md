# Deployment handoff — 9 November 2026

**Status:** source published on `main`; fresh Linux installation and all 133 tests passed, including real-model inference and PostgreSQL. [Verified run](https://github.com/soferscbe/valhalla/actions/runs/42658653667), source commit `0a0b418853d733af4b560b69f15f8e6b54b5a7b0`. No public application URL or hosted persistence has been verified. GitHub repository: https://github.com/soferscbe/valhalla (public; initial README and original project history preserved).

## Source and entrypoint

For Streamlit Community Cloud, select the repository above, the branch containing the verified checkpoint, **`deployment/streamlit_app.py`**, and **Python 3.12**. This entrypoint runs the same application while enforcing cloud storage mode. Its adjacent `deployment/requirements.txt` preserves the root research pins, selects the official hash-pinned Linux x86_64 CPU PyTorch wheel, and adds psycopg 3.3.8. The root `app.py` remains the local entrypoint.

A cross-platform pip dry-run initially resolved **72 packages** for Linux x86_64/Python 3.12 with no NVIDIA dependencies; receipt: `deployment/linux_dependency_receipt.json`. Subsequently, GitHub Actions installed the environment on Ubuntu 26.04 / Python 3.12.16, passed `pip check`, prepared the pinned model and passed **133 tests in 23.39s** against PostgreSQL 17.11 with Torch 2.15.0+cpu and psycopg 3.3.8. The local model revision and grouping thresholds are unchanged. Passing tests does not establish bit-for-bit equivalence of every saved macOS research result; the full ranking experiment was not rerun on Linux.

## Durable reviews

The cloud entrypoint refuses SQLite review fallback. Configure a dedicated PostgreSQL database and put its connection URL into the host's server-side secret manager:

```toml
PRODUCTLENS_DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

The example has placeholders only. URL-encode password punctuation. Prefer the database provider's documented TLS/pooler connection string; certificate-verifying modes are accepted. Never paste credentials into chat, commit them, or embed them in a public URL. `.streamlit/secrets.toml.example` is a template; real `.streamlit/secrets.toml` is ignored. The app role needs create-table/index and select/insert permissions in its dedicated schema. It must not be reused for unrelated confidential data.

A managed PostgreSQL service such as Supabase can provide the database. Account creation, provider terms, project configuration and access remain to be completed if no database already exists. No paid service has been purchased. A missing/unreachable database leaves the scoring demo available but prevents saving reviews with an explicit error. Do not describe that state as a complete deployed MVP.

Review workspace recovery keys isolate app queries but are bearer secrets, not authenticated identities. Keep the application limited to synthetic/nonconfidential demonstrations. Read `REVIEW_WORKFLOW.md` before sharing access. Retain both database backups and recovery keys; exporting history does not implement JSON re-import.

## Automated verification

`.github/workflows/tests.yml` prepares Python 3.12/Linux CPU dependencies, downloads the pinned model and runs the full suite against a disposable PostgreSQL 17 service. Its database password is a test-only constant for an isolated runner, not a production credential. The workflow has read-only repository permissions. Main run `42658653667` completed successfully on 9 November 2026 with **133 passed and no skips**; job `129303916147`. A separate source-branch run also succeeded. The earlier temporary import run failed at workflow-write permission before tests; it is not the application CI result.

Local checks:

```bash
PRODUCTLENS_OFFLINE=1 PRODUCTLENS_TEST_REAL_MODEL=1 python -m pytest -q
```

To test an explicitly designated disposable PostgreSQL database, configure `PRODUCTLENS_TEST_POSTGRES_URL` privately and run `python -m pytest tests/test_reviews.py -q`. The integration test appends synthetic records in a newly generated workspace. Do not point it at a database containing unrelated data. No database URL should be printed in logs.

## Hosted acceptance — record actual results

1. Verify build logs, exact dependency versions and pinned model load; record the real URL and commit.
2. Exercise sample, valid CSV/XLSX and invalid uploads. Run semantic grouping and inspect source rows; adjust weights and verify score contributions and fixed baselines.
3. Start a workspace, save its recovery key privately, and save a clearly marked synthetic defer/override reason. Export history and inspect its evidence snapshot.
4. Restart the hosted app, restore the workspace key, re-upload the same dataset and settings, and confirm the saved event remains. Change weights and confirm the prior event becomes historical. A different workspace must not see it.
5. Confirm missing/unavailable database errors never report a successful save; verify the exposed app uses cloud mode. Record memory/build limits and any failed checks candidly.

Local SQLite restart tests do not satisfy step 4. Dependency resolution does not replace a real Linux run. A GitHub repository URL is not a deployed application URL.

## Verified official references

- [Streamlit deployment preparation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app) and [dependency file placement](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
- [Streamlit's Supabase connection guide](https://docs.streamlit.io/develop/tutorials/databases/supabase) documents separate secrets and direct PostgreSQL access as an option.
- [Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html) and [official CPU PyTorch wheel index](https://download.pytorch.org/whl/cpu/torch/).
- [GitHub PostgreSQL service containers](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers), [checkout](https://github.com/actions/checkout) and [setup-python](https://github.com/actions/setup-python).

References checked on 9 November 2026; provider access and actual deployment state must still be verified.
