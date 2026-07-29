---
objective: La connexion SQLite est thread-safe sans dépendre de check_same_thread=False
status: pending
---

# Plan: Corriger la sécurité thread de la connexion SQLite

## Overview

| Field      | Value |
| ---------- | ----- |
| **Goal**   | Supprimer `check_same_thread=False` et garantir que chaque thread crée sa propre connexion |
| **Source** | Audit architecture 🔴 #2 |

## Phases

| # | Phase | File |
| --- | ----- | ---- |
| 1 | Restructurer la connexion pour per-thread sans check_same_thread=False | [`phase-1.md`](./phase-1.md) |

## Decisions

| Decision | Why |
| -------- | --- |
| Ne PAS garder `check_same_thread=False` | Désactive une protection intégrée de SQLite. Chaque thread doit avoir sa propre connexion |
| Conserver `_override_conn` | Nécessaire pour TestClient qui tourne dans un thread anyio séparé |
