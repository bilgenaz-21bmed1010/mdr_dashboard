import streamlit as st
import pandas as pd
import re
from datetime import date

DEVICES_PATH = "data/devices.csv"
INCIDENTS_PATH = "data/incidents.csv"
FSCA_PATH = "data/fsca.csv"

DEVICE_CLASSIFICATIONS = ["Class I", "Class IIa", "Class IIb", "Class III"]
CATEGORIES = [
    "Infusion & Injection", "Diagnostic Imaging", "Patient Monitoring",
    "Surgical Instruments", "Implantable Devices", "In Vitro Diagnostics",
    "Respiratory", "Cardiovascular", "Neurology", "Orthopedic",
    "Rehabilitation & Mobility", "Wound Care", "Sterilization Equipment",
    "Laboratory Equipment", "Other",
]
STATUS_OPTIONS = ["Active", "Inactive", "Under Review", "Recalled"]
STATUS_COLORS = {
    "Active":       ("#d4edda", "#155724"),
    "Inactive":     ("#e2e3e5", "#383d41"),
    "Under Review": ("#fff3cd", "#856404"),
    "Recalled":     ("#f8d7da", "#721c24"),
}

MDR_ERRORS = {
    "udi":      "EU MDR Art. 27 — UDI is mandatory for device traceability. Format: GS1 Application Identifier (01) followed by device identifier.",
    "name":     "EU MDR Art. 2(65) — Device identification is required for registration.",
    "category": "EU MDR Art. 2(1) — Device category must be specified for PMS purposes.",
    "udi_dup":  "EU MDR Art. 27 — This UDI already exists in the registry. UDI codes must be unique.",
}

MDR_WARNINGS = {
    "lot":      "EU MDR Art. 27(3) — Lot/batch number is strongly recommended for traceability.",
    "recalled": "EU MDR Art. 83 — This device has Recalled status. Verify FSCA initiation in M3.",
    "udi_fmt":  "UDI format should follow GS1 standard: (01) + 14-digit device identifier. — Art. 27 & Annex VI Part C",
}


def load_devices():
    try:
        return pd.read_csv(DEVICES_PATH)
    except FileNotFoundError:
        return pd.DataFrame()

def save_devices(df):
    df.to_csv(DEVICES_PATH, index=False)

def load_incidents():
    try:
        return pd.read_csv(INCIDENTS_PATH)
    except FileNotFoundError:
        return pd.DataFrame()

def load_fsca():
    try:
        return pd.read_csv(FSCA_PATH)
    except FileNotFoundError:
        return pd.DataFrame()

def validate_udi(udi: str) -> bool:
    return bool(re.match(r"^\(01\)\d{14}", udi.strip()))

def mdr_error(msg, ref=None):
    ref_part = f"<br/><span style='font-size:11px;color:#fca5a5;'>{ref}</span>" if ref else ""
    st.markdown(
        f"<div style='color:#f87171;font-size:13px;border-left:3px solid #f87171;"
        f"padding:8px 12px;background:#1e0a0a;border-radius:4px;margin-bottom:8px;'>"
        f"<strong>{msg}</strong>{ref_part}</div>",
        unsafe_allow_html=True,
    )

def mdr_warning(msg):
    st.markdown(
        f"<div style='color:#fbbf24;font-size:12px;border-left:3px solid #fbbf24;"
        f"padding:6px 10px;background:#1a1200;border-radius:4px;margin-bottom:8px;'>"
        f"{msg}</div>",
        unsafe_allow_html=True,
    )

