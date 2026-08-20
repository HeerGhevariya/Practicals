import pandas as pd
import os

INPUT_FILE = "../data/metrics.csv"
OUTPUT_DIR = "../data/partitions"

df = pd.read_csv(INPUT_FILE)

print("Total records:", len(df))

for (year, month, region), group in df.groupby(
    ["year", "month", "region"]
):

    partition_path = os.path.join(
        OUTPUT_DIR,
        f"year={year}",
        f"month={month}",
        f"region={region}"
    )

    os.makedirs(partition_path, exist_ok=True)

    file_path = os.path.join(
        partition_path,
        "data.csv"
    )

    group.to_csv(file_path, index=False)

print("Partitioning completed successfully!")