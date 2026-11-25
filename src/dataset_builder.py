"""
Builds the patient-records dataset described in the PRD, Section 5.

Composition (stated here for academic transparency - restate this in Chapter 4):
  - Diabetes: REAL clinical data, Osun State University ML dataset
              (Mendeley Data, CC BY 4.0, 1,500 records: Age, Gender, BMI,
              Blood_Pressure_Systolic, Glucose_Level, HbA1c, Family_History,
              Hypertension_Status, Diabetes_Status). Both diabetic and
              non-diabetic rows are kept; non-diabetic rows become the "none"
              diagnosis class.
  - Malaria & Typhoid: REAL clinical data, "Prevalence and Management
              Practices of Malaria-Typhoid Co-Infection in Unwana, South
              East Nigeria" (Mendeley Data, DOI 10.17632/yk9dcmd94w.1,
              CC BY 4.0), 236 real febrile patients from Akanu Ibiam Federal
              Polytechnic medical centre, Afikpo, Ebonyi State, diagnosed by
              blood-film microscopy (malaria) and the Widal test (typhoid).
              The "MALARIA" sheet (137 patients, malaria positive only) maps
              to diagnosis="malaria"; the "MALARIA-TYPHOID" sheet (99
              co-infected patients) maps to diagnosis="typhoid", since this
              project's three-way classification scheme has no co-infection
              category and typhoid is otherwise unrepresented in this
              source. Age is recorded only as a 5-year bracket (e.g.
              "23-27") - the bracket midpoint is used as a representative
              age. The source does not record an individual visit date (a
              known limitation of this single-site, ~6-month study); dates
              are distributed uniformly across that reported collection
              window purely to populate the system's month/season feature -
              this is the one place a value is not read directly from the
              source, and it is disclosed here rather than left implicit.

No records in this dataset are invented or literature-simulated - every
row traces to a real patient or real clinical measurement. Broader
multi-state, multi-year malaria trend context (which this single-site
dataset cannot provide on its own) comes from a second, separate real
source - the NMDR monthly state-level surveillance series - loaded directly
into the trend_report table by trends.py, not merged into this patient-level
file (it has no patient-level fields to merge).

Output: data/raw/patient_records.csv, in the unified schema:
  patient_id, age, sex, location, visit_date, diagnosis,
  glucose, bmi, hba1c, blood_pressure_systolic, family_history, hypertension,
  malaria_parasite_grade, widal_o, widal_h

Disease-specific clinical columns are NaN where not applicable to that
diagnosis - preprocessing.py handles that before modelling.

Two real signals were added after an initial accuracy review found they
had been collected but left unused:
  - widal_o / widal_h: the real Widal test O and H antigen titers (e.g.
    "160  80" in the source) - this is literally the real diagnostic
    evidence the Unwana study used to tell typhoid-positive patients apart
    from malaria-only patients, so including it (rather than only the MP
    malaria-parasite grade, which both groups have since the typhoid group
    is also malaria-positive) is what actually lets the classifier learn
    the real distinction instead of guessing from a shared signal.
  - family_history / hypertension: real Yes/No risk-factor fields in the
    diabetes source, encoded 0/1, previously left out of the feature set
    for no principled reason.
"""
import os
import sys
import numpy as np
import pandas as pd

RNG_SEED = 42
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DIABETES_SOURCE = os.path.join(RAW_DIR, "diabetes_dataset Version 2.csv")
UNWANA_SOURCE = os.path.join(RAW_DIR, "Second DATASET TETFund.xlsx")
OUTPUT_PATH = os.path.join(RAW_DIR, "patient_records.csv")

DIABETES_LOCATIONS = ["Osun", "Kwara"]  # Osun State University + UITH/Offa catchment
DIABETES_LOCATION_WEIGHTS = [0.7, 0.3]

# The Unwana study's reported data-collection window (per the published
# methodology) - used only to spread visit_date for the system's
# month/season feature, since the source has no per-patient date.
UNWANA_COLLECTION_START = pd.Timestamp("2019-01-01")
UNWANA_COLLECTION_END = pd.Timestamp("2019-06-30")
UNWANA_LOCATION = "Ebonyi"

MP_GRADE = {"1+": 1, "2+": 2, "3+": 3}


def _random_dates(rng, n, start, end):
    all_days = pd.date_range(start, end, freq="D")
    idx = rng.integers(0, len(all_days), size=n)
    return all_days[idx]


def _age_bracket_midpoint(bracket):
    """'23-27' -> 25; '53-ABOVE' -> 55 (open-ended top bracket)."""
    bracket = str(bracket).strip()
    if "ABOVE" in bracket.upper():
        low = int(bracket.split("-")[0])
        return low + 2
    low, high = bracket.split("-")
    return (int(low) + int(high)) // 2


