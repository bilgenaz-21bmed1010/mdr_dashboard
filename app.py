import streamlit as st
from modules import m0_dashboard
from modules import m1_udi

st.set_page_config(
    page_title="MDR Compliance Dashboard",
    page_icon="🏥",
    layout="wide"
)

pages = {
    "M0 – Home Dashboard": "m0_dashboard",
    "M1 – UDI Device Tracking": "m1_udi",
    "M2 – Incident Reporting": "m2_incident",
    "M3 – FSCA Panel": "m3_fsca",
    "M4 – Gap Analysis": "m4_gap",
    "M5 – PSUR Checklist": "m5_psur",
    "M6 – Trend Analysis": "m6_trend",
    "M7 – PMS Method Matrix": "m7_pms",
}

st.sidebar.title("MDR Compliance Dashboard")
st.sidebar.markdown("---")
selection = st.sidebar.radio("Select Module", list(pages.keys()))
st.sidebar.markdown("---")
st.sidebar.caption("EU MDR 2017/745 | WP4 Prototype")

if selection == "M0 – Home Dashboard":
    m0_dashboard.show()
elif selection == "M1 – UDI Device Tracking":
    m1_udi.show()
else:
    st.title(selection)
    st.info("🚧 This module is under construction.")