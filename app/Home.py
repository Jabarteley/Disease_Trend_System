"""
Streamlit entry point. Run with: streamlit run app/Home.py
Pages live in app/app_pages/ and are wired up below via st.navigation, which
gives each page a real icon and title in the sidebar.

NOTE for future edits: this file and common.py are imported as Python
modules. Streamlit hot-reloads the page script on save, but NOT modules it
imports (common.py, src/*.py) — after editing those, fully stop and
restart `streamlit run`, a browser refresh is not enough.
"""
import streamlit as st

st.set_page_config(
    page_title="Disease Trend Analysis System",
    page_icon=":material/monitoring:",
    layout="wide",
)

pages = [
    st.Page("app_pages/0_Overview.py", title="Overview", icon=":material/monitoring:", default=True),
    st.Page("app_pages/1_Upload.py", title="Upload", icon=":material/upload_file:"),
    st.Page("app_pages/2_Trends_Overview.py", title="Trends overview", icon=":material/timeline:"),
    st.Page("app_pages/3_Geographic_View.py", title="Geographic view", icon=":material/public:"),
    st.Page("app_pages/4_Demographic_View.py", title="Demographic view", icon=":material/group:"),
    st.Page("app_pages/5_Clusters.py", title="Clusters", icon=":material/hub:"),
    st.Page("app_pages/6_Model_Performance.py", title="Model performance", icon=":material/insights:"),
    st.Page("app_pages/7_Reports.py", title="Reports", icon=":material/description:"),
]

pg = st.navigation(pages)
pg.run()
