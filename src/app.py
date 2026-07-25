import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd

from db import get_connection
from llm_client import enrich_product, check_ollama, enrich_batch, MODEL

st.set_page_config(page_title="Volteyr — Catalogue Produits", layout="wide")


def quality_label(desc):
    if desc is None or (isinstance(desc, str) and desc.strip() == ""):
        return "Vide"
    if not isinstance(desc, str):
        desc = str(desc)
    length = len(desc)
    if length < 50:
        return "<50c"
    elif length < 200:
        return "50-200c"
    elif length < 500:
        return "200-500c"
    else:
        return ">500c"


def truncate_desc(desc, max_len=80):
    if desc is None:
        return ""
    s = str(desc)
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s


def enrichment_page():
    st.title("Enrichissement IA")
    conn = get_connection()

    products_df = conn.execute(
        "SELECT product_id, product_type, category, vendor, description, product_tags FROM products ORDER BY product_id"
    ).fetchdf()

    with st.expander("Test rapide", expanded=True):
        product_ids = products_df["product_id"].tolist()
        selected_id = st.selectbox("Produit à enrichir", product_ids, format_func=lambda x: f"#{x}")
        product = products_df[products_df["product_id"] == selected_id].iloc[0]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Type brut:** {product['product_type'] or ''}")
            st.markdown(f"**Catégorie:** {product['category'] or ''}")
            st.markdown(f"**Marque:** {product['vendor'] or ''}")
            st.markdown("**Description originale:**")
            st.info(product["description"] or "(vide)")

        if st.button("Enrichir un test", type="primary"):
            with st.spinner("Appel à Ollama..."):
                result = enrich_product(
                    description=product["description"],
                    product_type=product["product_type"],
                    vendor=product["vendor"],
                    category=product["category"],
                    tags=product["product_tags"],
                )

            if result is None:
                st.error("Échec de l'enrichissement — Ollama n'a pas retourné de réponse valide.")
                st.session_state["_enrich_test_ok"] = False
            else:
                st.session_state["_enrich_result"] = result
                st.session_state["_enrich_test_ok"] = True

                st.subheader("Résultat")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Description originale**")
                    st.info(product["description"] or "(vide)")
                with c2:
                    st.markdown("**Description enrichie**")
                    st.success(result.get("enriched_description", ""))

                attrs = {
                    "MATIÈRE": result.get("material", ""),
                    "ENTRETIEN": result.get("care_instructions", ""),
                    "STYLE": result.get("style", ""),
                    "SEO": result.get("seo_keywords", ""),
                }
                for label, val in attrs.items():
                    if val:
                        st.markdown(f"**{label}**")
                        st.write(val)

    with st.expander("Enrichissement par lot", expanded=True):
        quality_opts = ["Tous", "Vide", "<50c", "50-200c", ">200c"]
        q_filter = st.sidebar.selectbox("Qualité description", quality_opts, key="qual_filter")

        qual_map = {
            "Vide": "(description IS NULL OR description = '')",
            "<50c": "(LENGTH(description) < 50 AND description IS NOT NULL AND description != '')",
            "50-200c": "(LENGTH(description) >= 50 AND LENGTH(description) < 200 AND description IS NOT NULL AND description != '')",
            ">200c": "(LENGTH(description) >= 200 AND description IS NOT NULL AND description != '')",
        }

        base_conditions = ["1=1"]
        if q_filter != "Tous":
            base_conditions.append(qual_map[q_filter])

        all_types = [
            r[0]
            for r in conn.execute(
                f"SELECT DISTINCT category FROM products WHERE {' AND '.join(base_conditions)} AND category IS NOT NULL AND category != '' ORDER BY category"
            ).fetchall()
        ]
        t_filter = st.sidebar.multiselect("Catégorie", all_types, key="type_filter")

        prev_types = st.session_state.get("_prev_types", [])
        if t_filter != prev_types:
            st.session_state["vendor_filter"] = []
        st.session_state["_prev_types"] = t_filter

        vendor_conditions = base_conditions.copy()
        if t_filter:
            ph = ", ".join(["?"] * len(t_filter))
            vendor_conditions.append(f"category IN ({ph})")

        all_vendors = [
            r[0]
            for r in conn.execute(
                f"SELECT DISTINCT vendor FROM products WHERE {' AND '.join(vendor_conditions)} AND vendor IS NOT NULL AND vendor != '' ORDER BY vendor",
                t_filter,
            ).fetchall()
        ]
        v_filter = st.sidebar.multiselect("Marque", all_vendors, key="vendor_filter")

        conditions = base_conditions.copy()
        params = []
        if t_filter:
            ph = ", ".join(["?"] * len(t_filter))
            conditions.append(f"category IN ({ph})")
            params.extend(t_filter)
        if v_filter:
            ph = ", ".join(["?"] * len(v_filter))
            conditions.append(f"vendor IN ({ph})")
            params.extend(v_filter)

        where = " AND ".join(conditions)
        df = conn.execute(
            f"SELECT product_id, product_type, category, vendor, description FROM products WHERE {where} ORDER BY product_id",
            params,
        ).fetchdf()

        df["Qualité"] = df["description"].apply(quality_label)
        df["description"] = df["description"].apply(truncate_desc)

        if "sel_ids" not in st.session_state:
            st.session_state.sel_ids = set()

        cb1, cb2 = st.columns([1, 1])
        if cb1.button("Tout sélectionner", use_container_width=True):
            st.session_state.sel_ids = set(df["product_id"].tolist())
            st.rerun()
        if cb2.button("Tout désélectionner", use_container_width=True):
            st.session_state.sel_ids = set()
            st.rerun()

        current_ids = set(df["product_id"].tolist())
        st.session_state.sel_ids &= current_ids

        display = df[["product_id", "product_type", "category", "vendor", "description", "Qualité"]].copy()
        display.insert(0, "Sél.", display["product_id"].isin(st.session_state.sel_ids))

        edited = st.data_editor(
            display,
            column_config={
                "Sél.": st.column_config.CheckboxColumn("Sél."),
                "product_id": st.column_config.NumberColumn("ID"),
                "product_type": "Type brut",
                "category": "Catégorie",
                "vendor": "Marque",
                "description": "Description",
                "Qualité": "Qualité",
            },
            disabled=["product_id", "product_type", "category", "vendor", "description", "Qualité"],
            hide_index=True,
            use_container_width=True,
            key="editor",
        )

        st.session_state.sel_ids = set(edited[edited["Sél."]]["product_id"].tolist())

        st.sidebar.markdown("---")
        n_sel = len(st.session_state.sel_ids)
        if n_sel > 0:
            st.sidebar.success(f"{n_sel} produit(s) sélectionné(s)")

            if "batch_done" not in st.session_state:
                st.session_state.batch_done = False
            if "batch_enriched" not in st.session_state:
                st.session_state.batch_enriched = 0

            if st.sidebar.button(f"Enrichir la sélection ({n_sel})", use_container_width=True):
                if not check_ollama():
                    st.sidebar.error("Ollama n'est pas disponible. Vérifie que le service tourne.")
                else:
                    progress_bar = st.progress(0, text="Préparation...")
                    status = st.status("Enrichissement en cours...", expanded=True)

                    sel_ids_sorted = sorted(st.session_state.sel_ids)
                    products_data = []
                    for pid in sel_ids_sorted:
                        row = conn.execute(
                            "SELECT category, product_type, vendor, description, product_tags FROM products WHERE product_id = ?",
                            [pid],
                        ).fetchone()
                        if row:
                            products_data.append({
                                "description": row[3] or "",
                                "product_type": row[1] or "",
                                "category": row[0] or "",
                                "vendor": row[2] or "",
                                "tags": row[4] or "",
                            })

                    total = len(products_data)
                    enriched = 0
                    failed = 0

                    for i, result in enumerate(enrich_batch(products_data)):
                        if result["result"]:
                            r = result["result"]
                            conn.execute(
                                """UPDATE products SET
                                    enriched_description = ?,
                                    material = ?,
                                    care_instructions = ?,
                                    style = ?,
                                    seo_keywords = ?,
                                    enriched_at = CURRENT_TIMESTAMP,
                                    model_used = ?
                                WHERE product_id = ?""",
                                [r.get("enriched_description"), r.get("material"),
                                 r.get("care_instructions"), r.get("style"),
                                 r.get("seo_keywords"), MODEL,
                                 sel_ids_sorted[i]],
                            )
                            enriched += 1
                        else:
                            failed += 1

                        progress_bar.progress((i + 1) / total, text=f"{i+1}/{total} — {enriched} OK, {failed} échecs")

                    status.update(label=f"Terminé — {enriched} enrichis, {failed} échecs", state="complete" if failed == 0 else "error")
                    st.session_state.batch_done = True
                    st.session_state.batch_enriched = enriched
                    st.rerun()

            if st.session_state.batch_done and st.session_state.batch_enriched > 0:
                st.sidebar.markdown("---")
                ids = list(st.session_state.sel_ids)
                ph = ", ".join(["?"] * len(ids))
                export = conn.execute(
                    f"""
                    SELECT product_id, product_type, category, vendor, description,
                           enriched_description, material, care_instructions, style, seo_keywords, enriched_at
                    FROM products
                    WHERE product_id IN ({ph})
                """,
                    ids,
                ).fetchdf()
                csv_data = export.to_csv(index=False, encoding="utf-8-sig")
                st.sidebar.download_button(
                    "📥 Exporter le lot en CSV",
                    csv_data,
                    "produits_enrichis.csv",
                    "text/csv",
                    use_container_width=True,
                )
        else:
            st.sidebar.info("Sélectionnez des produits dans le tableau pour les enrichir")


st.sidebar.title("Volteyr")
page = st.sidebar.selectbox("Navigation", ["Enrichissement"], key="nav")

if page == "Enrichissement":
    enrichment_page()