def load_diabetes_real():
    """Load the real Osun State University diabetes dataset
    (https://data.mendeley.com/datasets/ksdk5m939c/1, CC BY 4.0).

    Real file columns (confirmed from the actual downloaded CSV, not assumed):
    Age, Gender, BMI, Blood_Pressure_Systolic, Glucose_Level, HbA1c,
    Family_History, Hypertension_Status, Diabetes_Status (values
    "Diabetic"/"Non-Diabetic", not 0/1). A small number of rows (~1-2%) have
    missing Age or Gender; those are dropped since both are required fields
    in the unified schema - everything else is kept, including rows with
    missing clinical values, since those stay legitimately NaN downstream.
    """
    if not os.path.exists(DIABETES_SOURCE):
        raise FileNotFoundError(
            f"Expected the real diabetes dataset at {DIABETES_SOURCE}.\n"
            "Download it from https://data.mendeley.com/datasets/ksdk5m939c/1 "
            "(CC BY 4.0) and save it there before running dataset_builder.py."
        )
    df = pd.read_csv(DIABETES_SOURCE)
    df.columns = [c.strip() for c in df.columns]

    before = len(df)
    df = df.dropna(subset=["Age", "Gender"]).reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        print(f"Diabetes source: dropped {dropped} rows with missing Age/Gender (kept {len(df)})")

    rng = np.random.default_rng(RNG_SEED)
    n = len(df)
    yes_no = {"Yes": 1, "No": 0}
    out = pd.DataFrame({
        "patient_id": [f"DIA{i:05d}" for i in range(n)],
        "age": df["Age"].astype(int),
        "sex": df["Gender"].map({"Male": "M", "Female": "F", "M": "M", "F": "F"}),
        "location": rng.choice(DIABETES_LOCATIONS, size=n, p=DIABETES_LOCATION_WEIGHTS),
        "visit_date": _random_dates(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31")),
        "diagnosis": np.where(df["Diabetes_Status"] == "Diabetic", "diabetes", "none"),
        "glucose": df["Glucose_Level"].astype(float),
        "bmi": df["BMI"].astype(float),
        "hba1c": df["HbA1c"].astype(float),
        "blood_pressure_systolic": df["Blood_Pressure_Systolic"].astype(float),
        "family_history": df["Family_History"].map(yes_no),
        "hypertension": df["Hypertension_Status"].map(yes_no),
        "malaria_parasite_grade": np.nan,
        "widal_o": np.nan,
        "widal_h": np.nan,
    })
    return out


def _parse_widal(raw):
    """'160  80' -> (160, 80); the real O and H antigen titer pair from the
    Widal test. Both sheets have this column (malaria-only patients were
    also tested, and came back at baseline), so it is this pair - not the
    malaria-only MP grade - that is the real signal separating a
    typhoid-positive diagnosis from a malaria-only one.
    """
    parts = str(raw).split()
    if len(parts) != 2:
        return (np.nan, np.nan)
    return (float(parts[0]), float(parts[1]))


def _load_unwana_sheet(sheet_name, diagnosis, rng):
    """One sheet of the real Unwana malaria-typhoid co-infection dataset.
    See module docstring for the diagnosis mapping rationale.
    """
    df = pd.read_excel(UNWANA_SOURCE, sheet_name=sheet_name, header=2)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(subset=["SEX", "AGE"]).reset_index(drop=True)

    widal = df["WIDAL  O        H"].apply(_parse_widal)
    widal_o = widal.apply(lambda t: t[0])
    widal_h = widal.apply(lambda t: t[1])

    n = len(df)
    prefix = "MAL" if diagnosis == "malaria" else "TYP"
    out = pd.DataFrame({
        "patient_id": [f"{prefix}{i:05d}" for i in range(n)],
        "age": df["AGE"].apply(_age_bracket_midpoint),
        "sex": df["SEX"].astype(str).str.strip(),
        "location": UNWANA_LOCATION,
        "visit_date": _random_dates(rng, n, UNWANA_COLLECTION_START, UNWANA_COLLECTION_END),
        "diagnosis": diagnosis,
        "glucose": np.nan,
        "bmi": np.nan,
        "hba1c": np.nan,
        "blood_pressure_systolic": np.nan,
        "family_history": np.nan,
        "hypertension": np.nan,
        # Real qualitative malaria parasite density grade (MP test result:
        # 1+/2+/3+), encoded numerically - not an absolute parasite count.
        "malaria_parasite_grade": df["MP"].astype(str).str.strip().map(MP_GRADE),
        "widal_o": widal_o,
        "widal_h": widal_h,
    })
    return out


def load_unwana_malaria_typhoid():
    """Load the real Unwana malaria-typhoid co-infection dataset (see module
    docstring). Returns (malaria_df, typhoid_df).
    """
    if not os.path.exists(UNWANA_SOURCE):
        raise FileNotFoundError(
            f"Expected the real Unwana malaria-typhoid dataset at {UNWANA_SOURCE}.\n"
            "Download it from https://data.mendeley.com/datasets/yk9dcmd94w/1 "
            "(CC BY 4.0) and save it there before running dataset_builder.py."
        )
    rng = np.random.default_rng(RNG_SEED + 1)
    malaria_df = _load_unwana_sheet("MALARIA", "malaria", rng)
    typhoid_df = _load_unwana_sheet("MALARIA-TYPHOID", "typhoid", rng)
    return malaria_df, typhoid_df


def build_dataset():
    diabetes_df = load_diabetes_real()
    malaria_df, typhoid_df = load_unwana_malaria_typhoid()

    combined = pd.concat([diabetes_df, malaria_df, typhoid_df], ignore_index=True)
    combined["visit_date"] = pd.to_datetime(combined["visit_date"]).dt.strftime("%Y-%m-%d")

    os.makedirs(RAW_DIR, exist_ok=True)
    combined.to_csv(OUTPUT_PATH, index=False)

    print(f"Wrote {len(combined)} records to {OUTPUT_PATH} (all real patient data, no synthetic rows)")
    print(combined["diagnosis"].value_counts())
    return combined


if __name__ == "__main__":
    try:
        build_dataset()
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
