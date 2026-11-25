# Disease Trend Analysis System

Analysis of Patient Health Records for Disease Trend Identification using Data Mining — an undergraduate project implementing classification and clustering over a real-data dataset (three real sources, no synthetic/fabricated records) covering diabetes, typhoid, and malaria.

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
data/raw/                 Real dataset source files
data/processed/           Cleaned, encoded datasets ready for modelling
db/                       SQLite database file + schema.sql
models/                   Trained model artifacts (.joblib)
src/preprocessing.py      Cleaning, encoding, normalisation
src/classification.py     RandomForestClassifier training + inference
src/clustering.py         KMeans training + inference
src/trends.py             Aggregation into Trend Report records (+ real NMDR surveillance import)
src/dataset_builder.py    Builds the patient-records dataset from the real sources
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

Every record in this system is real — patient data or official surveillance data. Nothing is fabricated, simulated, or literature-estimated. Three real sources, all CC BY 4.0:

1. **Diabetes** — `data/raw/diabetes_dataset Version 2.csv`, 1,500 real patient records (1,479 kept after dropping rows with missing age/gender): real age, sex, BMI, glucose, HbA1c, and diabetic/non-diabetic status for every row. [A Machine Learning Approach for Detecting Type 2 Diabetic Disease](https://data.mendeley.com/datasets/ksdk5m939c/1), Osun State University, Osogbo, Nigeria. Disclosed approximation: this source is a cross-sectional clinical dataset with no per-patient location or visit-date field, so a representative catchment-area location (Osun/Kwara, the publishing institution's state and its known referral catchment) and a representative date range are assigned to populate those two schema fields only — every clinical value is the real recorded measurement.
2. **Malaria & Typhoid (patient-level)** — `data/raw/Second DATASET TETFund.xlsx`, 236 real febrile patients from Akanu Ibiam Federal Polytechnic medical centre, Afikpo, Ebonyi State, diagnosed by blood-film microscopy (malaria) and the Widal test (typhoid). [Prevalence and Management Practices of Malaria-Typhoid Co-Infection in Unwana, South East Nigeria](https://data.mendeley.com/datasets/yk9dcmd94w/1) (DOI 10.17632/yk9dcmd94w.1). The 137 malaria-only patients map to `diagnosis="malaria"`; the 99 co-infected patients map to `diagnosis="typhoid"` (this project's classification scheme has no co-infection category, and typhoid would otherwise be unrepresented). Two things are not read directly from the source and are disclosed here rather than left implicit: age is recorded only as a 5-year bracket (e.g. "23-27") — the bracket midpoint is used — and the source has no per-patient visit date, so dates are spread uniformly across the study's reported ~6-month collection window purely to populate the month/season feature.
3. **Malaria (state/month aggregate, supplementary)** — `data/raw/Wavelets_data for Time series_malaria.csv`, real official monthly malaria case counts for Nasarawa, Kwara, and Zamfara states, January 2015–December 2024, sourced from Nigeria's National Malaria Data Repository. Supplementary data for a 2026 PLOS ONE paper (figshare DOI 10.6084/m9.figshare.30716729). This is aggregate, not patient-level, so `trends.py` loads it directly into `trend_report` (tagged `source='nmdr_surveillance'`) rather than merging it into `patient_records.csv` — it gives real multi-state, multi-year malaria trend context the single-site Unwana dataset can't provide alone.

**The one acknowledged limitation:** no single public dataset provides patient-level age+sex+location+date for all three diseases across multiple Nigerian states and years — this was confirmed by an extensive search (Kaggle, Mendeley, Zenodo, Dryad, Figshare, DHS, NCDC, published-paper supplementary files). The malaria/typhoid patient data is real but geographically narrow (one facility, Ebonyi State) and temporally approximate (dates spread within a known real collection window, not individually recorded). State this precisely in Chapter 4 — it's an honest, defensible position (real data with a disclosed scope limitation), not a claim of broader coverage than the sources actually support.

## Build order (see PRD Section 12 for the full timeline)

1. `src/dataset_builder.py` — assemble the real patient-records dataset into the unified schema
2. `db/schema.sql` + load script — create the SQLite database
3. `src/preprocessing.py` — cleaning, encoding, normalisation
4. `src/classification.py` — train/evaluate the Random Forest model
5. `src/clustering.py` — train/evaluate the K-Means model
6. `src/trends.py` — aggregate model output into Trend Report records
7. `app/` — Streamlit dashboard pages (Upload, Trends Overview, Geographic View, Demographic View, Clusters, Model Performance, Reports)
