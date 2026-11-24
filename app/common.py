"""
Shared setup for every Streamlit page: makes src/ importable and provides
cached data-loading helpers so pages don't each re-read the database.
"""
import os
import sys
import sqlite3
import pandas as pd
import streamlit as st

ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

DB_PATH = os.path.join(ROOT_DIR, "db", "disease_trend.sqlite")
PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")


def db_exists():
    return os.path.exists(DB_PATH)


@st.cache_data(ttl=60)
def load_trend_reports():
    if not db_exists():
        return pd.DataFrame(columns=["disease_code", "period", "location", "trend_value"])
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM trend_report", conn)
    conn.close()
    return df


@st.cache_data(ttl=60)
def load_patient_diagnoses():
    if not db_exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """SELECT p.patient_id, p.age, p.sex, p.location, v.visit_date, d.disease_code
           FROM diagnosis d
           JOIN visit v ON v.visit_id = d.visit_id
           JOIN patient p ON p.patient_id = v.patient_id""",
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=60)
def load_clustered_records():
    path = os.path.join(PROCESSED_DIR, "patient_records_clustered.csv")
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def clear_cache():
    st.cache_data.clear()
