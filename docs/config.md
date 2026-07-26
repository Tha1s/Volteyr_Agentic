# Documentation des modules config, cli, et api

---

## `src/config/` — Normalisation des catégories

### 1. `categories.yaml` — format, génération automatique

Fichier de mapping clé/valeur au format YAML (`config/categories.yaml:1-404`). Structure :

```yaml
mappings:
  "Pantalon": "Pantalons"
  "Jeans": "Pantalons"
  ...
default: "Autres"
```

Généré automatiquement par `_save_category_map()` (`src/config/categories.py:40-50`) : les clés sont triées alphabétiquement, les entrées système (`default`) sont préservées, et toutes les `DEFAULT_CATEGORIES` sont forcées en auto-référence.

### 2. `load_category_map()` — parsing YAML, lru_cache, terminal entries

`src/config/categories.py:16-37`

- Décorée `@functools.lru_cache(maxsize=1)` — parse une seule fois, résultat mis en cache.
- Fichier lu ligne à ligne (pas de dépendance PyYAML) : les lignes commençant par `default:` définissent la catégorie par défaut ; toutes les lignes `"key": "value"` (hors `mappings:` et `default:`) sont parsées dans un `dict`.
- Si le fichier n'existe pas, retourne `{"default": "Autres"}`.
- Après parsing, chaque catégorie de `DEFAULT_CATEGORIES` (ligne 8-13) est forcée comme identité (`cat -> cat`) via `mapping.setdefault()` (ligne 36), garantissant la présence de toutes les catégories canoniques.
- Le mapping inclut toujours la clé spéciale `"default"` pointant vers la catégorie de repli.

### 3. `_simple_match()` — matching par mots-clés, dictionnaire `_CAT_KEYWORDS`, 12 catégories

`src/config/categories.py:87-94`

- Si `product_type` est vide/None → `"Autres"`.
- Supprime les accents via `_strip_accents()` (ligne 90, implémentée lignes 83-84 avec `unicodedata.normalize("NFKD")`).
- Itère les entrées de `_CAT_KEYWORDS` (lignes 67-80) : 12 catégories :

| Catégorie | Mots-clés |
|---|---|
| `Pantalons` | pantalon, pants, trouser, jeans, denim, jogging, legging, short, bermuda, cycliste |
| `Hauts` | t-shirt, tshirt, tee, tees, top, haut, chemise, shirt, blouse, tunique, polo, body, blazer, kimono |
| `Vestes & Manteaux` | veste, manteau, jacket, coat, doudoune, parka, gilet, cardigan, softshell, blazer |
| `Pulls & Maille` | pull, sweat, sweater, jumper, knit, maille, teddy, hoodie |
| `Robes & Jupes` | robe, dress, gown, jupe, skirt |
| `Chaussures` | chaussure, shoe, basket, sneaker, derbie, derby, sandale, sandal, botte, boot, mule, mocassin, espadrille, espadrilla, tong, slide, ballerine, escarpin, pump, sabot, running, chausson, bateau, talon |
| `Sacs & Maroquinerie` | sac, bag, tote, maroquinerie, portefeuille, pochette, trousse, wallet, valise, anse |
| `Bijoux` | bijou, bague, bracelet, collier, boucle, creole, pendentif, broche, manchette |
| `Accessoires` | ceinture, belt, chapeau, bonnet, casquette, foulard, echarpe, lunette, parapluie, gant, mitaine, cravate, epingle, casque, masque |
| `Lingerie` | lingerie, soutien, brassiere, culotte, string, tanga, boxer, calecon, body, peignoir, pyjama, nuit, nightwear |
| `Maillots De Bain` | maillot, bain, swim, bikini, beach |
| `Bébé & Enfant` | bebe, nouveau ne, enfant, fille, garcon, boutchou |

- Chaque mot-clé est cherché par sous-chaîne (`w in t`, ligne 92), premier match gagnant.
- Aucun match → `"Autres"`.

### 4. `normalize_product_type()` — résolution de chaîne, strip des suffixes enfant, garde terminale

`src/config/categories.py:102-130`

1. **Garde initiale** : si `product_type` est vide → `"Autres"` (ligne 105-106).
2. **Strip du suffixe enfant/parent** : la regex `_CHILD_SUFFIX` (ligne 97-99) supprime tout suffixe de type `-Bébé`, `-Enfant`, `-Fille`, `-Garçon`, `-Mixte`, `-Homme`, `-Femme` (insensible à la casse). Exemple : `"Accessoires - Enfant - Mixte"` → `"Accessoires"`.
3. **Résolution en chaîne** : boucle `for _ in range(10)` (ligne 114) avec garde terminale anti-boucle infinie. Si le nom résolu pointe vers lui-même dans le mapping (`mapping[name] == name`), la résolution s'arrête.
4. **Fallback insensible à la casse** (lignes 122-127) : si le nom normalisé n'est pas dans le mapping, cherche une clé insensible à la casse.
5. **Retour par défaut** : si la boucle de 10 itérations est épuisée sans résolution, retourne le `default` du mapping (ligne 130).

