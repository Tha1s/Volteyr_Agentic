# Volteyr Agentic

Système d'enrichissement de descriptions produits par IA locale.
Pré-exercice technique.

Le catalogue e-commerce contient des milliers de produits de marques
(Sandro, Maje, AMI Paris…) avec des descriptions parfois vides ou trop
basiques. Ce système génère via IA des descriptions enrichies (matière,
entretien, style, mots-clés SEO) et les rend recherchables via API REST.

**Stack :** Python 3.12 — Streamlit — FastAPI — DuckDB — Ollama + Qwen2.5
**Tests :** pytest — 115 tests — base en mémoire — isolation totale

---

## Contraintes

- **LLM local uniquement** — pas d'API cloud (OpenAI, Anthropic). Ollama doit tourner sur `localhost:11434`
- **RAM limitée à ~7.6 Go** — modèle Qwen2.5:7b pour la qualité, fallback Qwen2.5:1.5b pour les lots
- **Dataset de 1000 produits** au format Shopify CSV : descriptions brutes avec des sauts de ligne dans les textes
- **Aucune clé API** — tout est gratuit et local

---

## Installation

### Prérequis système

Ollama est un service externe (binaire Go), à installer une fois **en dehors du venv** :

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b
ollama serve      # Laisse tourner en arrière-plan
```

Vérifier qu'Ollama répond :

```bash
curl http://localhost:11434/api/tags
```

### Setup Python

Le venv et les dépendances Python sont gérés par le Makefile :

```bash
make all          # Crée .venv + pip install -r requirements.txt
```

### Lancer

```bash
make api          # FastAPI sur http://localhost:8000
make streamlit    # Streamlit sur http://localhost:8501
make dev          # Les deux simultanément (API en arrière-plan)
make test         # 115 tests
make fclean       # Supprime .venv + caches
```

Premier lancement : ouvrir Streamlit, charger `data/products.csv` via le sidebar,
puis naviguer vers l'onglet Enrichissement pour générer des descriptions enrichies.

---

## Architecture

### Vue d'ensemble

```
┌──────────────┐    ┌──────────────┐
│   Streamlit   │    │   FastAPI    │
│  (port 8501)  │    │ (port 8000)  │
└──────┬───────┘    └──────┬───────┘
       │                   │
       ▼                   ▼
┌──────────────────────────────────────┐
│         DuckDB  (volteyr.db)         │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ products │  │ enrichissements  │  │
│  │1000 rows │  │    ~10 rows      │  │
│  └──────────┘  └──────────────────┘  │
└──────────────────────────────────────┘
       ▲
┌──────┴───────┐
│   Ollama     │
│ Qwen2.5:7b  │
└──────────────┘
```

### Design Patterns

**Repository.** `ProductRepository` et `EnrichmentRepository` encapsulent toutes les
requêtes SQL. Chaque accès DB appelle `get_connection()` via une `@property`,
garantissant qu'un repository utilise toujours la connexion courante, même après
un `close()` + `reconnect()`.

```python
class ProductRepository:
    @property
    def conn(self):
        return get_connection()  # frais à chaque accès, jamais de connexion périmée
```

**Strategy.** Le client LLM expose deux stratégies interchangeables :

| Stratégie | Modèle | Timeout | Usage |
|---|---|---|---|
| `SmallModelStrategy` | Qwen2.5:1.5b | 30s | Enrichissement par lots (Streamlit) |
| `LargeModelStrategy` | Qwen2.5:7b | 120s | Produit unique (API) |

**Factory.** `EnrichmentFactory.from_llm_response()` transforme le JSON brut du LLM
en objet `Enrichment` typé avec validation : si la description générée fait moins
de 20 caractères, elle est rejetée.

**Pipeline.** `EnrichmentPipeline` orchestre le flux :

```
GenerateStep (ThreadPoolExecutor, max 4 workers)
    → Appel Ollama avec retry (1 tentative supplémentaire)
    → Parse JSON / valide isinstance dict / break si non-dict
PersistStep (BEGIN TRANSACTION)
    → DELETE ancien enrichissement
    → INSERT nouveau
    → COMMIT ou ROLLBACK
