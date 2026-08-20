import pandas as pd
import time
import os

# ------------------------------------------------
# 1. FULL TABLE SCAN
# ------------------------------------------------

print("\n========== FULL TABLE SCAN ==========")

start_time = time.perf_counter()

df = pd.read_csv("../data/metrics.csv")

result_full = df[
    (df["year"] == 2025) &
    (df["region"] == "Gujarat")
]

end_time = time.perf_counter()

full_scan_time = end_time - start_time

print("Records found:", len(result_full))
print("Records scanned:", len(df))
print("Time:", round(full_scan_time * 1000, 3), "ms")


# ------------------------------------------------
# 2. PARTITIONED SCAN
# ------------------------------------------------

print("\n========== PARTITIONED SCAN ==========")

partition_path = (
    "../data/partitions/"
    "year=2025/"
    "month=1/"
    "region=Gujarat/"
)

start_time = time.perf_counter()

result_partition = pd.read_csv(
    partition_path + "data.csv"
)

end_time = time.perf_counter()

partition_time = end_time - start_time

print("Records found:", len(result_partition))
print("Records scanned:", len(result_partition))
print("Time:", round(partition_time * 1000, 3), "ms")


# ------------------------------------------------
# 3. PERFORMANCE COMPARISON
# ------------------------------------------------

print("\n========== PERFORMANCE COMPARISON ==========")

print(
    "Full table scan:",
    round(full_scan_time * 1000, 3),
    "ms"
)

print(
    "Partition scan:",
    round(partition_time * 1000, 3),
    "ms"
)

if partition_time > 0:

    improvement = (
        (full_scan_time - partition_time)
        / full_scan_time
    ) * 100

    print(
        "Performance improvement:",
        round(improvement, 2),
        "%"
    )