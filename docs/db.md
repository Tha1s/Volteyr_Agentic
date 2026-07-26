# Module `db/` — Base de données

## 1. Vue d'ensemble

Le module `db/` gère toute la couche de persistance de l'application Volteyr Agentic via **DuckDB** (base embarquée, fichier unique `data/volteyr.db`). Il expose :

- Une connexion unique (singleton).
- La création du schéma.
- Le chargement des données CSV.
- Deux repositories pour l'accès aux tables `products` et `enrichissements`.

Il est consommé par la couche `enrichment/` (écriture) et par les interfaces Streamlit/FastAPI (lecture/recherche).

---

## 2. Fichiers

### 2.1 `connection.py` — Connexion singleton

| Fonction | Ligne | Rôle |
|---|---|---|
| `get_connection()` | `:7` | Retourne une connexion unique (`duckdb.connect("data/volteyr.db")`). Crée la connexion au premier appel. Lève `RuntimeError` en cas d'échec. |
| `close()` | `:17` | Ferme la connexion et remet le singleton à `None`. |

La connexion est stockée dans une variable module-level `_connection` (`:4`). Tous les autres fichiers passent par `get_connection()` — aucun ne crée sa propre connexion.

### 2.2 `schema.py` — Création des tables

| Fonction | Ligne | Rôle |
|---|---|---|
| `init_schema()` | `:4` | Crée les tables `products` et `enrichissements` (avec `CREATE TABLE IF NOT EXISTS`) ainsi que la séquence `enrichissements_seq`. Appelée au démarrage de l'application. |

Les DDL sont exécutées directement via `conn.execute(...)` avec un `conn.commit()` final (`:36`).

### 2.3 `product_repository.py` — Accès aux produits

| Classe | Ligne | Rôle |
|---|---|---|
| `ProductRepository` | `:4` | Repository pour la table `products`. Prend la connexion via `get_connection()` dans `__init__` (`:6`). |

| Méthode | Ligne | Retour | Description |
|---|---|---|---|
| `count_all()` | `:8` | `int` | Nombre total de produits. |
| `count_empty()` | `:11` | `int` | Produits sans description. |
| `count_short(threshold=50)` | `:16` | `int` | Produits avec description < `threshold` caractères. |
| `count_medium()` | `:22` | `int` | Description entre 50 et 199 caractères. |
| `count_long()` | `:27` | `int` | Description entre 200 et 499 caractères. |
| `count_very_long()` | `:32` | `int` | Description >= 500 caractères. |
| `count_by_category()` | `:37` | `list[tuple[str, int]]` | Décompte par catégorie. |
| `count_by_vendor()` | `:42` | `list[tuple[str, int]]` | Décompte par vendeur. |
| `find_all(limit, offset)` | `:47` | `list[dict]` | Produits paginés. |
| `find_by_id(product_id)` | `:52` | `dict \| None` | Un produit par clé primaire. |
| `find_by_ids(ids)` | `:60` | `list[dict]` | Plusieurs produits par leurs IDs. Protégé contre liste vide (`:61-62`). |
| `find_filtered(quality, categories, vendors)` | `:69` | `list[dict]` | Filtre combiné qualité/catégories/vendeurs. Construit dynamiquement la clause `WHERE` (`:100`). |
| `get_distinct_categories()` | `:105` | `list[str]` | Catégories distinctes (exclut `None`). |
| `get_distinct_vendors()` | `:114` | `list[str]` | Vendeurs distincts (exclut `None`). |

Le filtre `quality` accepte : `"Vide"`, `"<50c"`, `"50-200c"`, `"200-500c"`, `">500c"` (`:78-88`).

### 2.4 `enrichment_repository.py` — Accès aux enrichissements

| Classe | Ligne | Rôle |
|---|---|---|
| `EnrichmentRepository` | `:11` | Repository pour la table `enrichissements`. Connexion stockée dans `self._conn` (`:13`). |

| Méthode | Ligne | Retour | Description |
|---|---|---|---|
| `save(enrichment)` | `:15` | `int` | Persiste un objet `Enrichment` via `EnrichmentFactory.to_db_params()` (`:18`). Retourne l'`id` généré. |
| `save_from_dict(**params)` | `:21` | `int` | Insertion directe par paramètres nommés. Utilise `RETURNING id` (`:36`). |
| `find_by_product_id(product_id)` | `:50` | `dict \| None` | Dernier enrichissement pour un produit (trié par `created_at DESC LIMIT 1`). Retourne un dict avec les colonnes mappées manuellement (`:64-74`). |
| `find_enriched_ids()` | `:76` | `set[int]` | Ensemble des `product_id` ayant au moins un enrichissement. |
| `delete_by_product_id(product_id)` | `:82` | `None` | Supprime tous les enrichissements d'un produit. |
| `find_enriched_with_products(category)` | `:87` | `list[dict]` | Jointure `products` ↔ `enrichissements`, filtrée optionnellement par catégorie. |
| `search(q, category, vendor, limit, offset)` | `:118` | `tuple[list[dict], int]` | Recherche full-text (`ILIKE` sur `enriched_description`, `:130`) avec filtres optionnels catégorie/vendeur. Pagination via `LIMIT/OFFSET`. Retourne `(results, total)`. |

