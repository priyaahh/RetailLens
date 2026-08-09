"""
sql_analytics.py
----------------
Python Analytics Layer executing parameterized SQL queries against PostgreSQL
and returning clean Pandas DataFrames for Plotly charting and Streamlit dashboard UI views.
Decouples database execution from frontend code.
"""

import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.connection import get_db_engine

logger = logging.getLogger(__name__)


class SQLAnalyticsService:
    """Service layer executing SQL analytical queries against PostgreSQL."""

    def __init__(self, engine: Optional[Engine] = None):
        """Dependency injection constructor for SQLAlchemy Engine."""
        self.engine = engine or get_db_engine()

    def execute_query(self, query_sql: str, params: Optional[dict] = None) -> pd.DataFrame:
        """
        Executes a raw or parameterized SQL query and returns a Pandas DataFrame.

        :param query_sql: SQL query string.
        :param params: Optional parameter dictionary for parameterized query binding.
        :return: Resulting Pandas DataFrame.
        """
        try:
            with self.engine.connect() as conn:
                logger.info("Executing SQL query via SQLAlchemy engine...")
                df = pd.read_sql_query(sql=text(query_sql), con=conn, params=params or {})
                return df
        except Exception as e:
            logger.error("Failed to execute SQL analytics query: %s", str(e), exc_info=True)
            return pd.DataFrame()

    def _build_where_clause(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        customer_type: Optional[str] = None,
        transaction_type: Optional[str] = None,
    ) -> Tuple[str, Dict[str, str]]:
        """Constructs parameterized WHERE clause conditions and parameters dict."""
        conditions = ["1=1"]
        params: Dict[str, str] = {}

        if start_date:
            conditions.append("invoice_timestamp >= :start_date")
            params["start_date"] = f"{start_date} 00:00:00"

        if end_date:
            conditions.append("invoice_timestamp <= :end_date")
            params["end_date"] = f"{end_date} 23:59:59"

        if country and country != "All Countries":
            conditions.append("country = :country")
            params["country"] = country

        if customer_type and customer_type != "All":
            conditions.append("customer_type = :customer_type")
            params["customer_type"] = customer_type

        if transaction_type == "Sales":
            conditions.append("is_cancellation = FALSE")
        elif transaction_type == "Cancellations":
            conditions.append("is_cancellation = TRUE")

        where_sql = "WHERE " + " AND ".join(conditions)
        return where_sql, params

    # -------------------------------------------------------------------------
    # CUSTOMER ANALYTICS
    # -------------------------------------------------------------------------

    def get_customer_summary(self, country: Optional[str] = None) -> pd.DataFrame:
        """Returns customer breakdown by account type (Registered vs Guest)."""
        where_sql, params = self._build_where_clause(country=country, transaction_type="Sales")
        query = f"""
            SELECT 
                customer_type,
                COUNT(DISTINCT customer_id) AS customer_count,
                COUNT(DISTINCT invoice_no) AS total_orders,
                COALESCE(SUM(total_amount), 0.00) AS total_revenue
            FROM fact_sales
            {where_sql}
            GROUP BY customer_type;
        """
        return self.execute_query(query, params=params)

    def get_top_customers_by_revenue(
        self, limit: int = 10, country: Optional[str] = None
    ) -> pd.DataFrame:
        """Returns top spending registered customers with rank and revenue."""
        where_sql, params = self._build_where_clause(country=country, transaction_type="Sales")
        params["limit_val"] = str(limit)

        query = f"""
            WITH customer_revenue AS (
                SELECT 
                    customer_id,
                    customer_type,
                    country,
                    COUNT(DISTINCT invoice_no) AS total_orders,
                    SUM(total_amount) AS total_revenue
                FROM fact_sales
                {where_sql} AND customer_id != 'GUEST'
                GROUP BY customer_id, customer_type, country
            )
            SELECT 
                DENSE_RANK() OVER (ORDER BY total_revenue DESC) AS rank,
                customer_id,
                customer_type,
                country,
                total_orders,
                total_revenue
            FROM customer_revenue
            ORDER BY rank ASC
            LIMIT :limit_val;
        """
        return self.execute_query(query, params=params)

    # -------------------------------------------------------------------------
    # PRODUCT ANALYTICS
    # -------------------------------------------------------------------------

    def get_top_products_by_revenue(
        self, limit: int = 10, country: Optional[str] = None
    ) -> pd.DataFrame:
        """Returns top revenue-generating products."""
        where_sql, params = self._build_where_clause(country=country, transaction_type="Sales")
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
            ORDER BY total_revenue DESC
            LIMIT :limit_val;
        """
        return self.execute_query(query, params=params)

    def get_top_products_by_quantity(
        self, limit: int = 10, country: Optional[str] = None
    ) -> pd.DataFrame:
        """Returns top products ordered by total units sold."""
        where_sql, params = self._build_where_clause(country=country, transaction_type="Sales")
        params["limit_val"] = str(limit)

        query = f"""
            SELECT 
                stock_code,
                description,
                SUM(quantity) AS total_units_sold,
                SUM(total_amount) AS total_revenue
            FROM fact_sales
            {where_sql}
            GROUP BY stock_code, description
            ORDER BY total_units_sold DESC
            LIMIT :limit_val;
        """
        return self.execute_query(query, params=params)

    def get_products_by_cancellation(
        self, limit: int = 10, country: Optional[str] = None
    ) -> pd.DataFrame:
        """Returns products with highest cancellation and return volume."""
        where_sql, params = self._build_where_clause(country=country, transaction_type="Cancellations")
        params["limit_val"] = str(limit)

        query = f"""
            SELECT 
                stock_code,
                description,
                ABS(SUM(quantity)) AS total_returned_units,
                ABS(SUM(total_amount)) AS total_returned_value
            FROM fact_sales
            {where_sql}
            GROUP BY stock_code, description
            ORDER BY total_returned_value DESC
            LIMIT :limit_val;
        """
        return self.execute_query(query, params=params)

    # -------------------------------------------------------------------------
    # GEOGRAPHIC & TEMPORAL ANALYTICS
    # -------------------------------------------------------------------------

    def get_revenue_by_country(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Returns revenue and order breakdown by country."""
        limit_clause = f"LIMIT {limit}" if limit else ""
        query = f"""
            SELECT 
                country,
                COUNT(DISTINCT invoice_no) AS total_orders,
                SUM(total_amount) AS total_revenue
            FROM fact_sales
            WHERE is_cancellation = FALSE
            GROUP BY country
            ORDER BY total_revenue DESC
            {limit_clause};
        """
        return self.execute_query(query)

    def get_available_countries(self) -> List[str]:
        """Returns distinct list of countries present in database."""
        query = "SELECT DISTINCT country FROM fact_sales ORDER BY country ASC;"
        df = self.execute_query(query)
        if df.empty:
            return ["All Countries"]
        countries = ["All Countries"] + df["country"].tolist()
        return countries

    def get_revenue_trend(
        self,
        granularity: str = "Monthly",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
    ) -> pd.DataFrame:
        """Returns revenue and order trends by Daily, Weekly, Monthly, or Quarterly granularity."""
        where_sql, params = self._build_where_clause(
            start_date=start_date, end_date=end_date, country=country, transaction_type="Sales"
        )

        if granularity == "Daily":
            group_col = "DATE_TRUNC('day', invoice_timestamp)"
        elif granularity == "Weekly":
            group_col = "DATE_TRUNC('week', invoice_timestamp)"
        elif granularity == "Quarterly":
            group_col = "DATE_TRUNC('quarter', invoice_timestamp)"
        else:  # Monthly default
            group_col = "DATE_TRUNC('month', invoice_timestamp)"

        query = f"""
            SELECT 
                {group_col} AS period,
                COUNT(DISTINCT invoice_no) AS total_orders,
                SUM(quantity) AS total_units,
                SUM(total_amount) AS total_revenue,
                ROUND(SUM(total_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2) AS average_order_value
            FROM fact_sales
            {where_sql}
            GROUP BY {group_col}
            ORDER BY period ASC;
        """
        return self.execute_query(query, params=params)

    def get_cancellation_trend(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Returns monthly cancellation volume and lost revenue trend."""
        where_sql, params = self._build_where_clause(
            start_date=start_date, end_date=end_date, transaction_type="Cancellations"
        )

        query = f"""
            SELECT 
                DATE_TRUNC('month', invoice_timestamp) AS period,
                COUNT(DISTINCT invoice_no) AS cancelled_orders,
                ABS(SUM(quantity)) AS cancelled_units,
                ABS(SUM(total_amount)) AS lost_revenue
            FROM fact_sales
            {where_sql}
            GROUP BY DATE_TRUNC('month', invoice_timestamp)
            ORDER BY period ASC;
        """
        return self.execute_query(query, params=params)
