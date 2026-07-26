import threading

import streamlit as st

from src.db.product_repository import ProductRepository
from src.enrichment.pipeline import EnrichmentPipeline
from src.llm.client import check_ollama


def _run_enrichment(ids: list[int], large_model: bool, shared: dict) -> None:
    try:
        repo = ProductRepository()
        products = repo.find_by_ids(ids)
        products_data = [
            {
                "product_id": p["product_id"],
                "product_type": p.get("product_type", ""),
                "category": p.get("category", ""),
                "vendor": p.get("vendor", ""),
                "description": p.get("description", ""),
                "product_tags": p.get("product_tags", ""),
            }
            for p in products
        ]

        shared["progress"] = 0.0
        shared["status"] = "Enrichissement en cours..."

        pipeline = EnrichmentPipeline()

        if large_model and len(products_data) == 1:
            result = pipeline.run_single(products_data[0])
            if result:
                pipeline.persist.process([result])
                shared["model"] = result.model_used
                shared["success"] = 1
                shared["failures"] = 0
                shared["result"] = result
                shared["status"] = f"Enrichi avec {result.model_used}"
            else:
                shared["success"] = 0
                shared["failures"] = 1
                shared["status"] = "Échec de l'enrichissement"
        else:
            success, failures = pipeline.run(products_data, batch_size=5)
            shared["success"] = success
            shared["failures"] = failures
            shared["status"] = f"Terminé: {success} OK, {failures} échecs"

        shared["progress"] = 1.0
    except Exception as e:
        shared["status"] = f"Erreur: {e}"
        shared["progress"] = 1.0
        shared["failures"] = len(ids)
        shared["success"] = 0


def show_batch_enrich(selected_ids: set[int]) -> None:
    if st.session_state.get("enriching", False):
        _render_enrichment_progress()
        return

    if not selected_ids:
        st.info("Sélectionnez des produits dans le tableau")
        return

    st.sidebar.success(f"{len(selected_ids)} produit(s) sélectionné(s)")

    if not st.sidebar.button(
        f"Enrichir la sélection ({len(selected_ids)})",
        type="primary",
    ):
        return

    if not check_ollama():
        st.error("Ollama n'est pas disponible")
        return

    ids = sorted(selected_ids)
    shared: dict = {}

    st.session_state.enriching = True
    st.session_state.enrich_shared = shared
    st.session_state.enrich_ids = ids
    st.session_state.enrich_large = len(ids) == 1

    t = threading.Thread(
        target=_run_enrichment,
        args=(ids, len(ids) == 1, shared),
        daemon=True,
    )
    t.start()
    st.rerun()


def _render_enrichment_progress() -> None:
    shared = st.session_state.get("enrich_shared", {})
    progress = shared.get("progress", 0.0)
    status_text = shared.get("status", "Enrichissement en cours...")
    success = shared.get("success", 0)
    failures = shared.get("failures", 0)

    st.info("⚠️ L'enrichissement est en cours — ne changez pas de page.")
    st.progress(progress, text=status_text)

    if progress >= 1.0:
        st.session_state.enriching = False
        st.rerun()

    import time
    time.sleep(1)
    st.rerun()
