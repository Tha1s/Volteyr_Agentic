---
objective: Les 3 fichiers de test utilisent init_schema() au lieu de DDL inline
status: implemented
---

# Plan: Remplacer le DDL inline dans les tests par init_schema()

## Overview

| Field      | Value |
| ---------- | ----- |
| **Goal**   | Supprimer la duplication du DDL dans les fixtures de test en appelant `init_schema()` |
| **Source** | Audit de code — finding 🔴 code-quality et 🟢 tests |

## Phases

| # | Phase | File |
| --- | ----- | ---- |
| 1 | Remplacer DDL inline par init_schema() dans 3 fichiers de test | [`phase-1.md`](./phase-1.md) |

## Resources

| Source | Verified |
| ------ | -------- |
| `tests/test_api.py:14-17` | Utilise déjà `init_schema()` — pattern à suivre |
| `src/db/schema.py` | `init_schema()` crée les tables `products` et `enrichissements` |

## Decisions

| Decision | Why |
| -------- | --- |
| Ne PAS modifier `test_api.py` | Il utilise déjà `init_schema()` correctement |
