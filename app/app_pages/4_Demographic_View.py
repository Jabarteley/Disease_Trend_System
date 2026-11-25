import os
import sys
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_patient_diagnoses, auth_gate, page_header  # noqa: E402

auth_gate()

page_header(":material/group: Demographic view", "Cases broken down by age group and sex, per disease.")

df = load_patient_diagnoses()
if df.empty:
    st.info("No data yet — open Upload first.", icon=":material/upload_file:")
    st.stop()


def age_group(age):
    if age < 5:
        return "under_5"
    if age < 18:
        return "5_17"
    if age < 35:
        return "18_34"
    if age < 60:
        return "35_59"
    return "60_plus"


df["age_group"] = df["age"].apply(age_group)
age_order = ["under_5", "5_17", "18_34", "35_59", "60_plus"]

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.subheader("Cases by age group")
        by_age = (
            df.groupby(["age_group", "disease_code"]).size()
            .unstack(fill_value=0)
            .reindex(age_order)
        )
        st.bar_chart(by_age, alt="Cases by age group, grouped by disease")

with col2:
    with st.container(border=True):
        st.subheader("Cases by sex")
        by_sex = df.groupby(["sex", "disease_code"]).size().unstack(fill_value=0)
        st.bar_chart(by_sex, alt="Cases by sex, grouped by disease")
