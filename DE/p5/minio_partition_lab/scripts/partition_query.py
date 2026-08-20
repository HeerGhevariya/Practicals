import pandas as pd
import glob
import time

YEAR = 2025
REGION = "Gujarat"

pattern = (
    f"../data/partitions/"
    f"year={YEAR}/"
    f"month=*/"
    f"region={REGION}/"
    f"data.csv"
)

files = glob.glob(pattern)

print("Partitions found:", len(files))

start_time = time.perf_counter()

dataframes = []

for file in files:
    df = pd.read_csv(file)
    dataframes.append(df)

result = pd.concat(dataframes, ignore_index=True)

end_time = time.perf_counter()

elapsed = end_time - start_time

print("Records found:", len(result))
print("Partitions scanned:", len(files))
print("Time:", round(elapsed * 1000, 3), "ms")