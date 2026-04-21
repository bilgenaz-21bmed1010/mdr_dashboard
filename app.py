import streamlit as st
from modules import m0_dashboard
from modules import m1_udi
from modules import m2_incident

st.set_page_config(
    page_title="MDR Compliance Dashboard",
    layout="wide"
)

st.markdown("""
<style>
.main .block-container {
    padding-top: 1.5rem;
    max-width: 1200px;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
    border-right: 1px solid #2563EB44;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}
[data-testid="stSidebar"] .stRadio label {
    color: #94A3B8 !important;
    font-size: 0.88rem !important;
    padding: 6px 8px;
    border-radius: 6px;
}
[data-testid="stSidebar"] .stRadio label:hover {
    color: #F1F5F9 !important;
    background: #2563EB22;
}
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #2563EB33;
    border-top: 3px solid #2563EB;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 4px 24px rgba(37,99,235,0.12);
}
[data-testid="stMetricLabel"] {
    color: #64748B !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="stMetricValue"] {
    color: #F1F5F9 !important;
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    line-height: 1.1;
}
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #2563EB22;
}
h1 {
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
    font-size: 1.9rem !important;
    color: #F1F5F9 !important;
}
h2, h3 {
    color: #CBD5E1 !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
}
hr {
    border-color: #2563EB22 !important;
    margin: 0.5rem 0 !important;
}
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left: 4px solid !important;
}
</style>
""", unsafe_allow_html=True)

pages = {
    "M0 - Home Dashboard": "m0_dashboard",
    "M1 - UDI Device Tracking": "m1_udi",
    "M2 - Incident Reporting": "m2_incident",
    "M3 - FSCA Panel": "m3_fsca",
    "M4 - Gap Analysis": "m4_gap",
    "M5 - PSUR Checklist": "m5_psur",
    "M6 - Trend Analysis": "m6_trend",
    "M7 - PMS Method Matrix": "m7_pms",
}

st.sidebar.title("MDR Compliance Dashboard")
st.sidebar.markdown("---")
selection = st.sidebar.radio("Select Module", list(pages.keys()))
st.sidebar.markdown("---")
st.sidebar.caption("EU MDR 2017/745 | WP4 Prototype")

if selection == "M0 - Home Dashboard":
    m0_dashboard.render()
elif selection == "M1 - UDI Device Tracking":
    m1_udi.render()
elif selection == "M2 - Incident Reporting":
    m2_incident.render()
else:
    st.title(selection)
    st.info("This module is under construction.")