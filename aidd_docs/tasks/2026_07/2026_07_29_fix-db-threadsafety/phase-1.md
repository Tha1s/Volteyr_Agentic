---
status: pending
---

# Instruction: Restructurer la connexion pour per-thread

## Architecture projection

```txt
.
✏️ src/db/connection.py
```

## Tasks to do

### `1)` Modifier `src/db/connection.py`

> Retirer `check_same_thread=False` et garantir qu'un thread n'accède jamais à une connexion créée par un autre thread

1. Supprimer `check_same_thread=False` de l'appel `sqlite3.connect()`
2. Vérifier que `_override_conn` pour TestClient est toujours fonctionnel
3. Vérifier que `threading.local()` crée bien une connexion par thread (inchangé : déjà le cas)

**Risque**: TestClient de Starlette utilise un thread anyio — `_override_conn` est déjà le mécanisme prévu, donc OK.

## Tests

### `1)` Vérifier la non-régression des tests

> `make test` doit toujours passer

1. Utiliser `_override_conn` dans les fixtures de test (déjà fait dans `test_api.py`)
2. Les autres tests utilisent `conn_mod._local.connection = conn` (déjà fait dans `test_db.py`, `test_enrichment.py`, `test_loader.py`)

## Test acceptance criteria

| Task | Acceptance criteria |
| ---- | ------------------- |
| 1 | `make test` passe |
| 1 | Le retrait de `check_same_thread=False` ne casse aucun test existant |
| 1 | La connexion par défaut (hors test) continue de fonctionner |
