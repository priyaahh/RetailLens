# ⚡ Phase 6 Cheat Sheet (5-Minute Scalable Data Platform Revision Guide)

---

## 📐 Milestone 1 Architecture

```text
Input File ──► WatermarkManager (SHA-256 Hash & High Watermark) ──► Filter New Rows ──► Anti-Join Load ──► fact_sales
```

---

## 🔑 Key Definitions

* **Incremental Load**: Processing only new or modified data records created since the last watermark timestamp, saving CPU and network resources.
* **Full Refresh**: Wiping out existing target tables and re-processing all historical data from scratch on every pipeline run.
* **Idempotency**: An engineering property where running a pipeline or query multiple times yields the exact same state as running it once.
* **High-Watermark**: Timestamp boundary representing the maximum timestamp processed in previous ETL runs (`MAX(invoice_timestamp)`).
* **Anti-Join Deduplication**: Comparing incoming batch keys against loaded DB natural keys `(invoice_no, stock_code, invoice_timestamp)` to filter out existing rows before appending.

---

## 💡 Top Milestone 1 Interview Talking Points

1. *"We achieved pipeline idempotency by combining SHA-256 file hash tracking in `etl_watermarks` with natural key anti-joins in `DatabaseLoader`."*
2. *"Our incremental processing engine reads the high-watermark timestamp (`MAX(invoice_timestamp)`) from `fact_sales` to filter out historical rows before validation and feature transformation."*
3. *"We enforced database-level idempotency by placing a composite unique constraint on `fact_sales(invoice_no, stock_code, invoice_timestamp)`."*
