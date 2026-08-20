"""
ELT Pipeline Implementation (Extract -> Load -> Transform)
- Extract & Load: Fast direct ingestion of unnormalized raw CSV into DuckDB staging database table.
- Transform: In-database set-based SQL transformations utilizing DuckDB's C++ vectorized query engine.
"""

import os
import time
import duckdb

def run_elt_pipeline(csv_path: str, db_path: str):
    metrics = {
        "architecture": "ELT",
        "extract_load_time_sec": 0.0,
        "transform_time_sec": 0.0,
        "total_time_sec": 0.0,
        "raw_rows_loaded": 0,
        "clean_rows_transformed": 0
    }
    
    t_start = time.perf_counter()
    
    if os.path.exists(db_path):
        os.remove(db_path)
        
    con = duckdb.connect(db_path)
    
    # -------------------------------------------------------------
    # STAGE 1: EXTRACT & LOAD (Direct DuckDB Ingestion)
    # -------------------------------------------------------------
    print("[ELT] Stage 1 & 2: Extracting & Loading raw CSV directly into DuckDB Staging...")
    t_el_start = time.perf_counter()
    
    # Ingest raw CSV as text columns into staging table
    con.execute(f"""
        CREATE TABLE stg_raw_sales AS 
        SELECT * FROM read_csv_auto('{csv_path.replace('\\', '/')}', all_varchar=TRUE)
    """)
    
    t_el_end = time.perf_counter()
    metrics["extract_load_time_sec"] = round(t_el_end - t_el_start, 4)
    
    raw_count = con.execute("SELECT COUNT(*) FROM stg_raw_sales").fetchone()[0]
    metrics["raw_rows_loaded"] = raw_count
    print(f"[ELT] Direct raw ingestion completed: {raw_count} records loaded in {metrics['extract_load_time_sec']}s")
    
    # -------------------------------------------------------------
    # STAGE 3: TRANSFORM (In-Database SQL Transformations)
    # -------------------------------------------------------------
    print("[ELT] Stage 3: Executing SQL Transformations inside DuckDB Engine...")
    t_tf_start = time.perf_counter()
    
    # 1. Cleaned Staging View using DuckDB SQL Functions
    con.execute("""
        CREATE VIEW stg_cleaned_sales AS
        SELECT
            transaction_id,
            COALESCE(
                TRY_CAST(transaction_date AS TIMESTAMP),
                TRY_STRPTIME(transaction_date, '%d-%m-%Y %H:%M:%S'),
                TRY_STRPTIME(transaction_date, '%Y/%m/%d %H:%M:%S')
            ) AS transaction_date,
            TRIM(customer_id) AS customer_id,
            CONCAT(UPPER(SUBSTRING(TRIM(customer_name), 1, 1)), LOWER(SUBSTRING(TRIM(customer_name), 2))) AS customer_name,
            LOWER(TRIM(customer_email)) AS customer_email,
            TRIM(store_id) AS store_id,
            TRIM(store_location) AS store_location,
            TRIM(product_id) AS product_id,
            TRIM(product_name) AS product_name,
            CONCAT(UPPER(SUBSTRING(TRIM(product_category), 1, 1)), LOWER(SUBSTRING(TRIM(product_category), 2))) AS product_category,
            TRY_CAST(TRIM(quantity) AS INTEGER) AS quantity,
            TRY_CAST(REPLACE(TRIM(unit_price), '$', '') AS DOUBLE) AS unit_price,
            COALESCE(TRY_CAST(REPLACE(TRIM(discount_amount), '$', '') AS DOUBLE), 0.0) AS discount_amount,
            CONCAT(UPPER(SUBSTRING(TRIM(payment_method), 1, 1)), LOWER(SUBSTRING(TRIM(payment_method), 2))) AS payment_method
        FROM stg_raw_sales
        WHERE 
            COALESCE(
                TRY_CAST(transaction_date AS TIMESTAMP),
                TRY_STRPTIME(transaction_date, '%d-%m-%Y %H:%M:%S'),
                TRY_STRPTIME(transaction_date, '%Y/%m/%d %H:%M:%S')
            ) IS NOT NULL
            AND TRY_CAST(TRIM(quantity) AS INTEGER) > 0
            AND TRY_CAST(REPLACE(TRIM(unit_price), '$', '') AS DOUBLE) > 0;
    """)
    
    # 2. Build Dimension Tables
    con.execute("""
        CREATE TABLE dim_customers AS
        SELECT DISTINCT customer_id, customer_name, customer_email
        FROM stg_cleaned_sales;
    """)
    
    con.execute("""
        CREATE TABLE dim_products AS
        SELECT DISTINCT product_id, product_name, product_category
        FROM stg_cleaned_sales;
    """)
    
    con.execute("""
        CREATE TABLE dim_stores AS
        SELECT DISTINCT store_id, store_location
        FROM stg_cleaned_sales;
    """)
    
    # 3. Build Fact Table with Calculated Net Amount
    con.execute("""
        CREATE TABLE fact_sales AS
        SELECT
            transaction_id,
            transaction_date,
            customer_id,
            product_id,
            store_id,
            quantity,
            unit_price,
            discount_amount,
            ROUND((quantity * unit_price) - discount_amount, 2) AS net_amount,
            payment_method
        FROM stg_cleaned_sales;
    """)
    
    # 4. Build Analytical Data Mart
    con.execute("""
        CREATE TABLE mart_daily_sales_summary AS
        SELECT
            CAST(transaction_date AS DATE) AS sales_date,
            store_id,
            COUNT(transaction_id) AS total_transactions,
            SUM(quantity) AS total_units_sold,
            ROUND(SUM(quantity * unit_price), 2) AS gross_revenue,
            ROUND(SUM(discount_amount), 2) AS total_discounts,
            ROUND(SUM(net_amount), 2) AS net_revenue
        FROM fact_sales
        GROUP BY CAST(transaction_date AS DATE), store_id;
    """)
    
    t_tf_end = time.perf_counter()
    metrics["transform_time_sec"] = round(t_tf_end - t_tf_start, 4)
    
    clean_count = con.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    metrics["clean_rows_transformed"] = clean_count
    
    con.close()
    
    t_end = time.perf_counter()
    metrics["total_time_sec"] = round(t_end - t_start, 4)
    
    print(f"[ELT] SQL transformations finished in {metrics['transform_time_sec']}s")
    print(f"[ELT] Total ELT execution time: {metrics['total_time_sec']}s ({clean_count} clean fact rows produced)")
    
    return metrics

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    csv_file = os.path.join(base_dir, "data", "raw_retail_sales.csv")
    db_file = os.path.join(base_dir, "elt_warehouse.duckdb")
    
    if os.path.exists(csv_file):
        run_elt_pipeline(csv_file, db_file)
    else:
        print(f"Error: {csv_file} does not exist. Run generate_dataset.py first.")
