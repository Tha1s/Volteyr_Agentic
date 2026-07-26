import streamlit as st
from src.db.product_repository import ProductRepository
from src.enrichment.pipeline import EnrichmentPipeline
from src.llm.client import check_ollama


def show_batch_enrich(selected_ids: set[int]) -> None:
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

    progress_bar = st.progress(0, text="Récupération des produits...")
    status = st.status("Enrichissement...")

    repo = ProductRepository()
    products = repo.find_by_ids(list(selected_ids))
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

    if not products_data:
        status.update(label="Aucun produit trouvé", state="error")
        return

    pipeline = EnrichmentPipeline()

    if len(selected_ids) == 1:
        progress_bar.progress(0, text="Enrichissement unitaire...")
        result = pipeline.run_single(products_data[0])
        if result:
            pipeline.persist.process([result])
            st.session_state["_last_enrichment"] = result
            status.update(label=f"Enrichi avec {result.model_used}", state="complete")
            st.write(f"**Modèle utilisé:** {result.model_used}")
            st.write(f"**Description:** {result.enriched_description[:200]}...")
        else:
            status.update(label="Échec de l'enrichissement", state="error")
        progress_bar.progress(1.0, text="Terminé")
        return

    progress_bar.progress(0, text="Enrichissement batch...")

    success, failures = pipeline.run(products_data, batch_size=5)

    progress_bar.progress(1.0, text="Terminé")
    status.update(
        label=f"Terminé: {success} OK, {failures} échecs",
        state="complete" if failures == 0 else "error",
    )

    st.rerun()
