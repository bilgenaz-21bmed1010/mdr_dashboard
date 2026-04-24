import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF
import os
import io
import unicodedata

# ── paths ─────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
FSCA_CSV = os.path.join(DATA_DIR, "fsca.csv")
DEV_CSV  = os.path.join(DATA_DIR, "devices.csv")

# ── constants ─────────────────────────────────────────────────────────────────
STAGES = ["Signal Detection", "Risk Assessment", "Planning", "Implementation", "Closure"]
STAGE_ARTICLES = {
    "Signal Detection": "Art. 83 - PMS System",
    "Risk Assessment":  "Art. 84 - PMS Plan",
    "Planning":         "Art. 87 - Vigilance Reporting",
    "Implementation":   "Art. 85 / 89 - Corrective Actions",
    "Closure":          "Art. 86 - PSUR Review",
}
STAGE_COLORS = {
    "Signal Detection": "#e67e22",
    "Risk Assessment":  "#f39c12",
    "Planning":         "#3498db",
    "Implementation":   "#9b59b6",
    "Closure":          "#2ecc71",
}
STATUS_COLORS = {
    "Active":  "#4ade80",
    "Overdue": "#f87171",
    "Closed":  "#94a3b8",
}
CLOSURE_EVIDENCE = [
    ("corrective_action", "Corrective Action Report",               "Art. 85 / 89 - Corrective Actions",            "Upload the Corrective Action Report confirming implementation for all affected devices."),
    ("fsn_distributed",   "FSN Distribution Record",                "Art. 87 - Vigilance Reporting",                 "Upload the FSN distribution list with signed acknowledgements from affected hospitals/users."),
    ("effectiveness",     "Effectiveness Check Report",             "Art. 83 - PMS System",                          "Upload the effectiveness verification report confirming the corrective action resolved the risk."),
    ("nca_notified",      "NCA / TITCK Notification Confirmation",  "Art. 87 - Competent Authority Notification",    "Upload the official submission confirmation from TITCK or the relevant national competent authority."),
    ("eudamed_updated",   "EUDAMED Update Evidence",                "Art. 27 - EUDAMED",                             "Upload a screenshot or export from EUDAMED confirming the manufacturer updated the FSCA record."),
    ("psur_updated",      "PSUR Update Confirmation",               "Art. 86 - PSUR",                                "Upload the relevant PSUR section or update report confirming FSCA findings are incorporated."),
]

# ── helpers ───────────────────────────────────────────────────────────────────

def load_fsca():
    df = pd.read_csv(FSCA_CSV)
    df["baslangic"]    = pd.to_datetime(df["baslangic"],    errors="coerce")
    df["bitis"]        = pd.to_datetime(df["bitis"],        errors="coerce")
    df["fsn_deadline"] = pd.to_datetime(df["fsn_deadline"], errors="coerce")
    return df

def load_devices():
    return pd.read_csv(DEV_CSV)

def save_fsca(df: pd.DataFrame):
    out = df.copy()
    out["baslangic"]    = out["baslangic"].dt.strftime("%Y-%m-%d")
    out["bitis"]        = out["bitis"].dt.strftime("%Y-%m-%d")
    if "fsn_deadline" in out.columns:
        out["fsn_deadline"] = out["fsn_deadline"].dt.strftime("%Y-%m-%d")
    out.to_csv(FSCA_CSV, index=False)

def compute_status(row) -> str:
    if row["mevcut_asama"] == "Closure":
        return "Closed"
    if pd.notna(row["bitis"]) and row["bitis"] < pd.Timestamp(date.today()):
        return "Overdue"
    return "Active"

def stage_index(stage: str) -> int:
    try:
        return STAGES.index(stage)
    except ValueError:
        return 0

