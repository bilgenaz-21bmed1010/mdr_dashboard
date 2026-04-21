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
    10: "#f87171",
    15: "#fb923c",
    30: "#fbbf24",
    90: "#60a5fa",
}

INCIDENT_TYPES = [
    "Device Malfunction",
    "Software Error",
    "Labeling Error",
    "User Error",
    "Unexpected Side Effect",
    "Sterility Failure",
    "Electrical Hazard",
    "Mechanical Failure",
    "Biocompatibility Failure",
    "Battery / Power Failure",
    "Alarm Failure",
    "Connectivity / Cybersecurity Incident",
    "Packaging Defect",
    "Calibration Error",
    "Counterfeit Device",
    "Other",
]

DEVICE_CLASSIFICATIONS = ["Class I", "Class IIa", "Class IIb", "Class III"]

CATEGORIES = [
    "Infusion & Injection", "Diagnostic Imaging", "Patient Monitoring",
    "Surgical Instruments", "Implantable Devices", "In Vitro Diagnostics",
    "Respiratory", "Cardiovascular", "Neurology", "Orthopedic",
    "Rehabilitation & Mobility", "Wound Care", "Sterilization Equipment",
    "Laboratory Equipment", "Other",
]

MDR_ERRORS = {
    "device":           "This field is mandatory under EU MDR Article 2(65) — a serious incident must include device identification.",
    "udi":              "This field is mandatory under EU MDR Article 27 — UDI is required for device traceability.",
    "incident_date":    "This field is mandatory under EU MDR Article 87(1) — the reporting timeline starts from the date of awareness.",
    "future_date":      "Invalid date under EU MDR Article 87(1) — the incident date cannot be a future date.",
    "severity":         "This field is mandatory under EU MDR Article 87(1a/1b) — severity determines the reporting window.",
    "incident_type":    "This field is mandatory under EU MDR Article 2(65) — the nature of the incident must be identified.",
    "description":      "This field is mandatory under EU MDR Article 87(4) — the initial report must describe the incident.",
    "reporter":         "This field is mandatory under EU MDR Article 87(1) — the manufacturer is responsible for submission.",
    "new_device_name":  "This field is mandatory under EU MDR Article 2(65) — device identification is required.",
    "new_device_udi":   "This field is mandatory under EU MDR Article 27 — UDI is required for device traceability.",
    "other_type":       "This field is mandatory under EU MDR Article 2(65) — the nature of the incident must be identified.",
    "other_category":   "Please specify the category to ensure accurate device classification.",
}

MDR_WARNINGS = {
    "lot_number": "Strongly recommended under EU MDR Article 27(3) — lot/batch number improves device traceability.",
}


def mdr_error(msg):
    st.markdown(
        f"<div style='color:#f87171;font-size:12px;margin-top:2px;margin-bottom:8px;'>"
        f"{msg}</div>",
        unsafe_allow_html=True,
    )


def mdr_warning(msg):
    st.markdown(
        f"<div style='color:#fbbf24;font-size:12px;margin-top:2px;margin-bottom:8px;'>"
        f"{msg}</div>",
        unsafe_allow_html=True,
    )


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


def save_new_device(name, udi_code, classification, category):
    df = load_devices()
    if not df.empty and "cihaz_id" in df.columns:
        nums = df["cihaz_id"].astype(str).str.extract(r"(\d+)")[0].dropna().astype(int)
        next_num = nums.max() + 1 if not nums.empty else 1
    else:
        next_num = 1
    new_cihaz_id = f"CIH-{next_num:03d}"
    new_row = {
        "cihaz_id": new_cihaz_id,
        "udi_kodu": udi_code,
        "isim": name,
        "risk_sinifi": classification,
        "kategori": category,
        "durum": "Active",
        "kayit_tarihi": date.today().strftime("%Y-%m-%d"),
    }
    for col in df.columns:
        if col not in new_row:
            new_row[col] = ""
    new_df = pd.DataFrame([new_row])
    combined = pd.concat([df, new_df], ignore_index=True) if not df.empty else new_df
    combined.to_csv(DEVICES_PATH, index=False)
    return new_cihaz_id


