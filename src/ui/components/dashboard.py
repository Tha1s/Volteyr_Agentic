import streamlit as st
import pandas as pd

from src.db.product_repository import ProductRepository


@st.cache_data(ttl=60)
def _get_dashboard_stats(data_loaded: int):
    repo = ProductRepository()
    total = repo.count_all()
    empty = repo.count_empty()
    short = repo.count_short(50)
    medium = repo.count_medium()
    long_ = repo.count_long()
    very_long = repo.count_very_long()
    categories = repo.count_by_category()
    vendors = repo.count_by_vendor()
    products = repo.find_all(100)
    return total, empty, short, medium, long_, very_long, categories, vendors, products


def show_dashboard():
    st.header("Tableau de bord")

    data_version = st.session_state.get("data_loaded", 0)
    total, empty, short, medium, long_, very_long, categories, vendors, products = (
        _get_dashboard_stats(data_version)
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total produits", total)
    col2.metric("Descriptions vides", empty)
    col3.metric("Descriptions < 50c", short)
    col4.metric("Descriptions < 200c", short + medium)

    if total == 0:
        st.info("Aucun produit dans la base. Chargez un CSV pour commencer.")
        return

    quality_df = pd.DataFrame({
        "Catégorie": ["Vide", "< 50c", "50–200c", "200–500c", "> 500c"],
        "Nombre": [empty, short, medium, long_, very_long],
    })
    st.bar_chart(quality_df.set_index("Catégorie"))

    cat_df = pd.DataFrame(categories[:15], columns=["Catégorie", "Nombre"])
    st.bar_chart(cat_df.set_index("Catégorie"))

    ven_df = pd.DataFrame(vendors[:15], columns=["Vendeur", "Nombre"])
    st.bar_chart(ven_df.set_index("Vendeur"))

    preview = pd.DataFrame(products)[["product_id", "product_type", "category", "vendor", "description"]]
    preview["description"] = preview["description"].astype(str).str[:80]
    st.dataframe(preview)
