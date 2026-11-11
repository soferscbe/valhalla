# Deployment handoff — 10 November 2026

**Status:** source published on `main`; fresh Linux installation and all 133 tests passed, including real-model inference and PostgreSQL. [Verified run](https://github.com/soferscbe/valhalla/actions/runs/42658653667), source commit `0a0b418853d733af4b560b69f15f8e6b54b5a7b0`. Live app: https://valhalla-arkjg4bdxtfmm3d9z55dwu.streamlit.app/. Browser upload, validation, real grouping and scoring are verified on 500 synthetic records. Hosted PostgreSQL saving, rereading across reruns, strategy-context separation and two-workspace isolation are verified. Fresh-session recovery and restoration after an owner-reported app reboot are verified; the owner performed the reboot and the agent observed the restored original event. GitHub repository: https://github.com/soferscbe/valhalla (public; initial README and original project history preserved).

## Source and entrypoint

For Streamlit Community Cloud, select the repository above, the branch containing the verified checkpoint, **`deployment/streamlit_app.py`**, and **Python 3.12**. This entrypoint runs the same application while enforcing cloud storage mode. Its adjacent `deployment/requirements.txt` preserves the root research pins, selects the official hash-pinned Linux x86_64 CPU PyTorch wheel, and adds psycopg 3.3.8. The root `app.py` remains the local entrypoint.

A cross-platform pip dry-run initially resolved **72 packages** for Linux x86_64/Python 3.12 with no NVIDIA dependencies; receipt: `deployment/linux_dependency_receipt.json`. Subsequently, GitHub Actions installed the environment on Ubuntu 26.04 / Python 3.12.16, passed `pip check`, prepared the pinned model and passed **133 tests in 23.39s** against PostgreSQL 17.11 with Torch 2.15.0+cpu and psycopg 3.3.8. The local model revision and grouping thresholds are unchanged. Passing tests does not establish bit-for-bit equivalence of every saved macOS research result; the full ranking experiment was not rerun on Linux.

## Durable reviews

The cloud entrypoint refuses SQLite review fallback. Configure a dedicated PostgreSQL database and put its connection URL into the host's server-side secret manager:

```toml
PRODUCTLENS_DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

The example has placeholders only. URL-encode password punctuation. Prefer the database provider's documented TLS/pooler connection string; certificate-verifying modes are accepted. Never paste credentials into chat, commit them, or embed them in a public URL. `.streamlit/secrets.toml.example` is a template; real `.streamlit/secrets.toml` is ignored. The app role needs create-table/index and select/insert permissions in its dedicated schema. It must not be reused for unrelated confidential data.

A managed PostgreSQL service such as Supabase can provide the database. The student has set up accounts and a database connection; PostgreSQL read/write through the hosted app now succeeds. No paid service has been purchased. A missing/unreachable database leaves the scoring demo available but prevents saving reviews with an explicit error. Do not describe that state as a complete deployed MVP.

Review workspace recovery keys isolate app queries but are bearer secrets, not authenticated identities. Keep the application limited to synthetic/nonconfidential demonstrations. Read `REVIEW_WORKFLOW.md` before sharing access. Retain both database backups and recovery keys; exporting history does not implement JSON re-import.

### Supabase setup clarification — 10 November 2026

For the dedicated ProductLens project, disable **Enable Data API** in the Data API integration/settings. This application uses server-side PostgreSQL directly and does not need Supabase REST/GraphQL access. Its automatically created SQL tables must not be exposed through a second access route that bypasses the application's workspace filtering. See [Supabase's guidance](https://supabase.com/docs/guides/api/securing-your-api). This provider setting has been instructed but not yet observed; include its confirmation in final hosted acceptance.

In **Connect**, choose the **Session pooler** URI on port **5432** for IPv4 compatibility. Copy the provider's exact host and username, replace the password placeholder privately with the URL-encoded database password, and ensure the query contains `sslmode=require`. Put the full URI in Streamlit Advanced settings → Secrets under `PRODUCTLENS_DATABASE_URL`. Select Python **3.12**, repository `soferscbe/valhalla`, branch `main`, main file `deployment/streamlit_app.py`. Never substitute a Supabase API key for the database connection URI.

## Automated verification

`.github/workflows/tests.yml` prepares Python 3.12/Linux CPU dependencies, downloads the pinned model and runs the full suite against a disposable PostgreSQL 17 service. Its database password is a test-only constant for an isolated runner, not a production credential. The workflow has read-only repository permissions. Main run `42658653667` completed successfully on 9 November 2026 with **133 passed and no skips**; job `129303916147`. A separate source-branch run also succeeded. The earlier temporary import run failed at workflow-write permission before tests; it is not the application CI result.

Local checks:

```bash
PRODUCTLENS_OFFLINE=1 PRODUCTLENS_TEST_REAL_MODEL=1 python -m pytest -q
```

To test an explicitly designated disposable PostgreSQL database, configure `PRODUCTLENS_TEST_POSTGRES_URL` privately and run `python -m pytest tests/test_reviews.py -q`. The integration test appends synthetic records in a newly generated workspace. Do not point it at a database containing unrelated data. No database URL should be printed in logs.

## Hosted acceptance — record actual results

### If the build reports an unsupported `cp312` wheel

The supplied 10 November build log selected Python **3.14.10**, while the deployment wheel is explicitly for Python **3.12** (`cp312`). Both uv and pip rejected that mismatch before application startup. Keep the validated dependencies unchanged. Streamlit Community Cloud requires deleting and recreating the app to change Python: first preserve its private Secrets and URL/settings, delete only the failed Streamlit app, then deploy the same repository/branch/entrypoint with **Advanced settings → Python 3.12**, restore Secrets and click Save before Deploy. The GitHub repository and Supabase project should remain in place. Rebooting the same deployment does not change its interpreter. See [official Python-version instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/upgrade-python).

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

## Hosted verification evidence — 10 November 2026

The 500-record CSV uploaded and validated in the live browser (98 customers), grouped into 21 candidates and scored the 10 with sufficient inputs. A synthetic Defer review was saved to PostgreSQL (event prefix `4eb2bbec`, context prefix `29106999a6bc`). Changing account-value weight made it historical; restoring the original weight made it applicable again. A new workspace could not see the first event. Screenshots: `hosted-scoring-2026-11-10.jpg` and `hosted-review-2026-11-10.jpg`. A separate six-row fixture verified rejection of an empty review reason, fresh-session recovery, recovery after an owner-reported host reboot, and review/evidence JSON download. The restored original event is `df84da63-51d7-499c-9070-97c7bb378a5e`; screenshot `hosted-recovery-2026-11-10.jpg`. Provider Data API setting, hosted XLSX/error cases, score/assumption downloads and recovery-key download remain unverified. The saved review is automated test evidence, not a participant review.

### 11 November acceptance update

The owner confirms the dedicated Supabase Data API is disabled. Hosted sample XLSX passed six records/five customers, real grouping and scoring for two candidates. The downloaded score CSV reproduces benefit/effort within 1e-10. An assumptions-download attempt timed out and browser automation reset; that path, invalid uploads and recovery-key download remain unverified on the host. Existing PostgreSQL recovery evidence is unchanged.

Later on 11 November, the hosted missing-feedback_text CSV was rejected with the explicit required-column error and no grouping action. Invalid-input acceptance passed; assumptions and private-key download checks remain open.
