# 🔍 SQL Analytics Reference & Concept Guide

This document serves as a comprehensive technical guide to SQL syntax, query execution orders, functions, and relational database patterns used in RetailLens.

---

## 📐 1. SQL Logical Query Execution Order

When a database engine processes a SQL query, it executes clauses in a strict logical order (not the visual written order):

```text
1. FROM / JOIN     ──────► Identifies source tables and executes joins
2. WHERE           ──────► Filters raw individual rows BEFORE aggregation
3. GROUP BY        ──────► Groups matching rows into aggregated buckets
4. HAVING          ──────► Filters aggregated group buckets AFTER aggregation
5. SELECT          ──────► Computes select expressions, column aliases, and aggregates
6. WINDOW          ──────► Evaluates window functions (RANK, LAG, SUM OVER)
7. DISTINCT        ──────► Removes duplicate rows from result set
8. ORDER BY        ──────► Sorts output rows by specified columns
9. LIMIT / OFFSET  ──────► Restricts returned row count
```

---

## 🛠️ 2. Core SQL Functions & Expressions

### Aggregations & Null Protection
* `SUM(column)`: Calculates total sum of numeric column values.
* `COUNT(DISTINCT column)`: Returns total unique non-null values.
* `AVG(column)`: Computes arithmetic mean.
* `COALESCE(val1, val2)`: Returns the first non-null argument.
* `NULLIF(val1, val2)`: Returns `NULL` if `val1 == val2`, preventing division-by-zero errors.

### Case Statements
```sql
CASE 
    WHEN condition THEN result
    ELSE fallback
END
```

---

## 🪟 3. Advanced Window Functions

Window functions perform calculations across a set of table rows related to the current row without collapsing rows into a single summary output.

```sql
FUNCTION() OVER (
    PARTITION BY group_column 
    ORDER BY sort_column ASC/DESC
)
```

### Key Window Functions:
1. `ROW_NUMBER()`: Assigns unique sequential integer to each row.
2. `RANK()`: Assigns rank with gaps on ties (1, 2, 2, 4).
3. `DENSE_RANK()`: Assigns rank without gaps on ties (1, 2, 2, 3).
4. `LAG(column, offset)`: Accesses data from a previous row in the partition (used for MoM growth).
5. `LEAD(column, offset)`: Accesses data from a subsequent row in the partition.
6. `SUM(column) OVER (ORDER BY date)`: Calculates running cumulative sum.

---

## 📅 4. Date & Time Analytics Functions

* `DATE_TRUNC('month', timestamp)`: Truncates timestamp to the first day of specified interval (e.g. `'2010-12-01 00:00:00'`).
* `EXTRACT(MONTH FROM timestamp)`: Returns numerical integer part (e.g., `12`).
* `TIMESTAMP` vs `TIMESTAMPTZ`: `TIMESTAMP` stores date and time without time zone offset; `TIMESTAMPTZ` converts timestamps to UTC for storage and converts to client local timezone on retrieval.
