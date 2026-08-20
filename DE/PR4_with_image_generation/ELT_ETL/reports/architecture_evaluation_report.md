# Data Integration Architecture Evaluation Report: ETL vs ELT

## 1. Executive Summary

Modern enterprise analytics platforms require high-throughput, low-latency data integration. This laboratory experiment designs, implements, and evaluates two foundational data architecture paradigms—**ETL (Extract -> Transform -> Load)** and **ELT (Extract -> Load -> Transform)**—using an identical unnormalized retail sales dataset containing 200,000 raw transactions (32.8 MB CSV).

Using **Python (Pandas)** for application-side ETL transformations and **DuckDB** as the analytical database engine for ELT set-based SQL transformations, both pipelines were executed under identical hardware conditions. The transformed target models were verified to ensure 100% data parity (**194,052 clean fact records** yielding **$82,301,308.02 in Net Revenue**).

### Key Empirical Findings
- **Execution Performance**: ELT completed the end-to-end pipeline in **1.0263 seconds**, whereas ETL took **5.9357 seconds**. ELT achieved a **5.78x speedup** overall.
- **Transformation Velocity**: In-database SQL transformations (**0.3816 seconds**) outperformed Python Pandas memory-bound transformations (**5.1246 seconds**) by **13.4x**.
- **Memory Efficiency**: ETL consumed **158.49 MB of application RAM**, whereas ELT offloaded transformation execution entirely to DuckDB's vectorized C++ execution engine, minimizing memory footprint on the application server.
- **Storage Profile**: ETL stored clean normalized tables (5.01 MB), whereas ELT stored raw staging tables alongside target marts (10.26 MB), reflecting the storage trade-off inherent in preserving raw data lineage.

---

## 2. Architectural Comparison & Lineage

### ETL Architecture (Pandas + DuckDB)
In traditional ETL, data transformation occurs on an intermediate application server prior to loading cleaned data into the destination database.

```
┌───────────────────────────────┐
│ Raw Retail CSV (32.8 MB)      │
└───────────────┬───────────────┘
                │ Extract: pd.read_csv()
                ▼
┌───────────────────────────────┐
│ Python Application Server RAM │
│ • Pandas vectorized regex     │
│ • String trimming & casing    │
│ • Date parsing & filtering    │
│ • Dimensional split           │
└───────────────┬───────────────┘
                │ Load: CREATE TABLE AS SELECT
                ▼
┌───────────────────────────────┐
│ DuckDB Target Database        │
│ • dim_customers, dim_products │
│ • dim_stores, fact_sales      │
└───────────────────────────────┘
```

**Characteristics**:
1. Transformations are memory-bound to the application process.
2. Only clean, normalized data enters the database warehouse.
3. Raw data is ephemeral; full historical lineage requires external data lake archives.

---

### ELT Architecture (DuckDB SQL + dbt)
In modern cloud-native ELT, raw data is directly loaded into a staging layer within the target analytical engine. Transformations are executed using SQL pushdown.

```
┌───────────────────────────────┐
│ Raw Retail CSV (32.8 MB)      │
└───────────────┬───────────────┘
                │ Extract & Load: read_csv_auto()
                ▼
┌───────────────────────────────┐
│ DuckDB Staging Database       │
│ • stg_raw_sales (Raw CSV)     │
└───────────────┬───────────────┘
                │ Transform: Vectorized C++ SQL Engine
                ▼
┌───────────────────────────────┐
│ Analytical Warehouses & Marts │
│ • stg_cleaned_sales (View)    │
│ • dim_customers, dim_products │
│ • fact_sales                  │
│ • mart_daily_sales_summary    │
└───────────────────────────────┘
```

**Characteristics**:
1. Raw transactions are preserved immediately upon landing.
2. Transformations leverage database query optimization, columnar vectorization, and multi-threading.
3. Full data lineage (Raw -> Staging -> Dimensions -> Marts) is tracked directly via SQL views and dbt DAGs.

---

## 3. Empirical Performance & Resource Benchmark

Both pipelines were benchmarked on a 200,000-record retail sales dataset.

### Benchmark Metrics Matrix

