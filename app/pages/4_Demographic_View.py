import os
import sys
import streamlit as st
import plotly.express as px
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_patient_diagnoses  # noqa: E402

st.title("Demographic View")

df = load_patient_diagnoses()
if df.empty:
    st.warning("No data yet — go to the Upload page first.")
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

col1, col2 = st.columns(2)
with col1:
    by_age = df.groupby(["age_group", "disease_code"], as_index=False).size()
    fig1 = px.bar(
        by_age, x="age_group", y="size", color="disease_code", barmode="group",
        category_orders={"age_group": ["under_5", "5_17", "18_34", "35_59", "60_plus"]},
        labels={"age_group": "Age group", "size": "Cases", "disease_code": "Disease"},
        title="Cases by age group",
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    by_sex = df.groupby(["sex", "disease_code"], as_index=False).size()
    fig2 = px.bar(
        by_sex, x="sex", y="size", color="disease_code", barmode="group",
        labels={"sex": "Sex", "size": "Cases", "disease_code": "Disease"},
        title="Cases by sex",
    )
    st.plotly_chart(fig2, use_container_width=True)
