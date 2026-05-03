import streamlit as st
import pandas as pd
import os

DEVICES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "devices.csv")

# ── PMS method matrix (MDR Art. 83-86, MDCG 2025-10) ─────────────────────────

PMS_METHODS = [
    {
        "method":      "Complaint Handling & User Feedback",
        "article":     "MDR Art. 83 · ISO 13485 §8.2.2",
        "description": "Collection and analysis of complaints, user error reports, and adverse event near-misses from clinical staff and patients.",
        "class_I":     "Required",
        "class_IIa":   "Required",
        "class_IIb":   "Required",
        "class_III":   "Required",
    },
    {
        "method":      "Serious Incident Reporting (MIR)",
        "article":     "MDR Art. 87 · MDCG 2023-3 Rev.2",
        "description": "Mandatory reporting of serious incidents and near-serious incidents to Competent Authority within statutory deadlines (2/10/15/30 days).",
        "class_I":     "Required",
        "class_IIa":   "Required",
        "class_IIb":   "Required",
        "class_III":   "Required",
    },
    {
        "method":      "Literature Surveillance",
        "article":     "MDR Art. 83 · Annex XIV Part A",
        "description": "Systematic monitoring of scientific literature for clinical data on the device and equivalent devices, safety signals, and state-of-the-art updates.",
        "class_I":     "Required",
        "class_IIa":   "Required",
        "class_IIb":   "Required",
        "class_III":   "Required",
    },
    {
        "method":      "EUDAMED / Registry Monitoring",
        "article":     "MDR Art. 92 · Art. 83",
        "description": "Monitoring of EUDAMED vigilance data, national device registries, and Competent Authority safety communications for signals relevant to the device.",
        "class_I":     "Recommended",
        "class_IIa":   "Required",
        "class_IIb":   "Required",
        "class_III":   "Required",
    },
    {
        "method":      "FSCA Tracking & FSN Distribution",
        "article":     "MDR Art. 90-91 · MDCG 2022-21",
        "description": "Tracking of Field Safety Corrective Actions initiated by the manufacturer or competitors, and distribution of Field Safety Notices to affected hospitals.",
        "class_I":     "Recommended",
        "class_IIa":   "Required",
        "class_IIb":   "Required",
        "class_III":   "Required",
    },
    {
        "method":      "Post-Market Clinical Follow-Up (PMCF)",
        "article":     "MDR Annex XIV Part B · MDCG 2020-7",
        "description": "Structured clinical data collection from real-world use: registries, clinical studies, surveys, or observational studies. Must address residual risks and long-term safety.",
        "class_I":     "Not Required",
        "class_IIa":   "Recommended",
        "class_IIb":   "Required",
        "class_III":   "Required",
    },
    {
        "method":      "Periodic Safety Update Report (PSUR)",
        "article":     "MDR Art. 86 · MDCG 2022-21",
        "description": "Periodic synthesis of all PMS data into a structured safety update report. Submitted to Notified Body for Class IIb/III; kept available for Class I/IIa.",
        "class_I":     "On Request",
        "class_IIa":   "Every 2 Years",
        "class_IIb":   "Annual",
        "class_III":   "Annual",
    },
    {
        "method":      "Clinical Evaluation Report (CER) Update",
        "article":     "MDR Art. 61 · Annex XIV Part A · MDCG 2020-13",
        "description": "Update of the Clinical Evaluation Report integrating new PMS/PMCF findings. Must confirm that benefit-risk balance remains favourable.",
        "class_I":     "Recommended",
        "class_IIa":   "Required",
        "class_IIb":   "Required",
        "class_III":   "Required",
    },
    {
        "method":      "Risk Management Update (ISO 14971)",
        "article":     "MDR Art. 10 · ISO 14971:2019 §10",
        "description": "Review and update of the risk management file based on PMS data, new hazard identification, and residual risk re-evaluation.",
        "class_I":     "Required",
        "class_IIa":   "Required",
        "class_IIb":   "Required",
        "class_III":   "Required",
    },
    {
        "method":      "UDI-Based Traceability & Recall Readiness",
        "article":     "MDR Art. 27 · Art. 83",
        "description": "Maintenance of UDI linkage in PMS data to enable lot-specific signal detection, targeted FSCA, and rapid recall execution if required.",
        "class_I":     "Recommended",
        "class_IIa":   "Required",
        "class_IIb":   "Required",
        "class_III":   "Required",
    },
]

