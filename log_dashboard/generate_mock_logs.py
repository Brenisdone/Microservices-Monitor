import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

NUM_REQUESTS = 333

SERVICES = [
    "api-gateway",
    "order-service",
    "payment-service",
]

LEVELS = ["INFO", "INFO", "INFO", "WARNING", "ERROR"]

MESSAGES = {
    "INFO": [
        "Request processed successfully",
        "Operation completed",
        "Database query completed",
    ],
    "WARNING": [
        "Response time above normal",
        "Retrying downstream request",
    ],
    "ERROR": [
        "Internal server error",
        "Database connection timeout",
        "Payment processing failed",
    ],
}

random.seed(42)
np.random.seed(42)

now = datetime.now(timezone.utc)
start = now - timedelta(days=1)

logs = []

for request_number in range(1, NUM_REQUESTS + 1):
    # One ID represents one simulated request.
    correlation_id = f"req-{request_number:04d}"

    request_start = start + timedelta(
        seconds=random.randint(0, 86_000)
    )

    # Some requests fail at one of the three services.
    failure_index = (
        random.randrange(len(SERVICES))
        if random.random() < 0.12
        else None
    )

    # A failed request stops at the failing service.
    services_in_trace = (
        SERVICES[:failure_index + 1]
        if failure_index is not None
        else SERVICES
    )

    for service_index, service in enumerate(services_in_trace):
        level = "INFO"
        message = random.choice(MESSAGES["INFO"])
        duration = max(5, int(np.random.normal(150, 40)))

        if (
            failure_index is not None
            and service_index == failure_index
        ):
            level = "ERROR"

            failure_messages = {
                "api-gateway": "Downstream request failed",
                "order-service": "Database connection timeout",
                "payment-service": "Payment processing failed",
            }

            message = failure_messages[service]
            duration = random.randint(1000, 3000)

        elif random.random() < 0.08:
            level = "WARNING"
            message = random.choice(MESSAGES["WARNING"])
            duration = max(
                duration,
                random.randint(300, 1400),
            )

        timestamp = request_start + timedelta(
            milliseconds=service_index * 100
        )

        logs.append({
            "timestamp": timestamp.isoformat(),
            "service": service,
            "level": level,
            "message": message,
            "duration_ms": duration,
            "correlation_id": correlation_id,
        })

output = Path(__file__).resolve().parent / "logs.jsonl"

with output.open("w", encoding="utf-8") as file:
    for log in sorted(logs, key=lambda x: x["timestamp"]):
        file.write(json.dumps(log) + "\n")

print(f"Generated {len(logs)} log events.")
print(f"Saved to: {output}")