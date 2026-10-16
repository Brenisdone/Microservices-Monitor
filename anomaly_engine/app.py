from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Log Triage Dashboard",
    layout="wide",
)

st.title("Distributed Log Anomaly & Error Triage Engine")
st.caption("Investigate flagged events and monitor service health.")

LOG_FILE = Path(__file__).resolve().with_name("triaged_logs.jsonl")

if not LOG_FILE.exists():
    st.error("Triaged logs not found. Run detect_anomalies.py first.")
    st.stop()

df = pd.read_json(LOG_FILE, lines=True)

df["timestamp"] = pd.to_datetime(
    df["timestamp"], utc=True, errors="coerce"
)
df["duration_ms"] = pd.to_numeric(
    df["duration_ms"], errors="coerce"
)
df["level"] = df["level"].astype(str).str.upper()
df["severity"] = df["severity"].astype(str).str.upper()
df["is_anomaly"] = df["is_anomaly"].fillna(False).astype(bool)

df = df.dropna(subset=["timestamp", "duration_ms"])

# Sidebar filters
st.sidebar.header("Filters")

services = sorted(df["service"].dropna().unique().tolist())
severities = [
    level for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    if level in df["severity"].unique()
]
anomaly_types = sorted(df["anomaly_type"].dropna().unique().tolist())

selected_services = st.sidebar.multiselect(
    "Services", services, default=services
)
selected_severities = st.sidebar.multiselect(
    "Triage severity", severities, default=severities
)
selected_types = st.sidebar.multiselect(
    "Event classification", anomaly_types, default=anomaly_types
)
show_only_anomalies = st.sidebar.checkbox(
    "Show only flagged events", value=False
)

filtered_df = df[
    df["service"].isin(selected_services)
    & df["severity"].isin(selected_severities)
    & df["anomaly_type"].isin(selected_types)
].copy()

if show_only_anomalies:
    filtered_df = filtered_df[filtered_df["is_anomaly"]]

if filtered_df.empty:
    st.warning("No events match the selected filters.")
    st.stop()

# Summary metrics
total = len(filtered_df)
flagged = int(filtered_df["is_anomaly"].sum())
critical = int((filtered_df["severity"] == "CRITICAL").sum())
high = int((filtered_df["severity"] == "HIGH").sum())
avg_latency = filtered_df["duration_ms"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Events Shown", total)
c2.metric("Flagged Events", flagged)
c3.metric("Critical", critical)
c4.metric("High", high)
c5.metric("Average Latency", f"{avg_latency:.0f} ms")

st.divider()

# Severity by service
st.subheader("Severity by Service")

severity_counts = (
    filtered_df.groupby(["service", "severity"])
    .size()
    .reset_index(name="count")
)

fig_severity = px.bar(
    severity_counts,
    x="service",
    y="count",
    color="severity",
    barmode="stack",
    title="Log events grouped by triage severity",
)
st.plotly_chart(fig_severity, use_container_width=True)

# Latency distribution
st.subheader("Request Duration")

fig_latency = px.histogram(
    filtered_df,
    x="duration_ms",
    color="severity",
    nbins=30,
    title="Distribution of request durations",
    labels={"duration_ms": "Duration (ms)"},
)
st.plotly_chart(fig_latency, use_container_width=True)

# Events requiring investigation
st.subheader("Events Requiring Investigation")

flagged_df = filtered_df[
    filtered_df["is_anomaly"]
].sort_values("timestamp", ascending=False).head(50)

columns = [
    "timestamp",
    "service",
    "level",
    "severity",
    "anomaly_type",
    "message",
    "duration_ms",
    "recommended_action",
    "correlation_id",
]

if flagged_df.empty:
    st.info("No flagged events match these filters.")
else:
    st.dataframe(
        flagged_df[columns],
        use_container_width=True,
        hide_index=True,
    )


#trace explorer
st.divider()
st.subheader("Distributed Request Trace")

correlation_ids = sorted(
    df["correlation_id"].dropna().unique().tolist()
)

if not correlation_ids:
    st.info("No correlation IDs are available.")
else:
    selected_id = st.selectbox(
        "Select a request",
        options=correlation_ids,
    )

    trace = (
        df[df["correlation_id"] == selected_id]
        .sort_values("timestamp")
        .copy()
    )

    services_in_trace = " → ".join(
        trace["service"].astype(str).tolist()
    )

    st.caption(
        f"{len(trace)} log event(s) | "
        f"Service flow: {services_in_trace}"
    )

    trace_columns = [
        "timestamp",
        "service",
        "level",
        "severity",
        "message",
        "duration_ms",
        "recommended_action",
    ]

    st.dataframe(
        trace[trace_columns],
        use_container_width=True,
        hide_index=True,
    )