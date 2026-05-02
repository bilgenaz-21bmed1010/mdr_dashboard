import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "gap_analysis.csv")

SCORE_LABELS = {4: "Critical", 3: "High", 2: "Contributing", 1: "Indirect", 0: "—"}

GAP_MDR = {
    "Incident Reporting Channel":    "Art. 87",
    "FSCA Acknowledgement Loop":     "Art. 90-91",
    "UDI Point-of-Care Integration": "Art. 27",
    "PMCF Data Contribution":        "Annex XIV",
    "PMS Data Intake Formalisation": "Art. 83-84",
    "Transparency / Feedback":       "Art. 89",
    "EUDAMED Operationalisation":    "Art. 92",
}

GAP_OVERALL = {
    "Incident Reporting Channel":    "High",
    "FSCA Acknowledgement Loop":     "Critical",
    "UDI Point-of-Care Integration": "High",
    "PMCF Data Contribution":        "Medium",
    "PMS Data Intake Formalisation": "High",
    "Transparency / Feedback":       "Medium",
    "EUDAMED Operationalisation":    "High",
}

SCENARIOS = {
    "adverse_event": {
        "short":   "S1 — Adverse Event Reporting",
        "article": "MDR Art. 87 & 89",
        "problem": (
            "When a medical device causes or may cause patient harm, "
            "both the hospital and the manufacturer must report the incident. "
            "However, there is no standardised channel for hospitals to notify manufacturers — "
            "reports are sent via informal emails or phone calls, with no mandatory acknowledgement. "
            "Hospitals also receive no feedback on investigation outcomes, which discourages future reporting."
        ),
        "key_gap": "No standard MIR template or reporting channel for hospitals.",
    },
    "fsca": {
        "short":   "S2 — FSCA Workflow",
        "article": "MDR Art. 90 & 91",
        "problem": (
            "When a manufacturer identifies a safety issue in devices already on the market, "
            "they must issue a Field Safety Notice (FSN) and execute corrective actions. "
            "Hospitals are expected to implement these actions — but MDR defines no mandatory "
            "acknowledgement mechanism. Manufacturers cannot confirm whether hospitals have "
            "actually received or acted on the FSN, creating an unverifiable safety loop."
        ),
        "key_gap": "No mandatory digital acknowledgement from hospital to manufacturer.",
    },
    "pms_pmcf": {
        "short":   "S3 — PMS / PMCF Data Collection",
        "article": "MDR Art. 83–86 & Annex XIV",
        "problem": (
            "Manufacturers are required to continuously collect real-world performance data "
            "from hospitals under their Post-Market Surveillance (PMS) obligations. "
            "Hospitals are the primary source of this data — yet they are not formally recognised "
            "as active PMS stakeholders. Data flows through informal channels, UDI is rarely "
            "captured at point-of-care, and hospitals receive no transparency on how their "
            "reports influence manufacturer risk decisions."
        ),
        "key_gap": "Hospitals contribute PMS data informally with no structured framework or feedback.",
    },
}

SCORE_COLOR_MAP = {
    "Critical":     "background-color:#e74c3c;color:white;font-weight:700;text-align:center;",
    "High":         "background-color:#e67e22;color:white;font-weight:700;text-align:center;",
    "Contributing": "background-color:#b7950b;color:white;font-weight:700;text-align:center;",
    "Medium":       "background-color:#f1c40f;color:#1a1a1a;font-weight:700;text-align:center;",
    "Indirect":     "background-color:#27ae60;color:white;font-weight:700;text-align:center;",
    "—":            "color:#64748b;text-align:center;",
}


def color_cell(val):
    return SCORE_COLOR_MAP.get(val, "")


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


