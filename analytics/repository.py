"""
repository.py
-------------
Analytics Repository Data Access Layer for RetailLens.
Executes parameterized PostgreSQL SQL queries via SQLAlchemy engine connection pooling,
decoupling database access from business KPI composition and Streamlit UI pages.
"""

import io
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from analytics.cache import RedisCache
from analytics.exceptions import DatabaseConnectionError, RepositoryError
from analytics.models import FilterParams
from database.connection import get_db_engine

logger = logging.getLogger(__name__)


class AnalyticsRepository:
    """Repository pattern encapsulating all PostgreSQL data-access queries for analytics."""

    def __init__(self, engine: Optional[Engine] = None, cache: Optional[RedisCache] = None):
        """Dependency injection constructor for SQLAlchemy Engine and RedisCache."""
        try:
            self.engine = engine or get_db_engine()
        except Exception as e:
            logger.error("Failed to initialize database engine in AnalyticsRepository: %s", str(e))
            raise DatabaseConnectionError(f"Database connection initialization failed: {str(e)}")

        self.cache = cache or RedisCache()

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
    # REDIS / MEMORY CACHING HELPERS
    # -------------------------------------------------------------------------

    def _make_cache_key(self, prefix: str, filters: Optional[FilterParams] = None, **kwargs) -> str:
        """Constructs a deterministic cache key string for query method and parameter set."""
        parts = [f"repo:{prefix}"]
        if filters:
            parts.append(
                f"sd={filters.start_date}:ed={filters.end_date}:c={filters.country}:ct={filters.customer_type}:tt={filters.transaction_type}"
            )
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}={v}")
        return ":".join(parts)

    def _cached_scalar(self, key: str, fetch_fn, ttl_seconds: int = 300) -> Any:
        """Executes scalar query with Redis / memory cache lookup and population."""
        if self.cache:
            try:
                cached_val = self.cache.get(key)
                if cached_val is not None:
                    logger.debug("Cache hit for scalar key '%s'", key)
                    return cached_val
            except Exception as e:
                logger.warning("Cache GET error for key '%s': %s", key, str(e))

        val = fetch_fn()
        if self.cache and val is not None:
            try:
                self.cache.set(key, val, ttl_seconds=ttl_seconds)
            except Exception as e:
                logger.warning("Cache SET error for key '%s': %s", key, str(e))
        return val

    def _cached_dataframe(self, key: str, fetch_fn, ttl_seconds: int = 300) -> pd.DataFrame:
        """Executes DataFrame query with Redis / memory cache lookup and serialization."""
        if self.cache:
            try:
                cached_dict = self.cache.get(key)
                if cached_dict is not None and isinstance(cached_dict, dict):
                    logger.debug("Cache hit for DataFrame key '%s'", key)
                    df_cached = pd.read_json(io.StringIO(json.dumps(cached_dict)), orient="split")
                    return df_cached
            except Exception as e:
                logger.warning("Cache GET/deserialization error for key '%s': %s", key, str(e))

        df = fetch_fn()
        if self.cache and isinstance(df, pd.DataFrame):
            try:
                serialized = json.loads(df.to_json(orient="split", date_format="iso"))
                self.cache.set(key, serialized, ttl_seconds=ttl_seconds)
            except Exception as e:
                logger.warning("Cache SET/serialization error for key '%s': %s", key, str(e))
        return df

    # -------------------------------------------------------------------------
    # CORE METRIC DATA ACCESS
    # -------------------------------------------------------------------------

    def get_total_revenue(self, filters: Optional[FilterParams] = None) -> float:
        """Retrieves total net monetary revenue excluding cancellations."""
        key = self._make_cache_key("total_revenue", filters)

        def _fetch():
            where_sql, params = self._build_where_clause(filters)
            if "is_cancellation" not in where_sql:
                where_sql += " AND (is_cancellation = FALSE OR is_cancellation = 0)"
            query = f"SELECT COALESCE(SUM(total_amount), 0.00) FROM fact_sales {where_sql};"
            val = self._execute_scalar(query, params)
            return float(val or 0.0)

        return float(self._cached_scalar(key, _fetch))

    def get_total_orders(self, filters: Optional[FilterParams] = None) -> int:
        """Retrieves distinct completed orders count."""
        key = self._make_cache_key("total_orders", filters)

        def _fetch():
            where_sql, params = self._build_where_clause(filters)
            if "is_cancellation" not in where_sql:
                where_sql += " AND (is_cancellation = FALSE OR is_cancellation = 0)"
            query = f"SELECT COUNT(DISTINCT invoice_no) FROM fact_sales {where_sql};"
            val = self._execute_scalar(query, params)
            return int(val or 0)

        return int(self._cached_scalar(key, _fetch))

    def get_total_units_sold(self, filters: Optional[FilterParams] = None) -> int:
        """Retrieves total items sold excluding cancellations."""
        key = self._make_cache_key("total_units_sold", filters)

        def _fetch():
            where_sql, params = self._build_where_clause(filters)
            if "is_cancellation" not in where_sql:
                where_sql += " AND (is_cancellation = FALSE OR is_cancellation = 0)"
            query = f"SELECT COALESCE(SUM(quantity), 0) FROM fact_sales {where_sql};"
            val = self._execute_scalar(query, params)
            return int(val or 0)

        return int(self._cached_scalar(key, _fetch))

    def get_total_customers(self, filters: Optional[FilterParams] = None) -> int:
        """Retrieves distinct count of buyers."""
        key = self._make_cache_key("total_customers", filters)

        def _fetch():
            where_sql, params = self._build_where_clause(filters)
            query = f"SELECT COUNT(DISTINCT customer_id) FROM fact_sales {where_sql};"
            val = self._execute_scalar(query, params)
            return int(val or 0)

        return int(self._cached_scalar(key, _fetch))

    def get_total_products(self, filters: Optional[FilterParams] = None) -> int:
        """Retrieves distinct catalog stock codes."""
        key = self._make_cache_key("total_products", filters)

        def _fetch():
            where_sql, params = self._build_where_clause(filters)
            query = f"SELECT COUNT(DISTINCT stock_code) FROM fact_sales {where_sql};"
            val = self._execute_scalar(query, params)
            return int(val or 0)

        return int(self._cached_scalar(key, _fetch))

    def get_average_order_value(self, filters: Optional[FilterParams] = None) -> float:
        """Calculates Average Order Value (AOV) directly in PostgreSQL."""
        key = self._make_cache_key("average_order_value", filters)

        def _fetch():
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

        return float(self._cached_scalar(key, _fetch))

    def get_cancellation_count(self, filters: Optional[FilterParams] = None) -> int:
        """Retrieves count of distinct cancelled invoices."""
        key = self._make_cache_key("cancellation_count", filters)

        def _fetch():
            where_sql, params = self._build_where_clause(filters)
            query = f"SELECT COUNT(DISTINCT CASE WHEN (is_cancellation = TRUE OR is_cancellation = 1) THEN invoice_no END) FROM fact_sales {where_sql};"
            val = self._execute_scalar(query, params)
            return int(val or 0)

        return int(self._cached_scalar(key, _fetch))

    def get_cancellation_rate(self, filters: Optional[FilterParams] = None) -> float:
        """Calculates Cancellation Rate % = (Cancelled Invoices / Total Invoices) * 100."""
        key = self._make_cache_key("cancellation_rate", filters)

        def _fetch():
            where_sql, params = self._build_where_clause(filters)
            query = f"""
                SELECT ROUND(
                    (1.0 * COUNT(DISTINCT CASE WHEN (is_cancellation = TRUE OR is_cancellation = 1) THEN invoice_no END) / 
                    NULLIF(COUNT(DISTINCT invoice_no), 0)) * 100, 2
                ) FROM fact_sales {where_sql};
            """
            val = self._execute_scalar(query, params)
            return float(val or 0.0)

        return float(self._cached_scalar(key, _fetch))

    def get_cancellation_revenue_impact(self, filters: Optional[FilterParams] = None) -> float:
        """Retrieves total lost revenue monetary sum from returns/cancellations."""
        key = self._make_cache_key("cancellation_revenue_impact", filters)

        def _fetch():
            where_sql, params = self._build_where_clause(filters)
            if "is_cancellation" not in where_sql:
                where_sql += " AND (is_cancellation = TRUE OR is_cancellation = 1)"
            query = f"SELECT COALESCE(ABS(SUM(total_amount)), 0.00) FROM fact_sales {where_sql};"
            val = self._execute_scalar(query, params)
            return float(val or 0.0)

        return float(self._cached_scalar(key, _fetch))

    # -------------------------------------------------------------------------
    # DATASET BREAKDOWN DATA ACCESS
    # -------------------------------------------------------------------------

    def get_revenue_by_month(self, filters: Optional[FilterParams] = None) -> pd.DataFrame:
        """Retrieves monthly aggregated revenue and order counts."""
        key = self._make_cache_key("revenue_by_month", filters)

        def _fetch():
            where_sql, params = self._build_where_clause(filters)
            if "is_cancellation" not in where_sql:
                where_sql += " AND (is_cancellation = FALSE OR is_cancellation = 0)"

            is_sqlite = getattr(self.engine, "dialect", None) and self.engine.dialect.name == "sqlite"
            group_col = "strftime('%Y-%m', invoice_timestamp)" if is_sqlite else "DATE_TRUNC('month', invoice_timestamp)"

            query = f"""
                SELECT 
                    {group_col} AS period,
                    invoice_year,
                    invoice_month,
                    COUNT(DISTINCT invoice_no) AS total_orders,
                    SUM(quantity) AS total_units,
                    SUM(total_amount) AS total_revenue,
                    ROUND(SUM(total_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2) AS average_order_value
                FROM fact_sales
                {where_sql}
                GROUP BY {group_col}, invoice_year, invoice_month
                ORDER BY period ASC;
            """
            return self._execute_query(query, params)

        return self._cached_dataframe(key, _fetch)

    def get_revenue_trend(
        self,
        granularity: str = "Monthly",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
    ) -> pd.DataFrame:
        """Convenience method delegating to SQLAnalyticsService for page compatibility."""
        from analytics.sql_analytics import SQLAnalyticsService
        service = SQLAnalyticsService(engine=self.engine)
        return service.get_revenue_trend(granularity, start_date, end_date, country)

    def get_customer_summary(self, country: Optional[str] = None) -> pd.DataFrame:
        """Convenience method delegating to SQLAnalyticsService for page compatibility."""
        from analytics.sql_analytics import SQLAnalyticsService
        service = SQLAnalyticsService(engine=self.engine)
        return service.get_customer_summary(country)

    def get_top_products_by_revenue(self, limit: int = 10, country: Optional[str] = None) -> pd.DataFrame:
        """Convenience method delegating to SQLAnalyticsService for page compatibility."""
        from analytics.sql_analytics import SQLAnalyticsService
        service = SQLAnalyticsService(engine=self.engine)
        return service.get_top_products_by_revenue(limit, country)

    def get_top_products_by_quantity(self, limit: int = 10, country: Optional[str] = None) -> pd.DataFrame:
        """Convenience method delegating to SQLAnalyticsService for page compatibility."""
        from analytics.sql_analytics import SQLAnalyticsService
        service = SQLAnalyticsService(engine=self.engine)
        return service.get_top_products_by_quantity(limit, country)

    def get_top_customers_by_revenue(self, limit: int = 10, country: Optional[str] = None) -> pd.DataFrame:
        """Convenience method delegating to SQLAnalyticsService for page compatibility."""
        from analytics.sql_analytics import SQLAnalyticsService
        service = SQLAnalyticsService(engine=self.engine)
        return service.get_top_customers_by_revenue(limit, country)

    def get_cancellation_trend(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Convenience method delegating to SQLAnalyticsService for page compatibility."""
        from analytics.sql_analytics import SQLAnalyticsService
        service = SQLAnalyticsService(engine=self.engine)
        return service.get_cancellation_trend(start_date, end_date)

    def get_products_by_cancellation(self, limit: int = 10, country: Optional[str] = None) -> pd.DataFrame:
        """Convenience method delegating to SQLAnalyticsService for page compatibility."""
        from analytics.sql_analytics import SQLAnalyticsService
        service = SQLAnalyticsService(engine=self.engine)
        return service.get_products_by_cancellation(limit, country)

    def get_revenue_by_country(
        self, filters: Optional[FilterParams] = None, limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Retrieves geographic market breakdown by country."""
        key = self._make_cache_key("revenue_by_country", filters, limit=limit or "all")

        def _fetch():
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

        return self._cached_dataframe(key, _fetch)

    def get_top_products(
        self, filters: Optional[FilterParams] = None, limit: int = 10, metric: str = "total_revenue"
    ) -> pd.DataFrame:
        """Retrieves top products ranked by revenue or quantity."""
        key = self._make_cache_key("top_products", filters, limit=limit, metric=metric)

        def _fetch():
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

        return self._cached_dataframe(key, _fetch)

    def get_customer_segments(self, filters: Optional[FilterParams] = None) -> pd.DataFrame:
        """Retrieves customer breakdown by account type (Registered vs Guest)."""
        key = self._make_cache_key("customer_segments", filters)

        def _fetch():
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

        return self._cached_dataframe(key, _fetch)

    def get_available_countries(self) -> List[str]:
        """Retrieves distinct sorted list of country names in database."""
        key = self._make_cache_key("available_countries")

        def _fetch():
            query = "SELECT DISTINCT country FROM fact_sales ORDER BY country ASC;"
            df = self._execute_query(query)
            if df.empty:
                return ["All Countries"]
            return ["All Countries"] + df["country"].tolist()

        return self._cached_scalar(key, _fetch)