def render():
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

    st.markdown(
        """
        <div style="background:#0a1018;border:1px solid rgba(255,255,255,0.07);border-radius:10px;
                    padding:16px 20px;margin-bottom:28px;">
            <div style="font-size:11px;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;
                        margin-bottom:12px;">Mandatory Reporting Windows</div>
            <div style="display:flex;gap:24px;flex-wrap:wrap;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="background:#f87171;border-radius:4px;padding:2px 8px;font-size:12px;font-weight:700;color:#0f1922;">10 days</span>
                    <span style="font-size:12px;color:#94a3b8;">Public health threat (Art. 87/1a)</span>
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="background:#fb923c;border-radius:4px;padding:2px 8px;font-size:12px;font-weight:700;color:#0f1922;">15 days</span>
                    <span style="font-size:12px;color:#94a3b8;">Death / unexpected deterioration (Art. 87/1b)</span>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="background:#fbbf24;border-radius:4px;padding:2px 8px;font-size:12px;font-weight:700;color:#0f1922;">30 days</span>
                    <span style="font-size:12px;color:#94a3b8;">Expected deterioration (Art. 87/1b)</span>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="background:#60a5fa;border-radius:4px;padding:2px 8px;font-size:12px;font-weight:700;color:#0f1922;">90 days</span>
                    <span style="font-size:12px;color:#94a3b8;">Trend reporting (Art. 88)</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Deadline Calculator", "Incident Records", "Report New Incident"])

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
            severity_label = st.selectbox("Severity Classification", options=list(SEVERITY_OPTIONS.keys()), key="m2_severity")
            incident_date = st.date_input("Incident Date", value=date.today(), key="m2_incident_date")

        days = SEVERITY_OPTIONS[severity_label]
        deadline_date = incident_date + timedelta(days=days)
        today = date.today()
        days_remaining = (deadline_date - today).days
        is_overdue = days_remaining < 0
        color = SEVERITY_COLORS[days]

        with col_right:
            border_color = "#f87171" if is_overdue else color
            bg_color = "rgba(248,113,113,0.08)" if is_overdue else "rgba(56,189,248,0.05)"
            st.markdown(
                f"""
                <div style="background:{bg_color};border:1.5px solid {border_color};border-radius:12px;padding:24px 28px;margin-top:8px;">
                    <div style="font-size:11px;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;margin-bottom:8px;">Reporting Deadline</div>
                    <div style="font-size:32px;font-weight:800;color:{border_color};letter-spacing:-0.5px;margin-bottom:4px;">
                        {deadline_date.strftime("%d %B %Y")}
                    </div>
                    <div style="font-size:13px;color:#94a3b8;margin-bottom:16px;">
                        Day 0 + {days} calendar days &nbsp;·&nbsp; {days_remaining:+d} days from today
                    </div>
                    <div style="display:flex;gap:16px;">
                        <div style="background:rgba(255,255,255,0.05);border-radius:8px;padding:10px 16px;text-align:center;">
                            <div style="font-size:20px;font-weight:700;color:{border_color};">{days}</div>
                            <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Window (days)</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.05);border-radius:8px;padding:10px 16px;text-align:center;">
                            <div style="font-size:20px;font-weight:700;color:{'#f87171' if is_overdue else '#4ade80'};">
                                {"PAST DUE" if is_overdue else days_remaining}
                            </div>
                            <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">{"Status" if is_overdue else "Days left"}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if is_overdue:
            st.error(f"OVERDUE — Reporting deadline was {deadline_date.strftime('%d %B %Y')} ({abs(days_remaining)} days ago). Immediate action required under Article 87.")
        elif days_remaining <= 3:
            st.warning(f"URGENT — Only {days_remaining} day(s) remaining. Report must be submitted by {deadline_date.strftime('%d %B %Y')}.")
        else:
            st.success(f"Deadline: {deadline_date.strftime('%d %B %Y')} — {days_remaining} days remaining.")

    # ══════════════════════════════════════════════════════════════════
    # TAB 2 — Incident Records
    # ══════════════════════════════════════════════════════════════════
    with tab2:
        df = load_incidents()
        if df.empty:
            st.info("No incident records found in data/incidents.csv.")
            return

        today_ts = pd.Timestamp(date.today())
        total = len(df)
        open_col = "durum" if "durum" in df.columns else None

        if open_col:
            open_count = len(df[df[open_col].isin(["Open", "Under Investigation"])])
            overdue_count = (
                len(df[(df["deadline"] < today_ts) & (~df[open_col].isin(["Closed"]))])
                if "deadline" in df.columns else 0
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
                                border-left:3px solid {accent};border-radius:10px;padding:14px 18px;margin-bottom:8px;">
                        <div style="font-size:10px;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;margin-bottom:4px;">{label}</div>
                        <div style="font-size:28px;font-weight:700;color:{accent};">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

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
            mask = filtered.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            filtered = filtered[mask]
        if status_filter != "All" and open_col:
            filtered = filtered[filtered[open_col] == status_filter]

        st.markdown(f"<div style='font-size:12px;color:#64748b;margin-bottom:10px;'>{len(filtered)} record(s) shown</div>", unsafe_allow_html=True)

        display_cols = [c for c in ["olay_id", "cihaz_id", "ciddiyet", "olay_tarihi", "deadline", "durum"] if c in filtered.columns]
        if display_cols:
            display_df = filtered[display_cols].copy()
            for date_col in ["olay_tarihi", "deadline"]:
                if date_col in display_df.columns:
                    display_df[date_col] = display_df[date_col].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "")
            col_rename = {
                "olay_id": "Incident ID", "cihaz_id": "Device ID",
                "ciddiyet": "Severity", "olay_tarihi": "Incident Date",
                "deadline": "Deadline", "durum": "Status",
            }
            display_df = display_df.rename(columns=col_rename)
            styled = display_df.style.apply(
                lambda row: [
                    "background-color:rgba(248,113,113,0.10);color:#f87171"
                    if row.get("Status", "") not in ["Closed"]
                    and row.get("Deadline", "") != ""
                    and row.get("Deadline", "") < today_ts.strftime("%Y-%m-%d")
                    else "" for _ in row
                ], axis=1,
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)
        else:
            st.dataframe(filtered, use_container_width=True, hide_index=True)

        st.markdown(
            "<div style='font-size:11px;color:#475569;margin-top:8px;'>"
            "Rows highlighted in red indicate overdue incidents (deadline passed, status not Closed)."
            "</div>",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════
    # TAB 3 — Report New Incident
    # ══════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown(
            "<div style='font-size:14px;color:#94a3b8;margin-bottom:24px;'>"
            "Complete all required fields to register a new incident. "
            "The reporting deadline will be calculated automatically based on severity."
            "</div>",
            unsafe_allow_html=True,
        )

        submitted = st.session_state.get("m2_submitted", False)
        devices_df = load_devices()

        NEW_DEVICE_KEY = "New Device (not in system)"
        if not devices_df.empty and "isim" in devices_df.columns and "cihaz_id" in devices_df.columns:
            device_options = {NEW_DEVICE_KEY: "__new__"}
            device_options.update({
                f"{row['isim']} ({row['cihaz_id']})": row["cihaz_id"]
                for _, row in devices_df.iterrows()
            })
        else:
            device_options = {NEW_DEVICE_KEY: "__new__"}

        col1, col2 = st.columns(2)

        with col1:
            selected_device_label = st.selectbox("Device *", options=list(device_options.keys()), key="form_device")

            # Auto-fill UDI for existing device
            if selected_device_label != NEW_DEVICE_KEY and not devices_df.empty:
                selected_cihaz_id = device_options[selected_device_label]
                device_row = devices_df[devices_df["cihaz_id"].astype(str) == str(selected_cihaz_id)]
                if not device_row.empty and "udi_kodu" in device_row.columns:
                    auto_udi = str(device_row.iloc[0]["udi_kodu"])
                else:
                    auto_udi = ""
                st.markdown(
                    f"<div style='font-size:12px;color:#64748b;margin-top:-8px;margin-bottom:12px;'>"
                    f"UDI Code (Art. 27): <span style='color:#38bdf8;'>{auto_udi if auto_udi else 'Not available'}</span></div>",
                    unsafe_allow_html=True,
                )

            incident_type = st.selectbox("Incident Type *", options=INCIDENT_TYPES, key="form_type")
            if incident_type == "Other":
                other_description = st.text_input("Please specify *", placeholder="Describe the incident type...", key="form_other_type")
                if submitted and not other_description.strip():
                    mdr_error(MDR_ERRORS["other_type"])
            else:
                other_description = ""

            form_severity = st.selectbox("Severity Classification *", options=list(SEVERITY_OPTIONS.keys()), key="form_severity")

        with col2:
            form_date = st.date_input("Incident Date *", value=date.today(), key="form_date", max_value=date.today())
            if form_date > date.today():
                mdr_error(MDR_ERRORS["future_date"])

            reporter = st.text_input("Reported By *", placeholder="Full name of the reporter", key="form_reporter")
            if submitted and not reporter.strip():
                mdr_error(MDR_ERRORS["reporter"])

            lot_number = st.text_input("Lot / Batch Number", placeholder="e.g. LOT-2024-001", key="form_lot")
            if not lot_number.strip():
                mdr_warning(MDR_WARNINGS["lot_number"])

            form_status = st.selectbox("Initial Status", options=["Open", "Under Investigation", "Closed"], key="form_status")

        # ── New Device fields ──────────────────────────────────────────
        new_device_name = ""
        new_device_udi = ""
        new_device_classification = DEVICE_CLASSIFICATIONS[0]
        new_device_category = CATEGORIES[0]
        new_device_category_other = ""

        if selected_device_label == NEW_DEVICE_KEY:
            st.markdown(
                """
                <div style="background:#0a1018;border:1px solid #38bdf8;border-radius:10px;
                            padding:16px 20px;margin:12px 0;">
                    <div style="font-size:11px;letter-spacing:1.5px;color:#38bdf8;
                                text-transform:uppercase;margin-bottom:12px;">New Device Registration</div>
                """,
                unsafe_allow_html=True,
            )
            nd_col1, nd_col2 = st.columns(2)
            with nd_col1:
                new_device_name = st.text_input("Device Name *", placeholder="e.g. Fresenius Kabi Agilia SP", key="new_dev_name")
                if submitted and not new_device_name.strip():
                    mdr_error(MDR_ERRORS["new_device_name"])

                new_device_classification = st.selectbox("Device Classification *", options=DEVICE_CLASSIFICATIONS, key="new_dev_class")

            with nd_col2:
                new_device_udi = st.text_input("UDI Code *", placeholder="e.g. UDI-DI-0123456789", key="new_dev_udi")
                if submitted and not new_device_udi.strip():
                    mdr_error(MDR_ERRORS["new_device_udi"])

                new_device_category = st.selectbox("Category *", options=CATEGORIES, key="new_dev_cat")
                if new_device_category == "Other":
                    new_device_category_other = st.text_input("Please specify category *", placeholder="e.g. Dental Equipment", key="new_dev_cat_other")
                    if submitted and not new_device_category_other.strip():
                        mdr_error(MDR_ERRORS["other_category"])

            st.markdown("</div>", unsafe_allow_html=True)

        # ── Description ────────────────────────────────────────────────
        description = st.text_area(
            "Incident Description *",
            placeholder="Describe the incident in detail — what happened, where, and what was the impact on the patient or user...",
            height=120,
            key="form_description",
        )
        if submitted and not description.strip():
            mdr_error(MDR_ERRORS["description"])

        # ── Live deadline preview ──────────────────────────────────────
        form_days = SEVERITY_OPTIONS[form_severity]
        form_deadline = form_date + timedelta(days=form_days)
        form_days_left = (form_deadline - date.today()).days
        dl_color = SEVERITY_COLORS[form_days]

        st.markdown(
            f"""
            <div style="background:#0a1018;border:1px solid rgba(255,255,255,0.07);
                        border-left:3px solid {dl_color};border-radius:10px;
                        padding:12px 18px;margin:8px 0 20px 0;display:flex;align-items:center;gap:16px;">
                <div>
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:2px;">Calculated Deadline</div>
                    <div style="font-size:18px;font-weight:700;color:{dl_color};">{form_deadline.strftime("%d %B %Y")}</div>
                </div>
                <div style="color:#475569;">·</div>
                <div style="font-size:13px;color:#94a3b8;">
                    {form_days}-day window &nbsp;·&nbsp;
                    <span style="color:{'#f87171' if form_days_left < 0 else '#4ade80'};">
                        {abs(form_days_left)} days {'overdue' if form_days_left < 0 else 'remaining'}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Save Incident Report", type="primary", key="form_save"):
            st.session_state["m2_submitted"] = True

            errors = []
            if not reporter.strip():
                errors.append("reporter")
            if not description.strip():
                errors.append("description")
            if form_date > date.today():
                errors.append("future_date")
            if incident_type == "Other" and not other_description.strip():
                errors.append("other_type")
            if selected_device_label == NEW_DEVICE_KEY:
                if not new_device_name.strip():
                    errors.append("new_device_name")
                if not new_device_udi.strip():
                    errors.append("new_device_udi")
                elif not devices_df.empty and "udi_kodu" in devices_df.columns:
                    if new_device_udi.strip() in devices_df["udi_kodu"].astype(str).values:
                        st.warning(f"UDI Code '{new_device_udi}' already exists in the system.")
                        errors.append("udi_duplicate")
                if new_device_category == "Other" and not new_device_category_other.strip():
                    errors.append("other_category")

            if errors:
                st.rerun()
            else:
                st.session_state["m2_submitted"] = False

                if selected_device_label == NEW_DEVICE_KEY:
                    final_category = (
                        f"Other: {new_device_category_other.strip()}"
                        if new_device_category == "Other" else new_device_category
                    )
                    final_device_id = save_new_device(
                        name=new_device_name.strip(),
                        udi_code=new_device_udi.strip(),
                        classification=new_device_classification,
                        category=final_category,
                    )
                    st.info(f"New device '{new_device_name.strip()}' registered successfully.")
                else:
                    final_device_id = device_options[selected_device_label]

                final_incident_type = (
                    f"Other: {other_description.strip()}" if incident_type == "Other" else incident_type
                )

                existing_df = load_incidents()
                if not existing_df.empty and "olay_id" in existing_df.columns:
                    nums = existing_df["olay_id"].astype(str).str.extract(r"(\d+)")[0].dropna().astype(int)
                    next_num = nums.max() + 1 if not nums.empty else 1
                else:
                    next_num = 1
                new_id = f"INC-{next_num:03d}"

                new_row = {
                    "olay_id": new_id,
                    "cihaz_id": final_device_id,
                    "ciddiyet": final_incident_type,
                    "olay_tarihi": form_date.strftime("%Y-%m-%d"),
                    "deadline": form_deadline.strftime("%Y-%m-%d"),
                    "durum": form_status,
                    "aciklama": description.strip(),
                    "raporlayan": reporter.strip(),
                    "lot_no": lot_number.strip(),
                    "severity_class": form_severity,
                }

                new_df = pd.DataFrame([new_row])
                combined = pd.concat([existing_df, new_df], ignore_index=True) if not existing_df.empty else new_df
                combined.to_csv(INCIDENTS_PATH, index=False)

                st.success(
                    f"Incident {new_id} saved successfully. "
                    f"Reporting deadline: {form_deadline.strftime('%d %B %Y')}."
                )
                st.rerun()