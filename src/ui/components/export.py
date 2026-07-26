import streamlit as st
import pandas as pd

from src.db.product_repository import ProductRepository
from src.db.enrichment_repository import EnrichmentRepository


def show_export_page():
    st.header("Export des enrichissements")
    repo = EnrichmentRepository()
    enriched_ids = repo.find_enriched_ids()

    if not enriched_ids:
        st.info("Aucun produit enrichi")
        return

    prod_repo = ProductRepository()
    categories = prod_repo.get_distinct_categories()
    selected_category = st.selectbox(
        "Filtrer par catégorie", ["Toutes"] + categories
    )

    rows = repo.find_enriched_with_products(
        category=selected_category if selected_category != "Toutes" else None
    )

    df = pd.DataFrame(rows)
    st.dataframe(df)
    csv_data = df.to_csv(index=False)
    st.download_button(
        label="📥 Exporter en CSV",
        data=csv_data,
        file_name="produits_enrichis.csv",
        mime="text/csv",
    )