```

**Override Pattern.** Pour les tests, `set_connection(conn)` remplace globalement
la connexion DuckDB via une variable `_override_conn`. Contrairement à
`threading.local()`, cela traverse les threads — nécessaire car le TestClient de
Starlette exécute les requêtes dans un thread `anyio` séparé.

```
Production : _override_conn = None → get_connection() → thread-local → fichier
Tests :      _override_conn = conn → get_connection() → mémoire
```

### Structure du projet

```
├── Makefile              → Commandes (all, venv, setup, api, streamlit, dev, test, fclean)
├── requirements.txt      → Dépendances Python (versions pinées avec ~=)
├── .gitignore            → .venv, __pycache__, data/volteyr.db, config/categories.yaml
├── data/
│   └── products.csv      → 1000 produits Shopify
├── src/
│   ├── api/              → Couche REST (FastAPI + Pydantic)
│   │   ├── main.py       → App FastAPI, CORS, lifespan
│   │   ├── routes.py     → Search + detail produits
│   │   ├── routes_meta.py→ Stats + catégories + health
│   │   └── models.py     → Contrats : ProductResponse, SearchResponse, StatsResponse
│   ├── config/
│   │   └── categories.py → Normalisation 402 types → 14 catégories
│   ├── db/               → Persistance DuckDB
│   │   ├── connection.py            → Thread-local + override pour tests
│   │   ├── schema.py                → CREATE TABLE IF NOT EXISTS
│   │   ├── loader.py                → Import CSV avec normalisation
│   │   ├── product_repository.py    → CRUD + stats produits
│   │   └── enrichment_repository.py → CRUD + recherche enrichissements
│   ├── enrichment/       → Pipeline IA
│   │   ├── pipeline.py              → Orchestrateur GenerateStep → PersistStep
│   │   ├── factory.py               → Construction Enrichment depuis JSON LLM
│   │   ├── models.py                → Dataclass Enrichment
│   │   └── steps/
│   │       ├── generate.py          → Appel parallélisé à Ollama
│   │       └── persist.py           → Sauvegarde transactionnelle
│   ├── llm/              → Interface Ollama
│   │   ├── client.py     → HTTP client avec timeout paramétrable
│   │   ├── prompts.py    → Template de prompt (français, anti-hallucination)
│   │   └── strategies.py → SmallModel / LargeModel avec leur timeout
│   └── ui/               → Interface Streamlit
│       ├── app.py        → Navigation, sidebar, cache
│       └── components/   → dashboard, filters, product_table, batch_enrich, export
└── tests/                → 115 tests (7 fichiers)
```

---

## API REST

L'API est documentée automatiquement sur `/docs` (Swagger UI) au lancement.

### `GET /api/health`

État de la base et d'Ollama.

```bash
curl http://localhost:8000/api/health
```

```json
{"status": "ok", "db": true, "ollama": true}
```

---

### `GET /api/stats`

Statistiques du catalogue : total produits, descriptions vides et courtes,
répartition par catégorie.

```bash
curl http://localhost:8000/api/stats
```

```json
{
  "total_products": 1000,
  "empty_descriptions": 133,
  "short_descriptions": 367,
  "categories": {
    "Autres": 218, "Hauts": 181, "Chaussures": 133,
    "Vestes & Manteaux": 79, "Pantalons & Shorts": 74,
    "Sacs & Maroquinerie": 57, "Robes & Jupes": 53,
    "Bijoux": 52, "Accessoires": 44, "Maillots De Bain": 21,
    "Lingerie": 17, "Bébé & Enfant": 10, "Pyjamas": 4
  }
}
```

---

### `GET /api/categories`

Liste des catégories avec comptage.

```bash
curl http://localhost:8000/api/categories
```

---

### `GET /api/products/search?q=&category=&vendor=&limit=&offset=`

Recherche plein texte dans les descriptions enrichies.
Ne retourne que les produits qui ont été enrichis (INNER JOIN).

```bash
curl "http://localhost:8000/api/products/search?q=soie&limit=2"
curl "http://localhost:8000/api/products/search?category=Chaussures"
curl "http://localhost:8000/api/products/search?vendor=SANDRO&limit=5"
```

| Paramètre | Type | Défaut | Description |
|---|---|---|---|
| `q` | string | - | Recherche insensible à la casse (ILIKE). `%` et `_` sont échappés |
| `category` | string | - | Filtre exact par catégorie |
| `vendor` | string | - | Filtre exact par marque |
| `limit` | int | 20 | Maximum de résultats (max 100) |
| `offset` | int | 0 | Pagination |

Réponse :

```json
{
  "results": [{
    "product_id": 6603864703072,
    "product_type": "Robe",
    "category": "Robes & Jupes",
    "vendor": "PAUL KA",
    "description": "",
    "enriched_description": "Cette robe Paul Ka est élégante et moderne…",
    "material": "Matière non précisée",
    "care_instructions": "Machine à 30°…",
    "style": "Élégant et moderne",
    "seo_keywords": "robe, Paul Ka, élégant"
  }],
  "total": 1,
  "limit": 2,
  "offset": 0
}
```

---

### `GET /api/products/{id}`

Détail d'un produit avec son enrichissement. `id` doit être un entier > 0.

```bash
curl http://localhost:8000/api/products/4640779042912
```

```json
{
  "product_id": 4640779042912,
  "product_type": "Pulls & Gilets",
  "category": "Vestes & Manteaux",
  "vendor": "DES PETITS HAUTS",
  "description": "",
  "enriched_description": "Pull en tricot fin…",
  "material": "Tricot fin",
  "care_instructions": "Machine à laver douce…",
  "style": "Chic et confortable",
  "seo_keywords": "pull DES PETITS HAUTS, tricot fin"
}
```

Retourne **404** si le produit n'existe pas, **422** si l'id est invalide (≤ 0).

---

## Normalisation des catégories

Le dataset brut contient **402 valeurs différentes** pour le champ `product_type` :
vides, en anglais, en français, singulier, pluriel, variantes (`Robe`, `Robes`,
`Robe midi`, `Robe De Soirée`…).

Pour naviguer et filtrer efficacement, tout est normalisé en **14 catégories** :

```
Autres           Hauts              Chaussures        Pulls & Maille
Pantalons & Shorts                  Robes & Jupes     Vestes & Manteaux
Sacs & Maroquinerie                 Bijoux            Accessoires
Maillots De Bain                    Lingerie          Bébé & Enfant
Pyjamas
```

**Algorithme à deux niveaux :**

1. **Exact match** — si le type brut correspond à un nom de catégorie (insensible à la casse/accents), il est mappé directement. Exemple : `"Accessoires"` → `Accessoires`
2. **Keyword matching** — chaque catégorie a une liste de mots-clés. Premier match gagne. L'ordre des catégories est important pour éviter les faux positifs (ex : `"Bijoux"` vérifié avant `"Sacs & Maroquinerie"` pour éviter que `"bag" ⊆ "bague"` mappe une bague vers les sacs)
3. **Fallback** — si aucun mot-clé ne correspond → `"Autres"`

Les correspondances sont persistées dans `config/categories.yaml` (généré automatiquement au premier chargement CSV) via pyyaml.

---

## Pipeline d'enrichissement

```
1. Sélection utilisateur (Streamlit) → filtres + sélection produits
2. Thread dédié → récupération des produits via ProductRepository
3. GenerateStep → appel parallélisé à Ollama
   ├── ThreadPoolExecutor (max 4 workers)
   ├── Prompt en français structuré
   └── Retry : 1 tentative supplémentaire en cas d'échec du parsing JSON
