import streamlit as st
import pandas as pd
from datetime import date, timedelta

INCIDENTS_PATH = "data/incidents.csv"
DEVICES_PATH = "data/devices.csv"

SEVERITY_OPTIONS = {
    "Immediate threat to public health (Article 87/1a)": 10,
    "Serious incident – Death / Unexpected deterioration (Article 87/1b)": 15,
    "Serious incident – Expected deterioration (Article 87/1b)": 30,
    "Trend report (Article 88)": 90,
}

SEVERITY_COLORS = {
    10: "#f87171",   # red
    15: "#fb923c",   # orange
    30: "#fbbf24",   # yellow
    90: "#60a5fa",   # blue
}

STATUS_COLORS = {
    "Open": "#38bdf8",
    "Under Investigation": "#fbbf24",
    "Closed": "#4ade80",
    "Overdue": "#f87171",
}

def load_incidents():
    try:
        df = pd.read_csv(INCIDENTS_PATH)
        if "olay_tarihi" in df.columns:
            df["olay_tarihi"] = pd.to_datetime(df["olay_tarihi"], errors="coerce")
        if "deadline" in df.columns:
            df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def load_devices():
    try:
        return pd.read_csv(DEVICES_PATH)
    except FileNotFoundError:
        return pd.DataFrame()

