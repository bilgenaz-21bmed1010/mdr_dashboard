import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import date

DEVICES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "devices.csv")

# ── PSUR frequency by risk class (MDR Art. 86) ────────────────────────────────
PSUR_FREQUENCY = {
    "III":  ("Annual",              "MDR Art. 86(1) — Class III devices require annual PSUR submission."),
    "IIb":  ("Annual",              "MDR Art. 86(1) — Class IIb devices require annual PSUR submission."),
    "IIa":  ("Every 2 years",       "MDR Art. 86(2) — Class IIa devices require PSUR every two years."),
    "I":    ("On request / as needed", "MDR Art. 86(3) — Class I devices: PSUR kept available, submitted on request."),
}

# ── 7 PSUR checklist items (MDCG 2022-21) ────────────────────────────────────
CHECKLIST = [
    {
        "id":      "sales_volume",
        "label":   "Sales Volume & Market Access Data",
        "article": "MDR Art. 86 · MDCG 2022-21 §4.1",
        "desc":    "Number of units sold/distributed, countries of distribution, and estimated market reach during the reporting period.",
        "expert_note": None,
    },
    {
        "id":      "patient_demographics",
        "label":   "Patient Population & Exposure Estimation",
        "article": "MDR Art. 86 · MDCG 2022-21 §4.2",
        "desc":    "Estimated number of patients exposed, demographic breakdown (age, sex, indication), and intended-use population alignment.",
        "expert_note": (
            "WP2 Expert Note: A device labelled for ages 18-50 was found in practice to be used "
            "exclusively by 18-year-old patients. Verify that the actual patient population matches "
            "the intended use population defined in the IFU."
        ),
    },
    {
        "id":      "incident_summary",
        "label":   "Serious Incident & Field Safety Summary",
        "article": "MDR Art. 86 · Art. 87 · MDCG 2022-21 §4.3",
        "desc":    "Summary of all serious incidents reported under Art. 87, FSCAs executed, and FSNs issued during the reporting period. Links to M2 incident log and M3 FSCA panel.",
        "expert_note": None,
    },
    {
        "id":      "pmcf_findings",
        "label":   "PMCF Study Findings",
        "article": "MDR Art. 86 · Annex XIV Part B · MDCG 2022-21 §4.4",
        "desc":    "Results of Post-Market Clinical Follow-up activities: registry data, literature surveillance, clinical studies. Must be sufficient to support CER benefit-risk revision.",
        "expert_note": None,
    },
    {
        "id":      "literature_update",
        "label":   "Literature Surveillance Update",
        "article": "MDR Art. 86 · MDCG 2022-21 §4.5",
        "desc":    "Systematic literature review update covering device performance, safety signals, and equivalent device data. Must be current within the reporting period.",
        "expert_note": None,
    },
    {
        "id":      "risk_benefit",
        "label":   "Risk-Benefit Assessment Update",
        "article": "MDR Art. 86 · ISO 14971:2019 · MDCG 2022-21 §4.6",
        "desc":    "Updated risk-benefit analysis integrating all PMS/PMCF data. Must conclude that benefits continue to outweigh risks. Feeds into CER update.",
        "expert_note": None,
    },
    {
        "id":      "corrective_actions",
        "label":   "Corrective Actions from Previous PSUR",
        "article": "MDR Art. 86 · MDCG 2022-21 §4.7",
        "desc":    "Status of all corrective and preventive actions (CAPAs) identified in the previous PSUR cycle. Each CAPA must be closed or have a documented rationale for continuation.",
        "expert_note": None,
    },
]

STATUS_OPTIONS = ["Not Started", "In Progress", "Complete", "Not Applicable"]

STATUS_COLORS = {
    "Complete":       "#2ecc71",
    "In Progress":    "#f1c40f",
    "Not Started":    "#e74c3c",
    "Not Applicable": "#64748b",
}