def style_status(val):
    bg, fg = STATUS_COLORS.get(val, ("#ffffff", "#000000"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:4px;font-weight:600;font-size:0.82em">{val}</span>'
    )


def render():
    st.markdown(
        '<p style="color:#38bdf8;font-size:12px;font-weight:600;'
        'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">'
        'EU MDR 2017/745</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h1 style='margin-top:0;margin-bottom:4px;'>Article 27 & Annex VI — UDI Device Registry</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#64748b;margin-top:0;margin-bottom:20px;'>"
        "Under EU MDR Article 27, healthcare institutions must maintain a registry of all medical devices "
        "in use, identified by their Unique Device Identifier (UDI). This module enables device registration, "
        "status management, and traceability across incident reporting and FSCA workflows.</p>",
        unsafe_allow_html=True,
    )

    df = load_devices()

    # ── KPI row ───────────────────────────────────────────────────────────
    if not df.empty and "durum" in df.columns:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Devices",  len(df))
        c2.metric("Active",         (df["durum"] == "Active").sum())
        c3.metric("Under Review",   (df["durum"] == "Under Review").sum())
        c4.metric("Recalled",       (df["durum"] == "Recalled").sum())

        if (df["durum"] == "Recalled").sum():
            st.warning(
                f"{(df['durum'] == 'Recalled').sum()} device(s) have Recalled status — "
                "verify FSCA initiation in M3 (Art. 83-87)."
            )

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Device Registry", "Register New Device", "Device Detail & Management"])

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1 — Registry Table
    # ══════════════════════════════════════════════════════════════════════
    with tab1:
        if df.empty:
            st.info("No devices registered yet. Use 'Register New Device' tab to add devices.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                device_names = ["All"] + sorted(df["isim"].dropna().unique().tolist())
                search_sel = st.selectbox("Search Device", device_names)
                search = "" if search_sel == "All" else search_sel
            with col2:
                risk_options = ["All", "Class I", "Class IIa", "Class IIb", "Class III"]
                risk_filter = st.selectbox("Device Classification", risk_options)
            with col3:
                categories = sorted(df["kategori"].dropna().unique().tolist())
                cat_filter = st.selectbox("Category", ["All"] + categories)
            with col4:
                status_filter = st.selectbox("Status", ["All"] + STATUS_OPTIONS)

            filtered = df.copy()
            if search:
                filtered = filtered[filtered["isim"] == search]
            if risk_filter != "All":
                filtered = filtered[filtered["risk_sinifi"] == risk_filter]
            if cat_filter != "All":
                filtered = filtered[filtered["kategori"] == cat_filter]
            if status_filter != "All":
                filtered = filtered[filtered["durum"] == status_filter]

            shown_cats = filtered["kategori"].nunique() if "kategori" in filtered.columns else 0
            st.caption(f"{len(filtered)} device(s) found across {shown_cats} categories")

            display_cols = ["udi_kodu", "isim", "kategori", "risk_sinifi", "durum", "kayit_tarihi"]
            display_cols = [c for c in display_cols if c in filtered.columns]
            col_labels = {
                "udi_kodu": "UDI Code", "isim": "Device Name", "kategori": "Category",
                "risk_sinifi": "Risk Class", "durum": "Status", "kayit_tarihi": "Registration Date",
            }

            header_cells = "".join(
                f"<th style='padding:8px 10px;text-align:left;background:#1e2a3a;"
                f"color:#90caf9;font-size:0.82em;text-transform:uppercase;letter-spacing:.05em'>"
                f"{col_labels.get(col, col)}</th>"
                for col in display_cols
            )
            html_rows = ""
            for _, row in filtered.iterrows():
                cells = ""
                for col in display_cols:
                    val = str(row.get(col, ""))
                    if col == "durum":
                        cells += f"<td style='padding:6px 10px'>{style_status(val)}</td>"
                    else:
                        cells += f"<td style='padding:6px 10px;font-size:0.88em;color:#cfd8dc'>{val}</td>"
                html_rows += f"<tr style='border-bottom:1px solid #1e2a3a'>{cells}</tr>"

            st.markdown(
                f"""<div style="overflow-x:auto;max-height:420px;overflow-y:auto;border-radius:8px;
                    border:1px solid #2e3c4f;margin-bottom:1rem">
                  <table style="width:100%;border-collapse:collapse;background:#0f1923">
                    <thead><tr>{header_cells}</tr></thead>
                    <tbody>{html_rows}</tbody>
                  </table></div>""",
                unsafe_allow_html=True,
            )


    # ══════════════════════════════════════════════════════════════════════
    # TAB 2 — Register New Device
    # ══════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### Register New Device")
        st.markdown(
            "<p style='color:#64748b;font-size:13px;'>Complete all required fields to register a new device. "
            "Upon registration, the device will be immediately available in M2 (Incident Reporting) and M3 (FSCA Panel).</p>",
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            new_name = st.text_input("Device Name *", placeholder="e.g. Fresenius Kabi Agilia SP", key="reg_name")
            new_udi  = st.text_input("UDI Code *", placeholder="e.g. (01)04044639988250(21)SN-IP-001", key="reg_udi")
            if new_udi and not validate_udi(new_udi):
                mdr_warning(MDR_WARNINGS["udi_fmt"])
            new_class = st.selectbox("Device Classification *", DEVICE_CLASSIFICATIONS, key="reg_class")
            new_cat   = st.selectbox("Category *", CATEGORIES, key="reg_cat")
            new_cat_other = ""
            if new_cat == "Other":
                new_cat_other = st.text_input("Please specify category *", placeholder="e.g. Dental Equipment", key="reg_cat_other")

        with col_b:
            new_status       = st.selectbox("Initial Status *", STATUS_OPTIONS, key="reg_status")
            if new_status == "Recalled":
                mdr_warning(MDR_WARNINGS["recalled"])
            new_lot          = st.text_input("Lot / Batch Number", placeholder="e.g. LOT-2024-001", key="reg_lot")
            if not new_lot:
                mdr_warning(MDR_WARNINGS["lot"])
            new_manufacturer = st.text_input("Manufacturer", placeholder="e.g. Fresenius Kabi AG", key="reg_mfr")
            new_reg_date     = st.date_input("Registration Date *", value=date.today(), key="reg_date")
            new_notes        = st.text_area("Notes (optional)", placeholder="Additional traceability notes...", height=80, key="reg_notes")

        if st.button("Register Device", type="primary", key="register_device_btn"):
            errs = []
            if not new_name.strip():
                errs.append(("Device Name is required.", MDR_ERRORS["name"]))
            if not new_udi.strip():
                errs.append(("UDI Code is required.", MDR_ERRORS["udi"]))
            elif not df.empty and "udi_kodu" in df.columns and new_udi.strip() in df["udi_kodu"].astype(str).values:
                errs.append(("This UDI already exists in the registry.", MDR_ERRORS["udi_dup"]))
            if new_cat == "Other" and not new_cat_other.strip():
                errs.append(("Please specify the category.", MDR_ERRORS["category"]))

            if errs:
                for title, ref in errs:
                    mdr_error(title, ref)
            else:
                df_existing = load_devices()
                if not df_existing.empty and "cihaz_id" in df_existing.columns:
                    nums = df_existing["cihaz_id"].astype(str).str.extract(r"(\d+)")[0].dropna().astype(int)
                    next_num = nums.max() + 1 if not nums.empty else 1
                else:
                    next_num = 1
                new_cihaz_id = f"CIH-{next_num:03d}"
                final_cat = f"Other: {new_cat_other.strip()}" if new_cat == "Other" else new_cat

                new_row = {
                    "cihaz_id":     new_cihaz_id,
                    "udi_kodu":     new_udi.strip(),
                    "isim":         new_name.strip(),
                    "kategori":     final_cat,
                    "risk_sinifi":  new_class,
                    "durum":        new_status,
                    "lot_no":       new_lot.strip(),
                    "uretici":      new_manufacturer.strip(),
                    "kayit_tarihi": new_reg_date.strftime("%Y-%m-%d"),
                    "notlar":       new_notes.strip(),
                }
                df_existing = pd.concat([df_existing, pd.DataFrame([new_row])], ignore_index=True) if not df_existing.empty else pd.DataFrame([new_row])
                save_devices(df_existing)
                st.success(
                    f"Device '{new_name.strip()}' registered as {new_cihaz_id}. "
                    f"UDI: {new_udi.strip()} — Now available in M2 and M3."
                )
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3 — Device Detail & Management
    # ══════════════════════════════════════════════════════════════════════
    with tab3:
        if df.empty:
            st.info("No devices registered yet.")
        else:
            st.markdown("#### Device Detail & Management")

            detail_options = df.apply(
                lambda r: f"{r.get('udi_kodu','?')} — {r.get('isim','?')}", axis=1
            ).tolist()
            selected_label = st.selectbox("Select a device to inspect:", detail_options, key="detail_sel")
            selected_idx   = detail_options.index(selected_label)
            device_row     = df.iloc[selected_idx]
            cihaz_id       = device_row.get("cihaz_id", "")
            status_val     = device_row.get("durum", "Unknown")
            bg, fg         = STATUS_COLORS.get(status_val, ("#1e293b", "#e2e8f0"))

            # Device info card
            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:16px;margin-bottom:16px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
                f'<div>'
                f'<div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">Device</div>'
                f'<div style="font-size:20px;color:#e2e8f0;font-weight:700;">{device_row.get("isim","—")}</div>'
                f'<div style="font-size:12px;color:#38bdf8;margin-top:2px;font-family:monospace;">{device_row.get("udi_kodu","—")}</div>'
                f'</div>'
                f'<span style="background:{bg};color:{fg};padding:4px 14px;border-radius:4px;font-size:13px;font-weight:600;">{status_val}</span>'
                f'</div>'
                f'<div style="display:flex;gap:32px;margin-top:12px;flex-wrap:wrap;">'
                f'<div><div style="font-size:11px;color:#64748b;">Classification</div><div style="color:#e2e8f0;">{device_row.get("risk_sinifi","—")}</div></div>'
                f'<div><div style="font-size:11px;color:#64748b;">Category</div><div style="color:#e2e8f0;">{device_row.get("kategori","—")}</div></div>'
                f'<div><div style="font-size:11px;color:#64748b;">Manufacturer</div><div style="color:#e2e8f0;">{device_row.get("uretici","—")}</div></div>'
                f'<div><div style="font-size:11px;color:#64748b;">Registered</div><div style="color:#e2e8f0;">{device_row.get("kayit_tarihi","—")}</div></div>'
                f'<div><div style="font-size:11px;color:#64748b;">Lot / Batch</div><div style="color:#e2e8f0;">{device_row.get("lot_no","—") or "—"}</div></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            # EUDAMED mock check
            udi_val    = str(device_row.get("udi_kodu", ""))
            eudamed_ok = validate_udi(udi_val)
            e_color    = "#4ade80" if eudamed_ok else "#f87171"
            e_label    = "Registered" if eudamed_ok else "Not Verified"
            e_msg      = "UDI format compliant — device traceable in EUDAMED. (Art. 27/4)" if eudamed_ok else "UDI format does not meet GS1 standard — EUDAMED registration may be incomplete. (Art. 27/4)"
            st.markdown(
                f'<div style="background:#0f172a;border:1px solid {e_color}44;border-left:3px solid {e_color};'
                f'border-radius:6px;padding:10px 14px;margin-bottom:12px;">'
                f'<span style="color:{e_color};font-weight:600;font-size:13px;">EUDAMED Status: {e_label}</span>'
                f'<span style="color:#64748b;font-size:12px;margin-left:12px;">{e_msg}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Linked Incidents
            incidents_df = load_incidents()
            st.markdown("**Linked Incidents** (M2 — Art. 87)")
            if not incidents_df.empty and "cihaz_id" in incidents_df.columns:
                linked_inc = incidents_df[incidents_df["cihaz_id"] == cihaz_id]
                if linked_inc.empty:
                    st.caption("No incidents recorded for this device.")
                else:
                    if "durum" in linked_inc.columns:
                        open_inc = linked_inc[linked_inc["durum"].isin(["Open", "Under Investigation", "Overdue"])]
                        if not open_inc.empty:
                            st.warning(f"{len(open_inc)} open/overdue incident(s) linked to this device.")
                    show_cols = [c for c in ["olay_id", "ciddiyet", "olay_tarihi", "durum"] if c in linked_inc.columns]
                    st.dataframe(linked_inc[show_cols].rename(columns={
                        "olay_id": "Incident ID", "ciddiyet": "Severity",
                        "olay_tarihi": "Date", "durum": "Status"
                    }), use_container_width=True, hide_index=True)
            else:
                st.caption("No incident data available.")

            # Linked FSCAs
            fsca_df = load_fsca()
            st.markdown("**Linked FSCAs** (M3 — Art. 83-87)")
            if not fsca_df.empty and "cihaz_id" in fsca_df.columns:
                linked_fsca = fsca_df[fsca_df["cihaz_id"] == cihaz_id]
                if linked_fsca.empty:
                    st.caption("No FSCAs linked to this device.")
                else:
                    if "durum" in linked_fsca.columns:
                        active_fsca = linked_fsca[linked_fsca["durum"] != "Closed"]
                        if not active_fsca.empty:
                            st.warning(f"{len(active_fsca)} active FSCA(s) linked to this device.")
                    show_fsca = [c for c in ["fsca_id", "mevcut_asama", "durum", "fsn_deadline"] if c in linked_fsca.columns]
                    st.dataframe(linked_fsca[show_fsca].rename(columns={
                        "fsca_id": "FSCA ID", "mevcut_asama": "Stage",
                        "durum": "Status", "fsn_deadline": "FSN Deadline"
                    }), use_container_width=True, hide_index=True)
            else:
                st.caption("No FSCA data available.")

            # Status Update
            st.markdown("---")
            st.markdown("**Update Device Status** (Art. 27/3)")
            with st.form("status_update_form"):
                new_status_upd = st.selectbox(
                    "New Status", STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(status_val) if status_val in STATUS_OPTIONS else 0,
                )
                upd_notes  = st.text_input("Reason for status change *", placeholder="e.g. Manufacturer recall notice received")
                upd_submit = st.form_submit_button("Update Status", use_container_width=True)

            if upd_submit:
                if not upd_notes.strip():
                    mdr_error(
                        "Reason for status change is required.",
                        "EU MDR Art. 27/3 — All status changes must be documented for traceability purposes."
                    )
                elif new_status_upd == status_val:
                    st.info("Status unchanged.")
                else:
                    df_updated = load_devices()
                    idx = df_updated[df_updated["cihaz_id"] == cihaz_id].index
                    if len(idx):
                        df_updated.at[idx[0], "durum"]  = new_status_upd
                        df_updated.at[idx[0], "notlar"] = upd_notes.strip()
                        save_devices(df_updated)
                        st.success(f"Status updated to '{new_status_upd}' for {device_row.get('isim','device')}.")
                        if new_status_upd == "Recalled":
                            st.warning("Device marked as Recalled — please initiate an FSCA in M3 if not already done. (Art. 83)")
                        st.rerun()