L'`import` de `Enrichment` et `EnrichmentFactory` est différé (`TYPE_CHECKING` au `:8`, import runtime au `:16`) pour éviter les imports circulaires.

### 2.5 `loader.py` — Chargement CSV

| Fonction | Ligne | Rôle |
|---|---|---|
| `load_csv_from_dictreader(reader)` | `:7` | Charge un `csv.DictReader` dans la table `products`. |

**Flux détaillé :**

1. Convertit le reader en liste (`:8`).
2. Vérifie les colonnes obligatoires (`:10-16`).
3. Collecte les `product_type` distincts pour auto-remplir le mapping de catégories (`:18-19`).
4. Charge le mapping (`categories.json`) via `load_category_map()` (`:21`).
5. Pour chaque ligne : normalise `product_type` → `category` (`:25`), caste les champs numériques (`:27-29`), ignore les lignes invalides (`:30-32`).
6. Vide les deux tables (`DELETE FROM`, `:46-47`) pour un rechargement complet.
7. Insère toutes les lignes en une transaction avec `executemany` (`:48-52`).
8. `commit()` et retourne le nombre de lignes insérées (`:53-54`).

---

## 3. Design pattern — Repository

Le **Repository Pattern** est utilisé pour isoler la logique d'accès aux données du reste de l'application.

**Pourquoi :**

- Les interfaces Streamlit et FastAPI ne manipulent jamais de SQL directement.
- Les requêtes sont centralisées, testables et réutilisables.
- Changement de base de données (ex. passer à PostgreSQL) = modifier uniquement les repositories.

**Comment :**

- Chaque table a sa classe repository (`ProductRepository`, `EnrichmentRepository`).
- Chaque repository obtient la connexion via `get_connection()` dans son `__init__`.
- Les méthodes exposent des noms métier (`find_by_id`, `count_short`, `search`) et retournent des types Python simples (`dict`, `list[dict]`, `int`).
- Aucun ORM : les lignes sont mappées manuellement ou via `.fetchdf().to_dict("records")`.

---

## 4. Schéma

### Table `products`

| Colonne | Type | Contrainte |
|---|---|---|
| `product_id` | `BIGINT` | `PRIMARY KEY` |
| `product_type` | `VARCHAR` | |
| `category` | `VARCHAR` | Remplie par `loader.py` à partir du mapping |
| `product_tags` | `VARCHAR` | |
| `images_array` | `VARCHAR` | |
| `vendor` | `VARCHAR` | |
| `inventory_quantity` | `BIGINT` | |
| `gross_amount_exc_tax_product` | `DOUBLE` | |
| `description` | `VARCHAR` | Description originale (peut être vide) |

Définition : `schema.py:7-17`

### Table `enrichissements`

| Colonne | Type | Contrainte |
|---|---|---|
| `id` | `BIGINT` | `PRIMARY KEY`, auto-incrémenté via séquence |
| `product_id` | `BIGINT` | `FOREIGN KEY → products(product_id)` |
| `enriched_description` | `VARCHAR` | |
| `material` | `VARCHAR` | |
| `care_instructions` | `VARCHAR` | |
| `style` | `VARCHAR` | |
| `seo_keywords` | `VARCHAR` | |
| `model_used` | `VARCHAR` | Nom du modèle Ollama utilisé |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` |

Définition : `schema.py:23-34`  
Séquence : `schema.py:20-21`

---

## 5. Flux des données

```
products.csv
    │
    ▼
csv.DictReader
    │
    ▼
loader.load_csv_from_dictreader()
    │
    ├─► Vérification des colonnes
    ├─► auto_fill_categories(types) → écrit dans categories.json si nouveaux types
    ├─► load_category_map() → lit categories.json
    ├─► normalize_product_type() → mappe product_type → category
    ├─► Cast numérique (int/float) + skip des lignes invalides
    ├─► DELETE FROM enrichissements + DELETE FROM products (vider)
    ├─► executemany INSERT → products
    └─► commit()
            │
            ▼
       products (table DuckDB)
            │
            ▼
     Ollama enrichment (EnrichmentService)
            │
            ▼
    EnrichmentRepository.save()
            │
            ▼
    enrichissements (table DuckDB)
```

Le loader vide toujours les deux tables avant insertion (`:46-47`) — il s'agit d'un rechargement complet, pas d'un upsert incrémental.

---

## 6. Conventions

- **Connexion singleton** — Une seule instance `DuckDB` partagée via `get_connection()` (`connection.py:7`). Pas de pool, pas de multi-connexions.
- **Pas d'ORM** — SQL brut via `conn.execute()`. Les résultats `fetchdf().to_dict("records")` pour `products`, mapping manuel pour `enrichissements`.
- **Noms snake_case** — Fonctions (`get_connection`, `init_schema`), méthodes (`find_by_id`, `count_all`), variables (`product_id`, `enriched_description`).
- **Colonnes en français** — Les tables reflètent le domaine métier : `enrichissements`, `produit` (implicite dans `product_id`), etc.
- **Chargement idempotent** — `CREATE TABLE IF NOT EXISTS`, `DELETE` avant `INSERT`.
- **Transactions explicites** — `conn.commit()` après chaque écriture (`schema.py:36`, `loader.py:53`). Les lectures ne commitent pas.
- **Typage** — Annotations de type sur toutes les signatures publiques (`: int`, `: dict | None`, `: list[dict]`).
