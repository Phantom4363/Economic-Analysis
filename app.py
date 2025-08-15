
"""Economics Portfolio Tracker (Streamlit v1) — G20 countries
---------------------------------------------------------
This is a Streamlit app with the COUNTRIES mapping expanded to include all G20 members plus the EU entry.
"""
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Optional APIs
try:
    from fredapi import Fred
except Exception:
    Fred = None

try:
    import wbgapi as wb
except Exception:
    wb = None

st.set_page_config(
    page_title="Economics Portfolio Tracker",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
    <style>
    .small-muted { color: var(--text-muted, #6b7280); font-size: 12px; }
    .kpi { border-radius: 16px; padding: 14px 16px; border: 1px solid #e5e7eb; }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(ttl=60 * 60)
def get_fred(series_id: str, pct_change_yoy: bool = False) -> pd.DataFrame:
    if Fred is None:
        raise RuntimeError("fredapi not installed")
    key = st.secrets.get("FRED_API_KEY") if hasattr(st, "secrets") else os.getenv("FRED_API_KEY")
    if not key:
        raise RuntimeError("Missing FRED_API_KEY (set in Streamlit secrets)")
    fred = Fred(api_key=key)
    s = fred.get_series(series_id)
    df = s.rename("value").to_frame()
    df.index = pd.to_datetime(df.index)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "date"}, inplace=True)
    if pct_change_yoy:
        df["value"] = df["value"].pct_change(12) * 100
        df = df.dropna()
    return df

@st.cache_data(ttl=60 * 60)
def get_wb(country: str, indicator: str) -> pd.DataFrame:
    if wb is None:
        raise RuntimeError("wbgapi not installed")
    try:
        data = wb.data.DataFrame(indicator, economy=country, time=range(datetime.now().year - 20, datetime.now().year+1))
        data = data.T.reset_index()
        data.columns = ["date", "value"]
        # ------------------------
        # NEW: Strip 'YR' prefix if present
        data["date"] = data["date"].astype(str).str.replace("YR", "")
        data["date"] = pd.to_datetime(data["date"], format="%Y", errors='coerce')
        # ------------------------
        data = data.sort_values("date")
        data["value"] = pd.to_numeric(data["value"], errors="coerce")
        data = data.dropna()
        return data
    except Exception as e:
        raise RuntimeError(f"World Bank fetch failed: {e}")

@st.cache_data
def synth_monthly(base=2.0, noise=0.5, months=36, seed=0):
    rng = np.random.default_rng(seed)
    start = datetime.today() - relativedelta(months=months)
    ts = [start + relativedelta(months=i) for i in range(months)]
    vals = base + np.cumsum(rng.normal(0, noise, size=months)) / 10.0
    return pd.DataFrame({"date": ts, "value": vals})

INDICATORS = {
    "CPI_YOY": {
        "label": "Inflation (CPI, % YoY)",
        "unit": "%",
        "source": "FRED/World Bank",
        "fetch": lambda country: (
            get_fred("CPIAUCSL", pct_change_yoy=True)
            if country == "US"
            else get_wb(country, "FP.CPI.TOTL.ZG")
        ),
    },
    "UNEMP": {
        "label": "Unemployment (%)",
        "unit": "%",
        "source": "FRED/World Bank",
        "fetch": lambda country: (
            get_fred("UNRATE") if country == "US" else get_wb(country, "SL.UEM.TOTL.ZS")
        ),
    },
    "GDP_YOY": {
        "label": "GDP Growth (Real, % YoY)",
        "unit": "%",
        "source": "FRED/World Bank",
        "fetch": lambda country: (
            get_fred("GDPC1", pct_change_yoy=True) if country == "US" else get_wb(country, "NY.GDP.MKTP.KD.ZG")
        ),
    },
    "POLICY": {
        "label": "Policy/Reference Rate (%)",
        "unit": "%",
        "source": "FRED/World Bank",
        "fetch": lambda country: (
            get_fred("DFF") if country == "US" else get_wb(country, "FR.INR.RINR")
        ),
    },
}

COUNTRIES = {
    "US": {"name": "United States", "wb": "USA"},
    "CA": {"name": "Canada", "wb": "CAN"},
    "MX": {"name": "Mexico", "wb": "MEX"},
    "BR": {"name": "Brazil", "wb": "BRA"},
    "AR": {"name": "Argentina", "wb": "ARG"},
    "GB": {"name": "United Kingdom", "wb": "GBR"},
    "DE": {"name": "Germany", "wb": "DEU"},
    "FR": {"name": "France", "wb": "FRA"},
    "IT": {"name": "Italy", "wb": "ITA"},
    "EU": {"name": "European Union", "wb": "EUU"},
    "RU": {"name": "Russia", "wb": "RUS"},
    "CN": {"name": "China", "wb": "CHN"},
    "IN": {"name": "India", "wb": "IND"},
    "JP": {"name": "Japan", "wb": "JPN"},
    "KR": {"name": "South Korea", "wb": "KOR"},
    "ID": {"name": "Indonesia", "wb": "IDN"},
    "AU": {"name": "Australia", "wb": "AUS"},
    "SA": {"name": "Saudi Arabia", "wb": "SAU"},
    "ZA": {"name": "South Africa", "wb": "ZAF"},
    "TR": {"name": "Türkiye", "wb": "TUR"},
}

st.sidebar.title("⚙️ Controls")
primary = st.sidebar.selectbox(
    "Primary economy",
    options=list(COUNTRIES.keys()),
    format_func=lambda k: COUNTRIES[k]["name"],
    index=0,
)
compare = st.sidebar.selectbox(
    "Compare to",
    options=list(COUNTRIES.keys()),
    format_func=lambda k: COUNTRIES[k]["name"],
    index=1,
)

sel_ind_1 = st.sidebar.selectbox(
    "Indicator",
    options=list(INDICATORS.keys()),
    format_func=lambda k: INDICATORS[k]["label"],
    index=0,
)
sel_ind_2 = st.sidebar.selectbox(
    "Second indicator (Charts tab)",
    options=list(INDICATORS.keys()),
    format_func=lambda k: INDICATORS[k]["label"],
    index=1,
)

def fetch_indicator(country_key: str, indicator_key: str) -> pd.DataFrame:
    meta = INDICATORS[indicator_key]
    try:
        if country_key == "US":
            df = meta["fetch"]("US")
        else:
            df = meta["fetch"](COUNTRIES[country_key]["wb"])
        df = df[["date", "value"]].dropna()
        return df
    except Exception as e:
        st.warning(f"Using demo data for {COUNTRIES[country_key]['name']} – {meta['label']}. Reason: {e}")
        base = {"CPI_YOY": 3.0, "UNEMP": 5.0, "GDP_YOY": 2.0, "POLICY": 4.0}[indicator_key]
        return synth_monthly(base=base, seed=hash(country_key + indicator_key) % 10)

primary_df_1 = fetch_indicator(primary, sel_ind_1)
primary_df_2 = fetch_indicator(primary, sel_ind_2)
compare_df_1 = fetch_indicator(compare, sel_ind_1)

def latest_value(df: pd.DataFrame):
    if df.empty:
        return np.nan, None
    last_row = df.sort_values("date").iloc[-1]
    return float(last_row["value"]), pd.to_datetime(last_row["date"]).date()

v1, d1 = latest_value(primary_df_1)
v2, d2 = latest_value(primary_df_2)

col_logo, col_title = st.columns([0.08, 0.92])
with col_logo:
    st.markdown("## 📈")
with col_title:
    st.markdown("# Economics Portfolio Tracker")
    st.markdown(
        f"<span class='small-muted'>Data sources: {INDICATORS[sel_ind_1]['source']} · Updated through {d1 or '—'}</span>",
        unsafe_allow_html=True,
    )

col1, col2, col3 = st.columns(3)

with col1:
    delta = (
        (primary_df_1.sort_values("date").iloc[-1]["value"] - primary_df_1.sort_values("date").iloc[-13]["value"]) if len(primary_df_1) > 13 else np.nan
    )
    st.markdown("### Key Metric")
    st.container().markdown(
        f"**{INDICATORS[sel_ind_1]['label']}**\n\n**{v1:.2f}{INDICATORS[sel_ind_1]['unit']}**  "+
        (f"12‑mo Δ: {delta:+.2f}{INDICATORS[sel_ind_1]['unit']}" if not np.isnan(delta) else "12‑mo Δ: —"),
        unsafe_allow_html=True
    )

with col2:
    st.markdown("### Secondary Metric")
    st.container().markdown(
        f"**{INDICATORS[sel_ind_2]['label']}**\n\n**{(v2 if not np.isnan(v2) else 0):.2f}{INDICATORS[sel_ind_2]['unit']}**",
        unsafe_allow_html=True
    )

with col3:
    st.markdown("### Notes quick-add")
    with st.form("note_form"):
        default_note = (
            "Demand-pull pressures easing as goods disinflation offsets services. "
            "Link to AD–AS: SRAS shift moderating; watch labor and credit."
        )
        note_text = st.text_area("Commentary", value=default_note, height=120)
        add_note = st.form_submit_button("Save note")
    if add_note:
        st.session_state.setdefault("notes", []).append({"ts": datetime.utcnow().isoformat(), "text": note_text})
        st.success("Note saved.")

T1, T2, T3, T4 = st.tabs(["Charts", "Compare", "Events", "Notes"])

with T1:
    st.subheader(f"{COUNTRIES[primary]['name']}: {INDICATORS[sel_ind_1]['label']}")
    if not primary_df_1.empty:
        fig1 = px.line(primary_df_1, x="date", y="value", labels={"value": INDICATORS[sel_ind_1]["label"], "date": "Date"})
        st.plotly_chart(fig1, use_container_width=True)

    st.caption("Two-indicator view")
    if not primary_df_1.empty and not primary_df_2.empty:
        df_merge = primary_df_1.merge(primary_df_2, on="date", suffixes=("_a", "_b"))
        df_m = df_merge.melt("date", value_vars=["value_a", "value_b"], var_name="series", value_name="value")
        df_m["series"] = df_m["series"].map({
            "value_a": INDICATORS[sel_ind_1]["label"],
            "value_b": INDICATORS[sel_ind_2]["label"],
        })
        fig2 = px.bar(df_m, x="date", y="value", color="series", barmode="group")
        st.plotly_chart(fig2, use_container_width=True)

with T2:
    st.subheader(f"{INDICATORS[sel_ind_1]['label']}: {COUNTRIES[primary]['name']} vs {COUNTRIES[compare]['name']}")
    if not primary_df_1.empty and not compare_df_1.empty:
        left = primary_df_1.rename(columns={"value": COUNTRIES[primary]["name"]})
        right = compare_df_1.rename(columns={"value": COUNTRIES[compare]["name"]})
        merged = pd.merge_asof(left.sort_values("date"), right.sort_values("date"), on="date")
        figc = px.line(merged, x="date", y=[COUNTRIES[primary]["name"], COUNTRIES[compare]["name"]])
        st.plotly_chart(figc, use_container_width=True)

with T3:
    st.subheader("Policy & Shock Events")
    st.caption("Tag central bank moves, fiscal changes, commodity shocks, etc., and link them to indicator trends.")

    with st.form("event_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 1, 3])
        with c1:
            e_date = st.date_input("Date", value=datetime.today())
        with c2:
            e_tag = st.text_input("Tag (Fed, Oil, Fiscal)")
        with c3:
            e_note = st.text_input("Short note")
        submitted = st.form_submit_button("Add event")

    if submitted:
        st.session_state.setdefault("events", []).insert(0, {"date": str(e_date), "tag": e_tag.strip() or "—", "note": e_note.strip() or ""})
        st.success("Event added.")

    events = st.session_state.get("events", [
        {"date": "2025-03-19", "tag": "Fed", "note": "FOMC holds rate; guidance unchanged"},
        {"date": "2025-05-28", "tag": "Oil", "note": "Brent spike after supply cut"},
    ])

    for ev in events:
        st.container().markdown(
            f"**{ev['tag']}** — {ev['note']}  \\n<span class='small-muted'>{ev['date']}</span>",
            unsafe_allow_html=True,
        )

with T4:
    st.subheader("Theory-backed Notes")
    st.caption("Tie real data to macro models: AD–AS, IS–LM, Phillips Curve, Taylor Rule.")

    notes = st.session_state.get("notes", [])
    if notes:
        for n in notes:
            st.container().markdown(
                f"{n['text']}  \\n<span class='small-muted'>Saved {n['ts']}</span>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No notes yet. Add some from the KPI panel.")

st.markdown("""
<div class='small-muted' style='margin-top:24px;'>
Built with Streamlit · Replace any demo data by adding a FRED API key and enabling World Bank access.\\
<br/>Indicators: CPI YoY (US: CPIAUCSL), Unemployment (US: UNRATE), Real GDP YoY (US: GDPC1), Policy Rate (US: DFF).\\
<br/>International proxies: CPI (FP.CPI.TOTL.ZG), Unemployment (SL.UEM.TOTL.ZS), GDP growth (NY.GDP.MKTP.KD.ZG), Lending rate proxy (FR.INR.RINR).
</div>
""", unsafe_allow_html=True)
