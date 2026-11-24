"""
Builds the hybrid patient-records dataset described in the PRD, Section 5.

Composition (stated here for academic transparency - restate this in Chapter 4):
  - Diabetes:  REAL clinical data from the Osun State University ML dataset
               (Mendeley Data, CC BY 4.0, 1,500 records: Age, Gender, BMI,
               Blood Pressure, Glucose, HbA1c, Family History, Hypertension,
               Diabetes Status). Both diabetic and non-diabetic rows are kept;
               non-diabetic rows become the "none" diagnosis class.
  - Typhoid:   LITERATURE-INFORMED SYNTHETIC. No real public tabular dataset
               with the required age/sex/location/date schema exists for
               Nigeria (confirmed by searching Kaggle, Mendeley, Zenodo, Dryad,
               and the NCDC portal). Geographic concentration follows Akinyemi
               et al. (2018), who documented typhoid trends across Lagos,
               Kano, and Abuja.
  - Malaria:   LITERATURE-INFORMED SYNTHETIC, same reason as typhoid. Seasonal
               and age patterns follow Ayoka & Nnadi (2026) and general
               Nigerian malaria epidemiology cited in Chapter 2 of the thesis
               (rainy-season peak, higher burden in under-5s).

Output: data/raw/patient_records.csv, in the unified schema:
  patient_id, age, sex, location, visit_date, diagnosis,
  glucose, bmi, hba1c, fever_days, parasite_density

Disease-specific clinical columns are NaN where not applicable to that
diagnosis - preprocessing.py handles that before modelling.
"""
import os
import sys
import numpy as np
import pandas as pd

RNG_SEED = 42
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DIABETES_SOURCE = os.path.join(RAW_DIR, "diabetes_osun.csv")
OUTPUT_PATH = os.path.join(RAW_DIR, "patient_records.csv")

# Nigerian states weighted toward where the cited literature draws its evidence from.
# Typhoid concentration: Lagos, Kano, Abuja (Akinyemi et al., 2018).
# Malaria: broader national spread with a rural/northern skew, consistent with
# general Nigerian malaria burden patterns discussed in Chapter 2.
TYPHOID_LOCATIONS = ["Lagos", "Kano", "FCT Abuja"]
TYPHOID_LOCATION_WEIGHTS = [0.45, 0.35, 0.20]

MALARIA_LOCATIONS = [
    "Lagos", "Kano", "FCT Abuja", "Rivers", "Oyo", "Kaduna", "Sokoto",
    "Borno", "Enugu", "Osun", "Benue", "Plateau",
]
MALARIA_LOCATION_WEIGHTS = [0.10, 0.12, 0.08, 0.08, 0.08, 0.10, 0.09,
                            0.08, 0.07, 0.06, 0.07, 0.07]

DIABETES_LOCATIONS = ["Osun", "Kwara"]  # Osun State University + UITH/Offa catchment
DIABETES_LOCATION_WEIGHTS = [0.7, 0.3]

DATE_START = pd.Timestamp("2024-01-01")
DATE_END = pd.Timestamp("2025-12-31")


def _random_dates(rng, n, seasonal_weights=None):
    """Random visit dates between DATE_START and DATE_END.

    seasonal_weights: optional dict {month: weight} to bias sampling toward
    particular months (used for malaria's rainy-season peak).
    """
    all_days = pd.date_range(DATE_START, DATE_END, freq="D")
    if seasonal_weights is None:
        idx = rng.integers(0, len(all_days), size=n)
        return all_days[idx]
    weights = np.array([seasonal_weights.get(d.month, 1.0) for d in all_days], dtype=float)
    weights /= weights.sum()
    idx = rng.choice(len(all_days), size=n, p=weights)
    return all_days[idx]


