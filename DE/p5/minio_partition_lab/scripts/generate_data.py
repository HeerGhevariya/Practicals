import pandas as pd
import random
from datetime import datetime, timedelta

NUM_RECORDS = 20000

regions = [
    "Gujarat",
    "Maharashtra",
    "Rajasthan",
    "Delhi",
    "Karnataka"
]

applications = [
    "MobileApp",
    "WebApp",
    "API",
    "Payment",
    "Analytics"
]

metrics = [
    "response_time",
    "cpu_usage",
    "memory_usage",
    "request_count",
    "error_count"
]

start_date = datetime(2022, 1, 1)

data = []

for i in range(NUM_RECORDS):

    timestamp = start_date + timedelta(
        minutes=random.randint(0, 4 * 365 * 24 * 60)
    )

    data.append({
        "timestamp": timestamp,
        "year": timestamp.year,
        "month": timestamp.month,
        "region": random.choice(regions),
        "application": random.choice(applications),
        "metric": random.choice(metrics),
        "value": round(random.uniform(10, 1000), 2)
    })

df = pd.DataFrame(data)

df.to_csv("../data/metrics.csv", index=False)

print("Dataset generated successfully!")
print("Records:", len(df))
print()
print(df.head())