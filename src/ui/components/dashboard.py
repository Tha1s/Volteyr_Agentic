import streamlit as st
import pandas as pd

from src.db.product_repository import ProductRepository


def show_dashboard():
    st.header("Tableau de bord")
    repo = ProductRepository()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total produits", repo.count_all())
    col2.metric("Descriptions vides", repo.count_empty())
    col3.metric("Descriptions < 50c", repo.count_short(50))
    col4.metric("Descriptions < 200c", repo.count_short(200))

    total = repo.count_all()
    empty = repo.count_empty()
    short = repo.count_short(50)
    medium = repo.conn.execute(
        "SELECT COUNT(*) FROM products WHERE LENGTH(description) >= 50 AND LENGTH(description) < 200"
    ).fetchone()[0]
    long_ = repo.conn.execute(
        "SELECT COUNT(*) FROM products WHERE LENGTH(description) >= 200 AND LENGTH(description) < 500"
    ).fetchone()[0]
    very_long = repo.conn.execute(
        "SELECT COUNT(*) FROM products WHERE LENGTH(description) >= 500"
    ).fetchone()[0]

    quality_df = pd.DataFrame({
        "Catégorie": ["Vide", "< 50c", "50–200c", "200–500c", "> 500c"],
        "Nombre": [empty, short, medium, long_, very_long],
    })
    st.bar_chart(quality_df.set_index("Catégorie"))

    categories = repo.count_by_category()
    cat_df = pd.DataFrame(categories[:15], columns=["Catégorie", "Nombre"])
    st.bar_chart(cat_df.set_index("Catégorie"))

    vendors = repo.count_by_vendor()
    ven_df = pd.DataFrame(vendors[:15], columns=["Vendeur", "Nombre"])
    st.bar_chart(ven_df.set_index("Vendeur"))

    products = repo.find_all(100)
    preview = pd.DataFrame(products)[["product_id", "product_type", "category", "vendor", "description"]]
    preview["description"] = preview["description"].astype(str).str[:80]
    st.dataframe(preview)
