import streamlit as st
import pandas as pd

from src.db.product_repository import ProductRepository


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
    df.insert(0, "Sél.", False)

    if "sel_ids" not in st.session_state:
        st.session_state.sel_ids = set()

    for i in df.index:
        pid = df.at[i, "product_id"]
        if pid in st.session_state.sel_ids:
            df.at[i, "Sél."] = True

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Tout sélectionner"):
            st.session_state.sel_ids = set(df["product_id"].tolist())
            st.rerun()
    with col2:
        if st.button("Tout désélectionner"):
            st.session_state.sel_ids = set()
            st.rerun()

    edited_df = st.data_editor(
        df,
        column_config={
            "Sél.": st.column_config.CheckboxColumn("Sél.", default=False),
            "Qualité": st.column_config.TextColumn("Qualité", disabled=True),
        },
        disabled=["product_id", "description", "Qualité"],
        hide_index=True,
        use_container_width=True,
        key="product_table_editor",
    )

    st.session_state.sel_ids = set(
        edited_df.loc[edited_df["Sél."] == True, "product_id"].tolist()
    )

    return st.session_state.sel_ids
