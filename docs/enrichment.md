# Module `enrichment` — Documentation

## 1. Vue d'ensemble

Le module `src/enrichment/` orchestre l'enrichissement des descriptions produits via un pipeline de traitement. Il prend en entrée des produits bruts issus du CSV, les fait passer par un LLM (Ollama) pour générer une description enrichie structurée (matière, entretien, style, mots-clés SEO), puis persiste le résultat en base DuckDB.

Structure :

```
src/enrichment/
├── models.py          # Dataclass Enrichment
├── factory.py         # EnrichmentFactory (pattern Factory)
├── pipeline.py        # EnrichmentPipeline (pattern Pipeline)
└── steps/
    ├── normalize.py   # NormalizeStep
    ├── generate.py    # GenerateStep
    └── persist.py     # PersistStep
```

---

## 2. Dataclass `Enrichment` — `models.py:4`

```python
@dataclass
class Enrichment:
    product_id: int
    enriched_description: str
    material: str = ""
    care_instructions: str = ""
    style: str = ""
    seo_keywords: str = ""
    model_used: str = ""
```

**Champs :**

| Champ | Type | Défaut | Rôle |
|---|---|---|---|
| `product_id` | `int` | *(obligatoire)* | Identifiant du produit enrichi |
| `enriched_description` | `str` | *(obligatoire)* | Description longue générée par le LLM |
| `material` | `str` | `""` | Matière du produit |
| `care_instructions` | `str` | `""` | Consignes d'entretien |
| `style` | `str` | `""` | Style / coupe |
| `seo_keywords` | `str` | `""` | Mots-clés SEO |
| `model_used` | `str` | `""` | Nom du modèle Ollama utilisé |

**`to_dict` property** (`models.py:14-24`) — Retourne un `dict` avec les 7 champs, utilisé pour l'affichage Streamlit et l'API REST.

---

## 3. `EnrichmentFactory` — `factory.py:4`

Pattern **Factory** : centralise la création d'instances `Enrichment` depuis différentes sources.

### `from_llm_response(product_id, llm_json, model_used)` — `factory.py:19`
Construit un `Enrichment` à partir de la réponse JSON brute du LLM.

- **Validation** (`factory.py:21`) — Si `enriched_description` n'est pas une `str` ou fait moins de 20 caractères après `strip()`, la chaîne est vidée (`""`).
- **Valeurs par défaut** (`factory.py:24-28`) — Pour `material`, `care_instructions`, `style`, `seo_keywords` : si le champ est absent, vide ou non‑`str`, la valeur devient `"Non précisé"`.
- Le `model_used` est passé explicitement (provient de `strategy.model`).

### `to_db_params(enrichment)` — `factory.py:7`
Convertit un `Enrichment` en `dict` prêt pour l'insertion DuckDB (clés = noms de colonnes).

### `from_db_row(row)` — `factory.py:41`
Reconstruit un `Enrichment` depuis une ligne DuckDB (dict), avec `""` comme défaut pour les champs absents.

---

## 4. `EnrichmentPipeline` — `pipeline.py:8`

Pattern **Pipeline** : orchestre l'exécution séquentielle des steps.

```python
@dataclass
class EnrichmentPipeline:
    generate: GenerateStep = field(default_factory=lambda: GenerateStep(use_large_model=False))
    persist: PersistStep = field(default_factory=PersistStep)
```

### `run(products, batch_size=5)` — `pipeline.py:13`
Pipeline batch pour le chargement initial / enrichissement en masse.

1. Découpe `products` en batches de `batch_size`.
2. Appelle `self.generate.process(batch)` sur chaque batch.
3. Appelle `self.persist.process(results)` sur les résultats.
4. Retourne `(total_success, total_failures)`.

Utilise le **petit modèle** (`use_large_model=False`) pour aller vite sur beaucoup de produits.

### `run_single(product)` — `pipeline.py:24`
Pipeline "single‑shot" pour l'UI Streamlit (enrichissement à la demande d'un seul produit).

- Instancie un **nouveau** `GenerateStep` avec `use_large_model=True` pour une qualité maximale.
- Retourne l'`Enrichment` ou `None` si échec.
- **Ne persiste pas** en base — c'est l'appelant (Streamlit) qui décide de sauvegarder ou non.