def clean(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    return unicodedata.normalize("NFKD", text).encode("latin-1", "replace").decode("latin-1")

def stage_progress_html(current_stage: str) -> str:
    idx = stage_index(current_stage)
    dots = []
    for i, s in enumerate(STAGES):
        if i < idx:
            color, symbol = "#4ade80", "+"
        elif i == idx:
            color, symbol = STAGE_COLORS.get(s, "#f39c12"), "●"
        else:
            color, symbol = "#334155", "○"
        dots.append(
            f'<div style="text-align:center;flex:1;">'
            f'<div style="font-size:18px;color:{color};">{symbol}</div>'
            f'<div style="font-size:10px;color:#64748b;margin-top:4px;">{s}</div>'
            f'</div>'
        )
    sep = '<div style="flex:none;width:30px;height:1px;background:#1e293b;margin-top:9px;"></div>'
    items = []
    for i, d in enumerate(dots):
        items.append(d)
        if i < len(dots) - 1:
            items.append(sep)
    return (
        '<div style="display:flex;align-items:flex-start;padding:10px 0;">'
        + "".join(items) + '</div>'
    )

def generate_pdf(row: pd.Series, dev_name: str, udi_code: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    def s(text):
        if not isinstance(text, str):
            text = str(text)
        return text.encode("latin-1", "replace").decode("latin-1")

    # ── Header ────────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, "FSCA Status Report", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "EU MDR 2017/745  |  Articles 83-87  |  Hospital-Side FSCA Tracking", ln=True)
    pdf.ln(3)
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.2)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    # ── Two column layout ─────────────────────────────────────────────────────
    left_x  = 20
    right_x = 115
    col_w_l = 90   # left column width
    col_w_r = 75   # right column width
    label_w = 42   # label width inside each column
    y_start = pdf.get_y()

    def lfield(label, value, x, cw):
        pdf.set_x(x)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(label_w, 5, s(label), ln=False)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(cw - label_w, 5, s(str(value))[:40], ln=True)

    def lsection(title, x, cw):
        pdf.set_x(x)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(56, 130, 200)
        pdf.cell(cw, 5, s(title.upper()), ln=True)
        pdf.set_draw_color(220, 220, 220)
        pdf.set_line_width(0.2)
        pdf.line(x, pdf.get_y(), x + cw, pdf.get_y())
        pdf.ln(3)

    # LEFT COLUMN
    pdf.set_xy(left_x, y_start)
    lsection("FSCA Information", left_x, col_w_l)
    lfield("FSCA ID:",       row.get("fsca_id", "—"),           left_x, col_w_l)
    lfield("Status:",        row.get("durum", "—"),              left_x, col_w_l)
    lfield("Stage:",         row.get("mevcut_asama", "—"),       left_x, col_w_l)
    lfield("MDR Ref.:",      STAGE_ARTICLES.get(str(row.get("mevcut_asama", "")), "—"), left_x, col_w_l)
    lfield("Category:",      row.get("kategori", "—"),           left_x, col_w_l)
    pdf.ln(4)

    pdf.set_x(left_x)
    lsection("Device Information", left_x, col_w_l)
    lfield("Device:",        dev_name,                           left_x, col_w_l)
    lfield("Device ID:",     row.get("cihaz_id", "—"),           left_x, col_w_l)
    lfield("UDI Code:",      udi_code,                           left_x, col_w_l)
    pdf.ln(4)

    pdf.set_x(left_x)
    lsection("Hospital Tracking", left_x, col_w_l)
    lfield("Coordinator:",   row.get("sorumlu", "—"),            left_x, col_w_l)
    lfield("Progress:",      f"Stage {stage_index(str(row.get('mevcut_asama',''))) + 1} of {len(STAGES)}", left_x, col_w_l)

    # RIGHT COLUMN
    pdf.set_xy(right_x, y_start)
    lsection("Timeline", right_x, col_w_r)
    lfield("Initiation:",    row["baslangic"].strftime("%d/%m/%Y") if pd.notna(row.get("baslangic")) else "—",       right_x, col_w_r)
    lfield("FSN Deadline:",  row["fsn_deadline"].strftime("%d/%m/%Y") if pd.notna(row.get("fsn_deadline")) else "—", right_x, col_w_r)
    lfield("Target Closure:",row["bitis"].strftime("%d/%m/%Y") if pd.notna(row.get("bitis")) else "—",               right_x, col_w_r)
    lfield("Report Date:",   date.today().strftime("%d/%m/%Y"),  right_x, col_w_r)
    pdf.ln(4)

    pdf.set_x(right_x)
    lsection("Topic", right_x, col_w_r)
    pdf.set_xy(right_x, pdf.get_y())
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(col_w_r, 5, s(str(row.get("konu", "—"))))

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.set_y(265)
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.2)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 5,
        f"MDR Compliance Dashboard  |  WP4 Prototype  |  Generated: {date.today().strftime('%d/%m/%Y')}",
        align="C"
    )

    return pdf.output()

# ── main ──────────────────────────────────────────────────────────────────────

