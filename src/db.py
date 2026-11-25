"""
SQLite helper: initialise the schema and load the cleaned patient-records
table (Patient -> Visit -> Diagnosis), per the ERD in PRD Section 6.
"""
import os
import sqlite3
import pandas as pd

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "db")
DB_PATH = os.path.join(DB_DIR, "disease_trend.sqlite")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db(conn=None):
    own_conn = conn is None
    conn = conn or get_connection()
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    if own_conn:
        conn.close()


def load_patient_records(df, conn=None):
    """Load a cleaned patient-records DataFrame (one row per patient visit +
    diagnosis) into the patient/visit/diagnosis tables. Idempotent: clears
    existing rows first so re-running after a new upload doesn't duplicate.
    """
    own_conn = conn is None
    conn = conn or get_connection()
    init_db(conn)
    cur = conn.cursor()

    cur.execute("DELETE FROM diagnosis")
    cur.execute("DELETE FROM visit")
    cur.execute("DELETE FROM patient")

    patients = df[["patient_id", "age", "sex", "location"]].drop_duplicates(subset=["patient_id"])
    patients.to_sql("patient", conn, if_exists="append", index=False)

    for _, row in df.iterrows():
        cur.execute(
            "INSERT INTO visit (patient_id, visit_date, facility) VALUES (?, ?, ?)",
            (row["patient_id"], str(row["visit_date"]), None),
        )
        visit_id = cur.lastrowid
        cur.execute(
            """INSERT INTO diagnosis
               (visit_id, disease_code, disease_name, glucose, bmi, hba1c, blood_pressure_systolic,
                family_history, hypertension, malaria_parasite_grade, widal_o, widal_h)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                visit_id, row["diagnosis"], row["diagnosis"],
                row.get("glucose"), row.get("bmi"), row.get("hba1c"), row.get("blood_pressure_systolic"),
                row.get("family_history"), row.get("hypertension"),
                row.get("malaria_parasite_grade"), row.get("widal_o"), row.get("widal_h"),
            ),
        )
    conn.commit()
    print(f"Loaded {len(patients)} patients / {len(df)} visits+diagnoses into {DB_PATH}")
    if own_conn:
        conn.close()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from preprocessing import run as run_preprocessing

    df, *_ = run_preprocessing()
    load_patient_records(df)
