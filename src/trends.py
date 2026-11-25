"""
Aggregates diagnosis records into Trend Report rows (PRD Section 6/10):
case counts per disease, per month, per location. This is what the
dashboard's Trends Overview / Geographic View pages read from - they never
recompute trends themselves.

Two REAL sources feed trend_report, tagged by the `source` column so it's
always clear which is which:
  - 'patient_records': computed from this app's own patient/visit/diagnosis
    tables (diabetes + the real Unwana malaria/typhoid patients).
  - 'nmdr_surveillance': the real, official National Malaria Data Repository
    monthly state-level case counts for Nasarawa, Kwara, and Zamfara
    (2015-2024), loaded directly - not patient-level, so it bypasses the
    patient/visit/diagnosis tables entirely, but it is genuine official
    Nigerian surveillance data, giving real multi-state, multi-year malaria
    trend context the single-site Unwana dataset cannot provide on its own.
"""
import os
import pandas as pd
from datetime import datetime, timezone

from db import get_connection, init_db

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
NMDR_SOURCE = os.path.join(RAW_DIR, "Wavelets_data for Time series_malaria.csv")

AGGREGATION_SQL = """
SELECT
    d.disease_code AS disease_code,
    strftime('%Y-%m', v.visit_date) AS period,
    p.location AS location,
    COUNT(*) AS trend_value
FROM diagnosis d
JOIN visit v ON v.visit_id = d.visit_id
JOIN patient p ON p.patient_id = v.patient_id
GROUP BY d.disease_code, period, p.location
ORDER BY period, disease_code, location
"""


def _load_nmdr_rows():
    """Real monthly malaria case counts for Nasarawa, Kwara, and Zamfara
    states (2015-2024), from the National Malaria Data Repository -
    supplementary data for a 2026 PLOS ONE paper, figshare DOI
    10.6084/m9.figshare.30716729. Not required for the app to run - skipped
    with a message if the file hasn't been downloaded.
    """
    if not os.path.exists(NMDR_SOURCE):
        print(f"NMDR surveillance file not found at {NMDR_SOURCE} - skipping (optional real supplementary data).")
        return []
    df = pd.read_csv(NMDR_SOURCE)
    df.columns = [c.strip() for c in df.columns]
    rows = []
    for _, r in df.iterrows():
        period = f"{int(r['year']):04d}-{int(r['month']):02d}"
        rows.append((str(r["State"]).strip(), period, float(r["cases"])))
    return rows


def compute_trend_reports(conn=None):
    own_conn = conn is None
    conn = conn or get_connection()
    init_db(conn)

    cur = conn.cursor()
    cur.execute("DELETE FROM trend_report")
    generated_at = datetime.now(timezone.utc).isoformat()

    patient_rows = conn.execute(AGGREGATION_SQL).fetchall()
    cur.executemany(
        "INSERT INTO trend_report (disease_code, period, location, trend_value, source, generated_at) VALUES (?, ?, ?, ?, ?, ?)",
        [(r[0], r[1], r[2], r[3], "patient_records", generated_at) for r in patient_rows],
    )

    nmdr_rows = _load_nmdr_rows()
    cur.executemany(
        "INSERT INTO trend_report (disease_code, period, location, trend_value, source, generated_at) VALUES (?, ?, ?, ?, ?, ?)",
        [("malaria", period, location, cases, "nmdr_surveillance", generated_at) for location, period, cases in nmdr_rows],
    )

    conn.commit()
    total = len(patient_rows) + len(nmdr_rows)
    print(f"Computed {len(patient_rows)} trend_report rows from patient records + loaded {len(nmdr_rows)} real NMDR surveillance rows = {total} total")
    if own_conn:
        conn.close()
    return total


if __name__ == "__main__":
    compute_trend_reports()
