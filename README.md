# Disease Trend Analysis System

Analysis of Patient Health Records for Disease Trend Identification using Data Mining — an undergraduate project implementing classification and clustering over a hybrid (real + literature-informed synthetic) dataset covering diabetes, typhoid, and malaria.

Full product requirements and implementation plan: see `docs/PRD.docx` (copied from the thesis project folder) for architecture, dataset sourcing, database schema, model choices, dashboard design, folder structure, and the phased build plan.

## Tech stack

- **Dashboard:** Streamlit
- **Database:** SQLite
- **ML:** scikit-learn (RandomForestClassifier for classification, KMeans for clustering)
- **Data handling:** pandas, NumPy
- **Charts:** Plotly

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

## Build order (see PRD Section 12 for the full timeline)

1. `src/dataset_builder.py` — assemble the hybrid dataset into the unified schema
2. `db/schema.sql` + load script — create the SQLite database
3. `src/preprocessing.py` — cleaning, encoding, normalisation
4. `src/classification.py` — train/evaluate the Random Forest model
5. `src/clustering.py` — train/evaluate the K-Means model
6. `src/trends.py` — aggregate model output into Trend Report records
7. `app/` — Streamlit dashboard pages (Upload, Trends Overview, Geographic View, Demographic View, Clusters, Model Performance, Reports)
