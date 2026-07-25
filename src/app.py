import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd

from db import get_connection, close as db_close

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


def dashboard_page():
    st.header("Tableau de bord")
    conn = get_connection()

    total = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    empty = conn.execute(
        "SELECT COUNT(*) FROM products WHERE description IS NULL OR description = ''"
    ).fetchone()[0]
    short = conn.execute(
        "SELECT COUNT(*) FROM products WHERE LENGTH(description) < 50 AND description IS NOT NULL AND description != ''"
    ).fetchone()[0]
    avg = conn.execute(
        "SELECT AVG(LENGTH(description)) FROM products WHERE description IS NOT NULL AND description != ''"
    ).fetchone()[0] or 0

    cols = st.columns(4)
    cols[0].metric("Total produits", total)
    cols[1].metric("Descriptions vides", empty)
    cols[2].metric("Descriptions < 50c", short)
    cols[3].metric("Longueur moyenne", f"{avg:.0f} caractères")

    med = conn.execute(
        "SELECT COUNT(*) FROM products WHERE LENGTH(description) >= 50 AND LENGTH(description) < 200 AND description IS NOT NULL AND description != ''"
    ).fetchone()[0]
    long_ = conn.execute(
        "SELECT COUNT(*) FROM products WHERE LENGTH(description) >= 200 AND LENGTH(description) < 500 AND description IS NOT NULL AND description != ''"
    ).fetchone()[0]
    xlong = conn.execute(
        "SELECT COUNT(*) FROM products WHERE LENGTH(description) >= 500 AND description IS NOT NULL AND description != ''"
    ).fetchone()[0]

    chart = pd.DataFrame({
        "Qualité": ["Vide", "<50c", "50-200c", "200-500c", ">500c"],
        "Nombre": [empty, short, med, long_, xlong],
    })
    st.subheader("Qualité des descriptions")
    st.bar_chart(chart.set_index("Qualité"), height=300)

    types_df = conn.execute("""
        SELECT product_type, COUNT(*) as nb
        FROM products
        WHERE product_type IS NOT NULL AND product_type != ''
        GROUP BY product_type
        ORDER BY nb DESC LIMIT 15
    """).fetchdf()
    st.subheader("Top 15 — Types de produits")
    st.bar_chart(types_df.set_index("product_type"), height=300)

    vendors_df = conn.execute("""
        SELECT vendor, COUNT(*) as nb
        FROM products
        WHERE vendor IS NOT NULL AND vendor != ''
        GROUP BY vendor
        ORDER BY nb DESC LIMIT 15
    """).fetchdf()
    st.subheader("Top 15 — Marques")
    st.bar_chart(vendors_df.set_index("vendor"), height=300)

    preview = conn.execute("""
        SELECT product_id, product_type, vendor, description
        FROM products LIMIT 100
    """).fetchdf()
    preview["Qualité"] = preview["description"].apply(quality_label)
    preview["description"] = preview["description"].apply(truncate_desc)
    st.subheader("Aperçu du catalogue")
    st.dataframe(
        preview.rename(columns={
            "product_id": "ID",
            "product_type": "Type",
            "vendor": "Marque",
            "description": "Description",
        }),
        use_container_width=True, hide_index=True,
    )

    db_close()