def show():
    st.markdown(
        '<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.12em;'
        'color:#2563EB;text-transform:uppercase;margin-bottom:0.25rem;">Module M4</div>',
        unsafe_allow_html=True,
    )
    st.title("Gap Analysis")
    st.caption("EU MDR 2017/745 · WP3-Derived Findings · Hospital-Manufacturer Interface Compliance Gaps")

    try:
        df = load_data()
    except FileNotFoundError:
        st.error("gap_analysis.csv not found. Place it in the data/ folder.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total   = len(df["gap_tipi"].unique())
    worst_k = df.groupby("senaryo")["ciddiyet_puani"].sum().idxmax()
    worst_s = SCENARIOS[worst_k]["short"]

    c1, c2 = st.columns(2)
    c1.metric("Gap Areas Identified", total,   help="Distinct compliance gap areas from WP3")
    c2.metric("Most Affected Scenario", worst_s)

    st.markdown("---")

    # ── per-scenario cards ────────────────────────────────────────────────────
    st.subheader("Scenario Overview")
    st.caption("Three critical hospital-manufacturer interface points analysed under MDR 2017/745.")

    for key, info in SCENARIOS.items():
        with st.container():
            st.markdown(f"### {info['short']}")
            st.markdown(
                f'<span style="font-size:0.78rem;color:#2563EB;font-weight:600;">'
                f'{info["article"]}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(info["problem"])
            st.error(f"**Key Gap:** {info['key_gap']}")

            # mini row for this scenario
            scenario_df = df[df["senaryo"] == key][["gap_tipi", "ciddiyet_puani"]].copy()
            scenario_df["Severity"] = scenario_df["ciddiyet_puani"].map(SCORE_LABELS)
            scenario_df["MDR Article"] = scenario_df["gap_tipi"].map(GAP_MDR)
            scenario_df = scenario_df.rename(columns={"gap_tipi": "Gap Area"})
            scenario_df = scenario_df.sort_values("ciddiyet_puani", ascending=False)
            scenario_df = scenario_df[["Gap Area", "MDR Article", "Severity"]]

            styled = scenario_df.style.map(color_cell, subset=["Severity"])
            st.dataframe(styled, use_container_width=True, hide_index=True, height=290)

        st.markdown("---")

    # ── full matrix ───────────────────────────────────────────────────────────
    st.subheader("Full Gap Area Matrix")
    st.caption(
        "Cross-scenario view: each cell shows severity per scenario. "
        "Overall reflects the WP3 cross-scenario rating."
    )

    pivot = df.pivot_table(
        index="gap_tipi",
        columns="senaryo",
        values="ciddiyet_puani",
        aggfunc="first",
    ).fillna(0).astype(int)

    for col in ["adverse_event", "fsca", "pms_pmcf"]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot = pivot[["adverse_event", "fsca", "pms_pmcf"]]
    pivot_labels = pivot.map(lambda x: SCORE_LABELS.get(x, "—"))
    pivot_labels = pivot_labels.reindex([g for g in GAP_MDR if g in pivot_labels.index])
    pivot_labels.columns = ["S1 — Adverse Event", "S2 — FSCA", "S3 — PMS / PMCF"]
    pivot_labels.insert(0, "MDR Article", [GAP_MDR.get(g, "—") for g in pivot_labels.index])
    pivot_labels["Overall"] = [GAP_OVERALL.get(g, "—") for g in pivot_labels.index]
    pivot_labels.index.name = "Gap Area"
    pivot_labels = pivot_labels.reset_index()

    score_cols = ["S1 — Adverse Event", "S2 — FSCA", "S3 — PMS / PMCF", "Overall"]
    styled_full = pivot_labels.style.map(color_cell, subset=score_cols)
    st.dataframe(styled_full, use_container_width=True, hide_index=True, height=290)

    st.markdown("---")

    # ── bar chart: scenario severity totals ───────────────────────────────────
    st.subheader("Severity Load by Scenario")
    st.caption("Total cumulative severity score per scenario — higher score means more compliance gaps concentrated in that scenario.")

    scenario_totals = df.groupby("senaryo")["ciddiyet_puani"].sum().reset_index()
    scenario_totals["label"] = scenario_totals["senaryo"].map({
        "adverse_event": "S1 — Adverse Event",
        "fsca":          "S2 — FSCA",
        "pms_pmcf":      "S3 — PMS / PMCF",
    })
    scenario_totals = scenario_totals.sort_values("ciddiyet_puani", ascending=True)

    bar_colors = ["#2563EB", "#e67e22", "#e74c3c"]

    fig = go.Figure(go.Bar(
        x=scenario_totals["ciddiyet_puani"],
        y=scenario_totals["label"],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=scenario_totals["ciddiyet_puani"],
        textposition="outside",
        textfont=dict(color="#F1F5F9", size=13),
        hovertemplate="<b>%{y}</b><br>Total Severity Score: %{x}<extra></extra>",
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=10, r=60, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        xaxis=dict(
            title=dict(text="Cumulative Severity Score", font=dict(color="#64748B", size=11)),
            tickfont=dict(color="#94A3B8", size=11),
            range=[0, scenario_totals["ciddiyet_puani"].max() + 3],
        ),
        yaxis=dict(tickfont=dict(color="#94A3B8", size=12)),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.info(
        f"All data derived from WP3 Section 4 (Cross-Scenario Gap Analysis). "
        f"{total} gap areas identified across 3 scenarios. "
        f"Most affected scenario: {worst_s}."
    )