### 5. `auto_fill_categories()` — flux automatique au chargement CSV

`src/config/categories.py:53-63`

- Prend un `set[str]` de tous les `product_type` uniques.
- Charge le mapping existant via `load_category_map()`.
- Calcule `unknown` — les types absents du mapping.
- Pour chaque inconnu, appelle `_simple_match()` pour deviner la catégorie, l'ajoute au mapping.
- Persiste via `_save_category_map()`.

### 6. `DEFAULT_CATEGORIES` — les 14 catégories canoniques

`src/config/categories.py:8-13`

```python
DEFAULT_CATEGORIES = [
    "Pantalons", "Hauts", "Vestes & Manteaux", "Pulls & Maille",
    "Robes & Jupes", "Chemises", "Chaussures", "Sacs & Maroquinerie",
    "Bijoux", "Accessoires", "Lingerie", "Maillots De Bain",
    "Bébé & Enfant", "Autres",
]
```

Utilisées pour garantir la présence de toutes les catégories dans le mapping (`load_category_map`, ligne 35-36) et pour réinjecter l'auto-référence après sauvegarde (`_save_category_map`, ligne 49-50). Note : `_CAT_KEYWORDS` contient **12** catégories (pas de `Autres` ni `Chemises` dédié — `Chemises` est absorbé dans `Hauts`), mais `DEFAULT_CATEGORIES` en liste **14**.

---

## `src/cli/` — Scripts en ligne de commande

### 1. `load_data.py` — `parse_and_load(csv_path)`, parsing CSV Shopify

`src/cli/load_data.py:1-21`

```python
def parse_and_load(csv_path: str = "data/products.csv"):
    init_schema()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = load_csv_from_dictreader(reader)
    print(f"✅ {count} products loaded")
```

- Point d'entrée CLI (`if __name__ == "__main__"`, ligne 20-21) : appelle `parse_and_load()` avec le chemin par défaut `data/products.csv`.
- Initialise le schéma DuckDB via `init_schema()` (`src.db.schema:20`).
- Ouvre le CSV Shopify avec `csv.DictReader` (gère les retours à la ligne dans les champs texte).
- Délègue le chargement à `load_csv_from_dictreader()` (`src.db.loader:1`), qui gère la normalisation des catégories, l'enrichissement Ollama, et l'insertion en base.
- Testable directement : `python -m src.cli.load_data`.

---

## `src/api/` — Modèles Pydantic (API REST future)

### 1. `models.py` — Modèles de données

`src/api/models.py:1-38` — 4 modèles Pydantic v2 :

#### `ProductResponse` (lignes 4-16)

```python
class ProductResponse(BaseModel):
    product_id: int
    product_type: str
    category: str
    vendor: str
    description: str | None = None
    enriched_description: str | None = None
    material: str | None = None
    care_instructions: str | None = None
    style: str | None = None
    seo_keywords: str | None = None
    model_config = {"from_attributes": True}
```

Modèle de réponse pour les endpoints de recherche. `from_attributes=True` permet la conversion directe depuis les tuples/lignes DuckDB (ou ORM). Les champs d'enrichissement (`enriched_description`, `material`, `care_instructions`, `style`, `seo_keywords`) sont optionnels.

#### `SearchParams` (lignes 19-24)

```python
class SearchParams(BaseModel):
    q: str | None = None
    category: str | None = None
    vendor: str | None = None
    limit: int = 20
    offset: int = 0
```

Paramètres de requête pour la recherche full-text. `limit` par défaut à 20, `offset` à 0.

#### `SearchResponse` (lignes 27-31)

```python
class SearchResponse(BaseModel):
    results: list[ProductResponse]
    total: int
    limit: int
    offset: int
```

Réponse paginée d'une recherche. `total` = nombre total de résultats (pour la pagination client).

#### `StatsResponse` (lignes 34-38)

```python
class StatsResponse(BaseModel):
    total_products: int
    empty_descriptions: int
    short_descriptions: int
    categories: dict[str, int] | None = None
```

Statistiques globales sur le catalogue : nombre total de produits, descriptions vides, descriptions courtes, et distribution par catégorie (optionnelle).

### 2. Point d'entrée FastAPI prévu

`src/api/main.py` est à créer. Le point d'entrée FastAPI exposera les endpoints de recherche (`GET /search`) et de statistiques (`GET /stats`) utilisant ces modèles Pydantic.
