# Product Requirements Document — Volteyr Agentic

**Version** : 1.0  
**Date** : 2026-07-25  
**Statut** : Approuvé  
**Auteur** : AIDD PM (via aidd-pm-03-prd)

---

## 1. Objectifs produit

### 1.1 Vision
Offrir aux équipes e‑commerce de [conversationsShop-ecommerce] un outil simple permettant d'enrichir automatiquement les descriptions produits via IA locale, puis d'exposer ces données via une API de recherche.

### 1.2 Problème résolu
- 136 descriptions vides et 502 < 50 caractères sur 1000 produits → impact SEO et conversion.
- Pas de moyen centralisé d'enrichir et de requêter les données enrichies.

### 1.3 Public cible
- Équipe catalogue (via Streamlit)
- Équipe technique / site e‑commerce (via API FastAPI)

---

## 2. User stories priorisées

| ID | Priorité | User story |
|---|---|---|
| US-01 | **P0** | En tant qu'utilisateur, je peux charger `products.csv` et voir les statistiques du catalogue. |
| US-02 | **P0** | En tant qu'utilisateur, je peux filtrer les produits par qualité de description, catégorie, marque. |
| US-03 | **P0** | En tant qu'utilisateur, je peux enrichir des descriptions via IA et voir le résultat. |
| US-04 | **P0** | En tant qu'utilisateur, je peux sauvegarder les enrichissements en base et exporter le résultat. |
| US-05 | **P0** | En tant que développeur, je peux interroger les produits enrichis via une API REST (recherche + filtres). |
| US-06 | **P1** | En tant qu'utilisateur, je vois l'état des appels IA (progression, erreurs). |
| US-07 | **P1** | En tant que développeur, je dispose d'une documentation API claire (Swagger / OpenAPI). |
| US-08 | **P2** | En tant qu'utilisateur, je peux prévisualiser l'ancienne et la nouvelle description côte à côte. |
| US-09 | **P2** | En tant que développeur, je peux utiliser des endpoints bonus (stats, CRUD enrichissement). |

---

## 3. Fonctionnalités

### 3.1 Must-have (livraison v1.0)

#### F‑01 : Chargement & analyse catalogue (US-01)
- Charger `products.csv` (gestion des embedded newlines, champs multi‑valeurs)
- Afficher : nb total produits, nb descriptions vides / courtes, répartition par type et vendeur

#### F‑02 : Filtrage produits (US-02)
- Filtre par qualité de description (vide / courte / < seuil)
- Filtre par `product_type`
- Filtre par `vendor`
- Combinaison des filtres

#### F‑03 : Enrichissement IA (US-03, US-06)
- Connexion à Ollama (modèle Qwen2.5 1.5B)
- Enrichissement : réécriture description + génération attributs (matière, entretien, style) + mots‑clés SEO
- Mode batch avec progression et gestion d'erreurs
- Prompts en français

#### F‑04 : Persistance & export (US-04)
- Schéma DuckDB : `products` (données brutes) + `enrichissements` (description enrichie, attributs, seo_keywords, timestamp)
- Sauvegarde unitaire et batch
- Export CSV des données enrichies

#### F‑05 : API de recherche (US-05, US-07)
- `GET /api/products/search?q=&product_type=&vendor=`
- Retour : données enrichies depuis DuckDB
- Documentation Swagger/OpenAPI intégrée

### 3.2 Nice-to-have (post‑v1.0)

#### F‑06 : Prévisualisation diff (US-08)
- Affichage côte à côte ancienne / nouvelle description

#### F‑07 : Endpoints bonus (US-09)
- `GET /api/products/:id` — détail produit
- `GET /api/stats` — statistiques catalogue
- `POST /api/products/:id/enrich` — enrichir un produit
- Pagination sur search

#### F‑08 : Configuration Ollama
- UI Streamlit pour choisir modèle / température

---

## 4. Critères d'acceptation

### 4.1 Streamlit
- [ ] L'application se lance avec `streamlit run app.py` sans erreur
- [ ] Les 1000 produits sont chargés et les stats affichées
- [ ] Les filtres qualité / type / marque fonctionnent et se combinent
- [ ] L'enrichissement IA produit une sortie valide pour un produit test
- [ ] La sauvegarde en DuckDB persiste et l'export CSV est lisible
- [ ] La barre de progression s'affiche pendant le batch

### 4.2 FastAPI
- [ ] L'API se lance avec `uvicorn api:app` sans erreur
- [ ] `GET /api/products/search?q=robe` retourne des résultats enrichis
- [ ] Les filtres `product_type` et `vendor` s'appliquent correctement
- [ ] La réponse est au format JSON structuré
- [ ] `/docs` affiche la documentation Swagger

### 4.3 Base de données
- [ ] DuckDB contient au moins 5 produits pré‑enrichis avant la démo
- [ ] Les colonnes enrichies (description, matière, entretien, style, seo_keywords) sont présentes

### 4.4 Qualité
- [ ] Le code respecte la stack validée (pas de dépendances cloud LLM)
- [ ] Les prompts LLM sont en français
- [ ] Le parser CSV gère les embedded newlines et guillemets

---

## 5. Contraintes techniques

| Domaine | Contrainte |
|---|---|
| **Langage** | Python 3.12 |
| **LLM** | Qwen2.5 1.5B via Ollama (local, ~1.5 GB RAM) — pas de clé cloud |
| **Base** | DuckDB (fichier `.db` local, zéro configuration) |
| **Frontend** | Streamlit — UX minimale (priorité à la fonction) |
| **API** | FastAPI + Uvicorn + Pydantic |
| **OS** | Linux, 7.6 GB RAM, 16 cœurs |
| **CSV** | Format Shopify : embedded newlines, guillemets, champs multi‑valeurs (`product_tags`) |
| **Langue** | Données en français → prompts et attributs en français |
| **Git** | Ne pas commiter `context.md`, `.opencode/`, `opencode.jsonc`, `conversations/`, `AGENTS.md` |

---

## 6. Dépendances

### 6.1 Externes (pip)

| Package | Justification |
|---|---|
| `streamlit` | Interface utilisateur |
| `fastapi` | Framework API REST |
| `uvicorn[standard]` | Serveur ASGI |
| `duckdb` | Base de données embarquée |
| `ollama` | Client Python pour LLM local |
| `pydantic` | Modèles de données / validation |

### 6.2 Externes (système)
- Ollama installé et service actif
- Modèle Qwen2.5:1.5B téléchargé via `ollama pull qwen2.5:1.5b`

### 6.3 Internes (projet)
- Aucune — projet from scratch

---

## 7. Roadmap

| Phase | Contenu | Dépendances |
|---|---|---|
| **P1 — Fondation** | Structure projet, `requirements.txt`, installation Ollama + modèle | — |
| **P2 — BDD & chargement** | Parser CSV, schéma DuckDB, `load_data.py` | P1 |
| **P3 — Streamlit** | Stats, filtrage, enrichissement, sauvegarde, export | P2 |
| **P4 — Pipeline LLM** | Client Ollama, prompts, batch processing | P1 |
| **P5 — FastAPI** | Search endpoint, modèles Pydantic, docs, endpoints bonus | P2 |
| **P6 — Finalisation** | Pré‑remplissage DB, README, test de bout en bout | P3, P4, P5 |
