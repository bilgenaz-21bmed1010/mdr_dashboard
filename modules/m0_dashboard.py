import streamlit as st
import pandas as pd
from datetime import date


def show():
    st.title("MDR Compliance Dashboard")
    st.markdown("**EU MDR 2017/745** - Post-Market Surveillance & Vigilance Overview")
    st.markdown("---")

    today = date.today()

    try:
        df_dev = pd.read_csv("data/devices.csv")
        df_inc = pd.read_csv("data/incidents.csv", parse_dates=["olay_tarihi", "deadline"])
        df_fsc = pd.read_csv("data/fsca.csv")
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}")
        return

    total_devices  = len(df_dev)
    active_devices = len(df_dev[df_dev["durum"] == "Active"])
    open_incidents = len(df_inc[df_inc["durum"] == "Open"])
    overdue        = len(df_inc[
        (df_inc["durum"].isin(["Open", "Overdue"])) &
        (df_inc["deadline"].dt.date < today)
    ])
    active_fsca    = len(df_fsc[df_fsc["durum"] == "Active"])
    closed_fsca    = len(df_fsc[df_fsc["durum"] == "Closed"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Registered Devices", total_devices, f"{active_devices} active")
        st.caption("MDR Art. 27 - UDI Registration")
    with col2:
        st.metric("Open Incidents", open_incidents,
                  f"{overdue} overdue" if overdue > 0 else "All on track",
                  delta_color="inverse")
        st.caption("MDR Art. 87 - Serious Incident Reporting")
    with col3:
        st.metric("Overdue Reports", overdue,
                  "Past MDR deadline" if overdue > 0 else "None overdue",
                  delta_color="inverse" if overdue > 0 else "normal")
        st.caption("MDR Art. 87 - 10 / 15 / 30 day limits")
    with col4:
        st.metric("Active FSCAs", active_fsca, f"{closed_fsca} closed")
        st.caption("MDR Art. 83-87 - Field Safety Corrective Actions")

    st.markdown("---")

    if overdue > 0:
        st.error(f"{overdue} incident(s) have passed their MDR reporting deadline. Go to Incident Reporting (M2) to review.")

    st.subheader("Device Registry - Category Overview")
    col_a, col_b = st.columns(2)
    with col_a:
        cat_counts = df_dev.groupby("kategori")["cihaz_id"].count().reset_index()
        cat_counts.columns = ["Category", "Count"]
        st.dataframe(cat_counts, use_container_width=True, hide_index=True)
    with col_b:
        risk_counts = df_dev.groupby("risk_sinifi")["cihaz_id"].count().reset_index()
        risk_counts.columns = ["Risk Class", "Count"]
        st.dataframe(risk_counts, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Recent Incidents")
    recent = df_inc.sort_values("olay_tarihi", ascending=False).head(5)[[
        "olay_id", "cihaz_adi", "ciddiyet", "olay_tarihi", "deadline", "durum"
    ]]
    recent.columns = ["ID", "Device", "Severity", "Event Date", "Deadline", "Status"]
    st.dataframe(recent, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption(f"Last updated: {date.today().strftime('%d %B %Y')} | EU MDR 2017/745 | MDR Compliance Dashboard v0.1")