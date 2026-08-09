-- ============================================================================
-- RetailLens PostgreSQL Analytical Database Schema DDL (Phase 3)
-- ============================================================================

-- Drop existing tables and views if re-initialization is required
DROP VIEW IF EXISTS view_monthly_sales_summary CASCADE;
DROP VIEW IF EXISTS view_top_products CASCADE;
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS raw_transactions CASCADE;

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
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 5. Analytical B-Tree Indexes
-- ----------------------------------------------------------------------------
CREATE INDEX idx_fact_sales_invoice_no ON fact_sales(invoice_no);
CREATE INDEX idx_fact_sales_customer_id ON fact_sales(customer_id);
CREATE INDEX idx_fact_sales_stock_code ON fact_sales(stock_code);
CREATE INDEX idx_fact_sales_timestamp ON fact_sales(invoice_timestamp);
CREATE INDEX idx_fact_sales_country ON fact_sales(country);
CREATE INDEX idx_fact_sales_year_month ON fact_sales(invoice_year, invoice_month);
CREATE INDEX idx_fact_sales_cancellation ON fact_sales(is_cancellation);

-- ----------------------------------------------------------------------------
-- 6. Analytical Views
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