def load_diabetes_real():
    """Load the real Osun State University diabetes dataset.

    ACTION required before running this: download the CSV from
    https://data.mendeley.com/datasets/ksdk5m939c/1 and save it to
    data/raw/diabetes_osun.csv (columns: Age, Gender, BMI, Blood Pressure,
    Glucose, HbA1c, Family History, Hypertension, Diabetes Status).
    """
    if not os.path.exists(DIABETES_SOURCE):
        raise FileNotFoundError(
            f"Expected the real diabetes dataset at {DIABETES_SOURCE}.\n"
            "Download it from https://data.mendeley.com/datasets/ksdk5m939c/1 "
            "(CC BY 4.0) and save it there before running dataset_builder.py."
        )
    df = pd.read_csv(DIABETES_SOURCE)
    df.columns = [c.strip() for c in df.columns]

    rng = np.random.default_rng(RNG_SEED)
    n = len(df)
    out = pd.DataFrame({
        "patient_id": [f"DIA{i:05d}" for i in range(n)],
        "age": df["Age"].astype(int),
        "sex": df["Gender"].map({"Male": "M", "Female": "F", "M": "M", "F": "F"}).fillna("F"),
        "location": rng.choice(DIABETES_LOCATIONS, size=n, p=DIABETES_LOCATION_WEIGHTS),
        "visit_date": _random_dates(rng, n),
        "diagnosis": np.where(df["Diabetes Status"].astype(int) == 1, "diabetes", "none"),
        "glucose": df["Glucose Level"].astype(float),
        "bmi": df["BMI"].astype(float),
        "hba1c": df["HbA1c"].astype(float),
        "fever_days": np.nan,
        "parasite_density": np.nan,
    })
    return out


def generate_typhoid_synthetic(n=400):
    """Literature-informed synthetic typhoid records (see module docstring)."""
    rng = np.random.default_rng(RNG_SEED + 1)
    age = rng.integers(2, 65, size=n)
    sex = rng.choice(["M", "F"], size=n)
    location = rng.choice(TYPHOID_LOCATIONS, size=n, p=TYPHOID_LOCATION_WEIGHTS)
    visit_date = _random_dates(rng, n)
    # Fever duration before presentation - typhoid typically presents after several
    # days of sustained fever rather than an acute 1-2 day onset (unlike malaria).
    fever_days = rng.integers(5, 21, size=n)

    return pd.DataFrame({
        "patient_id": [f"TYP{i:05d}" for i in range(n)],
        "age": age,
        "sex": sex,
        "location": location,
        "visit_date": visit_date,
        "diagnosis": "typhoid",
        "glucose": np.nan,
        "bmi": np.nan,
        "hba1c": np.nan,
        "fever_days": fever_days,
        "parasite_density": np.nan,
    })


def generate_malaria_synthetic(n=600):
    """Literature-informed synthetic malaria records (see module docstring).

    Seasonal weighting peaks April-October (Nigeria's rainy season, when
    mosquito-breeding conditions and transmission rise), per the general
    epidemiology cited in Chapter 2.
    """
    rng = np.random.default_rng(RNG_SEED + 2)
    # Under-5s and the 15-35 age band are the most frequently affected groups
    # in Nigerian malaria literature; sample a mixture rather than a flat range.
    under_five = rng.integers(0, 5, size=int(n * 0.35))
    adult = rng.integers(5, 70, size=n - len(under_five))
    age = rng.permutation(np.concatenate([under_five, adult]))
    sex = rng.choice(["M", "F"], size=n)
    location = rng.choice(MALARIA_LOCATIONS, size=n, p=MALARIA_LOCATION_WEIGHTS)
    seasonal_weights = {m: (2.5 if 4 <= m <= 10 else 1.0) for m in range(1, 13)}
    visit_date = _random_dates(rng, n, seasonal_weights=seasonal_weights)
    # Fever duration before presentation - malaria is typically acute (1-4 days)
    # in contrast to typhoid's longer sustained fever.
    fever_days = rng.integers(1, 5, size=n)
    # Parasite density proxy (parasites/uL blood), log-normal-ish spread.
    parasite_density = np.round(rng.lognormal(mean=7.5, sigma=1.2, size=n))

    return pd.DataFrame({
        "patient_id": [f"MAL{i:05d}" for i in range(n)],
        "age": age,
        "sex": sex,
        "location": location,
        "visit_date": visit_date,
        "diagnosis": "malaria",
        "glucose": np.nan,
        "bmi": np.nan,
        "hba1c": np.nan,
        "fever_days": fever_days,
        "parasite_density": parasite_density,
    })


def build_dataset():
    diabetes_df = load_diabetes_real()
    typhoid_df = generate_typhoid_synthetic()
    malaria_df = generate_malaria_synthetic()

    combined = pd.concat([diabetes_df, typhoid_df, malaria_df], ignore_index=True)
    combined["visit_date"] = pd.to_datetime(combined["visit_date"]).dt.strftime("%Y-%m-%d")

    os.makedirs(RAW_DIR, exist_ok=True)
    combined.to_csv(OUTPUT_PATH, index=False)

    print(f"Wrote {len(combined)} records to {OUTPUT_PATH}")
    print(combined["diagnosis"].value_counts())
    return combined


if __name__ == "__main__":
    try:
        build_dataset()
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
