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

st.set_page_config(page_title="Volteyr", layout="wide")

if "db_initialized" not in st.session_state:
    conn = get_connection()
    init_schema()
    st.session_state.db_initialized = True

st.sidebar.title("Volteyr")
st.sidebar.caption("Enrichissement catalogue")

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