4. PersistStep → sauvegarde transactionnelle
   ├── BEGIN TRANSACTION
   ├── DELETE ancien enrichissement
   ├── INSERT nouveau
   └── COMMIT ou ROLLBACK si échec
5. Callback on_progress → mise à jour de l'interface en temps réel
```

Le prompt LLM (français) demande les champs suivants :

```text
{
  "enriched_description": "...",
  "material": "...",
  "care_instructions": "...",
  "style": "...",
  "seo_keywords": "..."
}
```

Règles appliquées : ne jamais inventer d'information (utiliser "Non précisé" si
inconnu), mentionner le type de produit dans la première phrase, ton chic et
accessible.

---

## Tests

```bash
make test
```

**115 tests** dans 7 fichiers, tous avec DuckDB en mémoire :

| Fichier | Tests | Couverture |
|---|---|---|
| `test_api.py` | 13 | Tous les endpoints : health, stats, search, detail, 404 |
| `test_db.py` | ~30 | Repositories : CRUD, filtres, pagination, recherche ILIKE |
| `test_enrichment.py` | ~20 | Factory, generate step, persist step, pipeline |
| `test_categories.py` | ~15 | Normalisation 14 catégories, edge cases (accents, child suffixes) |
| `test_connection.py` | 4 | Singleton par thread, close/reconnect, création fichier |
| `test_loader.py` | 8 | Import CSV, validation, idempotence |
| `test_models.py` | 12 | Pydantic : ProductResponse, SearchResponse, StatsResponse |
| `test_ui_utils.py` | 8 | Utilitaires UI |

**Principe d'isolation :** chaque test crée sa base en mémoire via `set_connection()`.
Cette variable globale (`_override_conn`) garantit que toutes les requêtes —
y compris celles du TestClient FastAPI (qui s'exécutent dans un thread `anyio`) —
utilisent la même connexion mémoire.
