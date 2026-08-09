# ⚡ PostgreSQL Query Performance & Indexing Notes

This document provides a technical performance review of the **RetailLens PostgreSQL Analytical Database Layer** (Phase 3). It details index structures, execution plan analysis, and query optimization techniques.

---

## 📌 1. Indexing Strategy & B-Tree Mechanics

PostgreSQL defaults to **B-Tree (Balanced Tree)** index structures, which maintain sorted pointers to table rows in $O(\log N)$ search time.

### RetailLens Index Catalog (`database/schema.sql`)

| Index Name | Target Column(s) | Analytical Access Pattern Improved | Index Selectivity |
| :--- | :--- | :--- | :--- |
| `idx_fact_sales_invoice_no` | `fact_sales(invoice_no)` | Invoice-level aggregations (`COUNT(DISTINCT invoice_no)`), order lookups, and cancellation rate joins. | High (Distinct invoices) |
| `idx_fact_sales_customer_id` | `fact_sales(customer_id)` | Customer cohort analysis, Customer Lifetime Value (CLV), and registered vs guest spending queries. | High (Distinct buyers) |
| `idx_fact_sales_stock_code` | `fact_sales(stock_code)` | Product performance rankings, revenue by product, and inventory volume sales. | Medium-High |
| `idx_fact_sales_timestamp` | `fact_sales(invoice_timestamp)`| Date truncation (`DATE_TRUNC('day', invoice_timestamp)`), daily trend analysis, and time-series charts. | High (Continuous timestamps)|
| `idx_fact_sales_country` | `fact_sales(country)` | Geographic revenue breakdowns (`GROUP BY country`). | Low-Medium (Few unique countries)|
| `idx_fact_sales_year_month` | `fact_sales(invoice_year, invoice_month)` | **Composite Index**: Accelerates monthly sales summary queries without requiring full table scans. | High (Multi-column compound) |
| `idx_fact_sales_cancellation` | `fact_sales(is_cancellation)` | Filtered queries excluding returns (`WHERE is_cancellation = FALSE`). | Low (Boolean cardinality) |

---

## 🔍 2. Execution Plan Analysis (`EXPLAIN` & `EXPLAIN ANALYZE`)

### `EXPLAIN` vs `EXPLAIN ANALYZE`
* `EXPLAIN <query>`: Displays the PostgreSQL Query Planner's **estimated** execution plan and cost parameters without executing the SQL query.
* `EXPLAIN ANALYZE <query>`: Actually **executes** the SQL query, displaying both the estimated cost and the true execution timing metrics (in milliseconds), actual row counts, and memory usage.

### Execution Scan Types:
1. **Sequential Scan (`Seq Scan`)**: Reads every page of the table from disk sequentially. Used when tables are small or when a query retrieves a large percentage of total table rows.
2. **Index Scan (`Index Scan`)**: Traverses the B-Tree index to locate row pointers (`TID`), then fetches matching row data pages from the table.
3. **Index Only Scan (`Index Only Scan`)**: The fastest scan type; retrieves requested columns directly from the index structure without touching the main table heap pages.
4. **Bitmap Index Scan**: Scans the index to build a bitmask of matching pages, then reads table heap pages in sequential disk order, minimizing random I/O disk seeks.

---

## 💡 3. Key Query Optimization Patterns Applied

### 1. Filter Before Aggregating (`WHERE` before `GROUP BY`)
Filtering out cancellations (`WHERE is_cancellation = FALSE`) *before* executing `SUM(total_amount)` reduces the dataset size in memory before grouping.

### 2. Avoid Functions on Indexed Columns in `WHERE` Clauses
* ❌ **Slow**: `WHERE EXTRACT(YEAR FROM invoice_timestamp) = 2010` (Forces sequential scan because PostgreSQL cannot use `idx_fact_sales_timestamp` on wrapped functions).
* ✅ **Fast**: `WHERE invoice_year = 2010` (Uses composite index `idx_fact_sales_year_month` or date range bounds `WHERE invoice_timestamp >= '2010-01-01' AND invoice_timestamp < '2011-01-01'`).

### 3. Protecting Division-by-Zero via `NULLIF()`
```sql
-- Prevents division-by-zero runtime exceptions if count of orders is 0
SELECT SUM(total_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0) FROM fact_sales;
```

### 4. Avoiding `SELECT *` in Production Queries
In `SQLAnalyticsService`, queries select explicit columns (`invoice_no`, `total_amount`), enabling PostgreSQL to execute Index Only Scans and reducing network payload sizes.
