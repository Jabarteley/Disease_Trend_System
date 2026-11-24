"""
Aggregates diagnosis records into Trend Report rows (PRD Section 6/10):
case counts per disease, per month, per location. This is what the
dashboard's Trends Overview / Geographic View pages read from - they never
recompute trends themselves.
"""
import os
import sqlite3
from datetime import datetime, timezone

from db import get_connection, init_db

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


def compute_trend_reports(conn=None):
    own_conn = conn is None
    conn = conn or get_connection()
    init_db(conn)

    cur = conn.cursor()
    cur.execute("DELETE FROM trend_report")

    rows = conn.execute(AGGREGATION_SQL).fetchall()
    generated_at = datetime.now(timezone.utc).isoformat()
    cur.executemany(
        "INSERT INTO trend_report (disease_code, period, location, trend_value, generated_at) VALUES (?, ?, ?, ?, ?)",
        [(r[0], r[1], r[2], r[3], generated_at) for r in rows],
    )
    conn.commit()
    print(f"Computed {len(rows)} trend_report rows")
    if own_conn:
        conn.close()
    return rows


if __name__ == "__main__":
    compute_trend_reports()
