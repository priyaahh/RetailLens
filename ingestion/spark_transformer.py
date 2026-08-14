"""
spark_transformer.py
--------------------
PySpark Distributed Data Transformation & Feature Engineering Engine for RetailLens (Phase 7 Milestone 2).
Provides high-throughput distributed DataFrame transformations leveraging PySpark's Catalyst Optimizer
and lazy DAG evaluation, with graceful fallback to Pandas when PySpark is not available.
"""

import logging
from typing import Optional, Union

import pandas as pd

# Graceful PySpark Import Check
HAS_SPARK = False
try:
    from pyspark.sql import DataFrame as SparkDataFrame, SparkSession
    from pyspark.sql import functions as F
    from pyspark.sql.types import DoubleType, IntegerType, StringType
    HAS_SPARK = True
except ImportError:
    SparkSession = None
    SparkDataFrame = None
    F = None

from ingestion.transformer import DataTransformer

logger = logging.getLogger(__name__)


def get_spark_session(app_name: str = "RetailLens_Spark_Engine") -> Optional[Any]:
    """
    Creates or retrieves global PySpark SparkSession instance.

    :param app_name: Name of the Spark application.
    :return: SparkSession object or None if PySpark is not installed.
    """
    if not HAS_SPARK:
        logger.warning("PySpark is not installed in the current environment. PySpark features disabled.")
        return None

    try:
        spark = (
            SparkSession.builder.appName(app_name)
            .config("spark.sql.shuffle.partitions", "4")
            .config("spark.driver.memory", "1g")
            .getOrCreate()
        )
        return spark
    except Exception as e:
        logger.warning("Unable to initialize PySpark session: %s", str(e))
        return None


class SparkDataTransformer:
    """Distributed Feature Engineering Engine implementing PySpark transformations."""

    def __init__(self, spark: Optional[Any] = None):
        """Dependency injection constructor for PySpark SparkSession."""
        self.spark = spark or (get_spark_session() if HAS_SPARK else None)
        self.pandas_fallback = DataTransformer()

    def transform(self, data: Union[pd.DataFrame, Any]) -> Union[pd.DataFrame, Any]:
        """
        Executes distributed feature engineering transformations on Pandas or PySpark DataFrame.

        :param data: Input Pandas DataFrame or PySpark DataFrame.
        :return: Transformed DataFrame (matching input type).
        """
        if not HAS_SPARK or self.spark is None:
            logger.info("PySpark engine unavailable. Delegating transformation to Pandas DataTransformer.")
            if isinstance(data, pd.DataFrame):
                return self.pandas_fallback.transform(data)
            raise RuntimeError("PySpark is not available to process Spark DataFrame.")

        is_pandas = isinstance(data, pd.DataFrame)
        if is_pandas:
            logger.info("Converting Pandas DataFrame to PySpark DataFrame for distributed transformation...")
            spark_df = self.spark.createDataFrame(data)
        else:
            spark_df = data

        logger.info("Starting PySpark feature engineering transformations...")

        # 1. Whitespace Trimming & Casing Normalization
        if "StockCode" in spark_df.columns:
            spark_df = spark_df.withColumn("StockCode", F.upper(F.trim(F.col("StockCode"))))
        if "InvoiceNo" in spark_df.columns:
            spark_df = spark_df.withColumn("InvoiceNo", F.upper(F.trim(F.col("InvoiceNo"))))
        if "Country" in spark_df.columns:
            spark_df = spark_df.withColumn("Country", F.initcap(F.trim(F.col("Country"))))

        # 2. Null Imputation (CustomerID -> 'GUEST', Description -> 'UNKNOWN DESCRIPTION')
        if "CustomerID" in spark_df.columns:
            spark_df = spark_df.withColumn(
                "CustomerID",
                F.when(
                    F.col("CustomerID").isNull()
                    | (F.trim(F.col("CustomerID")) == "")
                    | (F.upper(F.trim(F.col("CustomerID"))).isin("NAN", "NONE", "NULL", "<NA>")),
                    F.lit("GUEST"),
                ).otherwise(F.trim(F.col("CustomerID"))),
            )

        if "Description" in spark_df.columns:
            spark_df = spark_df.withColumn(
                "Description",
                F.when(
                    F.col("Description").isNull()
                    | (F.trim(F.col("Description")) == "")
                    | (F.upper(F.trim(F.col("Description"))).isin("NAN", "NONE", "NULL")),
                    F.lit("UNKNOWN DESCRIPTION"),
                ).otherwise(F.trim(F.col("Description"))),
            )

        # 3. Total Line Item Amount (TotalPrice = Quantity * UnitPrice)
        if "Quantity" in spark_df.columns and "UnitPrice" in spark_df.columns:
            spark_df = spark_df.withColumn(
                "TotalPrice", F.round(F.col("Quantity") * F.col("UnitPrice"), 2)
            )
        else:
            spark_df = spark_df.withColumn("TotalPrice", F.lit(0.0))

        # 4. Temporal Feature Extraction (InvoiceYear, InvoiceMonth, InvoiceQuarter, InvoiceWeekday, InvoiceHour)
        if "InvoiceDate" in spark_df.columns:
            ts_col = F.to_timestamp(F.col("InvoiceDate"))
            spark_df = spark_df.withColumn("InvoiceYear", F.year(ts_col).cast("short"))
            spark_df = spark_df.withColumn("InvoiceMonth", F.month(ts_col).cast("byte"))
            spark_df = spark_df.withColumn("InvoiceQuarter", F.quarter(ts_col).cast("byte"))
            spark_df = spark_df.withColumn("InvoiceWeekday", F.date_format(ts_col, "EEEE"))
            spark_df = spark_df.withColumn("InvoiceHour", F.hour(ts_col).cast("byte"))

        # 5. Order Cancellation Flag
        if "InvoiceNo" in spark_df.columns and "Quantity" in spark_df.columns:
            starts_c = F.col("InvoiceNo").startswith("C")
            neg_qty = F.col("Quantity") < 0
            spark_df = spark_df.withColumn("IsCancellation", starts_c | neg_qty)
        else:
            spark_df = spark_df.withColumn("IsCancellation", F.lit(False))

        # 6. Customer Type Categorization
        if "CustomerID" in spark_df.columns:
            spark_df = spark_df.withColumn(
                "CustomerType",
                F.when(F.col("CustomerID") == "GUEST", F.lit("Guest")).otherwise(F.lit("Registered")),
            )
        else:
            spark_df = spark_df.withColumn("CustomerType", F.lit("Guest"))

        # 7. Revenue Segmentation Buckets
        if "TotalPrice" in spark_df.columns and "IsCancellation" in spark_df.columns:
            spark_df = spark_df.withColumn(
                "RevenueBucket",
                F.when(F.col("IsCancellation") == True, F.lit("Cancellation"))
                .when(F.col("TotalPrice") < 10.0, F.lit("Low (< £10)"))
                .when(
                    (F.col("TotalPrice") >= 10.0) & (F.col("TotalPrice") <= 50.0),
                    F.lit("Medium (£10-£50)"),
                )
                .otherwise(F.lit("High (> £50)")),
            )

        logger.info("PySpark feature engineering transformations compiled into Catalyst execution plan.")

        if is_pandas:
            logger.info("Collecting PySpark DataFrame back into Pandas DataFrame...")
            return spark_df.toPandas()

        return spark_df