def show():
    st.markdown(
        '<p style="color:#38bdf8;font-size:12px;font-weight:600;'
        'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">'
        'EU MDR 2017/745</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h1 style='margin-top:0;margin-bottom:4px;'>Articles 83-87 — FSCA Panel</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#64748b;margin-top:0;margin-bottom:20px;'>"
        "When a manufacturer initiates a Field Safety Corrective Action (FSCA), hospitals receive "
        "a Field Safety Notice (FSN) and are responsible for tracking implementation internally. "
        "This module simulates the hospital-side FSCA tracking process — recording manufacturer "
        "notifications, monitoring workflow stages, and ensuring timely follow-up in line with "
        "Articles 83-87 of EU MDR 2017/745.</p>",
        unsafe_allow_html=True,
    )

    try:
        df     = load_fsca()
        dev_df = load_devices()
    except Exception as e:
        st.error(f"Data load error: {e}")
        return

    df["durum"] = df.apply(compute_status, axis=1)
    today = pd.Timestamp(date.today())

    # ── KPI row ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total FSCAs", len(df))
    c2.metric("Active",      (df["durum"] == "Active").sum())
    c3.metric("Overdue",     (df["durum"] == "Overdue").sum())
    c4.metric("Closed",      (df["durum"] == "Closed").sum())

    n_overdue = (df["durum"] == "Overdue").sum()
    if n_overdue:
        st.warning(
            f"{n_overdue} FSCA action(s) are overdue. "
            "Delayed FSCA implementation may constitute a serious regulatory non-conformity under Art. 89."
        )

    st.markdown("---")

    tab1, tab2 = st.tabs(["FSCA Overview", "Workflow Tracker"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — Overview
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:

        # Stage flow badges
        st.markdown("**FSCA 5-Stage Workflow — EU MDR Articles 83-87**")
        flow_html = '<div style="display:flex;align-items:stretch;gap:0;margin:12px 0 20px 0;overflow-x:auto;">'
        for i, stage in enumerate(STAGES):
            color = STAGE_COLORS.get(stage, "#718096")
            art   = STAGE_ARTICLES.get(stage, "")
            count = (df["mevcut_asama"] == stage).sum()
            flow_html += (
                f'<div style="background:#0f172a;border:1px solid {color}44;'
                f'border-top:3px solid {color};border-radius:6px;padding:14px 16px;min-width:160px;flex:1;">'
                f'<div style="color:#475569;font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">Stage {i+1}</div>'
                f'<div style="color:{color};font-weight:700;font-size:14px;margin-top:4px;">{stage}</div>'
                f'<div style="color:#64748b;font-size:11px;margin-top:3px;margin-bottom:10px;">{art}</div>'
                f'<div style="color:#e2e8f0;font-size:26px;font-weight:800;">{count}</div>'
                f'<div style="color:#475569;font-size:10px;">cases</div>'
                f'</div>'
            )
            if i < len(STAGES) - 1:
                flow_html += '<div style="display:flex;align-items:center;padding:0 4px;color:#334155;font-size:20px;">&#8594;</div>'
        flow_html += '</div>'
        st.markdown(flow_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**Filter & Search FSCA Records**")

        # Filters row
        col_s0, col_s1, col_s2, col_s3 = st.columns([2, 1, 1, 1])
        with col_s0:
            all_device_names = ["All"] + sorted(dev_df["isim"].dropna().unique().tolist())
            device_search_sel = st.selectbox("Search by Device Name", all_device_names, key="dev_overview_sel")
            device_search = "" if device_search_sel == "All" else device_search_sel
        with col_s1:
            filter_coordinator = st.selectbox("Coordinator", ["All"] + sorted(df["sorumlu"].dropna().unique().tolist()))
        with col_s2:
            filter_status = st.selectbox("Status", ["All"] + list(STATUS_COLORS.keys()))
        with col_s3:
            filter_stage = st.selectbox("Stage", ["All"] + STAGES)

        # Build table
        df_tbl = df.merge(
            dev_df[["cihaz_id", "isim", "udi_kodu"]].rename(columns={"isim": "Device"}),
            on="cihaz_id", how="left"
        )
        df_tbl["Days Active"]    = (today - df_tbl["baslangic"]).dt.days.fillna(0).astype(int)
        df_tbl["FSN Deadline"]   = df_tbl["fsn_deadline"].dt.strftime("%d/%m/%Y")
        df_tbl["Target Closure"] = df_tbl["bitis"].dt.strftime("%d/%m/%Y")

        # Apply filters
        filtered = df_tbl.copy()
        if device_search:
            filtered = filtered[filtered["Device"].str.lower().str.contains(device_search.lower(), na=False)]
        if filter_coordinator != "All":
            filtered = filtered[filtered["sorumlu"] == filter_coordinator]
        if filter_status != "All":
            filtered = filtered[filtered["durum"] == filter_status]
        if filter_stage != "All":
            filtered = filtered[filtered["mevcut_asama"] == filter_stage]

        st.caption(f"Showing {len(filtered)} of {len(df)} FSCA records")

        display = filtered[[
            "fsca_id", "Device", "konu", "mevcut_asama", "sorumlu", "durum", "FSN Deadline", "Target Closure", "Days Active"
        ]].rename(columns={
            "fsca_id":      "FSCA ID",
            "konu":         "Topic",
            "mevcut_asama": "Stage",
            "sorumlu":      "Hospital Coordinator",
            "durum":        "Status",
        })

        st.dataframe(display, use_container_width=True, hide_index=True,
            column_config={"Days Active": st.column_config.NumberColumn("Days Active", format="%d days")})

        # PDF export
        st.markdown("---")
        st.markdown("**Export FSCA Status Report**")
        col_pdf1, col_pdf2 = st.columns([2, 1])
        with col_pdf1:
            pdf_fsca_id = st.selectbox("Select FSCA to export", df["fsca_id"].tolist(), key="pdf_select")
        with col_pdf2:
            pdf_row = df[df["fsca_id"] == pdf_fsca_id].iloc[0]
            pdf_dev = dev_df[dev_df["cihaz_id"] == pdf_row["cihaz_id"]]
            pdf_dev_name = pdf_dev["isim"].values[0] if not pdf_dev.empty else pdf_row["cihaz_id"]
            pdf_udi = pdf_dev["udi_kodu"].values[0] if not pdf_dev.empty else "—"
            pdf_bytes = generate_pdf(pdf_row, pdf_dev_name, pdf_udi)
            st.download_button(
                label="Download PDF Report",
                data=bytes(pdf_bytes),
                file_name=f"FSCA_Report_{pdf_fsca_id}_{date.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — Workflow Tracker
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### FSCA Workflow Management")

        fsca_ids    = df["fsca_id"].tolist()
        selected_id = st.selectbox("FSCA ID", fsca_ids, key="wf_select")
        row         = df[df["fsca_id"] == selected_id].iloc[0]

        dev_row  = dev_df[dev_df["cihaz_id"] == row["cihaz_id"]]
        dev_name = dev_row["isim"].values[0] if not dev_row.empty else row["cihaz_id"]
        udi_code = dev_row["udi_kodu"].values[0] if not dev_row.empty else "—"

        col_info, col_stage = st.columns(2)
        with col_info:
            s_color = STATUS_COLORS.get(row["durum"], "#718096")
            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:16px;">'
                f'<div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">FSCA ID</div>'
                f'<div style="font-size:20px;color:#e2e8f0;font-weight:700;margin-bottom:8px;">{row["fsca_id"]}</div>'
                f'<div style="font-size:12px;color:#64748b;">Device</div>'
                f'<div style="color:#e2e8f0;font-size:14px;">{dev_name}</div>'
                f'<div style="color:#475569;font-size:11px;margin-bottom:8px;">UDI: {udi_code}</div>'
                f'<div style="font-size:12px;color:#64748b;">Topic</div>'
                f'<div style="color:#e2e8f0;font-size:13px;margin-bottom:8px;">{row.get("konu","—")}</div>'
                f'<div style="font-size:12px;color:#64748b;">Hospital Coordinator</div>'
                f'<div style="color:#e2e8f0;font-size:14px;margin-bottom:12px;">{row["sorumlu"]}</div>'
                f'<span style="background:{s_color}22;color:{s_color};border:1px solid {s_color}44;'
                f'padding:3px 12px;border-radius:4px;font-size:12px;font-weight:600;">{row["durum"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_stage:
            stage_color = STAGE_COLORS.get(row["mevcut_asama"], "#718096")
            art_ref     = STAGE_ARTICLES.get(row["mevcut_asama"], "")
            start_str   = row["baslangic"].strftime("%d/%m/%Y") if pd.notna(row["baslangic"]) else "—"
            end_str     = row["bitis"].strftime("%d/%m/%Y")     if pd.notna(row["bitis"])     else "—"
            fsn_str     = row["fsn_deadline"].strftime("%d/%m/%Y") if pd.notna(row["fsn_deadline"]) else "—"
            fsn_overdue = pd.notna(row["fsn_deadline"]) and row["fsn_deadline"] < today and row["mevcut_asama"] != "Closure"
            fsn_color   = "#f87171" if fsn_overdue else "#e2e8f0"
            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:16px;">'
                f'<div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">Current Stage</div>'
                f'<div style="font-size:20px;color:{stage_color};font-weight:700;">{row["mevcut_asama"]}</div>'
                f'<div style="font-size:11px;color:#475569;margin-bottom:12px;">{art_ref}</div>'
                f'<div style="font-size:12px;color:#64748b;">FSCA Initiation Date</div>'
                f'<div style="color:#e2e8f0;font-size:14px;margin-bottom:8px;">{start_str}</div>'
                f'<div style="font-size:12px;color:#64748b;">FSN Implementation Deadline</div>'
                f'<div style="color:{fsn_color};font-size:14px;font-weight:600;margin-bottom:8px;">'
                f'{fsn_str}{"  - OVERDUE" if fsn_overdue else ""}</div>'
                f'<div style="font-size:12px;color:#64748b;">Target Closure</div>'
                f'<div style="color:#e2e8f0;font-size:14px;">{end_str}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("#### 5-Stage FSCA Workflow Progress")
        st.markdown(stage_progress_html(row["mevcut_asama"]), unsafe_allow_html=True)
        st.progress((stage_index(row["mevcut_asama"]) + 1) / len(STAGES))
        st.caption(
            f"Stage {stage_index(row['mevcut_asama'])+1} of {len(STAGES)} — "
            f"{row['mevcut_asama']}  ·  {STAGE_ARTICLES.get(row['mevcut_asama'], '')}"
        )

        st.markdown("---")
        st.markdown("#### Update FSCA Stage")

        new_stage = st.selectbox(
            "New Stage", STAGES,
            index=stage_index(row["mevcut_asama"]),
            key="new_stage_select"
        )

        closure_ready     = True
        uploaded_evidence = {}

        if new_stage == "Closure":
            st.markdown(
                '<div style="background:#0f172a;border:1px solid #f87171;border-left:4px solid #f87171;'
                'border-radius:6px;padding:14px 16px;margin:12px 0;">'
                '<div style="color:#f87171;font-weight:700;font-size:14px;margin-bottom:4px;">'
                'Closure Evidence Requirements — EU MDR Art. 86</div>'
                '<div style="color:#94a3b8;font-size:12px;">'
                'All six evidence documents must be uploaded before this FSCA can be closed. '
                'Unverified closure constitutes a regulatory non-conformity under Art. 89.'
                '</div></div>',
                unsafe_allow_html=True,
            )
            for key, doc_name, article, description in CLOSURE_EVIDENCE:
                col_ev1, col_ev2 = st.columns([2, 3])
                with col_ev1:
                    st.markdown(
                        f'<div style="padding:8px 0;">'
                        f'<div style="color:#e2e8f0;font-size:13px;font-weight:600;">{doc_name}</div>'
                        f'<div style="color:#38bdf8;font-size:11px;">{article}</div>'
                        f'<div style="color:#64748b;font-size:11px;margin-top:2px;">{description}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with col_ev2:
                    uploaded = st.file_uploader(
                        f"Upload {doc_name}",
                        type=["pdf", "png", "jpg", "jpeg", "docx"],
                        key=f"evidence_{key}_{selected_id}",
                        label_visibility="collapsed",
                    )
                    uploaded_evidence[key] = uploaded
                    if uploaded:
                        st.success(f"{uploaded.name} — uploaded")
                    else:
                        st.caption("No document uploaded")
                st.markdown('<hr style="border-color:#1e293b;margin:4px 0;">', unsafe_allow_html=True)

            missing = [doc_name for (key, doc_name, _, _) in CLOSURE_EVIDENCE if not uploaded_evidence.get(key)]
            closure_ready = len(missing) == 0
            if not closure_ready:
                st.warning(f"{len(missing)} document(s) still required: {', '.join(missing)}")

        with st.form("fsca_update_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.markdown(f"**Selected Stage:** {new_stage}")
                new_responsible = st.text_input("Hospital Coordinator", value=row["sorumlu"])
            with col_f2:
                new_start = st.date_input(
                    "FSCA Initiation Date",
                    value=row["baslangic"].date() if pd.notna(row["baslangic"]) else date.today(),
                )
                new_end = st.date_input(
                    "Target Closure Date",
                    value=row["bitis"].date() if pd.notna(row["bitis"]) else date.today() + timedelta(days=30),
                )
            st.text_area(
                "Update Notes (optional)",
                placeholder="Describe actions taken, findings, or rationale for stage change...",
                height=80,
            )
            submitted = st.form_submit_button("Save Update", use_container_width=True)

        if submitted:
            errors = []
            if not new_responsible.strip():
                errors.append("Hospital Coordinator is required.")
            if new_end < new_start:
                errors.append("Target closure date cannot be before initiation date.")
            if new_stage == "Closure" and not closure_ready:
                errors.append("All closure evidence documents must be uploaded before closing this FSCA (Art. 86).")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                df_updated = load_fsca()
                idx = df_updated[df_updated["fsca_id"] == selected_id].index[0]
                df_updated.at[idx, "mevcut_asama"] = new_stage
                df_updated.at[idx, "sorumlu"]      = new_responsible.strip()
                df_updated.at[idx, "baslangic"]    = pd.Timestamp(new_start)
                df_updated.at[idx, "bitis"]        = pd.Timestamp(new_end)
                if new_stage == "Closure":
                    df_updated.at[idx, "durum"] = "Closed"
                elif pd.Timestamp(new_end) < pd.Timestamp(date.today()):
                    df_updated.at[idx, "durum"] = "Overdue"
                else:
                    df_updated.at[idx, "durum"] = "Active"
                save_fsca(df_updated)
                st.success(f"{selected_id} updated to stage {new_stage} — coordinator: {new_responsible.strip()}")
                st.rerun()

        st.markdown("---")
        st.markdown("#### Add New FSCA Record")

        with st.form("new_fsca_form"):
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                new_fsca_id = st.text_input("FSCA ID *", placeholder="e.g. FSCA-051")
                new_device  = st.selectbox("Device *", dev_df["cihaz_id"].tolist())
                new_stage_n = st.selectbox("Initial Stage *", STAGES)
            with col_n2:
                new_resp   = st.text_input("Hospital Coordinator *", placeholder="e.g. Quality Manager")
                new_s_date = st.date_input("FSCA Initiation Date *", value=date.today())
                new_fsn    = st.date_input("FSN Implementation Deadline *", value=date.today() + timedelta(days=30))
                new_e_date = st.date_input("Target Closure Date *", value=date.today() + timedelta(days=60))
            add_submitted = st.form_submit_button("Add FSCA Record", use_container_width=True)

        if add_submitted:
            errs = []
            if not new_fsca_id.strip():
                errs.append("FSCA ID is required. (Art. 87 — each FSCA must have a unique identifier)")
            if new_fsca_id.strip() in df["fsca_id"].values:
                errs.append("This FSCA ID already exists.")
            if not new_resp.strip():
                errs.append("Hospital Coordinator is required.")
            if new_fsn < new_s_date:
                errs.append("FSN Implementation Deadline must be after initiation date.")
            if new_e_date < new_fsn:
                errs.append("Target Closure Date must be after FSN Implementation Deadline.")
            if errs:
                for e in errs:
                    st.error(e)
            else:
                df_existing = load_fsca()
                auto_status = "Closed" if new_stage_n == "Closure" else "Active"
                new_row = {
                    "fsca_id":      new_fsca_id.strip(),
                    "cihaz_id":     new_device,
                    "mevcut_asama": new_stage_n,
                    "sorumlu":      new_resp.strip(),
                    "baslangic":    pd.Timestamp(new_s_date),
                    "fsn_deadline": pd.Timestamp(new_fsn),
                    "bitis":        pd.Timestamp(new_e_date),
                    "durum":        auto_status,
                }
                df_existing = pd.concat([df_existing, pd.DataFrame([new_row])], ignore_index=True)
                save_fsca(df_existing)
                st.success(f"New FSCA {new_fsca_id.strip()} added at stage {new_stage_n} — Art. 83-87 workflow initiated.")
                st.rerun()
