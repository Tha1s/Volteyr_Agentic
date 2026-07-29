import csv
import io
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import streamlit as st

from src.ui.components.dashboard import show_dashboard
from src.ui.components.filters import show_filters
from src.ui.components.product_table import show_product_table
from src.ui.components.batch_enrich import show_batch_enrich
from src.ui.components.export import show_export_page
from src.db.product_repository import ProductRepository
from src.db.connection import get_connection

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Volteyr", layout="wide")


@st.cache_resource
def get_product_repo() -> ProductRepository:
    return ProductRepository()

if "db_initialized" not in st.session_state:
    conn = get_connection()
    try:
        conn.execute("SELECT 1 FROM products LIMIT 0")
    except Exception:
        st.error("Base de données non initialisée. Contactez l'administrateur.")
        st.stop()
    st.session_state.db_initialized = True

st.sidebar.title("Volteyr")
st.sidebar.caption("Enrichissement catalogue")

with st.sidebar.expander("📂 Charger un CSV", expanded=st.session_state.get("data_loaded", 0) == 0):
    uploaded = st.file_uploader("Fichier CSV (format Shopify)", type=["csv"])
    if uploaded:
        st.caption(f"Fichier : {uploaded.name}")
        if st.button("Charger les données", use_container_width=True):
            with st.spinner("Chargement..."):
                try:
                    content = uploaded.getvalue().decode("utf-8")
                    from src.db.loader import load_csv_from_dictreader

                    reader = csv.DictReader(io.StringIO(content))
                    count = load_csv_from_dictreader(reader)
                    st.session_state.data_loaded = count
                    st.rerun()
                    except (ValueError, KeyError) as e:
                        st.error(f"Erreur lors du chargement du CSV: {e}")
                    except Exception:
                        logger.exception("Erreur inattendue lors du chargement du CSV")
                        st.error("Erreur inattendue lors du chargement du CSV")

    if st.session_state.get("data_loaded", 0) > 0:
        st.success(f"✅ {st.session_state.data_loaded} produits chargés")

if st.session_state.get("enriching", False):
    st.sidebar.warning("⚠️ Enrichissement en cours...")
    show_batch_enrich(set())
else:
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
        repo = get_product_repo()
        try:
            products = repo.find_filtered(
                quality=filters.get("quality"),
                categories=filters.get("categories"),
                vendors=filters.get("vendors"),
            )
        except Exception:
            logger.exception("Erreur lors du filtrage des produits")
            st.error("Erreur lors de la récupération des produits")
            products = []
        if products:
            df = pd.DataFrame(products)
            selected = show_product_table(df)
            show_batch_enrich(selected)
        else:
            st.info("Aucun produit trouvé avec ces filtres")

    elif page == "📥 Export":
        show_export_page()
