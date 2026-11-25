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


@st.cache_data(ttl=60)
def load_kpis():
    """Total records and per-disease counts, for the KPI row on every page."""
    df = load_patient_diagnoses()
    if df.empty:
        return {"total": 0, "by_disease": {}}
    counts = df["disease_code"].value_counts()
    return {"total": len(df), "by_disease": counts.to_dict()}


@st.cache_data(ttl=60)
def load_month_over_month():
    """Per-disease case counts for the latest period vs the one before it, and
    the percent change — computed directly from trend_report, never invented.
    Returns a DataFrame with columns: disease_code, latest_period, latest,
    previous, pct_change (None where there's no prior period to compare).
    """
    df = load_trend_reports()
    if df.empty:
        return pd.DataFrame(columns=["disease_code", "latest_period", "latest", "previous", "pct_change"])

    by_period = df.groupby(["disease_code", "period"], as_index=False)["trend_value"].sum()
    rows = []
    for disease, g in by_period.groupby("disease_code"):
        g = g.sort_values("period")
        if len(g) == 0:
            continue
        latest_row = g.iloc[-1]
        previous = g.iloc[-2]["trend_value"] if len(g) >= 2 else None
        pct_change = None
        if previous is not None and previous > 0:
            pct_change = (latest_row["trend_value"] - previous) / previous * 100
        rows.append({
            "disease_code": disease,
            "latest_period": latest_row["period"],
            "latest": latest_row["trend_value"],
            "previous": previous,
            "pct_change": pct_change,
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=60)
def load_recent_aggregations(n=8):
    """The n most recent (period, disease, top location) rows from
    trend_report, each disease/period's single highest-count location,
    newest first — for the aggregation table on the Overview page."""
    df = load_trend_reports()
    if df.empty:
        return df
    idx = df.groupby(["period", "disease_code"])["trend_value"].idxmax()
    top_per_period_disease = df.loc[idx].sort_values("period", ascending=False)
    return top_per_period_disease.head(n).reset_index(drop=True)


def clear_cache():
    st.cache_data.clear()


def auth_gate():
    """Require a signed-in user before rendering the rest of the page.

    Uses Streamlit's built-in st.login/st.user (real OIDC identity, per the
    PRD's "manage user account" use case) - never a hand-rolled password
    check. Needs a real identity provider configured in
    .streamlit/secrets.toml (see .streamlit/secrets.toml.example and the
    README) - this code cannot work until real OAuth credentials are filled
    in there.
    """
    def _auth_not_configured():
        st.title(":material/monitoring: Disease trend analysis system")
        st.error(
            "Login is not configured yet. Copy `.streamlit/secrets.toml.example` to "
            "`.streamlit/secrets.toml` and fill in real OAuth credentials from an "
            "identity provider (see README → Authentication).",
            icon=":material/lock:",
        )
        st.stop()

    try:
        logged_in = st.user.is_logged_in
    except Exception:
        _auth_not_configured()
        return

    if not logged_in:
        st.title(":material/monitoring: Disease trend analysis system")
        st.caption("Sign in to continue.")
        with st.container(border=True):
            if st.button("Log in with Google", icon=":material/login:", type="primary"):
                try:
                    st.login("google")
                except Exception:
                    _auth_not_configured()
        st.stop()

    with st.sidebar:
        st.caption(f":material/account_circle: Signed in as **{st.user.get('name', st.user.get('email', 'user'))}**")
        if st.button("Log out", icon=":material/logout:"):
            st.logout()
