---
objective: Le rechargement CSV ne détruit pas les enrichissements existants
status: pending
---

# Plan: Protéger les enrichissements lors du rechargement CSV

## Overview

| Field      | Value |
| ---------- | ----- |
| **Goal**   | Remplacer `DELETE + INSERT` par `INSERT OR REPLACE` pour les produits sans toucher aux enrichissements |
| **Source** | Audit code-quality 🔴 #3 |

## Phases

| # | Phase | File |
| --- | ----- | ---- |
| 1 | Modifier le loader pour préserver les enrichissements | [`phase-1.md`](./phase-1.md) |

## Decisions

| Decision | Why |
| -------- | --- |
| `INSERT OR REPLACE` pour les produits | Met à jour si product_id existe déjà, insère sinon — préserve les foreign keys |
| Ne plus DELETE enrichissements | Les enrichissements existants restent liés aux product_id correspondants |
