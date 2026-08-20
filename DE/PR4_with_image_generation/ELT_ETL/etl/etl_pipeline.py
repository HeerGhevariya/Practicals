"""
ETL Pipeline Implementation (Extract -> Transform -> Load)
- Extract: Reads raw CSV dataset into Python/Pandas in-memory DataFrames.
- Transform: Cleans, parses, coerces, and normalizes data into Star Schema in application memory using vectorized Pandas operations.
- Load: Bulk loads cleaned dimensional and fact DataFrames into target DuckDB tables.
"""

import os
import time
import pandas as pd
import duckdb

def run_etl_pipeline(csv_path: str, db_path: str):
    metrics = {
        "architecture": "ETL",
        "extract_time_sec": 0.0,
        "transform_time_sec": 0.0,
        "load_time_sec": 0.0,
        "total_time_sec": 0.0,
        "raw_rows_extracted": 0,
        "clean_rows_loaded": 0
    }
    
    t_start = time.perf_counter()
    
    # -------------------------------------------------------------
    # STAGE 1: EXTRACT
    # -------------------------------------------------------------
    print("[ETL] Stage 1: Extracting raw CSV data via Pandas...")
    t_ext_start = time.perf_counter()
    
    df_raw = pd.read_csv(csv_path, dtype=str)
    
    t_ext_end = time.perf_counter()
    metrics["extract_time_sec"] = round(t_ext_end - t_ext_start, 4)
    metrics["raw_rows_extracted"] = len(df_raw)
    print(f"[ETL] Extracted {len(df_raw)} records in {metrics['extract_time_sec']}s")
    
    # -------------------------------------------------------------
    # STAGE 2: TRANSFORM (In-Memory Pandas)
    # -------------------------------------------------------------
    print("[ETL] Stage 2: Transforming raw data in application memory...")
    t_tf_start = time.perf_counter()
    
    df = df_raw.copy()
    
    # 1. Clean String Columns (trimming & casing)
    df["customer_name"] = df["customer_name"].astype(str).str.strip().str.title()
    df["customer_email"] = df["customer_email"].astype(str).str.strip().str.lower()
    df["store_location"] = df["store_location"].astype(str).str.strip()
    df["product_name"] = df["product_name"].astype(str).str.strip()
    df["product_category"] = df["product_category"].astype(str).str.strip().str.title()
    df["payment_method"] = df["payment_method"].astype(str).str.strip().str.title()
    
    # 2. Price & Discount Cleaning (Remove '$', strip whitespace, convert to float)
    df["unit_price"] = (
        df["unit_price"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.strip()
    )
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0)
    
    df["discount_amount"] = (
        df["discount_amount"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.strip()
    )
    df["discount_amount"] = pd.to_numeric(df["discount_amount"], errors="coerce").fillna(0.0)
    
    # 3. Quantity Cleaning & Filter Invalid Records
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int)
    
    # Filter out invalid quantity (<= 0) or unparseable unit price (<= 0)
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)].copy()
    
    # 4. Date Parsing
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], format="mixed", errors="coerce")
    df = df[df["transaction_date"].notnull()].copy()
    
    # 5. Feature Engineering: Net Amount
    df["net_amount"] = (df["quantity"] * df["unit_price"]) - df["discount_amount"]
    df["net_amount"] = df["net_amount"].round(2)
    
    # 6. Normalize into Star Schema Dimensions & Fact Tables
    dim_customers = (
        df[["customer_id", "customer_name", "customer_email"]]
        .drop_duplicates(subset=["customer_id"])
        .reset_index(drop=True)
    )
    
    dim_products = (
        df[["product_id", "product_name", "product_category"]]
        .drop_duplicates(subset=["product_id"])
        .reset_index(drop=True)
    )
    
    dim_stores = (
        df[["store_id", "store_location"]]
        .drop_duplicates(subset=["store_id"])
        .reset_index(drop=True)
    )
    
    fact_sales = df[[
        "transaction_id",
        "transaction_date",
        "customer_id",
        "product_id",
        "store_id",
        "quantity",
        "unit_price",
        "discount_amount",
        "net_amount",
        "payment_method"
    ]].reset_index(drop=True)
    
    t_tf_end = time.perf_counter()
    metrics["transform_time_sec"] = round(t_tf_end - t_tf_start, 4)
    metrics["clean_rows_loaded"] = len(fact_sales)
    print(f"[ETL] Transformed into {len(fact_sales)} valid fact rows in {metrics['transform_time_sec']}s")
    
    # -------------------------------------------------------------
    # STAGE 3: LOAD (Target Database Insertion)
    # -------------------------------------------------------------
    print("[ETL] Stage 3: Loading cleaned DataFrames into DuckDB warehouse...")
    t_ld_start = time.perf_counter()
    
    if os.path.exists(db_path):
        os.remove(db_path)
        
    con = duckdb.connect(db_path)
    
    con.execute("CREATE TABLE dim_customers AS SELECT * FROM dim_customers")
    con.execute("CREATE TABLE dim_products AS SELECT * FROM dim_products")
    con.execute("CREATE TABLE dim_stores AS SELECT * FROM dim_stores")
    con.execute("CREATE TABLE fact_sales AS SELECT * FROM fact_sales")
    
    con.close()
    
    t_ld_end = time.perf_counter()
    metrics["load_time_sec"] = round(t_ld_end - t_ld_start, 4)
    metrics["total_time_sec"] = round(t_ld_end - t_start, 4)
    
    print(f"[ETL] Loaded tables into DuckDB database in {metrics['load_time_sec']}s")
    print(f"[ETL] Total ETL execution time: {metrics['total_time_sec']}s")
    
    return metrics

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    csv_file = os.path.join(base_dir, "data", "raw_retail_sales.csv")
    db_file = os.path.join(base_dir, "etl_warehouse.duckdb")
    
    if os.path.exists(csv_file):
        run_etl_pipeline(csv_file, db_file)
    else:
        print(f"Error: {csv_file} does not exist. Run generate_dataset.py first.")
