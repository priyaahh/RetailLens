# 📈 Analytics Engine & Repository Pattern Notes

This document details the software design patterns, metrics architecture, and insight generation engine of the **RetailLens Analytics Layer**.

---

## 🏛️ 1. The Repository Pattern

The **Repository Pattern** abstracts database data access behind a domain-oriented interface. In RetailLens:

* **Separation of Concerns**: The Streamlit UI does not know or care whether data comes from PostgreSQL, SQLite, or an API.
* **Testability**: Analytics services and KPI engines can be unit tested independently of a live database connection by injecting mock repositories or in-memory SQLite instances.
* **Parameterization**: `AnalyticsRepository` constructs safe parameterized SQL queries, preventing SQL injection vulnerabilities.

---

## 📊 2. KPI Metric Taxonomy

| KPI Category | Metric Name | Formula / Query | Business Context |
| :--- | :--- | :--- | :--- |
| **CORE** | Total Net Revenue | `SUM(total_amount) WHERE is_cancellation = FALSE` | Gross revenue generated across all completed sales orders. |
| **CORE** | Average Order Value (AOV) | `SUM(total_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0)` | Average monetary spend per completed invoice order. |
| **CANCELLATION** | Cancellation Rate % | `(Cancelled Invoices / Total Invoices) * 100` | Percentage of generated invoices representing returns or cancellations. |
| **SALES** | MoM Revenue Growth % | `((Current Month Rev - Previous Month Rev) / Previous Month Rev) * 100` | Monthly revenue expansion or contraction trajectory. |
| **CUSTOMER** | Repeat Customer Rate % | `(Registered Customers with > 1 Order / Total Registered Customers) * 100` | Loyalty indicator measuring customer retention. |

---

## 💡 3. Automated Insight Generation Architecture

`InsightEngine` evaluates calculated metrics against configurable thresholds to produce structured `Insight` objects:

```text
Calculated Metrics ──► InsightEngine (Threshold Check) ──► Structured Insight Object
                                                                │
                                                                ├─► Severity: CRITICAL / HIGH / MEDIUM / LOW
                                                                ├─► Metric & Value: "Cancellation Rate = 12.5%"
                                                                ├─► Threshold: "10.0%"
                                                                └─► Action: "Audit top returned stock items..."
```
