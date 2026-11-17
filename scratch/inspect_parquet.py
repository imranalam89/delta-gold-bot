import os
import pandas as pd

parquet_path = os.path.join("data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")
print(f"Reading {parquet_path}...")
df = pd.read_parquet(parquet_path)

print(f"Row count: {len(df)}")
print(f"Index type: {type(df.index)}")
print(f"Start date: {df.index.min()}")
print(f"End date:   {df.index.max()}")
print(f"Columns: {list(df.columns)}")
print(f"Memory usage: {df.memory_usage().sum() / 1024 / 1024:.2f} MB")
