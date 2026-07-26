import csv
import io
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.ui.components.dashboard import show_dashboard
from src.ui.components.filters import show_filters
from src.ui.components.product_table import show_product_table
from src.ui.components.batch_enrich import show_batch_enrich
from src.ui.components.export import show_export_page
from src.db.product_repository import ProductRepository
from src.db.schema import init_schema
from src.db.connection import get_connection
from src.config.categories import normalize_product_type, load_category_map

st.set_page_config(page_title="Volteyr", layout="wide")

if "db_initialized" not in st.session_state:
    conn = get_connection()
    init_schema()
    st.session_state.db_initialized = True

st.sidebar.title("Volteyr")
st.sidebar.caption("Enrichissement catalogue")

with st.sidebar.expander("📂 Charger un CSV", expanded=st.session_state.get("data_loaded", 0) == 0):
    uploaded = st.file_uploader("Fichier CSV (format Shopify)", type=["csv"])
    if uploaded:
        st.caption(f"Fichier : {uploaded.name}")
        if st.button("Charger les données", use_container_width=True):
            mapping = load_category_map()
            reader = csv.DictReader(io.StringIO(uploaded.getvalue().decode("utf-8")))
            rows = []
            for row in reader:
                raw_type = row["product_type"]
                category = normalize_product_type(raw_type, mapping)
                rows.append((
                    int(row["product_id"]),
                    row["product_type"],
                    category,
                    row["product_tags"],
                    row["images_array"],
                    row["vendor"],
                    int(row["inventory_quantity"]),
                    float(row["gross_amount_exc_tax_product"]),
                    row["description"],
                ))
            conn = get_connection()
            conn.execute("DELETE FROM products")
            conn.executemany(
                """INSERT INTO products (product_id, product_type, category, product_tags, images_array, vendor, inventory_quantity, gross_amount_exc_tax_product, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            conn.commit()
            st.session_state.data_loaded = len(rows)
            st.rerun()

    if st.session_state.get("data_loaded", 0) > 0:
        st.success(f"✅ {st.session_state.data_loaded} produits chargés")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Tableau de bord", "✨ Enrichissement", "📥 Export"],
    key="nav",
)

if page == "📊 Tableau de bord":
    show_dashboard()

elif page == "✨ Enrichissement":
    st.title("Enrichissement IA")
    filters = show_filters()
    repo = ProductRepository()
    products = repo.find_filtered(
        quality=filters.get("quality"),
        categories=filters.get("categories"),
        vendors=filters.get("vendors"),
    )
    if products:
        import pandas as pd

        df = pd.DataFrame(products)
        selected = show_product_table(df)
        show_batch_enrich(selected)
    else:
        st.info("Aucun produit trouvé avec ces filtres")

elif page == "📥 Export":
    show_export_page()
