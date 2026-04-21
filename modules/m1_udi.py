import streamlit as st
import pandas as pd

def render():
    st.title(" M1 — UDI Device Registry")
    st.markdown("**EU MDR 2017/745 | Article 27 & Annex VI — UDI Traceability**")

    try:
        df = pd.read_csv("data/devices.csv")
    except FileNotFoundError:
        st.error("data/devices.csv not found.")
        return

    # ── Filters ──────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        search = st.text_input("🔍 Search Device", "")
    with col2:
        risk_options = ["All"] + sorted(df["risk_sinifi"].dropna().unique().tolist())
        risk_filter = st.selectbox("Device Classification", risk_options)
    with col3:
        categories = sorted(df["kategori"].dropna().unique().tolist())
        cat_filter = st.selectbox(f"Category (35 listed)", ["All"] + categories)
    with col4:
        status_options = ["All", "Active", "Inactive", "Under Review", "Recalled"]
        status_filter = st.selectbox("Status", status_options)

    # ── Apply Filters ─────────────────────────────────────────────────────
    filtered = df.copy()

    if search:
        filtered = filtered[
            filtered.apply(lambda row: search.lower() in str(row).lower(), axis=1)
        ]
    if risk_filter != "All":
        filtered = filtered[filtered["risk_sinifi"] == risk_filter]
    if cat_filter != "All":
        filtered = filtered[filtered["kategori"] == cat_filter]
    if status_filter != "All":
        filtered = filtered[filtered["durum"] == status_filter]

    shown_cats = filtered["kategori"].nunique()
    st.markdown(f"**{len(filtered)} device(s) found** across **{shown_cats} categories listed**")

    # ── Status color coding ───────────────────────────────────────────────
    STATUS_COLORS = {
        "Active":       ("#d4edda", "#155724"),
        "Inactive":     ("#e2e3e5", "#383d41"),
        "Under Review": ("#fff3cd", "#856404"),
        "Recalled":     ("#f8d7da", "#721c24"),
    }

    def style_status(val):
        bg, fg = STATUS_COLORS.get(val, ("#ffffff", "#000000"))
        return (
            f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:4px;font-weight:600;font-size:0.82em">{val}</span>'
        )

    display_cols = ["udi_kodu", "isim", "kategori", "risk_sinifi", "durum", "kayit_tarihi"]
    display_cols = [c for c in display_cols if c in filtered.columns]

    col_labels = {
        "udi_kodu": "UDI Code",
        "isim": "Device Name",
        "kategori": "Category",
        "risk_sinifi": "Risk Class",
        "durum": "Status",
        "kayit_tarihi": "Registration Date",
    }

    header_cells = "".join(
        f"<th style='padding:8px 10px;text-align:left;background:#1e2a3a;"
        f"color:#90caf9;font-size:0.82em;text-transform:uppercase;letter-spacing:.05em'>"
        f"{col_labels.get(col, col)}</th>"
        for col in display_cols
    )

    html_rows = ""
    for _, row in filtered.head(100).iterrows():
        cells = ""
        for col in display_cols:
            val = str(row.get(col, ""))
            if col == "durum":
                cells += f"<td style='padding:6px 10px'>{style_status(val)}</td>"
            else:
                cells += f"<td style='padding:6px 10px;font-size:0.88em;color:#cfd8dc'>{val}</td>"
        html_rows += f"<tr style='border-bottom:1px solid #1e2a3a'>{cells}</tr>"

    html_table = f"""
    <div style="overflow-x:auto;max-height:420px;overflow-y:auto;border-radius:8px;
                border:1px solid #2e3c4f;margin-bottom:1rem">
      <table style="width:100%;border-collapse:collapse;background:#0f1923">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{html_rows}</tbody>
      </table>
    </div>
    """
    st.markdown(html_table, unsafe_allow_html=True)

    if len(filtered) > 100:
        st.caption(f"Showing first 100 of {len(filtered)} results.")

    # ── Device Detail Panel ───────────────────────────────────────────────
    st.markdown("---")
    st.subheader(" Device Detail Panel")

    detail_options = filtered.apply(
        lambda r: f"{r.get('udi_kodu','?')} — {r.get('isim','?')}", axis=1
    ).tolist()

    if not detail_options:
        st.info("No devices match current filters.")
        return

    selected_label = st.selectbox("Select a device to inspect:", detail_options)
    selected_idx = detail_options.index(selected_label)
    device_row = filtered.iloc[selected_idx]

    with st.expander(" Device Details", expanded=True):
        c1, c2 = st.columns(2)
        status_val = device_row.get("durum", "Unknown")
        bg, fg = STATUS_COLORS.get(status_val, ("#ffffff", "#000000"))
        status_badge = (
            f'<span style="background:{bg};color:{fg};padding:3px 10px;'
            f'border-radius:5px;font-weight:700">{status_val}</span>'
        )
        with c1:
            st.markdown(f"**UDI Code:** `{device_row.get('udi_kodu', 'N/A')}`")
            st.markdown(f"**Device Name:** {device_row.get('isim', 'N/A')}")
            st.markdown(f"**Category:** {device_row.get('kategori', 'N/A')}")
        with c2:
            st.markdown(f"**Risk Class:** {device_row.get('risk_sinifi', 'N/A')}")
            st.markdown(f"**Registration Date:** {device_row.get('kayit_tarihi', 'N/A')}")
            st.markdown(f"**Status:** {status_badge}", unsafe_allow_html=True)

    # ── Category Summary ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(" Category Summary")

    summary = (
        df.groupby("kategori")
        .agg(
            Total=("udi_kodu", "count"),
            Active=("durum", lambda x: (x == "Active").sum()),
            Recalled=("durum", lambda x: (x == "Recalled").sum()),
        )
        .reset_index()
        .rename(columns={"kategori": "Category"})
        .sort_values("Total", ascending=False)
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)