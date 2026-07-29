---
status: pending
---

# Instruction: Créer le module partagé et mettre à jour les routers

## Architecture projection

> Tree of the final files. ✅ create · ✏️ modify · ❌ delete

```txt
.
✅ src/api/dependencies.py
✏️ src/api/routes.py
✏️ src/api/routes_meta.py
```

## Tasks to do

### `1)` Créer `src/api/dependencies.py`

> Module partagé contenant les deux factories

1. Créer le fichier avec les imports nécessaires
2. Déplacer `get_product_repo()` et `get_enrichment_repo()` depuis `routes.py`

### `2)` Modifier `src/api/routes.py`

> Importer depuis dependencies.py au lieu de définir les fonctions

1. Ajouter `from src.api.dependencies import get_product_repo, get_enrichment_repo`
2. Supprimer les lignes 10-15 (les deux fonctions factory)

### `3)` Modifier `src/api/routes_meta.py`

> Importer depuis dependencies.py au lieu de définir la fonction

1. Ajouter `from src.api.dependencies import get_product_repo`
2. Supprimer les lignes 10-12 (la fonction factory)

## Test acceptance criteria

| Task | Acceptance criteria |
| ---- | ------------------- |
| 1-3 | `make test` passe |
| 1-3 | `make api` démarre sans erreur |
| 1-3 | Les endpoints `/api/stats`, `/api/health`, `/api/products/search`, `/api/products/{id}` répondent 200 |
