# Data Integration Architecture Benchmark: ETL vs ELT

This repository contains a performance benchmark, architecture evaluation, and working implementation comparing **ETL (Extract -> Transform -> Load)** and **ELT (Extract -> Load -> Transform)** paradigms using Python, Pandas, DuckDB, and dbt.

## 📌 Project Overview

Modern enterprise data architectures face critical trade-offs between application-side transformation (ETL) and in-database set-based transformation (ELT). This project benchmarks both patterns using an unnormalized retail sales dataset containing 200,000 raw transactions.

### Key Highlights
- **ETL Implementation**: Extract CSV -> Clean & Transform in Python (Pandas) -> Load target dimensional tables into DuckDB.
- **ELT Implementation**: Extract CSV -> Load raw data directly into DuckDB staging -> Transform using set-based SQL / dbt models into dimensional target tables.
- **Parity & Validation**: Both pipelines produce identical analytical results (**194,052 clean fact records** yielding **$82,301,308.02 Net Revenue**).

## 🚀 Key Benchmark Results

| Metric | ETL (Pandas + DuckDB) | ELT (DuckDB + SQL) | Speedup / Impact |
|--------|----------------------|--------------------|------------------|
| **Transformation Time** | 5.12 s | 0.38 s | **13.4x faster** transformation |
| **Total Pipeline Time** | 5.94 s | 1.03 s | **5.78x faster** end-to-end |
| **App RAM Consumption** | ~158.5 MB | Minimal app RAM | Offloaded to C++ engine |

## 📁 Repository Structure

```
├── benchmark/
│   ├── benchmark_runner.py        # Pipeline execution & timing harness
│   ├── benchmark_results.json     # Output benchmark data
│   └── performance_comparison.png # Generated metric visual charts
├── data/
│   ├── generate_dataset.py        # Synthetic retail sales dataset generator
│   └── raw_retail_sales.csv       # Benchmark raw dataset (200k rows)
├── elt/
│   ├── elt_pipeline.py            # Python wrapper for ELT execution
│   └── dbt_project/               # dbt transformation models & profiles
│       ├── models/
│       │   ├── staging/           # Staging SQL models
│       │   └── marts/             # Target dimension & fact SQL models
│       ├── dbt_project.yml
│       └── profiles.yml
├── etl/
│   └── etl_pipeline.py            # Python Pandas ETL pipeline script
├── reports/
│   └── architecture_evaluation_report.md  # Detailed analytical report
├── .gitignore
└── README.md
```

## 🛠️ Getting Started

### 1. Prerequisites
- Python 3.10+
- Dependencies: `duckdb`, `pandas`, `matplotlib`, `dbt-duckdb`

### 2. Generate Dataset
```bash
python data/generate_dataset.py
```

### 3. Run Benchmark Suite
```bash
python benchmark/benchmark_runner.py
```

## 📜 Report & Evaluation
For a deep dive into data lineage, performance profiling, storage profiles, and strategic recommendations, see [reports/architecture_evaluation_report.md](reports/architecture_evaluation_report.md).
