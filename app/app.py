"""TenderLens app. Run with:  streamlit run app.py"""
import os

import streamlit as st

st.set_page_config(page_title="TenderLens", page_icon="🔍", layout="wide", initial_sidebar_state="expanded")

import tl_ui as U

# remember settings for the whole visit
if "plain" not in st.session_state:
    st.session_state["plain"] = True
if "checked" not in st.session_state:
    st.session_state["checked"] = {}
if "notes" not in st.session_state:
    st.session_state["notes"] = {}

pages = [
    st.Page("views/1_overview.py", title="Overview", icon=":material/space_dashboard:", default=True),
    st.Page("views/2_risk_list.py", title="Tender risk list", icon=":material/format_list_numbered:"),
    st.Page("views/3_tender_detail.py", title="Tender detail", icon=":material/search:"),
    st.Page("views/4_department.py", title="Department report card", icon=":material/apartment:"),
    st.Page("views/5_model_health.py", title="Model health", icon=":material/monitor_heart:"),
    st.Page("views/6_score_new.py", title="Score new tenders", icon=":material/add_circle:"),
    st.Page("views/7_beat_the_model.py", title="Beat the model", icon=":material/sports_esports:"),
    st.Page("views/8_about.py", title="About & behind the model", icon=":material/info:"),
]
nav = st.navigation(pages)
HERE = os.path.dirname(os.path.abspath(__file__))
st.logo(os.path.join(HERE, "assets", "logo.svg"), icon_image=os.path.join(HERE, "assets", "icon.svg"), size="large")
U.setup()
U.sidebar()
nav.run()
