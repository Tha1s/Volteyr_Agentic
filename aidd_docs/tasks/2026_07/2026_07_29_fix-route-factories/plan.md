---
objective: Les factories Depends() sont définies dans un fichier partagé et importées par les deux routers
status: pending
---

# Plan: Extraire les factories dupliquées dans src/api/dependencies.py

## Overview

| Field      | Value |
| ---------- | ----- |
| **Goal**   | Créer `src/api/dependencies.py` avec `get_product_repo()` et `get_enrichment_repo()`, importer dans les deux routers |
| **Source** | Audit code-quality 🔴 #4 et architecture 🔴 #5 |

## Phases

| # | Phase | File |
| --- | ----- | ---- |
| 1 | Créer le module partagé et mettre à jour les routers | [`phase-1.md`](./phase-1.md) |

## Decisions

| Decision | Why |
| -------- | --- |
| ✅ Créer `src/api/dependencies.py` | Point unique pour les factories DI — pattern standard FastAPI |
| ❌ Supprimer les fonctions des routers | Évite la duplication et les dérives futures |
