# Documentation UI — Volteyr

---

## Vue d'ensemble

L'interface utilisateur est une application **Streamlit** composée de 3 pages accessibles via une radio en sidebar :

| Page | Label | Fonction |
|---|---|---|
| Tableau de bord | `📊 Tableau de bord` | Statistiques et visualisation du catalogue |
| Enrichissement | `✨ Enrichissement` | Filtrage, sélection et enrichissement IA |
| Export | `📥 Export` | Export CSV des produits enrichis |

Toutes les pages partagent la même sidebar contenant la navigation et le chargeur CSV.

---

## `app.py` — Point d'entrée

**Fichier** : `src/ui/app.py:1-78`

### Initialisation (`:21-26`)

- `st.set_page_config(page_title="Volteyr", layout="wide")` — définit la page en mode *wide*.
- Au premier rendu (`db_initialized` absent de `session_state`), initialise le schéma DuckDB via `init_schema()` (`:23-26`).

### Sidebar : titre et upload CSV (`:28-51`)

- Titre `"Volteyr"` et sous-titre `"Enrichissement catalogue"`.
- Uploader CSV dans un `st.expander` (`:31-51`) :
  - L'expander est ouvert par défaut si aucune donnée n'est chargée (via `st.session_state.get("data_loaded", 0) == 0`).
  - Upload via `st.file_uploader("Fichier CSV (format Shopify)")`, accepte uniquement `.csv`.
  - Le bouton `"Charger les données"` décode le fichier, le passe à `csv.DictReader`, puis appelle `load_csv_from_dictreader()` (`:40-41`).
  - En cas de succès, `data_loaded` reçoit le nombre de produits et `st.rerun()` est déclenché (`:42-43`).
  - Gestion d'erreurs séparée pour `ValueError`/`KeyError` (format CSV invalide) et exceptions génériques (`:44-47`).
  - Affichage du nombre de produits chargés si > 0 (`:49-50`).

### Navigation (`:52-56`)

- `st.sidebar.radio` avec 3 options, stockées dans la clé `nav` du `session_state`.

### Routage des pages (`:58-78`)

- **Tableau de bord** (`:58-59`) : appelle `show_dashboard()`.
- **Enrichissement** (`:61-75`) :
  - Affiche `show_filters()` dans la sidebar (`:63`).
  - Récupère les produits filtrés via `ProductRepository.find_filtered()` (`:65-68`).
  - Si des produits existent : affiche `show_product_table()` pour sélection, puis `show_batch_enrich()` (`:71-73`).
  - Sinon : message `"Aucun produit trouvé avec ces filtres"` (`:75`).
- **Export** (`:77-78`) : appelle `show_export_page()`.

---

## Composants

### `dashboard.py` — Tableau de bord

**Fichier** : `src/ui/components/dashboard.py:1-54`

#### Cache (`:7-19`)

`_get_dashboard_stats()` est décorée avec `@st.cache_data(ttl=60)`. La clé de cache dépend de `data_loaded` pour invalider après un nouveau chargement CSV.

Statistiques récupérées :

| Variable | Méthode | Description |
|---|---|---|
| `total` | `repo.count_all()` | Nombre total de produits (`:11`) |
| `empty` | `repo.count_empty()` | Descriptions vides (`:12`) |
| `short` | `repo.count_short(50)` | Descriptions < 50 caractères (`:13`) |
| `medium` | `repo.count_medium()` | Descriptions 50–200 caractères (`:14`) |
| `long_` | `repo.count_long()` | Descriptions 200–500 caractères (`:15`) |
| `very_long` | `repo.count_very_long()` | Descriptions > 500 caractères (`:16`) |
| `categories` | `repo.count_by_category()` | Top catégories (`:17`) |
| `vendors` | `repo.count_by_vendor()` | Top vendeurs (`:18`) |
| `products` | `repo.find_all(100)` | 100 derniers produits pour preview (`:19`) |

#### Affichage (`:22-54`)

- **4 métriques** en colonnes (`:30-35`) : Total produits, Descriptions vides, <50c, <200c.
- Si le catalogue est vide (`total == 0`), message informatif et return (`:36-38`).
- **Bar chart qualité** : distribution des descriptions par tranche de longueur (`:40-44`).
- **Bar chart catégories** : top 15 catégories les plus représentées (`:46-47`).
- **Bar chart vendeurs** : top 15 marques les plus représentées (`:49-50`).
- **Table preview** : 100 derniers produits avec colonnes `product_id`, `product_type`, `category`, `vendor` et description tronquée à 80 caractères (`:52-54`).

---

### `filters.py` — Filtres sidebar