def render():
    # ─── Page header ──────────────────────────────────────────────────
    st.markdown(
        """
        <div style="margin-bottom:24px;">
            <div style="font-size:11px;letter-spacing:2px;color:#64748b;text-transform:uppercase;margin-bottom:4px;">
                EU MDR 2017/745
            </div>
            <div style="font-size:24px;font-weight:700;color:#f1f5f9;margin-bottom:6px;">
                Article 87 — Incident Reporting
            </div>
            <div style="font-size:13px;color:#94a3b8;line-height:1.6;">
                Serious incidents and field safety corrective actions must be reported
                to the relevant competent authority within mandatory timeframes.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─── Deadline rules reference ──────────────────────────────────────
    st.markdown(
        """
        <div style="background:#0a1018;border:1px solid rgba(255,255,255,0.07);border-radius:10px;
                    padding:16px 20px;margin-bottom:28px;">
            <div style="font-size:11px;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;
                        margin-bottom:12px;">Mandatory Reporting Windows</div>
            <div style="display:flex;gap:24px;flex-wrap:wrap;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="background:#f87171;border-radius:4px;padding:2px 8px;
                                 font-size:12px;font-weight:700;color:#0f1922;">10 days</span>
                    <span style="font-size:12px;color:#94a3b8;">Public health threat (Art. 87/1a)</span>
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="background:#fb923c;border-radius:4px;padding:2px 8px;
                                 font-size:12px;font-weight:700;color:#0f1922;">15 days</span>
                    <span style="font-size:12px;color:#94a3b8;">Death / unexpected deterioration (Art. 87/1b)</span>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="background:#fbbf24;border-radius:4px;padding:2px 8px;
                                 font-size:12px;font-weight:700;color:#0f1922;">30 days</span>
                    <span style="font-size:12px;color:#94a3b8;">Expected deterioration (Art. 87/1b)</span>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="background:#60a5fa;border-radius:4px;padding:2px 8px;
                                 font-size:12px;font-weight:700;color:#0f1922;">90 days</span>
                    <span style="font-size:12px;color:#94a3b8;">Trend reporting (Art. 88)</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─── Tabs ──────────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["Deadline Calculator", "Incident Records"])

    # ══════════════════════════════════════════════════════════════════
    # TAB 1 — Deadline Calculator
    # ══════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown(
            "<div style='font-size:14px;color:#94a3b8;margin-bottom:20px;'>"
            "Select severity class and incident date to calculate the Article 87 reporting deadline."
            "</div>",
            unsafe_allow_html=True,
        )

        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            severity_label = st.selectbox(
                "Severity Classification",
                options=list(SEVERITY_OPTIONS.keys()),
                key="m2_severity",
            )
            incident_date = st.date_input(
                "Incident Date",
                value=date.today(),
                key="m2_incident_date",
            )

        days = SEVERITY_OPTIONS[severity_label]
        deadline_date = incident_date + timedelta(days=days)
        today = date.today()
        days_remaining = (deadline_date - today).days
        is_overdue = days_remaining < 0
        color = SEVERITY_COLORS[days]

        with col_right:
            # Deadline result card
            border_color = "#f87171" if is_overdue else color
            bg_color = "rgba(248,113,113,0.08)" if is_overdue else "rgba(56,189,248,0.05)"

            st.markdown(
                f"""
                <div style="background:{bg_color};border:1.5px solid {border_color};
                            border-radius:12px;padding:24px 28px;margin-top:8px;">
                    <div style="font-size:11px;letter-spacing:1.5px;color:#64748b;
                                text-transform:uppercase;margin-bottom:8px;">Reporting Deadline</div>
                    <div style="font-size:32px;font-weight:800;color:{border_color};
                                letter-spacing:-0.5px;margin-bottom:4px;">
                        {deadline_date.strftime("%d %B %Y")}
                    </div>
                    <div style="font-size:13px;color:#94a3b8;margin-bottom:16px;">
                        Day 0 + {days} calendar days &nbsp;·&nbsp; {days_remaining:+d} days from today
                    </div>
                    <div style="display:flex;gap:16px;">
                        <div style="background:rgba(255,255,255,0.05);border-radius:8px;
                                    padding:10px 16px;text-align:center;">
                            <div style="font-size:20px;font-weight:700;color:{border_color};">{days}</div>
                            <div style="font-size:10px;color:#64748b;text-transform:uppercase;
                                        letter-spacing:1px;">Window (days)</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.05);border-radius:8px;
                                    padding:10px 16px;text-align:center;">
                            <div style="font-size:20px;font-weight:700;color:{'#f87171' if is_overdue else '#4ade80'};">
                                {"PAST DUE" if is_overdue else days_remaining}
                            </div>
                            <div style="font-size:10px;color:#64748b;text-transform:uppercase;
                                        letter-spacing:1px;">{"Status" if is_overdue else "Days left"}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Overdue alert
        if is_overdue:
            st.error(
                f"OVERDUE — Reporting deadline was {deadline_date.strftime('%d %B %Y')} "
                f"({abs(days_remaining)} days ago). Immediate action required under Article 87."
            )
        elif days_remaining <= 3:
            st.warning(
                f"URGENT — Only {days_remaining} day(s) remaining. Report must be submitted by "
                f"{deadline_date.strftime('%d %B %Y')}."
            )
        else:
            st.success(
                f"Deadline: {deadline_date.strftime('%d %B %Y')} — {days_remaining} days remaining."
            )

    # ══════════════════════════════════════════════════════════════════
    # TAB 2 — Incident Records
    # ══════════════════════════════════════════════════════════════════
    with tab2:
        df = load_incidents()

        if df.empty:
            st.info("No incident records found in data/incidents.csv.")
            return

        today = pd.Timestamp(date.today())

        # ── Summary metrics ──
        total = len(df)
        open_col = "durum" if "durum" in df.columns else None

        if open_col:
            open_count = len(df[df[open_col].isin(["Open", "Under Investigation"])])
            overdue_count = (
                len(df[(df["deadline"] < today) & (~df[open_col].isin(["Closed"]))])
                if "deadline" in df.columns
                else 0
            )
        else:
            open_count = 0
            overdue_count = 0

        m_col1, m_col2, m_col3 = st.columns(3)
        for col, label, value, accent in [
            (m_col1, "Total Incidents", total, "#38bdf8"),
            (m_col2, "Open / Under Investigation", open_count, "#fbbf24"),
            (m_col3, "Overdue Reports", overdue_count, "#f87171"),
        ]:
            with col:
                col.markdown(
                    f"""
                    <div style="background:#0a1018;border:1px solid rgba(255,255,255,0.07);
                                border-left:3px solid {accent};border-radius:10px;
                                padding:14px 18px;margin-bottom:8px;">
                        <div style="font-size:10px;letter-spacing:1.5px;color:#64748b;
                                    text-transform:uppercase;margin-bottom:4px;">{label}</div>
                        <div style="font-size:28px;font-weight:700;color:{accent};">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

        # ── Filters ──
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            search = st.text_input("Search Device / Incident ID", placeholder="e.g. INC-001", key="m2_search")
        with f_col2:
            status_opts = ["All"]
            if open_col and open_col in df.columns:
                status_opts += sorted(df[open_col].dropna().unique().tolist())
            status_filter = st.selectbox("Status Filter", status_opts, key="m2_status")

        filtered = df.copy()
        if search:
            mask = filtered.apply(
                lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1
            )
            filtered = filtered[mask]
        if status_filter != "All" and open_col:
            filtered = filtered[filtered[open_col] == status_filter]

        # ── Table ──
        st.markdown(
            f"<div style='font-size:12px;color:#64748b;margin-bottom:10px;'>"
            f"{len(filtered)} record(s) shown</div>",
            unsafe_allow_html=True,
        )

        def style_row(row):
            styles = [""] * len(row)
            if "deadline" in row.index and "durum" in row.index:
                dl = row["deadline"]
                status = row["durum"]
                if pd.notna(dl) and pd.Timestamp(dl) < today and status not in ["Closed"]:
                    styles = ["background-color: rgba(248,113,113,0.10); color: #f87171"] * len(row)
            return styles

        display_cols = [
            c for c in ["olay_id", "cihaz_id", "ciddiyet", "olay_tarihi", "deadline", "durum"]
            if c in filtered.columns
        ]

        if display_cols:
            display_df = filtered[display_cols].copy()
            for date_col in ["olay_tarihi", "deadline"]:
                if date_col in display_df.columns:
                    display_df[date_col] = display_df[date_col].apply(
                        lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
                    )

            col_rename = {
                "olay_id": "Incident ID",
                "cihaz_id": "Device ID",
                "ciddiyet": "Severity",
                "olay_tarihi": "Incident Date",
                "deadline": "Deadline",
                "durum": "Status",
            }
            display_df = display_df.rename(columns=col_rename)

            # Apply row styling
            styled = display_df.style.apply(
                lambda row: [
                    "background-color:rgba(248,113,113,0.10);color:#f87171"
                    if row.get("Status", "") not in ["Closed"]
                    and row.get("Deadline", "") != ""
                    and row.get("Deadline", "") < today.strftime("%Y-%m-%d")
                    else ""
                    for _ in row
                ],
                axis=1,
            )

            st.dataframe(
                styled,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(filtered, use_container_width=True, hide_index=True)

        st.markdown(
            "<div style='font-size:11px;color:#475569;margin-top:8px;'>"
            "Rows highlighted in red indicate overdue incidents (deadline passed, status not Closed)."
            "</div>",
            unsafe_allow_html=True,
        )