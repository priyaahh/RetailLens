"""
pipeline_monitor.py
-------------------
Pipeline Monitoring Dashboard View for RetailLens (Phase 6 Milestone 10).
Displays operational pipeline health metrics, latest run details, data quality summaries,
and data lineage tracking for engineering visibility.
"""

import streamlit as st

from analytics.pipeline_service import PipelineMonitoringService


def render_pipeline_monitor_page(monitoring_service: PipelineMonitoringService) -> None:
    """
    Renders operational pipeline execution monitoring page.

    :param monitoring_service: PipelineMonitoringService instance.
    """
    st.markdown("# ⚙️ Pipeline Execution Monitor & Data Quality Observability")
    st.markdown(
        "Real-time operational monitoring dashboard tracking ETL pipeline run status, "
        "incremental data loading, data quality rates, and source-to-target data lineage."
    )
    st.markdown("---")

    # 1. System Pipeline Health Banner
    health = monitoring_service.get_pipeline_health_status()
    col1, col2, col3, col4 = st.columns(4)

    status_color = "🟢 HEALTHY" if health["health_status"] == "HEALTHY" else ("🟡 WARNING" if health["health_status"] == "WARNING" else "🔴 CRITICAL")
    col1.metric("Pipeline Health", status_color)
    col2.metric("Success Rate", f"{health['success_rate_pct']}%")
    col3.metric("Total Runs", f"{health['total_runs']}")
    col4.metric("Avg Duration", f"{health['avg_duration_seconds']}s")

    st.markdown("---")

    # 2. Latest Pipeline Run Overview
    st.markdown("### 🚀 Latest Pipeline Run Details")
    latest_run = monitoring_service.get_latest_run()

    if latest_run:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Run ID", latest_run.get("run_id", "N/A")[:8] + "...")
        c2.metric("Status", latest_run.get("status", "N/A"))
        c3.metric("Rows Read", f"{latest_run.get('rows_read', 0):,}")
        c4.metric("Rows Inserted", f"{latest_run.get('rows_inserted', 0):,}")

        if latest_run.get("error_message"):
            st.error(f"⚠️ Latest Run Failure Error: {latest_run.get('error_message')}")
    else:
        st.info("No pipeline execution runs recorded yet. Execute the ETL pipeline to view audit records.")

    st.markdown("---")

    # 3. Recent Runs & Data Quality Tabs
    tab1, tab2, tab3 = st.tabs(["📜 Recent Pipeline Runs", "🛡️ Data Quality Audit", "🔗 Source Lineage Provenance"])

    with tab1:
        st.markdown("#### Recent Execution Runs Audit Trail")
        recent_df = monitoring_service.get_recent_runs(limit=20)
        if not recent_df.empty:
            st.dataframe(recent_df, use_container_width=True)
        else:
            st.info("No recent pipeline runs found.")

    with tab2:
        st.markdown("#### Data Quality Score Summary")
        dq_df = monitoring_service.get_data_quality_summary(limit=20)
        if not dq_df.empty:
            st.dataframe(dq_df, use_container_width=True)
        else:
            st.info("No data quality audit records found.")

    with tab3:
        st.markdown("#### Source-to-Target Data Lineage Provenance")
        lineage_df = monitoring_service.get_lineage(limit=20)
        if not lineage_df.empty:
            st.dataframe(lineage_df, use_container_width=True)
        else:
            st.info("No data lineage records found.")
