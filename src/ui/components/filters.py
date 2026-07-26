import streamlit as st

from src.db.product_repository import ProductRepository


def show_filters() -> dict:
    repo = ProductRepository()

    quality = st.sidebar.selectbox(
        "Qualité description",
        options=["Toutes", "Vide", "<50c", "50-200c", "200-500c", ">500c"],
    )

    categories = repo.get_distinct_categories()
    selected_categories = st.sidebar.multiselect("Catégorie", options=categories)

    if selected_categories:
        vendors = sorted({
            r["vendor"]
            for r in repo.find_filtered(categories=selected_categories)
            if r["vendor"] is not None
        })
    else:
        vendors = repo.get_distinct_vendors()

    selected_vendors = st.sidebar.multiselect("Marque", options=vendors)

    if quality == "Toutes":
        quality = None

    return {
        "quality": quality,
        "categories": selected_categories,
        "vendors": selected_vendors,
    }
