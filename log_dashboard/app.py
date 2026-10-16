from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --- PAGE CONFIGURATION ---

st.set_page_config(
    page_title="Distributed Log Monitor",
    page_icon="📊",
    layout="wide",
)

st.title("Distributed Log Anomaly & Error Triage Engine")
st.write(
    "Monitor service health, investigate errors, "
    "and identify unusually slow requests."
)


# --- LOAD LOG DATA ---

LOG_FILE = Path(__file__).resolve().with_name("logs.jsonl")

if not LOG_FILE.exists():
    st.error("Log file not found. Run generate_mock_logs.py first.")
    st.stop()

df = pd.read_json(LOG_FILE, lines=True)

df["timestamp"] = pd.to_datetime(
    df["timestamp"], utc=True, errors="coerce"
)
df["duration_ms"] = pd.to_numeric(
    df["duration_ms"], errors="coerce"
)
df["level"] = df["level"].astype(str).str.upper()

df = df.dropna(subset=["timestamp"])


# --- SIDEBAR FILTERS ---

st.sidebar.header("Log Filters")

services = sorted(df["service"].dropna().unique().tolist())
levels = sorted(df["level"].dropna().unique().tolist())

selected_services = st.sidebar.multiselect(
    "Select services",
    options=services,
    default=services,
)

selected_levels = st.sidebar.multiselect(
    "Select severity levels",
    options=levels,
    default=levels,
)

filtered_df = df[
    df["service"].isin(selected_services)
    & df["level"].isin(selected_levels)
].copy()


# --- HANDLE EMPTY FILTER RESULTS ---

if filtered_df.empty:
    st.warning("No logs match the selected filters.")
    st.stop()


# --- KEY METRICS ---

total_logs = len(filtered_df)

error_count = len(
    filtered_df[filtered_df["level"] == "ERROR"]
)

error_rate = (
    error_count / total_logs * 100
    if total_logs > 0
    else 0
)

avg_latency = filtered_df["duration_ms"].mean()

slow_requests = len(
    filtered_df[filtered_df["duration_ms"] > 1000]
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Log Events", total_logs)
col2.metric("Errors", error_count)
col3.metric("Error Rate", f"{error_rate:.1f}%")
col4.metric(
    "Slow Requests (>1s)",
    slow_requests,
)

st.divider()


# --- CHART 1: LOG LEVEL BY SERVICE ---

left, right = st.columns(2)

with left:
    st.subheader("Log Levels by Service")

    level_counts = (
        filtered_df.groupby(["service", "level"])
        .size()
        .reset_index(name="count")
    )

    fig_levels = px.bar(
        level_counts,
        x="service",
        y="count",
        color="level",
        barmode="group",
        title="Events by service and severity",
    )

    st.plotly_chart(fig_levels, use_container_width=True)


# --- CHART 2: REQUEST LATENCY ---

with right:
    st.subheader("Request Duration Distribution")

    fig_latency = px.histogram(
        filtered_df,
        x="duration_ms",
        color="service",
        nbins=30,
        title="Distribution of request durations",
        labels={"duration_ms": "Duration (ms)"},
    )

    st.plotly_chart(fig_latency, use_container_width=True)


# --- CHART 3: LOG VOLUME OVER TIME ---

st.subheader("Log Events Over Time")

time_series = (
    filtered_df.set_index("timestamp")
    .resample("h")
    .size()
    .rename("events")
    .reset_index()
)

fig_time = px.line(
    time_series,
    x="timestamp",
    y="events",
    markers=True,
    title="Events per hour (UTC)",
)

st.plotly_chart(fig_time, use_container_width=True)


# --- RECENT ERRORS ---

st.subheader("Recent Errors")

recent_errors = (
    filtered_df[filtered_df["level"] == "ERROR"]
    .sort_values("timestamp", ascending=False)
    .head(20)
)

if recent_errors.empty:
    st.info("No errors found for the selected filters.")
else:
    st.dataframe(
        recent_errors,
        use_container_width=True,
        hide_index=True,
    )