def filtering_page():
    st.header("Filtrage et export")
    conn = get_connection()

    quality_opts = ["Tous", "Vide", "<50c", "50-200c", ">200c"]
    q_filter = st.sidebar.selectbox("Qualité description", quality_opts, key="qual_filter")

    # Build base conditions from quality filter
    qual_map = {
        "Vide": "(p.description IS NULL OR p.description = '')",
        "<50c": "(LENGTH(p.description) < 50 AND p.description IS NOT NULL AND p.description != '')",
        "50-200c": "(LENGTH(p.description) >= 50 AND LENGTH(p.description) < 200 AND p.description IS NOT NULL AND p.description != '')",
        ">200c": "(LENGTH(p.description) >= 200 AND p.description IS NOT NULL AND p.description != '')",
    }

    base_conditions = ["1=1"]
    base_params = []
    if q_filter != "Tous":
        base_conditions.append(qual_map[q_filter])

    # Types filtered by quality
    all_types = [
        r[0]
        for r in conn.execute(
            f"SELECT DISTINCT p.product_type FROM products p WHERE {' AND '.join(base_conditions)} AND p.product_type IS NOT NULL AND p.product_type != '' ORDER BY p.product_type"
        ).fetchall()
    ]
    t_filter = st.sidebar.multiselect("Type de produit", all_types, key="type_filter")

    # Reset vendor selection when type filter changes
    prev_types = st.session_state.get("_prev_types", [])
    if t_filter != prev_types:
        st.session_state["vendor_filter"] = []
    st.session_state["_prev_types"] = t_filter

    # Vendors filtered by quality + type
    vendor_conditions = base_conditions.copy()
    vendor_params = base_params.copy()
    if t_filter:
        ph = ", ".join(["?"] * len(t_filter))
        vendor_conditions.append(f"p.product_type IN ({ph})")
        vendor_params.extend(t_filter)

    all_vendors = [
        r[0]
        for r in conn.execute(
            f"SELECT DISTINCT p.vendor FROM products p WHERE {' AND '.join(vendor_conditions)} AND p.vendor IS NOT NULL AND p.vendor != '' ORDER BY p.vendor",
            vendor_params,
        ).fetchall()
    ]
    v_filter = st.sidebar.multiselect("Marque", all_vendors, key="vendor_filter")

    conditions = base_conditions.copy()
    params = base_params.copy()

    if t_filter:
        ph = ", ".join(["?"] * len(t_filter))
        conditions.append(f"p.product_type IN ({ph})")
        params.extend(t_filter)

    if v_filter:
        ph = ", ".join(["?"] * len(v_filter))
        conditions.append(f"p.vendor IN ({ph})")
        params.extend(v_filter)

    where = " AND ".join(conditions)
    df = conn.execute(
        f"SELECT p.product_id, p.product_type, p.vendor, p.description FROM products p WHERE {where} ORDER BY p.product_id",
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

    display = df[["product_id", "product_type", "vendor", "description", "Qualité"]].copy()
    display.insert(0, "Sél.", display["product_id"].isin(st.session_state.sel_ids))

    edited = st.data_editor(
        display,
        column_config={
            "Sél.": st.column_config.CheckboxColumn("Sél."),
            "product_id": st.column_config.NumberColumn("ID"),
            "product_type": "Type",
            "vendor": "Marque",
            "description": "Description",
            "Qualité": "Qualité",
        },
        disabled=["product_id", "product_type", "vendor", "description", "Qualité"],
        hide_index=True,
        use_container_width=True,
        key="editor",
    )

    st.session_state.sel_ids = set(edited[edited["Sél."]]["product_id"].tolist())

    st.sidebar.markdown("---")
    n_sel = len(st.session_state.sel_ids)
    if n_sel > 0:
        st.sidebar.success(f"{n_sel} produit(s) sélectionné(s)")
        if st.sidebar.button("Exporter en CSV", use_container_width=True):
            ids = list(st.session_state.sel_ids)
            ph = ", ".join(["?"] * len(ids))
            export = conn.execute(
                f"""
                SELECT
                    p.product_id, p.product_type, p.vendor,
                    p.description AS original_description,
                    e.enriched_description, e.material,
                    e.care_instructions, e.style, e.seo_keywords
                FROM products p
                LEFT JOIN enrichissements e ON p.product_id = e.product_id
                WHERE p.product_id IN ({ph})
                ORDER BY p.product_id
            """,
                ids,
            ).fetchdf()

            csv = export.to_csv(index=False, encoding="utf-8-sig")
            st.sidebar.download_button(
                "Télécharger le CSV",
                csv,
                "produits_enrichis.csv",
                "text/csv",
                use_container_width=True,
            )
    else:
        st.sidebar.warning("Aucun produit sélectionné")

    db_close()


st.sidebar.title("Volteyr")
page = st.sidebar.selectbox(
    "Navigation", ["Tableau de bord", "Filtrage et export"], key="nav"
)

if page == "Tableau de bord":
    dashboard_page()
else:
    filtering_page()
