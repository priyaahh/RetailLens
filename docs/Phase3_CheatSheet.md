# ⚡ Phase 3 Cheat Sheet (5-Minute SQL & Analytics Revision Guide)

---

## 📐 Architecture Flow

```text
Streamlit UI  ──►  SQLAnalyticsService / KPICalculator  ──►  SQLAlchemy Pool  ──►  PostgreSQL fact_sales
```

---

## 🔑 Key SQL Formulas & Patterns

* **Average Order Value (AOV)**:
  ```sql
  SELECT ROUND(SUM(total_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2) FROM fact_sales WHERE is_cancellation = FALSE;
  ```
* **Cancellation Rate %**:
  ```sql
  SELECT ROUND((COUNT(DISTINCT CASE WHEN is_cancellation = TRUE THEN invoice_no END)::NUMERIC / NULLIF(COUNT(DISTINCT invoice_no), 0)) * 100, 2) FROM fact_sales;
  ```
* **Month-over-Month (MoM) Growth Rate**:
  ```sql
  LAG(revenue, 1) OVER (ORDER BY invoice_year, invoice_month)
  ```
* **Category Rank**:
  ```sql
  DENSE_RANK() OVER (PARTITION BY country ORDER BY SUM(total_amount) DESC)
  ```
* **Cumulative Running Revenue**:
  ```sql
  SUM(daily_revenue) OVER (ORDER BY sales_date ASC)
  ```

---

## 💡 Top 5 Phase 3 Interview Talking Points

1. *"We separate fact data (`fact_sales`) from dimensional attributes (`dim_customer`, `dim_product`), indexing key join and filter columns with B-Tree indexes for sub-second query performance."*
2. *"Our KPI layer (`KPICalculator`) executes direct SQL aggregations in PostgreSQL using `COALESCE` and `NULLIF`, returning single 8-byte scalar values over the network rather than loading 500,000 raw rows into Python memory."*
3. *"We use native PostgreSQL window functions (`DENSE_RANK()`, `LAG()`) inside CTEs to calculate Month-over-Month growth and country product rankings in a single pass without expensive self-joins."*
4. *"All SQL queries in `SQLAnalyticsService` use parameterized bindings (`text()`) to eliminate SQL injection vulnerabilities and decouple query execution from Streamlit UI code."*
5. *"We use composite indexes (`idx_fact_sales_year_month`) and pre-calculated temporal features (`invoice_year`, `invoice_month`) to avoid running `EXTRACT()` functions on indexed columns during query execution."*
