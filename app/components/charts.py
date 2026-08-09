"""
charts.py
---------
Interactive Plotly visualization generator functions for Streamlit UI views.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_revenue_trend(df: pd.DataFrame, granularity: str = "Monthly") -> go.Figure:
    """Generates an interactive Plotly line chart for Revenue trend over time."""
    if df.empty or "period" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title=f"{granularity} Revenue Trend (No Data Available)")
        return fig

    fig = px.line(
        df,
        x="period",
        y="total_revenue",
        title=f"📈 {granularity} Revenue Trend (£)",
        labels={"period": "Timeline", "total_revenue": "Total Revenue (£)"},
        markers=True,
    )
    fig.update_traces(line_color="#1E88E5", line_width=3)
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def plot_revenue_by_country(df: pd.DataFrame, limit: int = 10) -> go.Figure:
    """Generates a Plotly horizontal bar chart for Revenue by Country."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="Revenue by Country (No Data Available)")
        return fig

    plot_df = df.head(limit).sort_values("total_revenue", ascending=True)

    fig = px.bar(
        plot_df,
        x="total_revenue",
        y="country",
        orientation="h",
        title=f"🌍 Top {limit} Geographic Markets by Revenue (£)",
        labels={"total_revenue": "Revenue (£)", "country": "Country"},
        color="total_revenue",
        color_continuous_scale="Blues",
    )
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def plot_top_products(df: pd.DataFrame, metric: str = "total_revenue", limit: int = 10) -> go.Figure:
    """Generates a bar chart of top products by revenue or quantity."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="Top Products (No Data Available)")
        return fig

    plot_df = df.head(limit).sort_values(metric, ascending=True)
    title_label = "Revenue (£)" if metric == "total_revenue" else "Units Sold"

    fig = px.bar(
        plot_df,
        x=metric,
        y="description",
        orientation="h",
        title=f"📦 Top {limit} Products by {title_label}",
        labels={metric: title_label, "description": "Product Description"},
        color=metric,
        color_continuous_scale="Viridis",
    )
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def plot_customer_distribution(df: pd.DataFrame) -> go.Figure:
    """Generates a Donut chart of Customer Account Breakdown (Registered vs Guest)."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="Customer Share (No Data Available)")
        return fig

    fig = px.pie(
        df,
        names="customer_type",
        values="total_revenue",
        hole=0.4,
        title="👥 Revenue Share by Customer Type",
        color_discrete_sequence=["#2E7D32", "#FFA000"],
    )
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def plot_cancellation_trend(df: pd.DataFrame) -> go.Figure:
    """Generates a bar chart showing Lost Revenue due to Cancellations/Returns."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="Cancellation Loss Trend (No Data Available)")
        return fig

    fig = px.bar(
        df,
        x="period",
        y="lost_revenue",
        title="⚠️ Monthly Lost Revenue from Cancellations & Returns (£)",
        labels={"period": "Timeline", "lost_revenue": "Lost Revenue (£)"},
        color_discrete_sequence=["#D32F2F"],
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig
