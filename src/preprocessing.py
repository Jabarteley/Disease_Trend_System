"""
Data preparation (CRISP-DM phase 3) over the unified hybrid dataset produced
by dataset_builder.py.

Steps:
  1. Load data/raw/patient_records.csv
  2. Clean: drop exact duplicates, fill/flag missing clinical values
  3. Encode: sex, location, diagnosis -> numeric columns for modelling
  4. Derive: age_group, visit_month, visit_season (useful clustering/trend features)
  5. Split: stratified train/val/test (70/15/15) by diagnosis
  6. Save cleaned full table + splits to data/processed/
"""
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "patient_records.csv")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

CLINICAL_COLUMNS = ["glucose", "bmi", "hba1c", "fever_days", "parasite_density"]
SEED = 42


def _age_group(age):
    if age < 5:
        return "under_5"
    if age < 18:
        return "5_17"
    if age < 35:
        return "18_34"
    if age < 60:
        return "35_59"
    return "60_plus"


def _season(month):
    return "rainy" if 4 <= month <= 10 else "dry"


def load_raw():
    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(
            f"{RAW_PATH} not found - run dataset_builder.py first to build the hybrid dataset."
        )
    return pd.read_csv(RAW_PATH, parse_dates=["visit_date"])


def clean(df):
    before = len(df)
    df = df.drop_duplicates(subset=["patient_id"]).copy()
    dropped = before - len(df)
    if dropped:
        print(f"Dropped {dropped} duplicate patient_id rows")

    # Clinical columns are legitimately NaN when not applicable to that
    # diagnosis (e.g. glucose for a typhoid case) - leave those as NaN and
    # let the model-specific feature sets (Section 9 of the PRD) pick only
    # the columns relevant to each model, rather than imputing across
    # unrelated diseases.
    df["age"] = df["age"].clip(lower=0, upper=110)
    return df


def encode(df):
    df = df.copy()
    encoders = {}
    for col in ["sex", "location", "diagnosis"]:
        le = LabelEncoder()
        df[f"{col}_code"] = le.fit_transform(df[col])
        encoders[col] = le

    df["age_group"] = df["age"].apply(_age_group)
    df["visit_month"] = df["visit_date"].dt.month
    df["visit_season"] = df["visit_month"].apply(_season)

    age_group_le = LabelEncoder()
    df["age_group_code"] = age_group_le.fit_transform(df["age_group"])
    encoders["age_group"] = age_group_le

    season_le = LabelEncoder()
    df["visit_season_code"] = season_le.fit_transform(df["visit_season"])
    encoders["visit_season"] = season_le

    return df, encoders


def split(df):
    train_df, temp_df = train_test_split(
        df, test_size=0.30, stratify=df["diagnosis"], random_state=SEED
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.50, stratify=temp_df["diagnosis"], random_state=SEED
    )
    return train_df, val_df, test_df


def run():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    df = load_raw()
    df = clean(df)
    df, encoders = encode(df)

    full_path = os.path.join(PROCESSED_DIR, "patient_records_clean.csv")
    df.to_csv(full_path, index=False)

    train_df, val_df, test_df = split(df)
    train_df.to_csv(os.path.join(PROCESSED_DIR, "train.csv"), index=False)
    val_df.to_csv(os.path.join(PROCESSED_DIR, "val.csv"), index=False)
    test_df.to_csv(os.path.join(PROCESSED_DIR, "test.csv"), index=False)

    print(f"Cleaned dataset: {len(df)} rows -> {full_path}")
    print(f"Train: {len(train_df)}  Val: {len(val_df)}  Test: {len(test_df)}")
    print(df["diagnosis"].value_counts())
    return df, train_df, val_df, test_df


if __name__ == "__main__":
    run()