---

## 5. Steps

### `NormalizeStep` — `steps/normalize.py:7`

```python
@dataclass
class NormalizeStep:
    def process(self, products: list[dict]) -> list[dict]:
```

- **Utilisé au chargement CSV uniquement** (pas dans le pipeline runtime).
- Pour chaque produit dont le champ `category` est absent ou `None`, appelle `normalize_product_type(product["product_type"])` (de `src/config/categories.py`) pour mapper le `product_type` Shopify vers une catégorie normalisée.
- Log le nombre de normalisations effectuées (`normalize.py:17`).
- Passe-through : retourne la liste modifiée en place.

### `GenerateStep` — `steps/generate.py:11`

```python
@dataclass
class GenerateStep:
    max_retries: int = 1
    use_large_model: bool = False
```

**Flux** (`generate.py:15-44`) :

1. Sélectionne la stratégie LLM via `get_strategy(use_large_model)` (`generate.py:18`).
2. Pour chaque produit, construit le prompt avec `ENRICHMENT_USER.format(...)` (`generate.py:22-27`).
3. Boucle de **retry** : `range(self.max_retries + 1)` = 2 tentatives max (`generate.py:29`).
4. Appelle `strategy.generate(prompt, ENRICHMENT_SYSTEM)` (`generate.py:30`).
5. Parse la réponse en JSON via `json.loads()` (`generate.py:33`).
6. Si parsing OK et que le résultat est un `dict`, crée l'`Enrichment` via `EnrichmentFactory.from_llm_response()` et `break` (`generate.py:35-38`).
7. Si `JSONDecodeError`, log l'erreur et retente (`generate.py:39-40`).
8. Si toutes les tentatives échouent, `result` reste `None` (`generate.py:41`).

### `PersistStep` — `steps/persist.py:9`

```python
@dataclass
class PersistStep:
    repo: EnrichmentRepository = field(default_factory=EnrichmentRepository)
```

**Stratégie delete-before-insert** (`persist.py:12-24`) :

1. Pour chaque `Enrichment` non‑`None` :
   - `repo.delete_by_product_id(enrichment.product_id)` — supprime l'enrichment existant pour ce produit (`persist.py:19`).
   - `repo.save_from_dict(**params)` — insère le nouvel enrichment (`persist.py:20-21`).
2. Les `None` (échecs de génération) sont comptés comme `failures` (`persist.py:16-18`).
3. Retourne `(success, failures)`.

---

## 6. Flux complet

```
CSV (products.csv)
  │
  ▼
NormalizeStep.process()
  │  normalise product_type → category
  │  (chargement initial uniquement)
  ▼
GenerateStep.process()
  │  appel LLM (Ollama) + retry (2 tentatives)
  │  parsing JSON → Enrichment via Factory
  ▼
PersistStep.process()
  │  DELETE existing + INSERT new (atomique par produit)
  ▼
DuckDB (table enrichments)
  │
  ▼
Streamlit UI / FastAPI REST
```

---

## 7. Choix d'architecture

### Pourquoi du JSON structuré en sortie LLM ?

Le LLM reçoit un prompt système (`ENRICHMENT_SYSTEM`) qui lui demande de produire un objet JSON avec des clés fixes (`enriched_description`, `material`, `care_instructions`, `style`, `seo_keywords`). Cela permet un parsing déterministe dans `GenerateStep` (`generate.py:33`) et évite les heuristiques fragiles de découpage de texte.

### Pourquoi 2 modèles (petit / grand) ?

Le `run()` batch utilise `use_large_model=False` pour la rapidité sur ~1000 produits, tandis que `run_single()` (appelé depuis l'UI Streamlit) utilise `use_large_model=True` pour une qualité maximale sur un seul produit. La factory de stratégies (`src/llm/strategies.py`) sélectionne le bon modèle Ollama selon ce flag.

### Pourquoi delete-before-insert ?

Chaque `PersistStep.process()` fait un `DELETE` puis `INSERT` pour chaque produit (`persist.py:19-21`). Cela garantit l'**idempotence** : ré‑exécuter le pipeline sur un même produit écrase l'ancien enrichment sans créer de doublon. C'est atomique au niveau du produit (pas de transaction globale), ce qui est acceptable car DuckDB est mono‑écrivain.
