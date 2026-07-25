# INSTALL.md — Volteyr Agentic

## Vision

Système d'enrichissement automatique de descriptions produits e-commerce via IA locale (Ollama), avec interface Streamlit et API REST FastAPI.

## Décisions

| Décision | Choix | Justification |
|---|---|---|
| Architecture | Monolithe modulaire | Projet local, 2 composants (Streamlit + FastAPI) partagent la même BDD et le même client LLM |
| Frontend | Streamlit | Imposé par le spec ; interface basique |
| API | FastAPI + Uvicorn | Imposé par le spec ; documentation auto via Swagger |
| Base de données | DuckDB (fichier `.db`) | Zéro configuration, embeddings SQLite-compatible, idéal pour un dataset de 1000 lignes |
| LLM | Qwen2.5:1.5B via Ollama | Modèle open-source local (~1.5 GB RAM) ; pas de clé cloud, tient dans 7.6 GB RAM |
| Langue | Français | Données et prompts en français |
| Export | CSV | Format universel, compatible Shopify |

## Stack

- **Python** 3.12
- **Streamlit** — UI d'enrichissement
- **FastAPI** + **Uvicorn** — API REST
- **DuckDB** — stockage local
- **Ollama** + **Qwen2.5:1.5B** — inférence LLM locale
- **Pydantic** — validation des modèles

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  Streamlit  │────▶│   DuckDB     │◀────│  FastAPI  │
│  (app.py)   │     │  (volteyr.db)│     │  (api.py) │
└──────┬──────┘     └──────────────┘     └──────────┘
       │                                        │
       └──────────────┬─────────────────────────┘
                      ▼
               ┌──────────┐
               │  Ollama  │
               │ Qwen2.5  │
               └──────────┘
```

Deux applications distinctes partagent la même base DuckDB et le même LLM local :
1. **Streamlit** : chargement CSV, filtrage, enrichissement, export
2. **FastAPI** : API de recherche sur les données enrichies

## Structure du projet

```
volteyr_agentic/
├── src/
│   ├── app.py              # Application Streamlit
│   ├── api.py               # API FastAPI
│   ├── db.py                # Connexion et schéma DuckDB
│   ├── llm_client.py        # Client Ollama + prompts
│   ├── load_data.py         # Parsing CSV + import DuckDB
│   └── models.py            # Modèles Pydantic
├── data/
│   ├── products.csv         # Dataset source
│   └── volteyr.db           # Base DuckDB (créée au premier lancement)
├── docs/
│   ├── PRD.md               # Product Requirements Document
│   └── INSTALL.md           # Ce fichier
├── requirements.txt
└── README.md
```

## Installation

### 1. Prérequis système

```bash
# Python 3.12
python3 --version  # doit afficher 3.12.x

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b
ollama serve  # ou systemctl start ollama
```

### 2. Dépendances Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` :
```
streamlit>=1.28
fastapi>=0.104
uvicorn[standard]>=0.24
duckdb>=0.9
ollama>=0.1
pydantic>=2.0
```

### 3. Charger les données

```bash
python src/load_data.py
```

Crée `data/volteyr.db` avec la table `products` (1000 lignes).

### 4. Lancer l'application Streamlit

```bash
streamlit run src/app.py
```

Ouvre sur `http://localhost:8501`.

### 5. Lancer l'API FastAPI

```bash
uvicorn src.api:app --reload
```

Disponible sur `http://localhost:8000` — docs sur `http://localhost:8000/docs`.

## Utilisation de l'API

```bash
# Recherche par mot-clé
curl "http://localhost:8000/api/products/search?q=robe"

# Avec filtres
curl "http://localhost:8000/api/products/search?q=robe&vendor=SOEUR"

# Détail d'un produit
curl "http://localhost:8000/api/products/4709011030112"
```

## Audit des candidats

| Candidat | Verdict | Notes |
|---|---|---|
| **Ollama + Qwen2.5** | ✅ Recommandé | Modèle local, pas de coût, tient en RAM |
| OpenAI API | ❌ Rejeté | Nécessite clé cloud, contraire à la contrainte |
| Mistral API | ❌ Rejeté | Idem, pas de clé cloud autorisée |
