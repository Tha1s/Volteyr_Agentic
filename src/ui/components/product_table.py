import streamlit as st
import pandas as pd

from src.ui.utils import quality_label, truncate_desc

ROWS_PER_PAGE = 50


def show_product_table(products_df: pd.DataFrame) -> set[int]:
    df = products_df.copy()
    df["Qualité"] = df["description"].apply(quality_label)
    df["description"] = df["description"].apply(truncate_desc)

    display_df = df[["product_id", "product_type", "category", "vendor", "description", "Qualité"]]

    total_rows = len(display_df)
    total_pages = max(1, (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    page = st.session_state.get("product_page", 0)
    page = max(0, min(page, total_pages - 1))

    start = page * ROWS_PER_PAGE
    end = min(start + ROWS_PER_PAGE, total_rows)
    page_df = display_df.iloc[start:end]

    selection = st.dataframe(
        page_df,
        hide_index=True,
        use_container_width=True,
        selection_mode="multi-row",
        on_select="rerun",
        key=f"product_table_df_{page}",
    )

    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    with col2:
        if st.button("← Précédent", disabled=(page == 0), key="prev_page"):
            st.session_state["product_page"] = page - 1
            st.rerun()
    with col3:
        st.markdown(
            f'<p style="text-align:center;">Page {page + 1}/{total_pages}</p>',
            unsafe_allow_html=True,
        )
    with col4:
        if st.button("Suivant →", disabled=(page >= total_pages - 1), key="next_page"):
            st.session_state["product_page"] = page + 1
            st.rerun()

    selected_indices = list(selection.selection.rows) if selection.selection.rows else []
    if selected_indices:
        global_indices = [start + idx for idx in selected_indices]
        return set(df.iloc[global_indices]["product_id"].tolist())
    return set()
