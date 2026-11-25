import os
import sys
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import clear_cache, auth_gate, ROOT_DIR, PROCESSED_DIR  # noqa: E402

auth_gate()

sys.path.insert(0, os.path.join(ROOT_DIR, "src"))
import preprocessing  # noqa: E402
import db as db_module  # noqa: E402
import trends  # noqa: E402

st.title(":material/upload_file: Upload")

st.markdown(
    "Upload a patient-records CSV matching the unified schema "
    "(`patient_id, age, sex, location, visit_date, diagnosis, glucose, bmi, "
    "hba1c, fever_days, parasite_density`), or use the bundled hybrid dataset."
)

raw_path = os.path.join(ROOT_DIR, "data", "raw", "patient_records.csv")

with st.container(border=True):
    col1, col2 = st.columns(2, vertical_alignment="bottom")
    with col1:
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
    with col2:
        use_bundled = st.button(
            "Use bundled hybrid dataset",
            icon=":material/dataset:",
            disabled=not os.path.exists(raw_path),
            help="Loads data/raw/patient_records.csv (run src/dataset_builder.py first if missing).",
        )
        if not os.path.exists(raw_path):
            st.caption("Not found yet — run `python src/dataset_builder.py` first.")

df = None
if uploaded is not None:
    df = pd.read_csv(uploaded)
elif use_bundled:
    df = pd.read_csv(raw_path)

if df is not None:
    required = {"patient_id", "age", "sex", "location", "visit_date", "diagnosis"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Missing required columns: {sorted(missing)}", icon=":material/error:")
    else:
        st.success(f"Loaded {len(df)} rows.", icon=":material/check_circle:")
        st.dataframe(df.head(10), hide_index=True, width="stretch", alt="Preview of the first 10 uploaded rows")

        if "pending_raw" not in st.session_state or uploaded is not None:
            if uploaded is not None:
                os.makedirs(os.path.dirname(raw_path), exist_ok=True)
                df.to_csv(raw_path, index=False)
            st.session_state["pending_raw"] = True

        if st.button(
            "Run preprocessing → load database → compute trends",
            type="primary", icon=":material/play_arrow:",
        ):
            try:
                with st.spinner("Preprocessing..."):
                    clean_df, train_df, val_df, test_df = preprocessing.run()
                with st.spinner("Loading database..."):
                    db_module.load_patient_records(clean_df)
                with st.spinner("Computing trend reports..."):
                    trends.compute_trend_reports()
                clear_cache()
                st.success(
                    "Done. Visit Trends Overview, Geographic View, or Demographic View "
                    "to see results.",
                    icon=":material/check_circle:",
                )
            except Exception as e:
                st.error(f"Pipeline failed: {e}", icon=":material/error:")
                with st.expander("Full error details"):
                    st.exception(e)
