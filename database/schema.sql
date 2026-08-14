-- ============================================================================
-- RetailLens PostgreSQL Analytical Database Schema DDL (Phase 6 Complete)
-- ============================================================================

-- Drop existing tables and views if re-initialization is required
DROP VIEW IF EXISTS view_data_quality_summary CASCADE;
DROP VIEW IF EXISTS view_pipeline_daily_summary CASCADE;
DROP VIEW IF EXISTS view_failed_pipeline_runs CASCADE;
DROP VIEW IF EXISTS view_latest_pipeline_runs CASCADE;
DROP VIEW IF EXISTS view_monthly_sales_summary CASCADE;
DROP VIEW IF EXISTS view_top_products CASCADE;
DROP TABLE IF EXISTS data_lineage CASCADE;
DROP TABLE IF EXISTS pipeline_runs CASCADE;
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS raw_transactions CASCADE;
DROP TABLE IF EXISTS etl_watermarks CASCADE;

-- ----------------------------------------------------------------------------
-- 1. Raw / Staging Table: raw_transactions
-- ----------------------------------------------------------------------------
CREATE TABLE raw_transactions (
    raw_id BIGSERIAL PRIMARY KEY,
    InvoiceNo VARCHAR(20) NOT NULL,
    StockCode VARCHAR(20) NOT NULL,
    Description TEXT,
    Quantity INTEGER NOT NULL,
    InvoiceDate TIMESTAMP NOT NULL,
    UnitPrice NUMERIC(10,2) NOT NULL,
    CustomerID VARCHAR(20),
    Country VARCHAR(50) NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Customer Dimension Table: dim_customer
-- ----------------------------------------------------------------------------
CREATE TABLE dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL UNIQUE,
    customer_type VARCHAR(20) NOT NULL DEFAULT 'Guest',
    country VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert Default Guest Record
INSERT INTO dim_customer (customer_id, customer_type, country)
VALUES ('GUEST', 'Guest', 'Unknown')
ON CONFLICT (customer_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 3. Product Dimension Table: dim_product
-- ----------------------------------------------------------------------------
CREATE TABLE dim_product (
    product_key SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. Processed Analytics Fact Table: fact_sales
-- Grain: One row per transaction invoice line item.
-- ----------------------------------------------------------------------------
CREATE TABLE fact_sales (
    transaction_id BIGSERIAL PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity != 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0.00),
    total_amount NUMERIC(12,2) NOT NULL,
    invoice_timestamp TIMESTAMP NOT NULL,
    invoice_year SMALLINT NOT NULL,
    invoice_month SMALLINT NOT NULL CHECK (invoice_month BETWEEN 1 AND 12),
    invoice_quarter SMALLINT NOT NULL CHECK (invoice_quarter BETWEEN 1 AND 4),
    day_of_week VARCHAR(10) NOT NULL,
    invoice_hour SMALLINT NOT NULL CHECK (invoice_hour BETWEEN 0 AND 23),
    customer_id VARCHAR(20) NOT NULL DEFAULT 'GUEST',
    customer_type VARCHAR(20) NOT NULL DEFAULT 'Guest',
    country VARCHAR(50) NOT NULL,
    is_cancellation BOOLEAN NOT NULL DEFAULT FALSE,
    revenue_bucket VARCHAR(30) NOT NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_fact_sales_natural_key UNIQUE (invoice_no, stock_code, invoice_timestamp)
);

-- ----------------------------------------------------------------------------
-- 5. Incremental Watermark & File Audit Table: etl_watermarks
-- ----------------------------------------------------------------------------
CREATE TABLE etl_watermarks (
    watermark_id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    high_watermark_timestamp TIMESTAMP,
    rows_processed INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 6. Pipeline Execution Run Audit Table: pipeline_runs (Phase 6 Milestone 2)
-- ----------------------------------------------------------------------------
CREATE TABLE pipeline_runs (
    run_id VARCHAR(36) PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL DEFAULT 'RetailLens_ETL',
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    source_file TEXT NOT NULL,
    source_hash VARCHAR(64) NOT NULL,
    rows_read INTEGER NOT NULL DEFAULT 0,
    rows_valid INTEGER NOT NULL DEFAULT 0,
    rows_invalid INTEGER NOT NULL DEFAULT 0,
    rows_transformed INTEGER NOT NULL DEFAULT 0,
    rows_inserted INTEGER NOT NULL DEFAULT 0,
    rows_skipped INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    execution_duration NUMERIC(10,3) DEFAULT 0.0,
    watermark_before TIMESTAMP,
    watermark_after TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 7. Data Lineage Metadata Table: data_lineage (Phase 6 Milestone 3)
-- ----------------------------------------------------------------------------
CREATE TABLE data_lineage (
    lineage_id SERIAL PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    source_file TEXT NOT NULL,
    source_hash VARCHAR(64) NOT NULL,
    source_row_count INTEGER NOT NULL DEFAULT 0,
    target_table VARCHAR(100) NOT NULL DEFAULT 'fact_sales',
    target_row_count INTEGER NOT NULL DEFAULT 0,
    transformation_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 8. Analytical & Audit B-Tree Indexes
-- ----------------------------------------------------------------------------
CREATE INDEX idx_fact_sales_invoice_no ON fact_sales(invoice_no);
CREATE INDEX idx_fact_sales_customer_id ON fact_sales(customer_id);
CREATE INDEX idx_fact_sales_stock_code ON fact_sales(stock_code);
CREATE INDEX idx_fact_sales_timestamp ON fact_sales(invoice_timestamp);
CREATE INDEX idx_fact_sales_country ON fact_sales(country);
CREATE INDEX idx_fact_sales_year_month ON fact_sales(invoice_year, invoice_month);
CREATE INDEX idx_fact_sales_cancellation ON fact_sales(is_cancellation);
CREATE INDEX idx_pipeline_runs_started ON pipeline_runs(started_at DESC);
CREATE INDEX idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX idx_data_lineage_run_id ON data_lineage(run_id);

-- ----------------------------------------------------------------------------
-- 9. Analytical Views
-- ----------------------------------------------------------------------------
CREATE VIEW view_monthly_sales_summary AS
SELECT 
    invoice_year,
    invoice_month,
    COUNT(DISTINCT invoice_no) AS total_orders,
    SUM(total_amount) AS total_revenue,
    SUM(quantity) AS total_units_sold,
    COUNT(DISTINCT CASE WHEN customer_id != 'GUEST' THEN customer_id END) AS active_registered_customers
FROM fact_sales
WHERE is_cancellation = FALSE
GROUP BY invoice_year, invoice_month
ORDER BY invoice_year DESC, invoice_month DESC;

CREATE VIEW view_top_products AS
SELECT 
    stock_code,
    description,
    SUM(total_amount) AS total_revenue,
    SUM(quantity) AS total_quantity_sold,
    COUNT(DISTINCT invoice_no) AS total_orders
FROM fact_sales
WHERE is_cancellation = FALSE
GROUP BY stock_code, description
ORDER BY total_revenue DESC;

-- ----------------------------------------------------------------------------
-- 10. Operational Monitoring Views (Phase 6 Milestone 8)
-- ----------------------------------------------------------------------------
CREATE VIEW view_latest_pipeline_runs AS
SELECT 
    run_id,
    pipeline_name,
    source_file,
    status,
    started_at,
    completed_at,
    rows_read,
    rows_inserted,
    rows_skipped,
    rows_invalid,
    execution_duration
FROM pipeline_runs
ORDER BY started_at DESC
LIMIT 50;

CREATE VIEW view_failed_pipeline_runs AS
SELECT 
    run_id,
    pipeline_name,
    source_file,
    started_at,
    error_message,
    execution_duration
FROM pipeline_runs
WHERE status = 'FAILED'
ORDER BY started_at DESC;

CREATE VIEW view_pipeline_daily_summary AS
SELECT 
    DATE(started_at) AS run_date,
    COUNT(*) AS total_runs,
    COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) AS successful_runs,
    COUNT(CASE WHEN status = 'FAILED' THEN 1 END) AS failed_runs,
    SUM(rows_read) AS total_rows_read,
    SUM(rows_inserted) AS total_rows_inserted,
    SUM(rows_skipped) AS total_rows_skipped,
    ROUND(AVG(execution_duration), 2) AS avg_duration_seconds
FROM pipeline_runs
GROUP BY DATE(started_at)
ORDER BY run_date DESC;

CREATE VIEW view_data_quality_summary AS
SELECT 
    run_id,
    source_file,
    rows_read,
    rows_valid,
    rows_invalid,
    CASE 
        WHEN rows_read > 0 THEN ROUND((1.0 * rows_valid / rows_read) * 100, 2)
        ELSE 100.00 
    END AS data_quality_rate_pct,
    started_at
FROM pipeline_runs
ORDER BY started_at DESC;
