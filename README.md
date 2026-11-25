# Disease Trend Analysis System

Analysis of Patient Health Records for Disease Trend Identification using Data Mining — an undergraduate project implementing classification and clustering over a hybrid (real + literature-informed synthetic) dataset covering diabetes, typhoid, and malaria.

Full product requirements and implementation plan: see `docs/PRD.docx` (copied from the thesis project folder) for architecture, dataset sourcing, database schema, model choices, dashboard design, folder structure, and the phased build plan.

## Tech stack

- **Dashboard:** Streamlit
- **Database:** SQLite
- **ML:** scikit-learn (RandomForestClassifier for classification, KMeans for clustering)
- **Data handling:** pandas, NumPy
- **Charts:** native Streamlit (`st.line_chart`, `st.bar_chart`, `st.scatter_chart`)
- **Auth:** Streamlit's built-in `st.login`/`st.user` (real OIDC, not a password gate)

## Project structure

```
app/                      Streamlit dashboard pages
data/raw/                 Hybrid dataset source files
data/processed/           Cleaned, encoded datasets ready for modelling
db/                       SQLite database file + schema.sql
models/                   Trained model artifacts (.joblib)
src/preprocessing.py      Cleaning, encoding, normalisation
src/classification.py     RandomForestClassifier training + inference
src/clustering.py         KMeans training + inference
src/trends.py             Aggregation into Trend Report records
src/dataset_builder.py    Builds the hybrid dataset
tests/                    Unit tests for preprocessing and models
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Authentication

The dashboard gates every page behind a real sign-in (`st.login`/`st.user`), per the PRD's "manage user account" requirement — not a hardcoded password. It needs a real OAuth identity provider; this repo can't generate those credentials for you.

To set it up with Google:

1. Go to https://console.cloud.google.com/apis/credentials and create an OAuth 2.0 Client ID (type: Web application)
2. Add an authorized redirect URI: `http://localhost:8501/oauth2callback` (update this when you deploy)
3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
4. Fill in `client_id`, `client_secret`, and a random `cookie_secret`

Without this, every page shows a "Login is not configured yet" message instead of crashing.

**Important:** after editing `common.py` or anything in `src/`, fully stop (Ctrl+C) and restart `streamlit run` — Streamlit hot-reloads the page script on save, but not modules it imports, so a browser refresh alone won't pick up the change.

## Dataset

`data/raw/patient_records.csv` (built by `src/dataset_builder.py`, committed to this repo so the app auto-loads it on first run — see PRD Section 5) combines:

- **Diabetes** — real clinical data, 1,500 records (1,479 after dropping rows with missing age/gender): [A Machine Learning Approach for Detecting Type 2 Diabetic Disease](https://data.mendeley.com/datasets/ksdk5m939c/1), Osun State University, Osogbo, Nigeria. Licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- **Typhoid & Malaria** — literature-informed synthetic records (no real Nigerian tabular dataset with the required age/sex/location/date schema exists for either, confirmed by searching Kaggle, Mendeley, Zenodo, Dryad, and the NCDC portal). Geographic and seasonal patterns follow Akinyemi et al. (2018) and Ayoka & Nnadi (2026) respectively — see the docstring in `src/dataset_builder.py` for exactly which assumption maps to which parameter.

State this composition plainly in Chapter 4 — it's a defensible representative dataset per Chapter 1 Section 1.5, not a claim that the typhoid/malaria records are real observations.

## Build order (see PRD Section 12 for the full timeline)

1. `src/dataset_builder.py` — assemble the hybrid dataset into the unified schema
2. `db/schema.sql` + load script — create the SQLite database
3. `src/preprocessing.py` — cleaning, encoding, normalisation
4. `src/classification.py` — train/evaluate the Random Forest model
5. `src/clustering.py` — train/evaluate the K-Means model
6. `src/trends.py` — aggregate model output into Trend Report records
7. `app/` — Streamlit dashboard pages (Upload, Trends Overview, Geographic View, Demographic View, Clusters, Model Performance, Reports)
