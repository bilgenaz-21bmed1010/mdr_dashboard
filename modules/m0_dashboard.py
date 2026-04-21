import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render():
    st.title("M0 — Home Dashboard")
    st.markdown("**EU MDR 2017/745 | WP4 Prototype — Compliance Overview**")

    try:
        devices   = pd.read_csv("data/devices.csv")
        incidents = pd.read_csv("data/incidents.csv")
        fsca      = pd.read_csv("data/fsca.csv")
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}")
        return

    valid_classes = ["I", "IIa", "IIb", "III"]
    devices_clean = devices[devices["risk_sinifi"].isin(valid_classes)]

    total_devices = len(devices)
    active        = (devices["durum"] == "Active").sum()
    inactive      = (devices["durum"] == "Inactive").sum()
    under_review  = (devices["durum"] == "Under Review").sum()
    recalled      = (devices["durum"] == "Recalled").sum()

    open_incidents = (incidents["durum"] != "Closed").sum()
    overdue        = (incidents["durum"] == "Overdue").sum()
    investigating  = (incidents["durum"] == "Under Investigation").sum()
    reported       = (incidents["durum"] == "Reported").sum()

    overdue_10 = ((incidents["durum"] == "Overdue") & (incidents["deadline_gun"] == 10)).sum()
    overdue_15 = ((incidents["durum"] == "Overdue") & (incidents["deadline_gun"] == 15)).sum()
    overdue_30 = ((incidents["durum"] == "Overdue") & (incidents["deadline_gun"] == 30)).sum()
    overdue_90 = ((incidents["durum"] == "Overdue") & (incidents["deadline_gun"] == 90)).sum()

    active_fsca = (fsca["durum"] != "Closed").sum()
    fsca_open   = (fsca["durum"] == "Open").sum()
    fsca_inprog = (fsca["durum"] == "In Progress").sum()
    fsca_closed = (fsca["durum"] == "Closed").sum()

    udi_score      = round((1 - recalled / total_devices) * 100, 1)
    incident_score = round((1 - overdue / max(open_incidents, 1)) * 100, 1)
    fsca_score     = round((fsca_inprog + fsca_closed) / max(len(fsca), 1) * 100, 1)
    overall_score  = round((udi_score + incident_score + fsca_score) / 3, 1)

    def kpi_card(col, label, value, details, accent, detail_colors):
        rows_html = ""
        for i, (k, v) in enumerate(details):
            dc = detail_colors[i] if i < len(detail_colors) else "#64748B"
            rows_html += (
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.05)'>"
                f"<div style='display:flex;align-items:center;gap:8px'>"
                f"<div style='width:7px;height:7px;border-radius:50%;background:{dc};flex-shrink:0'></div>"
                f"<span style='color:#8899aa;font-size:0.8rem;font-weight:500'>{k}</span>"
                f"</div>"
                f"<span style='color:#c8d8e8;font-weight:700;font-size:0.82rem;"
                f"font-variant-numeric:tabular-nums'>{v}</span></div>"
            )
        with col:
            st.markdown(
                f"<div style='background:linear-gradient(160deg,#0f1922,#0a1018);"
                f"border:1px solid rgba(255,255,255,0.07);border-top:2px solid {accent};"
                f"border-radius:12px;padding:1.3rem 1.4rem 1rem;height:230px;"
                f"box-sizing:border-box;box-shadow:0 4px 24px rgba(0,0,0,0.4)'>"
                f"<div style='font-size:0.72rem;font-weight:700;color:#7a8fa0;"
                f"text-transform:uppercase;letter-spacing:0.13em;margin-bottom:0.45rem'>{label}</div>"
                f"<div style='font-size:2.1rem;font-weight:800;color:#e8f0f8;line-height:1;"
                f"margin-bottom:0.9rem;font-variant-numeric:tabular-nums;"
                f"text-shadow:0 0 20px {accent}55'>{value}</div>"
                f"<div style='border-top:1px solid rgba(255,255,255,0.06);padding-top:0.55rem'>"
                f"{rows_html}</div></div>",
                unsafe_allow_html=True
            )

    c1, c2, c3, c4 = st.columns(4)

    kpi_card(c1, "Registered Devices", total_devices,
        [("Active", active), ("Inactive", inactive),
         ("Under Review", under_review), ("Recalled", recalled)],
        accent="#38bdf8",
        detail_colors=["#4ade80", "#64748B", "#fbbf24", "#f87171"])

    kpi_card(c2, "Open Incidents", int(open_incidents),
        [("Overdue", overdue), ("Under Investigation", investigating), ("Reported", reported)],
        accent="#f87171",
        detail_colors=["#f87171", "#fbbf24", "#38bdf8"])

    kpi_card(c3, "Overdue Reports", int(overdue),
        [("10-day deadline", overdue_10), ("15-day deadline", overdue_15),
         ("30-day deadline", overdue_30), ("90-day deadline", overdue_90)],
        accent="#fbbf24",
        detail_colors=["#f87171", "#fb923c", "#fbbf24", "#a3e635"])

    kpi_card(c4, "Active FSCAs", int(active_fsca),
        [("Open", fsca_open), ("In Progress", fsca_inprog), ("Closed", fsca_closed)],
        accent="#4ade80",
        detail_colors=["#f87171", "#fbbf24", "#4ade80"])

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Device Classification Breakdown")

        class_counts = (
            devices_clean["risk_sinifi"]
            .value_counts()
            .reindex(valid_classes, fill_value=0)
            .reset_index()
        )
        class_counts.columns = ["Class", "Count"]
        total_clean = class_counts["Count"].sum()

        CLASS_COLORS = {
            "I":   "rgba(236,72,153,0.8)",
            "IIa": "rgba(59,130,246,0.8)",
            "IIb": "rgba(132,204,22,0.8)",
            "III": "rgba(234,179,8,0.8)",
        }

        rows = ""
        for _, row in class_counts.iterrows():
            cls = row["Class"]
            cnt = int(row["Count"])
            pct = round(cnt / total_clean * 100, 1)
            bg = CLASS_COLORS.get(cls, "rgba(148,163,184,0.8)")
            rows += (
                f"<div style='display:flex;align-items:center;justify-content:space-between;"
                f"padding:14px 16px;border-bottom:1px solid rgba(255,255,255,0.05)'>"
                f"<div style='display:flex;align-items:center;gap:12px'>"
                f"<div style='width:13px;height:13px;border-radius:3px;background:{bg};flex-shrink:0'></div>"
                f"<span style='color:#c8d8e8;font-size:0.9rem;font-weight:500'>Class {cls}</span>"
                f"</div>"
                f"<div style='display:flex;align-items:center;gap:20px'>"
                f"<span style='color:#64748B;font-size:0.82rem'>{pct}%</span>"
                f"<span style='color:#e2e8f0;font-weight:700;font-size:0.9rem;"
                f"min-width:28px;text-align:right'>{cnt}</span>"
                f"</div></div>"
            )

        header = (
            "<div style='padding:14px 16px;border-bottom:1px solid rgba(255,255,255,0.08);"
            "display:flex;justify-content:space-between;align-items:center'>"
            "<span style='color:#475569;font-size:0.72rem;font-weight:700;"
            "text-transform:uppercase;letter-spacing:0.1em'>MDR Risk Class</span>"
            "<span style='color:#475569;font-size:0.72rem;font-weight:700;"
            "text-transform:uppercase;letter-spacing:0.1em'>Devices</span></div>"
        )
        footer = (
            f"<div style='padding:12px 16px;display:flex;justify-content:space-between;"
            f"align-items:center;border-top:1px solid rgba(255,255,255,0.06)'>"
            f"<span style='color:#475569;font-size:0.78rem'>Total</span>"
            f"<span style='color:#e2e8f0;font-weight:700;font-size:0.9rem'>{total_clean}</span></div>"
        )

        st.markdown(
            "<div style='background:linear-gradient(160deg,#0f1922,#0a1018);"
            "border:1px solid rgba(255,255,255,0.07);border-radius:12px;"
            "overflow:hidden;margin-top:8px'>"
            + header + rows + footer + "</div>",
            unsafe_allow_html=True
        )

    with col_right:
        st.subheader("Compliance Score")

        gauge_color = (
            "#f87171" if overall_score < 60
            else "#fbbf24" if overall_score < 80
            else "#4ade80"
        )

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall_score,
            number=dict(suffix="%", font=dict(size=38, color="#e8f0f8")),
            gauge=dict(
                axis=dict(
                    range=[0, 100],
                    tickwidth=1,
                    tickcolor="#1E293B",
                    tickfont=dict(color="#475569", size=10),
                    nticks=6,
                ),
                bar=dict(color=gauge_color, thickness=0.22),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
                steps=[
                    dict(range=[0, 60],   color="rgba(248,113,113,0.08)"),
                    dict(range=[60, 80],  color="rgba(251,191,36,0.06)"),
                    dict(range=[80, 100], color="rgba(74,222,128,0.06)"),
                ],
                threshold=dict(
                    line=dict(color="#334155", width=2),
                    thickness=0.75,
                    value=80,
                ),
            ),
            domain=dict(x=[0, 1], y=[0.15, 1]),
        ))
        fig_gauge.add_annotation(
            text="Overall MDR Compliance",
            x=0.5, y=0.05,
            showarrow=False,
            font=dict(size=11, color="#475569"),
        )
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=10, l=20, r=20),
            height=270,
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        sub_scores = [
            ("UDI / Device Registry",  udi_score,      "#38bdf8"),
            ("Incident Reporting",     incident_score, "#f87171"),
            ("FSCA Management",        fsca_score,     "#4ade80"),
        ]
        rows_gauge = ""
        for lbl, val, c in sub_scores:
            rows_gauge += (
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.05)'>"
                f"<div style='display:flex;align-items:center;gap:8px'>"
                f"<div style='width:7px;height:7px;border-radius:50%;background:{c}'></div>"
                f"<span style='color:#8899aa;font-size:0.79rem'>{lbl}</span>"
                f"</div>"
                f"<span style='color:#c8d8e8;font-weight:700;font-size:0.82rem'>{val}%</span>"
                f"</div>"
            )

        st.markdown(
            "<div style='background:linear-gradient(160deg,#0f1922,#0a1018);"
            "border:1px solid rgba(255,255,255,0.07);border-radius:10px;"
            "padding:0.9rem 1.1rem;margin-top:-0.5rem'>"
            + rows_gauge + "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.subheader("Recent Incidents")

    recent = incidents.sort_values("olay_tarihi", ascending=False).head(10)

    STATUS_COLORS = {
        "Overdue":             "#f87171",
        "Under Investigation": "#fbbf24",
        "Reported":            "#38bdf8",
        "Closed":              "#4ade80",
    }

    def status_cell(val):
        color = STATUS_COLORS.get(val, "#94a3b8")
        return (
            f"<span style='color:{color};font-size:0.82rem;"
            f"font-weight:600;letter-spacing:0.04em'>{val}</span>"
        )

    show_cols = ["olay_id", "cihaz_adi", "kategori", "ciddiyet",
                 "deadline_gun", "deadline", "durum"]
    show_cols = [c for c in show_cols if c in recent.columns]

    col_labels = {
        "olay_id":      "Incident ID",
        "cihaz_adi":    "Device",
        "kategori":     "Category",
        "ciddiyet":     "Severity",
        "deadline_gun": "Deadline (days)",
        "deadline":     "Deadline Date",
        "durum":        "Status",
    }

    headers = "".join(
        f"<th style='padding:10px 14px;text-align:left;background:#080e16;"
        f"color:#334155;font-size:0.68rem;text-transform:uppercase;"
        f"letter-spacing:.1em;white-space:nowrap;font-weight:700'>"
        f"{col_labels.get(c, c)}</th>"
        for c in show_cols
    )

    rows_html = ""
    for _, row in recent.iterrows():
        cells = ""
        for col in show_cols:
            val = str(row.get(col, ""))
            if col == "durum":
                cells += f"<td style='padding:9px 14px'>{status_cell(val)}</td>"
            else:
                cells += (
                    f"<td style='padding:9px 14px;font-size:0.81rem;"
                    f"color:#7a8fa0;white-space:nowrap'>{val}</td>"
                )
        rows_html += (
            f"<tr style='background:#0f1922;"
            f"border-bottom:1px solid rgba(255,255,255,0.04)'>{cells}</tr>"
        )

    st.markdown(
        "<div style='overflow-x:auto;border-radius:8px;border:1px solid rgba(255,255,255,0.07)'>"
        "<table style='width:100%;border-collapse:collapse'>"
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table></div>",
        unsafe_allow_html=True
    )