STATUS_COLORS = {
    "Required":      ("background-color:#14532d;color:#86efac;font-weight:700;text-align:center;", "Required"),
    "Recommended":   ("background-color:#1e3a5f;color:#93c5fd;font-weight:600;text-align:center;", "Recommended"),
    "Every 2 Years": ("background-color:#3b1f6b;color:#c4b5fd;font-weight:600;text-align:center;", "Every 2 Years"),
    "Annual":        ("background-color:#7f1d1d;color:#fca5a5;font-weight:700;text-align:center;", "Annual"),
    "On Request":    ("background-color:#374151;color:#9ca3af;text-align:center;",                 "On Request"),
    "Not Required":  ("background-color:#1e293b;color:#475569;text-align:center;",                 "Not Required"),
}

CLASS_COLS = {
    "Class I":   "class_I",
    "Class IIa": "class_IIa",
    "Class IIb": "class_IIb",
    "Class III": "class_III",
}

CLASS_INFO = {
    "Class I":   ("Low risk devices. PMS obligations focus on complaint handling, literature surveillance, and risk management. PSUR submitted on request only.", "MDR Art. 83, 86(3)"),
    "Class IIa": ("Medium risk devices. Full PMS system required. CER and PSUR updates every 2 years. PMCF recommended where residual risks exist.", "MDR Art. 83-84, 86(2)"),
    "Class IIb": ("Medium-high risk devices. Annual PSUR submission. PMCF required. UDI-based traceability mandatory for lot-level signal detection.", "MDR Art. 83-86, Annex XIV"),
    "Class III": ("Highest risk devices (implantables, life-sustaining). Annual PSUR. PMCF mandatory. Full CER update. Notified Body oversight throughout PMS lifecycle.", "MDR Art. 83-86, Annex XIV"),
}


@st.cache_data
def load_devices():
    df = pd.read_csv(DEVICES_PATH)
    return df[df["durum"] == "Active"].copy()


def color_cell(val):
    return STATUS_COLORS.get(val, ("", val))[0]


