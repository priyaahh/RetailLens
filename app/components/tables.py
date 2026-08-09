"""
tables.py
---------
Reusable interactive data table component for Streamlit views.
Applies column formatting and rendering.
"""

import pandas as pd
import streamlit as st


def render_data_table(
    df: pd.DataFrame,
    column_config: dict = None,
    use_container_width: bool = True,
    hide_index: bool = True,
) -> None:
    """
    Renders an interactive DataFrame with custom formatting.

    :param df: Input DataFrame.
    :param column_config: Optional Streamlit column configuration dictionary.
    :param use_container_width: Stretch table width.
    :param hide_index: Hide index column.
    """
    if df.empty:
        st.info("ℹ️ No data available for the selected filters.")
        return

    st.dataframe(
        df,
        column_config=column_config,
        use_container_width=use_container_width,
        hide_index=hide_index,
    )