**Fichier** : `src/ui/components/filters.py:1-35`

**Fonction** : `show_filters() -> dict` — retourne un dictionnaire `{"quality", "categories", "vendors"}`.

#### Filtre qualité (`:9-12`)

- `st.sidebar.selectbox("Qualité description")` — options : `Toutes`, `Vide`, `<50c`, `50-200c`, `200-500c`, `>500c`.
- Si `"Toutes"`, la valeur est convertie en `None` (`:28-29`).

#### Filtre catégorie (`:14-15`)

- `st.sidebar.multiselect` alimenté par `repo.get_distinct_categories()`.

#### Filtre marque avec cascade (`:17-26`)

- Si des catégories sont sélectionnées, les marques sont filtrées sur cette sélection via `repo.find_filtered(categories=...)` (`:18-22`).
- Sinon, toutes les marques distinctes sont affichées (`:24`).
- `st.sidebar.multiselect` pour la sélection.

---

### `product_table.py` — Table de sélection

**Fichier** : `src/ui/components/product_table.py:1-53`

**Fonction** : `show_product_table(products_df: pd.DataFrame) -> set[int]` — retourne un `set` de `product_id` sélectionnés.

#### Préparation des données (`:10-14`)

- Ajoute une colonne `"Qualité"` via `quality_label()` (`:11`).
- Tronque les descriptions via `truncate_desc()` (80 caractères par défaut) (`:12`).
- Colonnes affichées : `product_id`, `product_type`, `category`, `vendor`, `description`, `Qualité` (`:14`).

#### Pagination (`:16-23`)

- **50 lignes par page** (`ROWS_PER_PAGE = 50`, `:6`).
- Calcul du nombre total de pages (`:17`).
- Page courante depuis `session_state["product_page"]`, bornée à `[0, total_pages - 1]` (`:18-19`).
- Slice du DataFrame : `page_df = display_df.iloc[start:end]` (`:21-23`).

#### Dataframe interactif (`:25-32`)

- `st.dataframe` avec `selection_mode="multi-row"` et `on_select="rerun"`.
- `key` unique par page : `f"product_table_df_{page}"` (`:31`) — chaque page a sa propre clé pour éviter les conflits de sélection.

#### Navigation (`:34-47`)

- 5 colonnes : layout centré avec boutons `← Précédent` (désactivé si `page == 0`) et `Suivant →` (désactivé si dernière page) (`:34-47`).
- Affichage centralisé `"Page X/Y"` en HTML (`:40-43`).
- Les boutons mettent à jour `session_state["product_page"]` puis déclenchent `st.rerun()`.

#### Sélection (`:49-53`)

- Convertit les indices de la page courante en indices globaux du DataFrame original.
- Retourne le `set` des `product_id` correspondants.

---

### `batch_enrich.py` — Enrichissement

**Fichier** : `src/ui/components/batch_enrich.py:1-71`

**Fonction** : `show_batch_enrich(selected_ids: set[int]) -> None`

#### Sans sélection (`:8-10`)

- Si `selected_ids` est vide, message informatif `"Sélectionnez des produits dans le tableau"` et return.

#### Compteur sidebar (`:12-13`)

- Affiche `"{n} produit(s) sélectionné(s)"` dans la sidebar.

#### Bouton d'action (`:14-18`)

- Bouton `"Enrichir la sélection ({n})"` de type `primary` dans la sidebar.
- Si non cliqué, retour immédiat.

#### Vérification Ollama (`:20-22`)

- Appelle `check_ollama()` avant de lancer l'enrichissement. Si indisponible, affiche un `st.error`.

#### Mode unitaire vs batch (`:47-71`)

- **1 produit** (`:47-59`) :
  - Appelle `pipeline.run_single(products_data[0])` (`:49`).
  - Utilise le **grand modèle** (configuré dans le pipeline comme `"large"`).
  - Persiste le résultat via `pipeline.persist.process([result])`.
  - Affiche le modèle utilisé et le début de la description enrichie (`:54-56`).
  - Stocke le dernier résultat dans `session_state["_last_enrichment"]` (`:52`).

- **Plusieurs produits** (`:61-71`) :
  - Appelle `pipeline.run(products_data, batch_size=5)` (`:63`) — traitement par lots de 5, avec **petit modèle**.
  - Affiche le résultat final : succès / échecs dans la barre de statut (`:66-69`).
  - Déclenche `st.rerun()` pour rafraîchir l'affichage (`:71`).

#### UI commune (`:24-43`)