def show():
    st.markdown(
        '<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.12em;'
        'color:#2563EB;text-transform:uppercase;margin-bottom:0.25rem;">Module M7</div>',
        unsafe_allow_html=True,
    )
    st.title("PMS Method Matrix")
    st.caption("EU MDR Art. 83–86 · MDCG 2025-10 · Recommended PMS Data Collection Methods by Device Classification")

    # ── device or class selection ──────────────────────────────────────────────
    st.subheader("Device Selection")

    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        selection_mode = st.radio(
            "Select by",
            options=["Device Classification", "Specific Device"],
            horizontal=True,
        )
    
    selected_classes = []

    if selection_mode == "Device Classification":
        with col_s2:
            class_sel = st.selectbox(
                "Device Classification",
                options=["Class I", "Class IIa", "Class IIb", "Class III"],
                index=2,
            )
        selected_classes = [class_sel]

    else:
        try:
            devices = load_devices()
            with col_s2:
                dev_sel = st.selectbox(
                    "Select Device",
                    options=devices["isim"].tolist(),
                    index=0,
                )
            dev_row   = devices[devices["isim"] == dev_sel].iloc[0]
            dev_class = dev_row["risk_sinifi"]
            selected_classes = [f"Class {dev_class}"]
            st.caption(f"Device: **{dev_sel}** · Classification: **Class {dev_class}** · Category: {dev_row['kategori']} · UDI: `{dev_row['udi_kodu']}`")
        except FileNotFoundError:
            st.error("devices.csv not found.")
            return

    if not selected_classes:
        st.warning("Please select at least one device classification.")
        return

    st.markdown("---")

    # ── class info cards ──────────────────────────────────────────────────────
    if len(selected_classes) == 1:
        cls = selected_classes[0]
        desc, article = CLASS_INFO[cls]
        st.markdown(
            f'<div style="background:#1e293b;border:1px solid #2563EB33;border-left:4px solid #2563EB;'
            f'border-radius:8px;padding:14px 18px;margin-bottom:1rem;">'
            f'<div style="color:#2563EB;font-size:0.75rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.08em;margin-bottom:6px;">{cls} · {article}</div>'
            f'<div style="color:#CBD5E1;font-size:0.88rem;">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        cols = st.columns(len(selected_classes))
        for i, cls in enumerate(selected_classes):
            desc, article = CLASS_INFO[cls]
            cols[i].markdown(
                f'<div style="background:#1e293b;border:1px solid #2563EB33;border-left:4px solid #2563EB;'
                f'border-radius:8px;padding:12px 14px;height:100%;">'
                f'<div style="color:#2563EB;font-size:0.72rem;font-weight:700;text-transform:uppercase;'
                f'margin-bottom:6px;">{cls}</div>'
                f'<div style="color:#CBD5E1;font-size:0.82rem;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("&nbsp;")
    st.markdown("---")

    # ── method matrix table ───────────────────────────────────────────────────
    st.subheader("Recommended PMS Data Collection Methods")
    st.caption(f"MDR/MDCG-aligned obligations for {', '.join(selected_classes)}. Based on MDCG 2025-10 and MDR 2017/745 Articles 83–86.")

    for m in PMS_METHODS:
        col_key = CLASS_COLS[selected_classes[0]]
        status = m[col_key]
        style, _ = STATUS_COLORS.get(status, ("", status))

        # extract background color for badge
        bg = "#1e293b"
        fg = "#94A3B8"
        for s, (st_style, _) in STATUS_COLORS.items():
            if s == status:
                parts = {p.split(":")[0].strip(): p.split(":")[1].strip() for p in st_style.split(";") if ":" in p}
                bg = parts.get("background-color", "#1e293b")
                fg = parts.get("color", "#F1F5F9")
                break

        label = (
            f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:4px;'
            f'font-size:0.78rem;font-weight:700;margin-right:10px;">{status}</span>'
            f'<span style="font-weight:600;">{m["method"]}</span>'
            f'<span style="color:#2563EB;font-size:0.78rem;margin-left:10px;">{m["article"]}</span>'
        )

        with st.expander(m["method"] + f"  —  {status}", expanded=False):
            st.markdown(
                f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:4px;'
                f'font-size:0.78rem;font-weight:700;">{status}</span>'
                f'&nbsp;&nbsp;<span style="color:#2563EB;font-size:0.82rem;">{m["article"]}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f"{m['description']}")

    st.markdown("&nbsp;")

    # ── legend ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="display:flex;gap:16px;flex-wrap:wrap;">'
        + "".join([
            f'<span style="{style.split(";font-weight")[0]};padding:2px 10px;border-radius:4px;font-size:0.75rem;">{label}</span>'
            for label, (style, _) in [
                ("Required",      STATUS_COLORS["Required"]),
                ("Recommended",   STATUS_COLORS["Recommended"]),
                ("Annual",        STATUS_COLORS["Annual"]),
                ("Every 2 Years", STATUS_COLORS["Every 2 Years"]),
                ("On Request",    STATUS_COLORS["On Request"]),
                ("Not Required",  STATUS_COLORS["Not Required"]),
            ]
        ])
        + '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.info(
        "PMS obligations are defined in MDR 2017/745 Articles 83–86 and Annex XIV. "
        "Detailed guidance is provided in MDCG 2025-10 (PMS guidance), MDCG 2022-21 (PSUR), "
        "and MDCG 2020-7 (PMCF). Risk management integration follows ISO 14971:2019."
    )