"""
insights.py
-----------
Automated Business Insight Engine for RetailLens.
Evaluates metrics against configurable business thresholds to generate structured Insight objects
with severity levels, quantitative metrics, and actionable recommendations.
"""

import logging
from typing import Dict, List, Optional

from analytics.models import FilterParams, Insight, KPIMetric
from analytics.repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class InsightEngine:
    """Business Insight Engine generating structured operational recommendations."""

    def __init__(
        self,
        repository: Optional[AnalyticsRepository] = None,
        cancellation_high_threshold: float = 5.0,
        cancellation_critical_threshold: float = 10.0,
        top_product_concentration_threshold: float = 20.0,
        guest_ratio_threshold: float = 40.0,
    ):
        """
        Dependency injection constructor for repository and threshold parameters.
        """
        self.repository = repository or AnalyticsRepository()
        self.cancellation_high_threshold = cancellation_high_threshold
        self.cancellation_critical_threshold = cancellation_critical_threshold
        self.top_product_concentration_threshold = top_product_concentration_threshold
        self.guest_ratio_threshold = guest_ratio_threshold

    def generate_insights(
        self, kpis: Dict[str, KPIMetric], filters: Optional[FilterParams] = None
    ) -> List[Insight]:
        """Evaluates metrics and dataset trends to produce structured business insights."""
        insights: List[Insight] = []

        # ---------------------------------------------------------------------
        # 1. CANCELLATION & RETURN INSIGHTS
        # ---------------------------------------------------------------------
        cancel_rate_metric = kpis.get("cancellation_rate")
        if cancel_rate_metric and isinstance(cancel_rate_metric.value, (int, float)):
            cancel_val = float(cancel_rate_metric.value)
            cancel_loss = kpis.get("cancellation_revenue_impact")
            loss_str = cancel_loss.formatted_value if cancel_loss else "N/A"

            if cancel_val >= self.cancellation_critical_threshold:
                insights.append(
                    Insight(
                        category="CANCELLATION",
                        title="Critical Return & Order Cancellation Volume",
                        description=f"Order cancellation rate has reached a critical {cancel_val:.1f}%, representing {loss_str} in gross lost revenue.",
                        severity="CRITICAL",
                        metric="Cancellation Rate",
                        value=f"{cancel_val:.1f}%",
                        threshold=f"{self.cancellation_critical_threshold:.1f}%",
                        recommendation="Audit top returned stock items in inventory; inspect supplier quality and logistics handling.",
                    )
                )
            elif cancel_val >= self.cancellation_high_threshold:
                insights.append(
                    Insight(
                        category="CANCELLATION",
                        title="Elevated Order Cancellation Rate",
                        description=f"Order cancellation rate is elevated at {cancel_val:.1f}%, exceeding normal operational thresholds.",
                        severity="HIGH",
                        metric="Cancellation Rate",
                        value=f"{cancel_val:.1f}%",
                        threshold=f"{self.cancellation_high_threshold:.1f}%",
                        recommendation="Review product descriptions and return policies to reduce customer order friction.",
                    )
                )

        # ---------------------------------------------------------------------
        # 2. REVENUE GROWTH & MOM TREND INSIGHTS
        # ---------------------------------------------------------------------
        mom_growth_metric = kpis.get("revenue_growth_pct")
        if mom_growth_metric and isinstance(mom_growth_metric.value, (int, float)):
            growth_val = float(mom_growth_metric.value)
            if growth_val > 5.0:
                insights.append(
                    Insight(
                        category="TREND",
                        title="Positive Month-over-Month Revenue Growth",
                        description=f"Monthly sales revenue expanded by +{growth_val:.1f}% compared to the previous calendar month.",
                        severity="LOW",
                        metric="MoM Revenue Growth",
                        value=f"+{growth_val:.1f}%",
                        threshold="> 0.0%",
                        recommendation="Maintain current marketing spend and ensure inventory fulfillment levels remain strong.",
                    )
                )
            elif growth_val < 0.0:
                insights.append(
                    Insight(
                        category="TREND",
                        title="Month-over-Month Revenue Contraction",
                        description=f"Monthly sales revenue contracted by {growth_val:.1f}% compared to the previous calendar month.",
                        severity="HIGH",
                        metric="MoM Revenue Growth",
                        value=f"{growth_val:.1f}%",
                        threshold="< 0.0%",
                        recommendation="Investigate regional order volume drops and run targeted promotional discount campaigns.",
                    )
                )

        # ---------------------------------------------------------------------
        # 3. PRODUCT CONCENTRATION RISK INSIGHTS
        # ---------------------------------------------------------------------
        top_prods = self.repository.get_top_products(filters, limit=1)
        tot_rev = float(kpis.get("total_revenue", KPIMetric("Revenue", 0.0, "£0.00", "CORE", "", "")).value or 0.0)

        if not top_prods.empty and tot_rev > 0:
            top_prod_name = str(top_prods.iloc[0]["description"])
            top_prod_rev = float(top_prods.iloc[0]["total_revenue"])
            concentration_pct = round((top_prod_rev / tot_rev) * 100, 1)

            if concentration_pct >= self.top_product_concentration_threshold:
                insights.append(
                    Insight(
                        category="PRODUCT",
                        title="High Product Revenue Concentration",
                        description=f"Single product '{top_prod_name}' generates {concentration_pct:.1f}% of total company sales revenue.",
                        severity="MEDIUM",
                        metric="Product Concentration Ratio",
                        value=f"{concentration_pct:.1f}%",
                        threshold=f"{self.top_product_concentration_threshold:.1f}%",
                        recommendation="Diversify product catalog promotions to mitigate single-item supply chain dependency.",
                    )
                )

        # ---------------------------------------------------------------------
        # 4. CUSTOMER SEGMENTATION INSIGHTS
        # ---------------------------------------------------------------------
        tot_cust = float(kpis.get("total_customers", KPIMetric("Cust", 0, "0", "CORE", "", "")).value or 0)
        guest_cust = float(kpis.get("guest_customers", KPIMetric("Guest", 0, "0", "CUSTOMER", "", "")).value or 0)

        if tot_cust > 0:
            guest_pct = round((guest_cust / tot_cust) * 100, 1)
            if guest_pct >= self.guest_ratio_threshold:
                insights.append(
                    Insight(
                        category="CUSTOMER",
                        title="Significant Reliance on Guest Checkouts",
                        description=f"Guest checkouts represent {guest_pct:.1f}% of total customer interactions.",
                        severity="MEDIUM",
                        metric="Guest Customer Ratio",
                        value=f"{guest_pct:.1f}%",
                        threshold=f"{self.guest_ratio_threshold:.1f}%",
                        recommendation="Introduce account creation incentives (e.g. 10% first order discount) to increase registered users.",
                    )
                )

        return insights
