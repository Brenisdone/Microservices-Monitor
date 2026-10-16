from pathlib import Path

import pandas as pd


# Locate the project and its input/output files.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "log_dashboard" / "logs.jsonl"
OUTPUT_FILE = Path(__file__).resolve().parent / "triaged_logs.jsonl"


def triage_log(row):
    level = str(row.get("level", "INFO")).upper()
    message = str(row.get("message", "")).lower()

    duration = pd.to_numeric(row.get("duration_ms"), errors="coerce")
    if pd.isna(duration):
        duration = 0

    # Rule 1: An error combined with very high latency.
    if level == "ERROR" and duration >= 2000:
        return {
            "anomaly_type": "critical_error_slow_request",
            "severity": "CRITICAL",
            "is_anomaly": True,
            "recommended_action": (
                "Inspect the error and investigate slow dependencies."
            ),
        }

    # Rule 2: Database or timeout errors.
    elif level == "ERROR" and any(
        term in message
        for term in ["database", "connection", "timeout"]
    ):
        return {
            "anomaly_type": "database_or_timeout_error",
            "severity": "HIGH",
            "is_anomaly": True,
            "recommended_action": (
                "Check database health, connection pools, and timeouts."
            ),
        }

    # Rule 3: Other errors.
    elif level == "ERROR":
        return {
            "anomaly_type": "error_event",
            "severity": "HIGH",
            "is_anomaly": True,
            "recommended_action": (
                "Inspect the error message and service logs."
            ),
        }

    # Rule 4: Requests taking at least one second.
    elif duration >= 1000:
        return {
            "anomaly_type": "slow_request",
            "severity": "MEDIUM",
            "is_anomaly": True,
            "recommended_action": (
                "Investigate database queries and dependency latency."
            ),
        }

    # Rule 5: Warnings that may need investigation.
    elif level == "WARNING":
        return {
            "anomaly_type": "warning_event",
            "severity": "LOW",
            "is_anomaly": True,
            "recommended_action": (
                "Review retries and check whether the issue repeats."
            ),
        }

    # Normal events.
    return {
        "anomaly_type": "none",
        "severity": "INFO",
        "is_anomaly": False,
        "recommended_action": "No immediate action required.",
    }


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Log file not found: {INPUT_FILE}\n"
            "Run the Day 1 log generator first."
        )

    logs = pd.read_json(INPUT_FILE, lines=True)

    # Apply triage rules to every log event.
    results = logs.apply(triage_log, axis=1, result_type="expand")
    triaged_logs = pd.concat([logs, results], axis=1)

    # Save enriched logs separately from the original data.
    triaged_logs.to_json(
        OUTPUT_FILE,
        orient="records",
        lines=True,
        date_format="iso",
    )

    print(f"Processed {len(triaged_logs)} log events.")
    print(
        f"Flagged events: "
        f"{int(triaged_logs['is_anomaly'].sum())}"
    )
    print("\nEvents by severity:")
    print(triaged_logs["severity"].value_counts().sort_index())
    print(f"\nSaved results to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()