- `st.progress` pour la barre de progression (`:24`, `:58`, `:61`, `:65`).
- `st.status` comme conteneur de statut (`:25`, `:42`, `:53`, `:57`, `:66-69`).
- Récupération des données produits via `repo.find_by_ids(list(selected_ids))` (`:28`).

---

### `export.py` — Export

**Fichier** : `src/ui/components/export.py:1-35`

#### Récupération des IDs enrichis (`:10-15`)

- `EnrichmentRepository.find_enriched_ids()` — liste des `product_id` ayant au moins un enrichissement.
- Si vide, message `"Aucun produit enrichi"` et return.

#### Filtre par catégorie (`:17-21`)

- `st.selectbox("Filtrer par catégorie")` — option `"Toutes"` + catégories distinctes.
- Option `"Toutes"` convertie en `None` pour la requête.

#### Table enrichie (`:23-28`)

- Appelle `repo.find_enriched_with_products(category=...)` pour obtenir les lignes jointes produits + enrichissements.
- Affiche le DataFrame résultant dans un `st.dataframe`.

#### Téléchargement CSV (`:29-35`)

- `st.download_button` avec `mime="text/csv"` et nom de fichier `"produits_enrichis.csv"`.

---

## `utils.py` — Utilitaires UI

**Fichier** : `src/ui/utils.py:1-16`

### `quality_label(desc: str | None) -> str` (`:1-10`)

Classifie la longueur d'une description :

| Condition | Label |
|---|---|
| `None` ou chaîne vide/nulle | `"Vide"` |
| `< 50` caractères | `"<50c"` |
| `50–199` caractères | `"50-200c"` |
| `200–499` caractères | `"200-500c"` |
| `≥ 500` caractères | `">500c"` |

Utilisé dans `product_table.py:11` pour la colonne `"Qualité"`.

### `truncate_desc(desc, max_len=80)` (`:12-16`)

Tronque une description à `max_len` caractères en ajoutant `"..."` si nécessaire. Protège contre `None` en retournant `""`.

Utilisé dans `product_table.py:12` pour l'affichage.

---

## Flux utilisateur

```
Charger CSV → Dashboard → Filtrer → Sélectionner → Enrichir → Exporter
```

1. **Charger CSV** — L'utilisateur upload le fichier via l'expander dans la sidebar (`app.py:31-47`). Les données sont persistées en DuckDB.
2. **Dashboard** — Visualisation des statistiques catalogue : métriques, bar charts qualité/catégories/marques, preview table (`dashboard.py:22-54`).
3. **Filtrer** — L'utilisateur navigue vers `✨ Enrichissement`. Dans la sidebar, il filtre par qualité, catégorie, et marque (cascade catégorie → marque) (`app.py:63`, `filters.py:6-35`).
4. **Sélectionner** — La table paginée (50 lignes/page) permet la multi-sélection via les checkboxes Streamlit (`product_table.py:25-32`, `app.py:72`).
5. **Enrichir** — Bouton dans la sidebar lance l'enrichissement : unitaire (grand modèle) si 1 produit, batch (petit modèle, lots de 5) si plusieurs (`batch_enrich.py:47-71`).
6. **Exporter** — Dans la page `📥 Export`, l'utilisateur peut filtrer par catégorie et télécharger le CSV des produits enrichis (`export.py:8-35`).

---

## Choix UX

| Choix | Emplacement | Justification |
|---|---|---|
| Sidebar pour filtres + actions | `app.py:28`, `filters.py:6-35`, `batch_enrich.py:12-18` | Garde l'espace principal dédié aux données ; actions contextuelles toujours visibles |
| Expander pour upload CSV | `app.py:31` | Évite d'encombrer la sidebar quand les données sont déjà chargées ; ouvert automatiquement quand la base est vide |
| `st.cache_data(ttl=60)` pour dashboard | `dashboard.py:7` | Évite de requêter la base à chaque interaction, TTL de 60s pour rester frais sans surcoût |
| Pagination 50 lignes | `product_table.py:6` | Équilibre entre visibilité et performance de rendu |
| Mode unitaire = grand modèle, batch = petit modèle | `batch_enrich.py:47-63` | Qualité maximale pour l'enrichissement d'un produit, vitesse pour les lots |
| Barre de progression + statut | `batch_enrich.py:24-25` | Feedback visuel pendant les opérations longues (appels LLM) |
| Sélection multi-page persistée | `product_table.py:31` (`key` par page) | Chaque page a sa propre clé de dataframe pour éviter les conflits de sélection Streamlit |
| Rafraîchissement après enrichissement | `batch_enrich.py:71` | Met à jour les données affichées (compteurs, statuts) sans rechargement manuel |
