"""
Comprehensive ETL vs ELT Benchmark Runner
Measures:
- Phase execution times (Extract, Transform, Load / Ingestion)
- Memory utilization (Peak RAM in MB via tracemalloc & psutil)
- CPU time & Storage footprint
- Target data integrity verification across both pipelines
- Data lineage mapping
"""

import os
import sys
import time
import json
import tracemalloc
import psutil
import duckdb
import matplotlib.pyplot as plt
from tabulate import tabulate

# Add workspace directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from data.generate_dataset import generate_retail_data
from etl.etl_pipeline import run_etl_pipeline
from elt.elt_pipeline import run_elt_pipeline

def run_benchmarks(num_records: int = 200000):
    print("=" * 70)
    print("      DATA INTEGRATION ARCHITECTURE BENCHMARK SUITE (ETL vs ELT)")
    print("=" * 70)
    
    csv_file = os.path.join(BASE_DIR, "data", "raw_retail_sales.csv")
    etl_db_file = os.path.join(BASE_DIR, "etl_warehouse.duckdb")
    elt_db_file = os.path.join(BASE_DIR, "elt_warehouse.duckdb")
    
    # 1. Generate Dataset
    print(f"\n[STEP 1] Generating Raw Retail Dataset ({num_records} rows)...")
    generate_retail_data(csv_file, num_records=num_records)
    csv_size_mb = round(os.path.getsize(csv_file) / (1024 * 1024), 2)
    print(f"Raw CSV File Size: {csv_size_mb} MB")
    
    process = psutil.Process(os.getpid())
    
    # 2. Benchmark ETL Pipeline
    print("\n" + "-" * 50)
    print("[STEP 2] Running ETL Pipeline (Pandas In-Memory Cleansing)...")
    print("-" * 50)
    tracemalloc.start()
    cpu_etl_start = process.cpu_times()
    
    etl_metrics = run_etl_pipeline(csv_file, etl_db_file)
    
    cpu_etl_end = process.cpu_times()
    _, etl_peak_mem_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    etl_metrics["peak_memory_mb"] = round(etl_peak_mem_bytes / (1024 * 1024), 2)
    etl_metrics["cpu_user_time_sec"] = round(cpu_etl_end.user - cpu_etl_start.user, 4)
    etl_metrics["db_size_mb"] = round(os.path.getsize(etl_db_file) / (1024 * 1024), 2)
    
    # 3. Benchmark ELT Pipeline
    print("\n" + "-" * 50)
    print("[STEP 3] Running ELT Pipeline (DuckDB In-Database SQL)...")
    print("-" * 50)
    tracemalloc.start()
    cpu_elt_start = process.cpu_times()
    
    elt_metrics = run_elt_pipeline(csv_file, elt_db_file)
    
    cpu_elt_end = process.cpu_times()
    _, elt_peak_mem_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    elt_metrics["peak_memory_mb"] = round(elt_peak_mem_bytes / (1024 * 1024), 2)
    elt_metrics["cpu_user_time_sec"] = round(cpu_elt_end.user - cpu_elt_start.user, 4)
    elt_metrics["db_size_mb"] = round(os.path.getsize(elt_db_file) / (1024 * 1024), 2)
    
    # 4. Verify Data Consistency between ETL & ELT
    print("\n" + "-" * 50)
    print("[STEP 4] Verifying Data Parity & Accuracy Across Databases...")
    print("-" * 50)
    
    con_etl = duckdb.connect(etl_db_file)
    con_elt = duckdb.connect(elt_db_file)
    
    etl_fact_cnt = con_etl.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    elt_fact_cnt = con_elt.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    
    etl_net_rev = con_etl.execute("SELECT ROUND(SUM(net_amount), 2) FROM fact_sales").fetchone()[0]
    elt_net_rev = con_elt.execute("SELECT ROUND(SUM(net_amount), 2) FROM fact_sales").fetchone()[0]
    
    con_etl.close()
    con_elt.close()
    
    parity = (etl_fact_cnt == elt_fact_cnt) and (etl_net_rev == elt_net_rev)
    print(f"ETL Fact Row Count : {etl_fact_cnt:,}")
    print(f"ELT Fact Row Count : {elt_fact_cnt:,}")
    print(f"ETL Net Revenue    : ${etl_net_rev:,.2f}")
    print(f"ELT Net Revenue    : ${elt_net_rev:,.2f}")
    print(f"Data Parity Result : {'MATCH (100% Validated)' if parity else 'MISMATCH'}")
    
    # 5. Build Data Lineage Metadata
    lineage = {
        "ETL": {
            "source": ["raw_retail_sales.csv"],
            "transformations": [
                "Pandas string trim & casing",
                "Pandas currency string replace ($)",
                "Pandas date parsing & invalid row drop",
                "Pandas net_amount derivation",
                "Pandas drop_duplicates for dimensions"
            ],
            "targets": ["dim_customers", "dim_products", "dim_stores", "fact_sales"]
        },
        "ELT": {
            "source": ["raw_retail_sales.csv"],
            "ingestion": ["DuckDB read_csv_auto -> stg_raw_sales"],
            "transformations": [
                "DuckDB View stg_cleaned_sales (SQL INITCAP, LOWER, TRY_CAST)",
                "DuckDB SQL set-based DISTINCT for dimensions",
                "DuckDB SQL GROUP BY aggregate mart_daily_sales_summary"
            ],
            "targets": [
                "stg_raw_sales",
                "stg_cleaned_sales",
                "dim_customers",
                "dim_products",
                "dim_stores",
                "fact_sales",
                "mart_daily_sales_summary"
            ]
        }
    }
    
    # 6. Generate Summary Table & Export JSON
    summary_data = [
        ["Dataset Records", f"{num_records:,}", f"{num_records:,}"],
        ["Raw File Size", f"{csv_size_mb} MB", f"{csv_size_mb} MB"],
        ["Extract / Direct Ingest Time", f"{etl_metrics['extract_time_sec']}s", f"{elt_metrics['extract_load_time_sec']}s"],
        ["Transform Time", f"{etl_metrics['transform_time_sec']}s", f"{elt_metrics['transform_time_sec']}s"],
        ["Load / Warehouse Time", f"{etl_metrics['load_time_sec']}s", "0.00s (Integrated)"],
        ["Total Pipeline Runtime", f"{etl_metrics['total_time_sec']}s", f"{elt_metrics['total_time_sec']}s"],
        ["Peak Memory Usage (RAM)", f"{etl_metrics['peak_memory_mb']} MB", f"{elt_metrics['peak_memory_mb']} MB"],
        ["CPU User Mode Time", f"{etl_metrics['cpu_user_time_sec']}s", f"{elt_metrics['cpu_user_time_sec']}s"],
        ["Final DB Storage Size", f"{etl_metrics['db_size_mb']} MB", f"{elt_metrics['db_size_mb']} MB"],
        ["Clean Rows Produced", f"{etl_metrics['clean_rows_loaded']:,}", f"{elt_metrics['clean_rows_transformed']:,}"]
    ]
    
    print("\n" + "=" * 70)
    print("                     BENCHMARK RESULTS COMPARISON")
    print("=" * 70)
    headers = ["Metric / Dimension", "ETL (Pandas + DuckDB)", "ELT (DuckDB In-Database SQL)"]
    table_str = tabulate(summary_data, headers=headers, tablefmt="github")
    print(table_str)
    
    results = {
        "dataset_records": num_records,
        "raw_csv_size_mb": csv_size_mb,
        "data_parity_matched": parity,
        "etl_metrics": etl_metrics,
        "elt_metrics": elt_metrics,
        "lineage": lineage
    }
    
    json_path = os.path.join(BASE_DIR, "benchmark", "benchmark_results.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[INFO] Benchmark JSON report saved to: {json_path}")
    
    # 7. Generate Visualization Chart
    create_comparison_chart(etl_metrics, elt_metrics)
    
    return results

