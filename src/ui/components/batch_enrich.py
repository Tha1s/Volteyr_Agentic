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
    products_data = []
    for pid in selected_ids:
        product = repo.find_by_id(pid)
        if product:
            products_data.append({
                "product_id": product["product_id"],
                "product_type": product.get("product_type", ""),
                "category": product.get("category", ""),
                "vendor": product.get("vendor", ""),
                "description": product.get("description", ""),
                "product_tags": product.get("product_tags", ""),
            })

    if not products_data:
        status.update(label="Aucun produit trouvé", state="error")
        return

    pipeline = EnrichmentPipeline()

    progress_bar.progress(0, text="Normalisation...")
    norm_products = pipeline.normalize.process(products_data)

    total = len(norm_products)
    batch_size = 5
    success_ids: list[int] = []
    fail_ids: list[int] = []

    for i in range(0, total, batch_size):
        batch = norm_products[i : i + batch_size]
        batch_results = pipeline.generate.process(batch)
        for product, result in zip(batch, batch_results):
            if result is not None:
                success_ids.append(product["product_id"])
            else:
                fail_ids.append(product["product_id"])
        batch_success, batch_failures = pipeline.persist.process(batch_results)

        progress = min(i + len(batch), total)
        progress_bar.progress(progress / total, text=f"{progress}/{total}")
        status.update(
            label=f"Enrichissement... {len(success_ids)} OK, {len(fail_ids)} échecs",
        )

    progress_bar.progress(1.0, text="Terminé")
    status.update(
        label=f"Terminé: {len(success_ids)} OK, {len(fail_ids)} échecs",
        state="complete" if not fail_ids else "error",
    )

    with status:
        if success_ids:
            st.write(f"✅ Réussis ({len(success_ids)}) : {sorted(success_ids)}")
        if fail_ids:
            st.write(f"❌ Échecs ({len(fail_ids)}) : {sorted(fail_ids)}")

    st.rerun()
