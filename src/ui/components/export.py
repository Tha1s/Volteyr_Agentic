import streamlit as st
import pandas as pd

from src.db.product_repository import ProductRepository
from src.db.enrichment_repository import EnrichmentRepository


EXPORT_COLUMNS = [
    "product_id", "category", "enriched_description", "material",
    "care_instructions", "style", "seo_keywords", "model_used", "created_at",
]


def _fetch_enriched(selected_ids: set[int]) -> pd.DataFrame:
    repo = EnrichmentRepository()
    if not selected_ids:
        return pd.DataFrame(columns=EXPORT_COLUMNS)
    placeholders = ",".join("?" * len(selected_ids))
    rows = repo._conn.execute(
        f"""
        SELECT p.product_id, p.category, e.enriched_description, e.material,
               e.care_instructions, e.style, e.seo_keywords, e.model_used, e.created_at
        FROM products p
        INNER JOIN enrichissements e ON p.product_id = e.product_id
        WHERE p.product_id IN ({placeholders})
        ORDER BY p.product_id
        """,
        list(selected_ids),
    ).fetchall()
    return pd.DataFrame(rows, columns=EXPORT_COLUMNS)


def show_export(selected_ids: set[int]):
    if not selected_ids and not st.session_state.get("batch_completed"):
        return
    st.sidebar.divider()
    df = _fetch_enriched(selected_ids)
    if df.empty:
        return
    csv_data = df.to_csv(index=False)
    st.sidebar.download_button(
        label="📥 Exporter le lot en CSV",
        data=csv_data,
        file_name="produits_enrichis.csv",
        mime="text/csv",
    )


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

    query = """
        SELECT p.product_id, p.category, e.enriched_description, e.material,
               e.care_instructions, e.style, e.seo_keywords, e.model_used, e.created_at
        FROM products p
        INNER JOIN enrichissements e ON p.product_id = e.product_id
    """
    params = []
    if selected_category != "Toutes":
        query += " WHERE p.category = ?"
        params.append(selected_category)
    query += " ORDER BY p.product_id"

    rows = repo._conn.execute(query, params).fetchall()
    df = pd.DataFrame(rows, columns=EXPORT_COLUMNS)

    st.dataframe(df)
    csv_data = df.to_csv(index=False)
    st.download_button(
        label="📥 Exporter en CSV",
        data=csv_data,
        file_name="produits_enrichis.csv",
        mime="text/csv",
    )
