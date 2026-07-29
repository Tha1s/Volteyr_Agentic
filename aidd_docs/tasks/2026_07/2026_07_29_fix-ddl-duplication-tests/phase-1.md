---
status: in-progress
---

# Instruction: Remplacer le DDL inline dans les fixtures de test

## Architecture projection

> Tree of the final files. ✅ create · ✏️ modify · ❌ delete

```txt
.
✏️ tests/test_db.py
✏️ tests/test_enrichment.py
✏️ tests/test_loader.py
```

## User Journey

```mermaid
flowchart TD
  A[Fixture existante: DDL inline] --> B[Remplacer par init_schema()]
  B --> C[Tests passent toujours]
```

## Tasks to do

### `1)` Remplacer la fixture `db_conn` dans `tests/test_db.py`

> Supprimer les 2 appels `conn.execute("CREATE TABLE...")` et utiliser `init_schema()`

1. Ajouter `from src.db.schema import init_schema` en haut du fichier
2. Remplacer les lignes 15-40 par `init_schema()`
3. Garder le reste de la fixture inchangé

### `2)` Remplacer la fixture `db_conn` dans `tests/test_enrichment.py`

> Supprimer les 2 appels `conn.execute("CREATE TABLE...")` et utiliser `init_schema()`

1. Ajouter `from src.db.schema import init_schema` en haut du fichier
2. Remplacer les lignes 30-55 par `init_schema()`
3. Garder le reste de la fixture inchangé

### `3)` Remplacer la fixture `db_conn` dans `tests/test_loader.py`

> Supprimer les 2 appels `conn.execute("CREATE TABLE...")` et utiliser `init_schema()`

1. Ajouter `from src.db.schema import init_schema` en haut du fichier
2. Remplacer les lignes 17-42 par `init_schema()`
3. Garder le reste de la fixture inchangé

## Test acceptance criteria

| Task | Acceptance criteria |
| ---- | ------------------- |
| 1-3 | `make test` passe — tous les tests existants continuent de fonctionner |
| 1-3 | Aucune ligne `CREATE TABLE` dans les 3 fixtures |
| 1-3 | Chaque fixture appelle `init_schema()` après avoir créé la connexion mémoire |
