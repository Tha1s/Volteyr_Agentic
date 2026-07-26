import streamlit as st
import pandas as pd


def quality_label(desc: str | None) -> str:
    if not desc:
        return "Vide"
    length = len(desc)
    if length < 50:
        return "<50c"
    if length < 200:
        return "50-200c"
    if length < 500:
        return "200-500c"
    return ">500c"


def truncate_desc(desc: str | None, max_len: int = 80) -> str:
    if not desc:
        return ""
    if len(desc) > max_len:
        return desc[:max_len] + "..."
    return desc


def show_product_table(products_df: pd.DataFrame) -> set[int]:
    df = products_df.copy()
    df["Qualité"] = df["description"].apply(quality_label)
    df["description"] = df["description"].apply(truncate_desc)

    display_df = df[["product_id", "product_type", "category", "vendor", "description", "Qualité"]]

    selection = st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        selection_mode="multi-row",
        on_select="rerun",
        key="product_table_df",
    )

    selected_indices = list(selection.selection.rows) if selection.selection.rows else []
    if selected_indices:
        return set(df.iloc[selected_indices]["product_id"].tolist())
    return set()
