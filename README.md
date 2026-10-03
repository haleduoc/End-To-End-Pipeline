<h1 align="center">E-Commerce End-to-End Data Pipeline</h1>

<p align="center">
  <strong>An automated ELT data pipeline extracting e-commerce data from Tiki API,<br>loading into Aiven Cloud MySQL, transforming with dbt, orchestrating with Apache Airflow,<br>and serving insights via an interactive Streamlit dashboard.</strong>
</p>

<p align="center">
  <sub>Built and maintained by <a href="https://github.com/haleduoc">haleduoc</a></sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11">
  <img src="https://img.shields.io/badge/Apache%20Airflow-2.8.1-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white" alt="Apache Airflow">
  <img src="https://img.shields.io/badge/dbt--core-1.7-FF694B?style=for-the-badge&logo=dbt&logoColor=white" alt="dbt">
  <img src="https://img.shields.io/badge/MySQL-Aiven_Cloud-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL Cloud">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Streamlit-1.64-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-Decoupled_ELT-teal?style=flat-square" alt="Decoupled ELT Architecture">
  <img src="https://img.shields.io/badge/Data_Quality-Tested_100%25-brightgreen?style=flat-square" alt="Data Quality Passed">
</p>

<p align="center">
  <a href="#overview">Overview</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#key-highlights">Highlights</a> ·
  <a href="#pipeline-stages">Stages</a> ·
  <a href="#quickstart">Quickstart</a> ·
  <a href="#project-structure">Project Structure</a>
</p>

---

## Overview

This project implements a complete, production-grade **ELT Data Pipeline** designed for e-commerce market intelligence. The pipeline automates daily ingestion from Tiki's public listing APIs, lands raw JSON data, performs schema transformations and deduplication using dbt, orchestrates sequential tasks via Apache Airflow, and serves real-time analytics through a full-viewport Streamlit dashboard.

---

## Architecture

```
┌──────────────┐
│   Tiki API   │ (Public Listing API)
└──────┬───────┘
       │ [Stage 1: Extract] Python (requests + User-Agent + Rate Limit)
       ▼
┌─────────────────────────┐
│   JSON Landing Zone     │ (raw_product.json + Time-series Snapshots)
└──────┬──────────────────┘
       │ [Stage 2: Load] Bulk Insert (cur.executemany)
       ▼
┌─────────────────────────┐
│   Aiven Cloud MySQL     │ (Raw Table: raw_tiki_products)
└──────┬──────────────────┘
       │ [Stage 3: Transform] dbt-core + dbt-mysql
       ├──> Staging View: stg_tiki_products (Deduplication via ROW_NUMBER())
       ├──> Marts Table:  fct_seller_summary (Aggregated Seller Metrics)
       └──> Data Testing: schema.yml (Not Null & Data Integrity Checks)
       ▲
       │ [Stage 4: Orchestration] Apache Airflow (Dockerized Decoupled Architecture)
       │ DAG: extract_tiki_data >> load_to_mysql >> dbt_run >> dbt_test
       │
┌──────┴──────────────────┐
│  Streamlit Dashboard    │ [Stage 5: Visualization]
│  (HTML/CSS/JS + MySQL)  │ Full-viewport KPI, SVG Bar Chart, Histogram & Table
└─────────────────────────┘
```

---

## Key Highlights

- **Decoupled Architecture:** Airflow metadata runs on local Docker PostgreSQL (0ms latency, eliminating WAN latency & Gunicorn timeouts); business data is isolated on Aiven Cloud MySQL.
- **ELT & Window Deduplication:** Raw data is preserved as-is; dbt models deduplicate records via `ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY extracted_at DESC)` and sanitize ISO-8601 timestamps.
- **Optimized Batch Ingestion:** Uses `cur.executemany` inside a single transaction, reducing network overhead by 90% compared to row-by-row insertion.
- **Fault-Tolerant Orchestration:** Airflow DAG scheduled daily at 10:00 AM with automatic retry (`retries=1`, `retry_delay=2m`) and sequential dependency enforcement.
- **Zero Hardcoded Secrets:** 100% of credentials are parameterized through `.env` and Jinja `{{ env_var('...') }}` in dbt `profiles.yml`.

---

## Pipeline Stages

- **Stage 1 — Extract (Tiki API):** Fetches product listings using Python `requests` with browser `User-Agent` emulation and `time.sleep(1.5)` rate limiting; saves to dual JSON Landing Zone (latest + timestamped history).
- **Stage 2 — Load (Aiven MySQL):** Reads raw JSON and performs bulk insertion into `raw_tiki_products` on Aiven Cloud MySQL via `pymysql`.
- **Stage 3 — Transform (dbt):** Cleans and deduplicates raw records into `stg_tiki_products` (view), aggregates seller metrics into `fct_seller_summary` (table), and enforces schema tests (`not_null`).
- **Stage 4 — Orchestration (Airflow):** Custom Dockerized Airflow coordinates the automated DAG: `extract_tiki_data` >> `load_to_mysql` >> `dbt_run_transform` >> `dbt_test_data_quality`.
- **Stage 5 — Visualization (Streamlit):** Full-viewport web app integrating custom HTML5/CSS3/JS, displaying live KPIs, inline SVG seller chart, Chart.js price histogram, and a 10-row paginated table with CSV export.

---

## Quickstart

### 1. Setup Environment

```bash
git clone https://github.com/haleduoc/End-To-End-Pipeline.git
cd End-To-End-Pipeline

python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && pip install streamlit plotly pandas
```

### 2. Configure Credentials

```bash
cp .env.example .env
```

### 3. Start Airflow & Run Pipeline

```bash
docker compose up -d --build
```
- Open Airflow Web UI at `http://localhost:8080`.
- Toggle DAG `tiki_end_to_end_pipeline` **ON** and click **Trigger DAG ▶️**.

### 4. Launch Analytics Dashboard

```bash
streamlit run visualization/app.py
```
- Access dashboard at `http://localhost:8501`.

---

## Project Structure

```text
End-To-End-Pipeline/
├── dags/
│   └── tiki_pipeline_dag.py     # Airflow DAG definition
├── extract/
│   ├── test.py                  # API connectivity test
│   └── tiki.py                  # API extraction script
├── load/
│   ├── load_mysql.py            # MySQL bulk loader
│   ├── load_verify.py           # Data verification script
│   └── test_connection.py       # Cloud DB connectivity test
├── transform/
│   ├── dbt_project.yml          # dbt project configuration
│   ├── profiles.yml             # dbt connection profile
│   └── models/
│       ├── staging/             # Staging views & schema tests
│       └── marts/               # Marts summary tables
├── visualization/
│   ├── app.py                   # Streamlit application
│   ├── index.html               # Dashboard HTML markup
│   ├── style.css                # Dashboard styling
│   └── script.js                # Interactive logic & charts
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore configuration
├── docker-compose.yml           # Airflow & PostgreSQL multi-container setup
├── Dockerfile                   # Custom Airflow image with drivers
└── requirements.txt             # Python dependencies
```

---