@st.cache_data
def load_devices():
    df = pd.read_csv(DEVICES_PATH)
    df = df[df["durum"] == "Active"].copy()
    df["display"] = df["isim"] + " — " + df["risk_sinifi"] + " · " + df["kategori"]
    return df


def show():
    st.markdown(
        '<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.12em;'
        'color:#2563EB;text-transform:uppercase;margin-bottom:0.25rem;">Module M5</div>',
        unsafe_allow_html=True,
    )
    st.title("PSUR Checklist")
    st.caption("EU MDR Art. 86 · MDCG 2022-21 · Periodic Safety Update Report Readiness Assessment")

    try:
        devices = load_devices()
    except FileNotFoundError:
        st.error("devices.csv not found. Place it in the data/ folder.")
        return

    # ── device selection ──────────────────────────────────────────────────────
    st.subheader("Device Selection")

    col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
    with col_f1:
        class_filter = st.selectbox(
            "Device Classification",
            options=["All", "Class I", "Class IIa", "Class IIb", "Class III"],
            index=0,
        )
    
    # filter devices by class
    class_map = {"All": None, "Class I": "I", "Class IIa": "IIa", "Class IIb": "IIb", "Class III": "III"}
    filtered_devices = devices.copy()
    if class_map[class_filter]:
        filtered_devices = filtered_devices[filtered_devices["risk_sinifi"] == class_map[class_filter]]

    device_options = ["All Devices"] + filtered_devices["isim"].tolist()

    with col_f2:
        selected_device = st.selectbox(
            "Select Device",
            options=device_options,
            index=0,
            help="Only Active devices listed. Source: M1 Device Registry.",
        )
    with col_f3:
        report_period = st.selectbox(
            "Reporting Period",
            options=["2024", "2023", "2022", "2021"],
            index=0,
        )

    # ── if All Devices selected, show summary table ───────────────────────────
    if selected_device == "All Devices":
        st.markdown("---")
        st.subheader("Active Device Registry Overview")
        st.caption(f"Showing {len(filtered_devices)} active devices · Select a specific device to run PSUR checklist.")

        summary = filtered_devices[["cihaz_id", "isim", "risk_sinifi", "kategori", "kayit_tarihi"]].copy()
        summary.columns = ["Device ID", "Device Name", "Risk Class", "Category", "Registration Date"]

        freq_map = {"I": "On request", "IIa": "Every 2 years", "IIb": "Annual", "III": "Annual"}
        summary["PSUR Frequency"] = summary["Risk Class"].map(freq_map)
        st.dataframe(summary, use_container_width=True, hide_index=True)

        # KPIs for filtered set
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Devices", len(filtered_devices))
        k2.metric("Class III", len(filtered_devices[filtered_devices["risk_sinifi"] == "III"]))
        k3.metric("Class IIb", len(filtered_devices[filtered_devices["risk_sinifi"] == "IIb"]))
        k4.metric("Class IIa / I", len(filtered_devices[filtered_devices["risk_sinifi"].isin(["IIa", "I"])]))
        return

    # ── specific device selected ──────────────────────────────────────────────
    selected_row = filtered_devices[filtered_devices["isim"] == selected_device].iloc[0]
    dev_name     = selected_row["isim"]
    dev_class    = selected_row["risk_sinifi"]
    dev_category = selected_row["kategori"]
    dev_udi      = selected_row["udi_kodu"]
    dev_id       = selected_row["cihaz_id"]

    # ── device info card ──────────────────────────────────────────────────────
    freq_label, freq_article = PSUR_FREQUENCY.get(dev_class, ("—", "—"))
    freq_short = {"Annual": "Annual", "Every 2 years": "2-Year", "On request / as needed": "On Request"}.get(freq_label, freq_label)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Device ID",      dev_id)
    c2.metric("Risk Class",     f"Class {dev_class}", help=freq_article)
    c3.metric("PSUR Frequency", freq_short,           help=freq_article)
    c4.metric("Category",       dev_category[:20] + ("..." if len(dev_category) > 20 else ""))

    st.caption(f"UDI: `{dev_udi}`")
    st.markdown("---")

    # ── checklist ─────────────────────────────────────────────────────────────
    st.subheader("PSUR Data Element Checklist")
    st.caption(
        f"MDCG 2022-21 — 7 mandatory data elements for PSUR readiness assessment. "
        f"Device: **{dev_name}** · Reporting Period: **{report_period}**"
    )

    statuses = {}

    for item in CHECKLIST:
        with st.container():
            col_label, col_status = st.columns([3, 1])

            with col_label:
                st.markdown(f"**{item['label']}**")
                st.markdown(
                    f'<span style="font-size:0.78rem;color:#2563EB;">{item["article"]}</span>',
                    unsafe_allow_html=True,
                )
                st.caption(item["desc"])

                if item["expert_note"]:
                    st.markdown(
                        f'<div style="font-size:0.75rem;color:#94A3B8;margin-top:4px;'
                        f'border-left:2px solid #2563EB;padding-left:8px;">'
                        f'{item["expert_note"]}</div>',
                        unsafe_allow_html=True,
                    )

            with col_status:
                status = st.selectbox(
                    "Status",
                    options=STATUS_OPTIONS,
                    key=f"status_{dev_id}_{item['id']}_{report_period}",
                    label_visibility="collapsed",
                )
                statuses[item["id"]] = status

                color = STATUS_COLORS.get(status, "#64748b")
                st.markdown(
                    f'<div style="background:{color};color:white;text-align:center;'
                    f'padding:4px 8px;border-radius:6px;font-size:0.78rem;font-weight:700;">'
                    f'{status}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<hr style="border-color:#1e293b;margin:0.4rem 0;">', unsafe_allow_html=True)

    # ── results ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("PSUR Readiness Assessment")

    complete      = sum(1 for s in statuses.values() if s == "Complete")
    in_progress   = sum(1 for s in statuses.values() if s == "In Progress")
    not_started   = sum(1 for s in statuses.values() if s == "Not Started")
    not_applicable = sum(1 for s in statuses.values() if s == "Not Applicable")
    effective_total = len(CHECKLIST) - not_applicable
    score = round((complete / effective_total * 100) if effective_total > 0 else 0, 1)

    rc1, rc2, rc3, rc4 = st.columns(4)
    rc1.metric("Complete",       complete)
    rc2.metric("In Progress",    in_progress)
    rc3.metric("Not Started",    not_started)
    rc4.metric("Readiness Score", f"{score}%", help="Complete / (Total - Not Applicable)")

    # ── verdict ───────────────────────────────────────────────────────────────
    if not_started == 0 and in_progress == 0:
        st.success(
            f"**PSUR READY** — All {effective_total} applicable data elements are complete. "
            f"This device ({dev_name}, {dev_class}) is ready for PSUR submission for the {report_period} reporting period. "
            f"Submission frequency: {freq_label} ({freq_article})"
        )
    elif not_started > 0:
        missing = [item["label"] for item in CHECKLIST if statuses.get(item["id"]) == "Not Started"]
        st.error(
            f"**NOT READY** — {not_started} data element(s) not started. "
            f"Missing: {', '.join(missing)}. "
            f"Readiness score: {score}%."
        )
    else:
        pending = [item["label"] for item in CHECKLIST if statuses.get(item["id"]) == "In Progress"]
        st.warning(
            f"**IN PROGRESS** — {in_progress} data element(s) still in progress. "
            f"Pending: {', '.join(pending)}. "
            f"Readiness score: {score}%."
        )

    st.markdown("---")
    st.info(
        f"MDR Art. 86 requires manufacturers to prepare a PSUR for each device. "
        f"Class III and IIb: annual submission to Notified Body via EUDAMED. "
        f"Class IIa: every two years. Class I: available on request. "
        f"Reference: MDCG 2022-21 Guidance on PSUR According to MDR 2017/745."
    )