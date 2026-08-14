"""
metrics.py
----------
Prometheus Metrics Exporter Layer for RetailLens (Phase 8 Milestone 8).
Collects operational pipeline execution metrics, duration histograms, data quality scores,
and cache hit/miss counters formatted in standard Prometheus text format.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class PrometheusMetricsExporter:
    """Collects and exports Prometheus metrics for operational observability."""

    def __init__(self):
        self.pipeline_runs_total = 0
        self.pipeline_failures_total = 0
        self.pipeline_duration_sum = 0.0
        self.rows_processed_total = 0
        self.rows_inserted_total = 0
        self.rows_skipped_total = 0
        self.last_data_quality_score = 100.0
        self.cache_hits_total = 0
        self.cache_misses_total = 0
        self.engine_counts = {"pandas": 0, "spark": 0}

    def record_run(
        self,
        status: str,
        engine: str = "pandas",
        duration_seconds: float = 0.0,
        rows_read: int = 0,
        rows_inserted: int = 0,
        rows_skipped: int = 0,
        quality_score: float = 100.0,
    ) -> None:
        """Records metrics from a pipeline execution run."""
        self.pipeline_runs_total += 1
        if status.upper() == "FAILED":
            self.pipeline_failures_total += 1

        self.pipeline_duration_sum += duration_seconds
        self.rows_processed_total += rows_read
        self.rows_inserted_total += rows_inserted
        self.rows_skipped_total += rows_skipped
        self.last_data_quality_score = quality_score

        eng_clean = engine.lower()
        if eng_clean in self.engine_counts:
            self.engine_counts[eng_clean] += 1

    def record_cache(self, hit: bool) -> None:
        """Records cache hit or miss event."""
        if hit:
            self.cache_hits_total += 1
        else:
            self.cache_misses_total += 1

    def export_prometheus_text(self) -> str:
        """Exports metrics in standard Prometheus Exposition Text Format."""
        lines = [
            "# HELP pipeline_runs_total Total number of pipeline execution runs.",
            "# TYPE pipeline_runs_total counter",
            f"pipeline_runs_total {self.pipeline_runs_total}",
            "# HELP pipeline_failures_total Total number of failed pipeline execution runs.",
            "# TYPE pipeline_failures_total counter",
            f"pipeline_failures_total {self.pipeline_failures_total}",
            "# HELP pipeline_duration_seconds_total Total duration of pipeline executions in seconds.",
            "# TYPE pipeline_duration_seconds_total counter",
            f"pipeline_duration_seconds_total {round(self.pipeline_duration_sum, 3)}",
            "# HELP rows_processed_total Total raw rows processed across runs.",
            "# TYPE rows_processed_total counter",
            f"rows_processed_total {self.rows_processed_total}",
            "# HELP rows_inserted_total Total rows inserted into database.",
            "# TYPE rows_inserted_total counter",
            f"rows_inserted_total {self.rows_inserted_total}",
            "# HELP rows_skipped_total Total rows skipped by incremental deduplication.",
            "# TYPE rows_skipped_total counter",
            f"rows_skipped_total {self.rows_skipped_total}",
            "# HELP data_quality_score Last evaluated data quality score percentage.",
            "# TYPE data_quality_score gauge",
            f"data_quality_score {self.last_data_quality_score}",
            "# HELP cache_hits_total Total analytics cache hit count.",
            "# TYPE cache_hits_total counter",
            f"cache_hits_total {self.cache_hits_total}",
            "# HELP cache_misses_total Total analytics cache miss count.",
            "# TYPE cache_misses_total counter",
            f"cache_misses_total {self.cache_misses_total}",
            "# HELP engine_runs_total Engine run breakdown.",
            "# TYPE engine_runs_total counter",
            f'engine_runs_total{{engine="pandas"}} {self.engine_counts["pandas"]}',
            f'engine_runs_total{{engine="spark"}} {self.engine_counts["spark"]}',
        ]
        return "\n".join(lines) + "\n"
