"""
repository.py
-------------
Analytics Repository Data Access Layer for RetailLens.
Executes parameterized PostgreSQL SQL queries via SQLAlchemy engine connection pooling,
decoupling database access from business KPI composition and Streamlit UI pages.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from analytics.exceptions import DatabaseConnectionError, RepositoryError
from analytics.models import FilterParams
from database.connection import get_db_engine

logger = logging.getLogger(__name__)


class AnalyticsRepository:
    """Repository pattern encapsulating all PostgreSQL data-access queries for analytics."""

    def __init__(self, engine: Optional[Engine] = None):
        """Dependency injection constructor for SQLAlchemy Engine."""
        try:
            self.engine = engine or get_db_engine()
        except Exception as e:
            logger.error("Failed to initialize database engine in AnalyticsRepository: %s", str(e))
            raise DatabaseConnectionError(f"Database connection initialization failed: {str(e)}")

    def _build_where_clause(self, filters: Optional[FilterParams] = None) -> Tuple[str, Dict[str, Any]]:
        """Constructs parameterized WHERE clause conditions and parameters dictionary."""
        conditions = ["1=1"]
        params: Dict[str, Any] = {}

        if not filters:
            return "WHERE 1=1", params

        filters.validate()

        if filters.start_date:
            conditions.append("invoice_timestamp >= :start_date")
            params["start_date"] = f"{filters.start_date} 00:00:00"

        if filters.end_date:
            conditions.append("invoice_timestamp <= :end_date")
            params["end_date"] = f"{filters.end_date} 23:59:59"

        if filters.country and filters.country != "All Countries":
            conditions.append("country = :country")
            params["country"] = filters.country

        if filters.customer_type and filters.customer_type != "All":
            conditions.append("customer_type = :customer_type")
            params["customer_type"] = filters.customer_type

        if filters.transaction_type == "Sales":
            conditions.append("(is_cancellation = FALSE OR is_cancellation = 0)")
        elif filters.transaction_type == "Cancellations":
            conditions.append("(is_cancellation = TRUE OR is_cancellation = 1)")

        where_sql = "WHERE " + " AND ".join(conditions)
        return where_sql, params

    def _execute_query(self, query_sql: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Executes a parameterized SQL query safely and returns a Pandas DataFrame."""
        try:
            with self.engine.connect() as conn:
                logger.debug("Executing analytics SQL query...")
                df = pd.read_sql_query(sql=text(query_sql), con=conn, params=params or {})
                return df
        except Exception as e:
            logger.error("Repository error executing query: %s", str(e), exc_info=True)
            raise RepositoryError(f"Query execution failed: {str(e)}")

    def _execute_scalar(self, query_sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Executes a single-scalar SQL query safely."""
        try:
            with self.engine.connect() as conn:
                return conn.execute(text(query_sql), params or {}).scalar()
        except Exception as e:
            logger.error("Repository error executing scalar query: %s", str(e), exc_info=True)
            raise RepositoryError(f"Scalar query execution failed: {str(e)}")

    # -------------------------------------------------------------------------
    # CORE METRIC DATA ACCESS
    # -------------------------------------------------------------------------

    def get_total_revenue(self, filters: Optional[FilterParams] = None) -> float:
        """Retrieves total net monetary revenue excluding cancellations."""
        where_sql, params = self._build_where_clause(filters)
        if "is_cancellation" not in where_sql:
            where_sql += " AND (is_cancellation = FALSE OR is_cancellation = 0)"
        query = f"SELECT COALESCE(SUM(total_amount), 0.00) FROM fact_sales {where_sql};"
        val = self._execute_scalar(query, params)
        return float(val or 0.0)

    def get_total_orders(self, filters: Optional[FilterParams] = None) -> int:
        """Retrieves distinct completed orders count."""
        where_sql, params = self._build_where_clause(filters)
        if "is_cancellation" not in where_sql:
            where_sql += " AND (is_cancellation = FALSE OR is_cancellation = 0)"
        query = f"SELECT COUNT(DISTINCT invoice_no) FROM fact_sales {where_sql};"
        val = self._execute_scalar(query, params)
        return int(val or 0)

    def get_total_units_sold(self, filters: Optional[FilterParams] = None) -> int:
        """Retrieves total items sold excluding cancellations."""
        where_sql, params = self._build_where_clause(filters)
        if "is_cancellation" not in where_sql:
            where_sql += " AND (is_cancellation = FALSE OR is_cancellation = 0)"
        query = f"SELECT COALESCE(SUM(quantity), 0) FROM fact_sales {where_sql};"
        val = self._execute_scalar(query, params)
        return int(val or 0)

    def get_total_customers(self, filters: Optional[FilterParams] = None) -> int:
        """Retrieves distinct count of buyers."""
        where_sql, params = self._build_where_clause(filters)
        query = f"SELECT COUNT(DISTINCT customer_id) FROM fact_sales {where_sql};"
        val = self._execute_scalar(query, params)
        return int(val or 0)

    def get_total_products(self, filters: Optional[FilterParams] = None) -> int:
        """Retrieves distinct catalog stock codes."""
        where_sql, params = self._build_where_clause(filters)
        query = f"SELECT COUNT(DISTINCT stock_code) FROM fact_sales {where_sql};"
        val = self._execute_scalar(query, params)
        return int(val or 0)

    def get_average_order_value(self, filters: Optional[FilterParams] = None) -> float:
        """Calculates Average Order Value (AOV) directly in PostgreSQL."""
        where_sql, params = self._build_where_clause(filters)
        if "is_cancellation" not in where_sql:
            where_sql += " AND (is_cancellation = FALSE OR is_cancellation = 0)"
        query = f"""
            SELECT ROUND(
                COALESCE(SUM(total_amount), 0.00) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2
            ) FROM fact_sales {where_sql};
        """
        val = self._execute_scalar(query, params)
        return float(val or 0.0)

    def get_cancellation_count(self, filters: Optional[FilterParams] = None) -> int:
        """Retrieves count of distinct cancelled invoices."""
        where_sql, params = self._build_where_clause(filters)
        query = f"SELECT COUNT(DISTINCT CASE WHEN (is_cancellation = TRUE OR is_cancellation = 1) THEN invoice_no END) FROM fact_sales {where_sql};"
        val = self._execute_scalar(query, params)
        return int(val or 0)

    def get_cancellation_rate(self, filters: Optional[FilterParams] = None) -> float:
        """Calculates Cancellation Rate % = (Cancelled Invoices / Total Invoices) * 100."""
        where_sql, params = self._build_where_clause(filters)
        query = f"""
            SELECT ROUND(
                (1.0 * COUNT(DISTINCT CASE WHEN (is_cancellation = TRUE OR is_cancellation = 1) THEN invoice_no END) / 
                NULLIF(COUNT(DISTINCT invoice_no), 0)) * 100, 2
            ) FROM fact_sales {where_sql};
        """
        val = self._execute_scalar(query, params)
        return float(val or 0.0)

    def get_cancellation_revenue_impact(self, filters: Optional[FilterParams] = None) -> float:
        """Retrieves total lost revenue monetary sum from returns/cancellations."""
        where_sql, params = self._build_where_clause(filters)
        if "is_cancellation" not in where_sql:
            where_sql += " AND (is_cancellation = TRUE OR is_cancellation = 1)"
        query = f"SELECT COALESCE(ABS(SUM(total_amount)), 0.00) FROM fact_sales {where_sql};"
        val = self._execute_scalar(query, params)
        return float(val or 0.0)

    # -------------------------------------------------------------------------
    # DATASET BREAKDOWN DATA ACCESS
    # -------------------------------------------------------------------------

    def get_revenue_by_month(self, filters: Optional[FilterParams] = None) -> pd.DataFrame:
        """Retrieves monthly aggregated revenue and order counts."""
        where_sql, params = self._build_where_clause(filters)
        if "is_cancellation" not in where_sql:
            where_sql += " AND is_cancellation = FALSE"

        query = f"""
            SELECT 
                DATE_TRUNC('month', invoice_timestamp) AS period,
                invoice_year,
                invoice_month,
                COUNT(DISTINCT invoice_no) AS total_orders,
                SUM(quantity) AS total_units,
                SUM(total_amount) AS total_revenue,
                ROUND(SUM(total_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2) AS average_order_value
            FROM fact_sales
            {where_sql}
            GROUP BY DATE_TRUNC('month', invoice_timestamp), invoice_year, invoice_month
            ORDER BY period ASC;
        """
        return self._execute_query(query, params)

    def get_revenue_by_country(
        self, filters: Optional[FilterParams] = None, limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Retrieves geographic market breakdown by country."""
        where_sql, params = self._build_where_clause(filters)
        if "is_cancellation" not in where_sql:
            where_sql += " AND is_cancellation = FALSE"

        limit_clause = f"LIMIT {limit}" if limit else ""
        query = f"""
            SELECT 
                country,
                COUNT(DISTINCT invoice_no) AS total_orders,
                SUM(total_amount) AS total_revenue
            FROM fact_sales
            {where_sql}
            GROUP BY country
            ORDER BY total_revenue DESC
            {limit_clause};
        """
        return self._execute_query(query, params)

    def get_top_products(
        self, filters: Optional[FilterParams] = None, limit: int = 10, metric: str = "total_revenue"
    ) -> pd.DataFrame:
        """Retrieves top products ranked by revenue or quantity."""
        where_sql, params = self._build_where_clause(filters)
        if "is_cancellation" not in where_sql:
            where_sql += " AND is_cancellation = FALSE"

        sort_col = "total_revenue" if metric == "total_revenue" else "total_units_sold"
        params["limit_val"] = str(limit)

        query = f"""
            SELECT 
                stock_code,
                description,
                SUM(quantity) AS total_units_sold,
                SUM(total_amount) AS total_revenue,
                COUNT(DISTINCT invoice_no) AS total_orders
            FROM fact_sales
            {where_sql}
            GROUP BY stock_code, description
            ORDER BY {sort_col} DESC
            LIMIT :limit_val;
        """
        return self._execute_query(query, params)

    def get_customer_segments(self, filters: Optional[FilterParams] = None) -> pd.DataFrame:
        """Retrieves customer breakdown by account type (Registered vs Guest)."""
        where_sql, params = self._build_where_clause(filters)
        if "is_cancellation" not in where_sql:
            where_sql += " AND is_cancellation = FALSE"

        query = f"""
            SELECT 
                customer_type,
                COUNT(DISTINCT customer_id) AS customer_count,
                COUNT(DISTINCT invoice_no) AS total_orders,
                COALESCE(SUM(total_amount), 0.00) AS total_revenue,
                ROUND(COALESCE(SUM(total_amount), 0.00) / NULLIF(COUNT(DISTINCT customer_id), 0), 2) AS revenue_per_customer
            FROM fact_sales
            {where_sql}
            GROUP BY customer_type;
        """
        return self._execute_query(query, params)

    def get_available_countries(self) -> List[str]:
        """Retrieves distinct sorted list of country names in database."""
        query = "SELECT DISTINCT country FROM fact_sales ORDER BY country ASC;"
        df = self._execute_query(query)
        if df.empty:
            return ["All Countries"]
        return ["All Countries"] + df["country"].tolist()