def create_comparison_chart(etl: dict, elt: dict):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Chart 1: Execution Time Breakdown
    categories = ['Extract/Ingest', 'Transform', 'Load', 'Total']
    etl_times = [etl['extract_time_sec'], etl['transform_time_sec'], etl['load_time_sec'], etl['total_time_sec']]
    elt_times = [elt['extract_load_time_sec'], elt['transform_time_sec'], 0.0, elt['total_time_sec']]
    
    x = list(range(len(categories)))
    width = 0.35
    
    axes[0].bar([i - width/2 for i in x], etl_times, width, label='ETL (Pandas)', color='#3498db')
    axes[0].bar([i + width/2 for i in x], elt_times, width, label='ELT (DuckDB SQL)', color='#2ecc71')
    axes[0].set_ylabel('Time (seconds)')
    axes[0].set_title('Pipeline Execution Time Comparison')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(categories)
    axes[0].legend()
    axes[0].grid(axis='y', linestyle='--', alpha=0.7)
    
    # Chart 2: Resource Utilization (Memory & Storage)
    metrics_names = ['Peak Memory (MB)', 'DB Size (MB)']
    etl_res = [etl['peak_memory_mb'], etl['db_size_mb']]
    elt_res = [elt['peak_memory_mb'], elt['db_size_mb']]
    
    x2 = list(range(len(metrics_names)))
    axes[1].bar([i - width/2 for i in x2], etl_res, width, label='ETL (Pandas)', color='#e74c3c')
    axes[1].bar([i + width/2 for i in x2], elt_res, width, label='ELT (DuckDB SQL)', color='#9b59b6')
    axes[1].set_ylabel('Megabytes (MB)')
    axes[1].set_title('Resource Utilization & Storage Footprint')
    axes[1].set_xticks(x2)
    axes[1].set_xticklabels(metrics_names)
    axes[1].legend()
    axes[1].grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    chart_path = os.path.join(BASE_DIR, "benchmark", "performance_comparison.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"[INFO] Performance chart saved to: {chart_path}")

if __name__ == "__main__":
    run_benchmarks(num_records=200000)
