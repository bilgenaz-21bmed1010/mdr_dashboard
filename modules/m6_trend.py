import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

INCIDENTS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "incidents.csv")
DEVICES_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "devices.csv")

SEVERITY_COLORS = {
    "Serious (Public Health Threat)": "#e74c3c",
    "Serious (Life-threatening)":     "#e67e22",
    "Serious (Hospitalization)":      "#f1c40f",
    "Non-Serious":                    "#2ecc71",
}

SEVERITY_SHORT = {
    "Serious (Public Health Threat)": "Public Health Threat",
    "Serious (Life-threatening)":     "Life-threatening",
    "Serious (Hospitalization)":      "Hospitalization",
    "Non-Serious":                    "Non-Serious",
}


@st.cache_data
def load_data():
    df = pd.read_csv(INCIDENTS_PATH)
    df["olay_tarihi"]      = pd.to_datetime(df["olay_tarihi"])
    df["raporlama_tarihi"] = pd.to_datetime(df["raporlama_tarihi"])
    df["month_dt"]         = df["olay_tarihi"].dt.to_period("M").dt.to_timestamp()

    # merge risk class from devices.csv
    devices = pd.read_csv(DEVICES_PATH)[["cihaz_id", "risk_sinifi", "kategori"]].drop_duplicates()
    # build category → risk class map (use highest class per category)
    risk_order = {"III": 4, "IIb": 3, "IIa": 2, "I": 1}
    cat_risk = (
        devices.groupby("kategori")["risk_sinifi"]
        .apply(lambda x: max(x, key=lambda r: risk_order.get(r, 0)))
        .reset_index()
        .rename(columns={"risk_sinifi": "cat_risk_class"})
    )
    df = df.merge(cat_risk, on="kategori", how="left")
    df["cat_risk_class"] = df["cat_risk_class"].fillna("IIb")
    return df


def flag_trend(monthly_counts):
    if len(monthly_counts) < 3:
        return []
    mean = monthly_counts.mean()
    std  = monthly_counts.std()
    return monthly_counts[monthly_counts > mean + std].index.tolist()


