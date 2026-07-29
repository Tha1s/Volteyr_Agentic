---
status: pending
---

# Instruction: Modifier le loader pour préserver les enrichissements

## Architecture projection

```txt
.
✏️ src/db/loader.py
```

## Tasks to do

### `1)` Modifier `src/db/loader.py:45-52`

> Remplacer DELETE + INSERT par INSERT OR REPLACE

1. Supprimer la ligne `conn.execute("DELETE FROM enrichissements")`
2. Supprimer la ligne `conn.execute("DELETE FROM products")`
3. Remplacer `INSERT INTO products` par `INSERT OR REPLACE INTO products`
4. Conserver `conn.commit()` à la fin
5. `load_csv_from_dictreader` reste idempotent (mêmes données = même état)

## Test acceptance criteria

| Task | Acceptance criteria |
| ---- | ------------------- |
| 1 | `make test` passe — test `test_load_idempotent` vérifie l'idempotence |
| 1 | Après reload CSV, les enrichissements existants sont toujours en base |
| 1 | Les produits sont mis à jour si leurs données changent entre deux imports |