| Evaluation Dimension | ETL Pipeline (Pandas) | ELT Pipeline (DuckDB SQL) | Performance Delta / Advantage |
| :--- | :--- | :--- | :--- |
| **Dataset Raw Records** | 200,000 rows | 200,000 rows | Identical Input |
| **Raw Dataset Size** | 32.80 MB | 32.80 MB | Identical Input |
| **Extract / Ingestion Time** | 0.5259 sec | 0.6098 sec | ETL Pandas Extract (+13.7% faster) |
| **Transformation Time** | 5.1246 sec | 0.3816 sec | **ELT SQL (13.4x faster)** |
| **Load / Warehouse Write** | 0.2850 sec | 0.0000 sec (Integrated) | ELT eliminates load step |
| **Total End-to-End Runtime** | **5.9357 sec** | **1.0263 sec** | **ELT Pipeline (5.78x overall speedup)** |
| **Peak Memory Usage (RAM)** | **158.49 MB** | **< 0.01 MB (App Heap)** | **ELT (100% RAM offload to DB)** |
| **CPU User Mode Time** | 5.8438 sec | 1.1406 sec | ELT uses 80.5% less CPU time |
| **Target Database Storage Size**| 5.01 MB | 10.26 MB | ETL database footprint 51% smaller |
| **Clean Fact Rows Produced** | 194,052 rows | 194,052 rows | **100% Data Parity Verified** |
| **Total Net Revenue Calculated**| $82,301,308.02 | $82,301,308.02 | **100% Financial Accuracy** |

---

## 4. Architectural Trade-off & Suitability Analysis

```
                    ETL vs ELT Trade-off Spectrum

    [ ETL Focus ]                                     [ ELT Focus ]
 --------------------                              --------------------
 • Privacy & Compliance                            • Query Performance
 • Legacy Warehouses                               • Storage Elasticity
 • Upfront Data Quality                            • Self-Service Analytics
 • Low Storage Footprint                           • Complete Data Lineage
```

### Comparative Evaluation Matrix

| Criteria | ETL (Extract-Transform-Load) | ELT (Extract-Load-Transform) |
| :--- | :--- | :--- |
| **Performance & Scalability** | Limited by application server memory/CPU. Hard to scale horizontally without cluster frameworks (e.g. PySpark). | Highly scalable. Offloads processing to MPP cloud engines (Snowflake, BigQuery, DuckDB). |
| **Data Lineage & Traceability** | Low. Raw data is transformed in-flight and lost unless explicitly logged to storage. | High. Raw data is preserved in staging; lineage is documented via dbt DAGs. |
| **Resource Utilization** | High CPU and RAM burden on extract/application servers. | Low app server footprint; compute cost moved to cloud database warehouse. |
| **Maintainability & DX** | Complex Python Pandas code requiring custom unit tests, error handling, and memory optimization. | High DX using declarative SQL, Jinja templating, modular dbt models, and automated SQL testing. |
| **Data Flexibility** | Low. Schema must be predefined before loading. Transformation logic changes require full re-ingestion. | High. Raw data is stored once; business transformations can be re-run or altered retroactively. |
| **Security & Privacy (GDPR)** | High. Sensitive PII can be sanitized/masked before entering the data warehouse. | Requires row/column-level access control within staging tables to restrict unmasked raw PII. |

---

## 5. Modern Modular Transformations with dbt

In modern data engineering workflows, ELT pipeline transformations are managed declaratively using **dbt (data build tool)**.

### Benefits of dbt Modular Transformations:
1. **Modular SQL**: Transformations are partitioned into logical layers:
   - `staging/stg_raw_retail_sales.sql`: Type casting, trimming, string regex.
   - `marts/dim_customers.sql`, `dim_products.sql`: Deduplicated dimensions.
   - `marts/fact_sales.sql`: Clean transaction facts with business metrics (`net_amount`).
   - `marts/mart_daily_sales_summary.sql`: Pre-aggregated reporting tables.
2. **Automated Lineage Graphs**: dbt builds a Directed Acyclic Graph (DAG) mapping `stg_raw_sales` -> `stg_cleaned_sales` -> `fact_sales` -> `mart_daily_sales_summary`.
3. **Data Governance & Testing**: Declarative schema tests (`not_null`, `unique`, `foreign_key`) guarantee data quality without imperative python checks.

---

## 6. Architectural Recommendations

1. **Adopt ELT for Modern Cloud Data Warehouses**:
   When using modern columnar analytical engines (DuckDB, Snowflake, Google BigQuery, AWS Redshift), **ELT is the recommended architecture**. SQL pushdown achieves superior vectorization, parallel processing, and drastically reduces compute time.

2. **Reserve ETL for Compliance & Edge Processing**:
   Use **ETL** when handling strict regulatory privacy mandates (e.g. GDPR/HIPAA PII masking before cloud upload), streaming edge data ingestion, or when target database storage costs heavily outweigh compute costs.

---

*Report generated automatically from empirical benchmark execution on 200,000 retail sales transactions.*