def show():
    st.markdown(
        '<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.12em;'
        'color:#2563EB;text-transform:uppercase;margin-bottom:0.25rem;">Module M6</div>',
        unsafe_allow_html=True,
    )
    st.title("Trend Analysis")

    try:
        df = load_data()
    except FileNotFoundError:
        st.error("incidents.csv not found. Place it in the data/ folder.")
        return

    date_range = (
        f"{df['olay_tarihi'].min().strftime('%b %Y')} – "
        f"{df['olay_tarihi'].max().strftime('%b %Y')}"
    )
    st.caption(f"EU MDR Art. 88 · Incident frequency trends · Statistical signal detection · Period: {date_range}")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total   = len(df)
    serious = len(df[df["ciddiyet"] != "Non-Serious"])
    overdue = len(df[df["durum"] == "Overdue"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Incidents",   total)
    c2.metric("Serious Incidents", serious, help="Excludes Non-Serious")
    c3.metric("Overdue Reports",   overdue, help="Art. 87 deadline exceeded")

    st.markdown("---")

    # ── filters ────────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        severity_filter = st.selectbox(
            "Severity",
            options=["All Severities"] + list(SEVERITY_COLORS.keys()),
        )
    with col_f2:
        all_cats = sorted(df["kategori"].unique().tolist())
        cat_filter = st.selectbox(
            "Device Category",
            options=["All Categories"] + all_cats,
        )
    with col_f3:
        status_filter = st.selectbox(
            "Status",
            options=["All Statuses", "Overdue", "Under Investigation", "Reported", "Closed"],
        )

    df_f = df.copy()
    if severity_filter != "All Severities":
        df_f = df_f[df_f["ciddiyet"] == severity_filter]
    if cat_filter != "All Categories":
        df_f = df_f[df_f["kategori"] == cat_filter]
    if status_filter != "All Statuses":
        df_f = df_f[df_f["durum"] == status_filter]

    if df_f.empty:
        st.warning("No records match the selected filters.")
        return

    st.markdown("---")

    # ── severity summary cards ─────────────────────────────────────────────────
    st.subheader("Severity Breakdown")
    st.caption("Incident counts by MDR Art. 87 severity classification — current filter applied.")

    sev_cols = st.columns(4)
    for i, (sev, color) in enumerate(SEVERITY_COLORS.items()):
        count = len(df_f[df_f["ciddiyet"] == sev])
        short = SEVERITY_SHORT[sev]
        sev_cols[i].markdown(
            f'<div style="background:{color}22;border:1px solid {color}55;border-top:3px solid {color};'
            f'border-radius:10px;padding:14px 16px;">'
            f'<div style="color:{color};font-size:0.72rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.08em;margin-bottom:6px;">{short}</div>'
            f'<div style="color:#F1F5F9;font-size:2rem;font-weight:800;">{count}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("&nbsp;")
    st.markdown("---")

    # ── time-series ───────────────────────────────────────────────────────────
    st.subheader("Monthly Incident Frequency")
    st.caption("Incidents per month. Red star marks months exceeding mean + 1 standard deviation — potential Art. 88 trend signal.")

    monthly = df_f.groupby("month_dt").size().reset_index(name="count").sort_values("month_dt")
    flagged = flag_trend(monthly.set_index("month_dt")["count"])

    fig_line = go.Figure()

    fig_line.add_trace(go.Scatter(
        x=monthly["month_dt"],
        y=monthly["count"],
        mode="lines+markers",
        name="Incidents",
        line=dict(color="#2563EB", width=2.5),
        marker=dict(size=7, color="#2563EB"),
        hovertemplate="<b>%{x|%B %Y}</b><br>Incidents: %{y}<extra></extra>",
    ))

    flagged_df = monthly[monthly["month_dt"].isin(flagged)]
    if not flagged_df.empty:
        fig_line.add_trace(go.Scatter(
            x=flagged_df["month_dt"],
            y=flagged_df["count"],
            mode="markers",
            name="Signal",
            marker=dict(size=14, color="#e74c3c", symbol="star"),
            hovertemplate="<b>%{x|%B %Y}</b><br>Signal detected: %{y}<extra></extra>",
        ))

    mean_val = monthly["count"].mean()
    fig_line.add_hline(
        y=mean_val,
        line_dash="dash",
        line_color="#64748b",
        annotation_text=f"Mean: {mean_val:.1f}",
        annotation_font_color="#94A3B8",
        annotation_position="bottom right",
    )

    fig_line.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        xaxis=dict(tickfont=dict(color="#94A3B8", size=11), gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(
            tickfont=dict(color="#94A3B8", size=11),
            title=dict(text="Incident Count", font=dict(color="#64748B", size=11)),
            gridcolor="rgba(255,255,255,0.04)",
        ),
        legend=dict(font=dict(color="#94A3B8"), bgcolor="rgba(0,0,0,0)"),
    )

    st.plotly_chart(fig_line, use_container_width=True)

    if flagged:
        labels = ", ".join([m.strftime("%B %Y") for m in flagged])
        st.warning(f"Signal detected in: **{labels}** — review under MDR Art. 88 trend reporting obligations.")
    else:
        st.success("No statistically significant trend signals detected in the selected period.")

    st.markdown("---")

    # ── per device category trend table ───────────────────────────────────────
    st.subheader("Incident Frequency per Device Category")

    # build summary per category (full dataset, not df_f)
    cat_summary = []
    cat_totals = df.groupby("kategori").size()
    global_median = cat_totals.median()

    for cat, group in df.groupby("kategori"):
        monthly_cat = group.groupby("month_dt").size()
        total = len(group)
        peak_month = monthly_cat.idxmax().strftime("%b %Y") if not monthly_cat.empty else "—"
        peak_count = int(monthly_cat.max()) if not monthly_cat.empty else 0
        mean_c = monthly_cat.mean()
        std_c  = monthly_cat.std() if len(monthly_cat) > 1 else 0
        elevated = any(monthly_cat > mean_c + std_c) if std_c > 0 else False
        has_pht      = "Serious (Public Health Threat)" in group["ciddiyet"].values
        most_severe  = group["ciddiyet"].value_counts().index[0] if not group.empty else "—"
        risk_class   = group["cat_risk_class"].iloc[0] if "cat_risk_class" in group.columns else "IIb"
        high_risk    = risk_class in ["IIb", "III"]

        if elevated and has_pht and high_risk:
            status = "Critical"
        elif elevated:
            status = "Elevated"
        else:
            status = "Normal"

        cat_summary.append({
            "Category":             cat,
            "Device Classification": risk_class,
            "Total Incidents":       total,
            "Peak Month":           peak_month,
            "Peak Count":           peak_count,
            "Most Severe":          most_severe,
            "Status":               status,
        })

    summary_df = pd.DataFrame(cat_summary).sort_values("Category").reset_index(drop=True)

    # ── table filters ──────────────────────────────────────────────────────────
    tf1, tf2 = st.columns([2, 1])
    with tf1:
        cat_search = st.selectbox(
            "Filter by Category",
            options=["All Categories"] + sorted(summary_df["Category"].tolist()),
            key="cat_table_filter",
        )
    with tf2:
        status_search = st.selectbox(
            "Filter by Status",
            options=["All Statuses", "Critical", "Elevated", "Normal"],
            key="status_table_filter",
        )

    filtered_summary = summary_df.copy()
    if cat_search != "All Categories":
        filtered_summary = filtered_summary[filtered_summary["Category"] == cat_search]
    if status_search != "All Statuses":
        filtered_summary = filtered_summary[filtered_summary["Status"] == status_search]

    st.caption(f"Showing {len(filtered_summary)} of {len(summary_df)} categories.")

    def color_status(val):
        return {
            "Critical": "background-color:#7f1d1d;color:#fca5a5;font-weight:700;text-align:center;",
            "Elevated": "background-color:#78350f;color:#fcd34d;font-weight:700;text-align:center;",
            "Normal":   "background-color:#14532d;color:#86efac;text-align:center;",
        }.get(val, "")

    def color_severity(val):
        return {
            "Serious (Public Health Threat)": "color:#e74c3c;font-weight:600;",
            "Serious (Life-threatening)":     "color:#e67e22;font-weight:600;",
            "Serious (Hospitalization)":      "color:#f1c40f;font-weight:600;",
            "Non-Serious":                    "color:#2ecc71;",
        }.get(val, "")

    styled_summary = (
        filtered_summary.style
        .map(color_status, subset=["Status"])
        .map(color_severity, subset=["Most Severe"])
    )

    st.dataframe(styled_summary, use_container_width=True, hide_index=True, height=420)

    # ── legend ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="display:flex;gap:24px;flex-wrap:wrap;margin-top:8px;">'
        '<div><span style="background:#7f1d1d;color:#fca5a5;padding:2px 10px;border-radius:4px;font-size:0.78rem;font-weight:700;">Critical</span>'
        '<span style="color:#64748b;font-size:0.78rem;margin-left:6px;">Statistically elevated + Public Health Threat incident present</span></div>'
        '<div><span style="background:#78350f;color:#fcd34d;padding:2px 10px;border-radius:4px;font-size:0.78rem;font-weight:700;">Elevated</span>'
        '<span style="color:#64748b;font-size:0.78rem;margin-left:6px;">Monthly count exceeds category mean + 1 SD — Art. 88 review required</span></div>'
        '<div><span style="background:#14532d;color:#86efac;padding:2px 10px;border-radius:4px;font-size:0.78rem;font-weight:700;">Normal</span>'
        '<span style="color:#64748b;font-size:0.78rem;margin-left:6px;">Within expected frequency range</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.info(
        "MDR Art. 88 requires trend analysis of PMS data for signals indicating serious risk. "
        "Signal threshold: mean + 1 standard deviation of monthly incident frequency. "
        "Data source: M2 Incident Reporting module."
    )