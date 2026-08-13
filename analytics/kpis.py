"""
kpis.py
-------
Reusable Business Key Performance Indicator (KPI) metric calculation engine for RetailLens.
Executes direct SQL aggregations against PostgreSQL using SQLAlchemy connection pooling,
handling null values, empty databases, and division-by-zero safely.
"""

import logging
from typing import Dict, Optional, Tuple, Union

from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.connection import get_db_engine

logger = logging.getLogger(__name__)


class KPICalculator:
    """KPI Metric Calculator Engine executing direct SQL queries."""

    def __init__(self, engine: Optional[Engine] = None):
        """Dependency injection constructor for SQLAlchemy Engine."""
        self.engine = engine or get_db_engine()

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
            conditions.append("(is_cancellation = FALSE OR is_cancellation = 0)")
        elif transaction_type == "Cancellations":
            conditions.append("(is_cancellation = TRUE OR is_cancellation = 1)")

        where_sql = "WHERE " + " AND ".join(conditions)
        return where_sql, params

    def get_all_kpis(self) -> Dict[str, Union[float, int, str]]:
        """Calculates and returns a dictionary of all core executive KPIs."""
        res = self.get_filtered_kpis()
        res["cancellation_rate"] = res.get("cancellation_rate_pct", 0.0)
        res["repeat_customer_rate"] = res.get("repeat_customer_rate_pct", 0.0)
        return res

    def get_filtered_kpis(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> Dict[str, Union[float, int, str]]:
        """Calculates and returns a dictionary of all core executive KPIs using filter parameters."""
        return {
            "total_revenue": self.total_revenue(start_date, end_date, country, customer_type),
            "total_orders": self.total_orders(start_date, end_date, country, customer_type),
            "total_units_sold": self.total_units(start_date, end_date, country, customer_type),
            "total_customers": self.total_customers(start_date, end_date, country, customer_type),
            "average_order_value": self.average_order_value(start_date, end_date, country, customer_type),
            "cancellation_rate_pct": self.cancellation_rate(start_date, end_date, country, customer_type),
            "average_unit_price": self.average_unit_price(start_date, end_date, country, customer_type),
            "repeat_customer_rate_pct": self.repeat_customer_rate(start_date, end_date, country),
            "top_product": self.top_product(start_date, end_date, country),
            "top_country": self.top_country(start_date, end_date),
        }

    def total_revenue(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> float:
        """Returns total net monetary revenue excluding cancellations."""
        where_sql, params = self._build_where_clause(start_date, end_date, country, customer_type, "Sales")
        query = f"SELECT COALESCE(SUM(total_amount), 0.00) FROM fact_sales {where_sql};"
        return float(self._execute_scalar(query, params) or 0.0)

    def total_orders(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> int:
        """Returns count of distinct completed orders."""
        where_sql, params = self._build_where_clause(start_date, end_date, country, customer_type, "Sales")
        query = f"SELECT COUNT(DISTINCT invoice_no) FROM fact_sales {where_sql};"
        return int(self._execute_scalar(query, params) or 0)

    def total_units(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> int:
        """Returns total item units sold excluding cancellations."""
        where_sql, params = self._build_where_clause(start_date, end_date, country, customer_type, "Sales")
        query = f"SELECT COALESCE(SUM(quantity), 0) FROM fact_sales {where_sql};"
        return int(self._execute_scalar(query, params) or 0)

    def total_customers(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> int:
        """Returns distinct count of all buyers (including Guest marker)."""
        where_sql, params = self._build_where_clause(start_date, end_date, country, customer_type)
        query = f"SELECT COUNT(DISTINCT customer_id) FROM fact_sales {where_sql};"
        return int(self._execute_scalar(query, params) or 0)

    def average_order_value(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> float:
        """Calculates Average Order Value (AOV = Total Net Revenue / Distinct Completed Orders)."""
        where_sql, params = self._build_where_clause(start_date, end_date, country, customer_type, "Sales")
        query = f"""
            SELECT ROUND(
                COALESCE(SUM(total_amount), 0.00) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2
            )
            FROM fact_sales
            {where_sql};
        """
        return float(self._execute_scalar(query, params) or 0.0)

    def cancellation_rate(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> float:
        """Calculates Cancellation Rate % = (Cancelled Invoices / Total Invoices) * 100."""
        where_sql, params = self._build_where_clause(start_date, end_date, country, customer_type)
        query = f"""
            SELECT ROUND(
                (1.0 * COUNT(DISTINCT CASE WHEN (is_cancellation = TRUE OR is_cancellation = 1) THEN invoice_no END) / 
                NULLIF(COUNT(DISTINCT invoice_no), 0)) * 100, 2
            )
            FROM fact_sales
            {where_sql};
        """
        return float(self._execute_scalar(query, params) or 0.0)

    def average_unit_price(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> float:
        """Returns average item selling price."""
        where_sql, params = self._build_where_clause(start_date, end_date, country, customer_type, "Sales")
        query = f"SELECT ROUND(COALESCE(AVG(unit_price), 0.00), 2) FROM fact_sales {where_sql};"
        return float(self._execute_scalar(query, params) or 0.0)

    def repeat_customer_rate(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
    ) -> float:
        """Calculates % of registered customers with > 1 completed order."""
        where_sql, params = self._build_where_clause(start_date, end_date, country, "Registered", "Sales")
        query = f"""
            WITH registered_orders AS (
                SELECT customer_id, COUNT(DISTINCT invoice_no) AS order_count
                FROM fact_sales
                {where_sql} AND customer_id != 'GUEST'
                GROUP BY customer_id
            )
            SELECT ROUND(
                (1.0 * COUNT(CASE WHEN order_count > 1 THEN 1 END) / 
                NULLIF(COUNT(*), 0)) * 100, 2
            )
            FROM registered_orders;
        """
        return float(self._execute_scalar(query, params) or 0.0)

    def top_product(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
    ) -> str:
        """Returns description of top revenue-generating product."""
        where_sql, params = self._build_where_clause(start_date, end_date, country, transaction_type="Sales")
        query = f"""
            SELECT description 
            FROM fact_sales 
            {where_sql}
            GROUP BY description 
            ORDER BY SUM(total_amount) DESC 
            LIMIT 1;
        """
        res = self._execute_scalar(query, params)
        return str(res) if res else "N/A"

    def top_country(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Returns country generating highest total sales revenue."""
        where_sql, params = self._build_where_clause(start_date, end_date, transaction_type="Sales")
        query = f"""
            SELECT country 
            FROM fact_sales 
            {where_sql}
            GROUP BY country 
            ORDER BY SUM(total_amount) DESC 
            LIMIT 1;
        """
        res = self._execute_scalar(query, params)
        return str(res) if res else "N/A"

    def _execute_scalar(
        self, query_sql: str, params: Optional[dict] = None
    ) -> Optional[Union[float, int, str]]:
        """Executes a single-scalar result SQL query safely."""
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text(query_sql), params or {}).scalar()
                return res
        except Exception as e:
            logger.error("Failed to calculate scalar KPI: %s", str(e), exc_info=True)
            return None
