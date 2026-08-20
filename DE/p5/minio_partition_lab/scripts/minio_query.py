import boto3
import pandas as pd
import io
import time

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="Minio@12345"
)

BUCKET = "metrics"

YEAR = 2025
REGION = "Gujarat"

prefix = f"year={YEAR}/"

start_time = time.perf_counter()

response = s3.list_objects_v2(
    Bucket=BUCKET,
    Prefix=prefix
)

matching_files = []

for obj in response.get("Contents", []):

    key = obj["Key"]

    if (
        f"region={REGION}" in key
        and key.endswith("data.csv")
    ):
        matching_files.append(key)

print("Matching partitions:")

for key in matching_files:
    print("-", key)

dataframes = []

for key in matching_files:

    response = s3.get_object(
        Bucket=BUCKET,
        Key=key
    )

    content = response["Body"].read()

    df = pd.read_csv(
        io.BytesIO(content)
    )

    dataframes.append(df)

if dataframes:

    result = pd.concat(
        dataframes,
        ignore_index=True
    )

else:

    result = pd.DataFrame()

end_time = time.perf_counter()

print("\n========== RESULT ==========")

print("Records found:", len(result))

print(
    "Partitions scanned:",
    len(matching_files)
)

print(
    "Time:",
    round((end_time - start_time) * 1000, 3),
    "ms"
)