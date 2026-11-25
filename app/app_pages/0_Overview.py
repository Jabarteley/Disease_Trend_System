import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import (  # noqa: E402
    load_kpis, load_month_over_month, load_recent_aggregations, load_trend_reports,
    auth_gate, clear_cache, db_exists, inject_theme_css, DISEASE_COLORS, ROOT_DIR,
)

auth_gate()

DISEASE_ICONS = {
    "diabetes": ":material/monitor_heart:",
    "malaria": ":material/pest_control:",
    "typhoid": ":material/water_drop:",
    "none": ":material/health_and_safety:",
}

# --- One-time auto-bootstrap: if the bundled dataset exists but the
# database has never been built, load it automatically so nobody has to
# click through Upload just to see the dashboard. ---
RAW_PATH = os.path.join(ROOT_DIR, "data", "raw", "patient_records.csv")
if not db_exists() and os.path.exists(RAW_PATH):
    with st.spinner("First run: loading the dataset into the database..."):
        sys.path.insert(0, os.path.join(ROOT_DIR, "src"))
        import preprocessing
        import db as db_module
        import trends
        try:
            clean_df, *_ = preprocessing.run()
            db_module.load_patient_records(clean_df)
            trends.compute_trend_reports()
            clear_cache()
        except Exception as e:
            st.error(f"Could not auto-load the bundled dataset: {e}", icon=":material/error:")

inject_theme_css()
_kpi_css = "\n".join(
    f".st-key-kpi-{disease} {{ border-top: 4px solid {color}; border-radius: 10px; }}"
    for disease, color in DISEASE_COLORS.items()
)
st.html(f"<style>.st-key-kpi-total {{ border-top: 4px solid #515F74; border-radius: 10px; }}\n{_kpi_css}</style>")

with st.container(key="app-header"):
    header_col, status_col = st.columns([3, 2], vertical_alignment="center")
    with header_col:
        st.title(":material/monitoring: Disease trend analysis system")
        st.caption("Analysis of patient health records for disease trend identification using data mining")

kpis = load_kpis()
mom = load_month_over_month()

if kpis["total"] == 0:
    st.info(
        "No data loaded yet. Open **Upload** in the sidebar, use the bundled "
        "dataset (or upload your own CSV), and run the pipeline.",
        icon=":material/upload_file:",
    )
    st.stop()

with status_col:
    with st.container(horizontal=True, horizontal_alignment="right"):
        st.badge("Pipeline ready", icon=":material/check_circle:", color="green")
        st.badge(f"Dataset: real, N={kpis['total']:,}", icon=":material/database:", color="blue")
        st.badge("RF + K-Means", icon=":material/psychology:", color="violet")

# --- Real, data-driven alert: the disease with the largest month-over-month increase ---
movers = mom.dropna(subset=["pct_change"])
if not movers.empty:
    top_mover = movers.loc[movers["pct_change"].idxmax()]
    if top_mover["pct_change"] > 0:
        st.warning(
            f"**{top_mover['disease_code'].title()} rose {top_mover['pct_change']:.1f}%** "
            f"in {top_mover['latest_period']} versus the prior period "
            f"({int(top_mover['previous'])} → {int(top_mover['latest'])} cases).",
            icon=":material/crisis_alert:",
        )

st.divider()

# --- KPI row ---
with st.container(horizontal=True):
    with st.container(key="kpi-total"):
        st.metric("Total records", f"{kpis['total']:,}", border=True)
    for disease, count in sorted(kpis["by_disease"].items(), key=lambda kv: -kv[1]):
        pct = count / kpis["total"] * 100
        delta = None
        match = mom[mom["disease_code"] == disease]
        if not match.empty and match.iloc[0]["pct_change"] is not None:
            delta = f"{match.iloc[0]['pct_change']:+.1f}% latest period"
        with st.container(key=f"kpi-{disease}"):
            st.metric(
                f"{DISEASE_ICONS.get(disease, ':material/health_and_safety:')} {disease.title()}",
                f"{count:,}",
                delta,
                delta_description=f"{pct:.1f}% of cohort" if delta is None else None,
                border=True,
            )

st.divider()

# --- Trajectory + decomposition ---
col_trend, col_decomp = st.columns([2, 1])
with col_trend:
    with st.container(border=True):
        st.subheader("Case counts over time")
        trend_df = load_trend_reports()
        monthly = (
            trend_df.groupby(["period", "disease_code"], as_index=False)["trend_value"]
            .sum()
            .pivot(index="period", columns="disease_code", values="trend_value")
            .fillna(0)
        )
        st.line_chart(monthly, alt="Monthly case counts by disease")

with col_decomp:
    with st.container(border=True):
        st.subheader("Cohort decomposition")
        st.metric("Total load", f"{kpis['total']:,}", border=False)
        for disease, count in sorted(kpis["by_disease"].items(), key=lambda kv: -kv[1]):
            pct = count / kpis["total"]
            st.markdown(f"**{disease.title()}** — {count:,} ({pct * 100:.1f}%)")
            st.progress(pct)

st.divider()

# --- Recent aggregations + insights ---
col_table, col_insights = st.columns([2, 1])
with col_table:
    with st.container(border=True):
        st.subheader("Recent aggregations")
        st.caption("Each disease's highest-count location for its most recent reporting periods.")
        recent = load_recent_aggregations(n=8)
        if recent.empty:
            st.caption("No trend data yet.")
        else:
            display = recent.rename(columns={
                "period": "Period", "disease_code": "Disease",
                "location": "Top location", "trend_value": "Cases",
            })[["Period", "Disease", "Top location", "Cases"]]
            st.dataframe(display, hide_index=True, width="stretch", alt="Recent trend aggregations by period and disease")

with col_insights:
    with st.container(border=True):
        st.subheader(":material/school: Dataset notes")
        st.caption("Every record in this system is real patient or real surveillance data — see README → Dataset for full sourcing.")
        st.markdown(
            "- **Diabetes**: real clinical records, 1,479 patients — Osun State University, Nigeria (Mendeley, CC BY 4.0)\n"
            "- **Malaria & Typhoid**: real clinical records, 236 patients — Unwana malaria-typhoid "
            "co-infection study, Ebonyi State (Mendeley, CC BY 4.0)\n"
            "- **Malaria (extra)**: real official surveillance counts, 3 states × 10 years — "
            "National Malaria Data Repository, via a 2026 PLOS ONE paper's supplementary data"
        )
