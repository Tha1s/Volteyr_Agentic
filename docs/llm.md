# Module `llm/` — Documentation

## 1. Vue d'ensemble

Le module `src/llm/` encapsule toute la logique d'interaction avec **Ollama**, le moteur LLM local. Il est structuré en trois couches :

| Fichier | Rôle |
|---|---|
| `client.py` | Client HTTP bas niveau vers l'API REST d'Ollama |
| `prompts.py` | Templates de prompts pour l'enrichissement produit |
| `strategies.py` | Pattern Strategy : sélection du modèle (petit vs. grand) |

Le flux de données est unidirectionnel : l'application choisit une stratégie (`strategies.py`), qui appelle le client (`client.py`) avec les prompts formatés (`prompts.py`), et le client envoie la requête à Ollama via HTTP.

---

## 2. `client.py` — Client HTTP Ollama

**`src/llm/client.py`** est le point d'entrée unique vers l'API REST d'Ollama.

### Constantes

| Constante | Valeur | Ligne |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | `:5` |
| `OLLAMA_TIMEOUT_LARGE` | `120` secondes | `:6` |
| `OLLAMA_TIMEOUT_SMALL` | `30` secondes | `:7` |

Une `requests.Session()` unique est instanciée au niveau module (`:9`) pour bénéficier du **keep-alive** (réutilisation des connexions TCP).

### Fonctions

#### `generate(model, prompt, system, temperature)` — `:12-37`

Envoie une requête de génération à Ollama.

**Paramètres :**

| Paramètre | Type | Défaut | Description |
|---|---|---|---|
| `model` | `str` | — | Nom du modèle Ollama (ex. `qwen2.5:1.5b`) |
| `prompt` | `str` | — | Le prompt utilisateur |
| `system` | `str` | `""` | Le prompt système |
| `temperature` | `float` | `0.7` | Température d'échantillonnage |

**Retour :** `str | None` — le texte généré, ou `None` en cas d'erreur.

**Fonctionnement :**

1. **Timeout adaptatif** (`:18`) : si le nom du modèle contient `"large"`, le timeout est de 120s ; sinon 30s. Cela évite des erreurs de timeout sur les modèles lourds tout en gardant une latence faible sur les petits.

2. **Payload JSON** (`:19-26`) :
   ```json
   {
     "model": "...",
     "prompt": "...",
     "system": "...",
     "stream": false,
     "options": { "temperature": 0.7 },
     "format": "json"
   }
   ```
   - `stream: false` — réponse unique, pas de streaming SSE
   - `format: "json"` — force Ollama à répondre en JSON structuré (mode JSON natif d'Ollama)

3. **Gestion d'erreurs** (`:27-37`) : deux blocs `except` distincts :
   - `requests.RequestException` (`:32`) — erreurs réseau, timeout, HTTP 4xx/5xx
   - `json.JSONDecodeError` (`:35`) — réponse Ollama malformée

   En cas d'erreur, un message est imprimé sur stderr et `None` est retourné. **Pas d'exception remontée** — l'appelant doit vérifier le retour.

#### `check_ollama()` — `:40-45`

Vérifie que le serveur Ollama est en ligne en appelant `GET /api/tags` (timeout 10s). Retourne `True` si le serveur répond avec un statut 200, `False` sinon.

---

## 3. `prompts.py` — Templates de prompts

**`src/llm/prompts.py`** contient les deux templates utilisés pour l'enrichissement de descriptions produits.

### `ENRICHMENT_SYSTEM` — `:1`

```
Tu es un rédacteur e-commerce spécialisé dans les descriptions de mode.
Réponds UNIQUEMENT en JSON, sans texte avant ni après.
```

**Rôle :** prompt système qui définit la persona du LLM (rédacteur mode e-commerce) et impose une sortie JSON stricte.

### `ENRICHMENT_USER` — `:3-21`

Template formaté avec 4 variables :

| Variable | Description |
|---|---|
| `{product_type}` | Type de produit (ex. "Robe", "Veste") |
| `{category}` | Catégorie produit |
| `{vendor}` | Marque / fabricant |
| `{description}` | Description originale du produit |

**Règles imposées au LLM :**

- Ne jamais inventer d'information — utiliser `"Non précisé"` si inconnu
- Mentionner le type de produit dans la première phrase
- Ton chic et accessible

**Sortie JSON attendue :**

| Champ | Description |
|---|---|
| `enriched_description` | Description enrichie en français |
| `material` | Matière(s) du produit |
| `care_instructions` | Conseils d'entretien |
| `style` | Style vestimentaire |
| `seo_keywords` | Mots-clés SEO |

Les doubles accolades `{{` / `}}` dans le template (`:15`, `:21`) sont une échappatoire pour `str.format()` : elles produisent des accolades littérales `{` / `}` dans la sortie, permettant au LLM de voir le squelette JSON attendu.

---

## 4. `strategies.py` — Pattern Strategy

**`src/llm/strategies.py`** implémente le **pattern Strategy** pour sélectionner dynamiquement le modèle Ollama à utiliser.

### Constantes

| Constante | Valeur | Ligne |
|---|---|---|
| `SMALL_MODEL` | `"qwen2.5:1.5b"` | `:5` |
| `LARGE_MODEL` | `"qwen2.5:7b"` | `:6` |

### Interface : `LLMStrategy` — `:9-14`

C'est un **`typing.Protocol`**, donc du duck-typing structurel (pas besoin d'hériter explicitement). Il définit le contrat :

- Attributs : `model: str`, `temperature: float`, `timeout: int`
- Méthode : `generate(prompt, system) -> str | None`

### `SmallModelStrategy` — `:17-23`

Utilise **Qwen2.5 1.5B** — modèle léger, rapide, faible empreinte mémoire (~1.5 Go).

| Attribut | Valeur |
|---|---|
| `model` | `qwen2.5:1.5b` |
| `temperature` | `0.7` |
| `timeout` | `30s` |

**Quand l'utiliser :** enrichissements rapides, produits simples, volume élevé, contraintes mémoire faibles. La qualité de description est correcte mais moins nuancée.

### `LargeModelStrategy` — `:26-32`

Utilise **Qwen2.5 7B** — modèle plus lourd (~4 Go), plus lent, mais meilleure qualité de génération.

| Attribut | Valeur |
|---|---|
| `model` | `qwen2.5:7b` |
| `temperature` | `0.7` |
| `timeout` | `120s` |

**Quand l'utiliser :** produits premium, descriptions complexes, quand la qualité prime sur la vitesse. Le timeout passe à 120s pour accommoder le temps d'inférence plus long.

### Factory : `get_strategy(use_large)` — `:35-36`

```
Retourne LargeModelStrategy() si use_large=True, sinon SmallModelStrategy().
```

Point d'entrée unique pour l'application. L'appelant n'a pas besoin de connaître les classes concrètes — il appelle `get_strategy(use_large=True/False)` et obtient un objet respectant `LLMStrategy`.

### Pourquoi deux modèles ?

1. **Trade-off qualité/vitesse** : le modèle 1.5B traite un produit en ~2-5s, le 7B en ~10-30s
2. **Contraintes mémoire** : sur une machine avec 7.6 Go de RAM, le 7B seul occupe ~4 Go, rendant le 1.5B utile en parallèle d'autres processus
3. **Coût d'expérimentation** : le petit modèle permet des itérations rapides en développement

---

## 5. Flux d'appel

```
Application (Streamlit / FastAPI)
        │
        ▼
get_strategy(use_large=True/False)          ← strategies.py:35-36
        │
        ▼
SmallModelStrategy / LargeModelStrategy     ← strategies.py:17, 26
        │ .generate(prompt, system)
        ▼
generate(model, prompt, system, temp)       ← client.py:12
        │
        ▼
requests.Session().post(OLLAMA_URL, ...)    ← client.py:9, 28
        │
        ▼
Ollama (localhost:11434/api/generate)
        │
        ▼
Réponse JSON parsée → str | None            ← client.py:30-31
```

Étape par étape :

1. L'application appelle `get_strategy(use_large=...)` qui instancie la stratégie appropriée
2. L'application formate `ENRICHMENT_USER` avec les données produit via `str.format()`
3. L'application appelle `strategy.generate(prompt=formatted, system=ENRICHMENT_SYSTEM)`
4. La stratégie délègue à `client.generate()` avec son modèle et sa température
5. `client.generate()` construit le payload JSON, l'envoie via `requests.Session().post()` à Ollama
6. La réponse Ollama est parsée : le champ `"response"` contient le texte JSON généré
7. Le texte est retourné à l'appelant (ou `None` si erreur)

---

## 6. Choix techniques

### Pourquoi JSON structuré ?

Le paramètre `"format": "json"` (`client.py:25`) utilise le **mode JSON natif d'Ollama**, qui contraint la grammaire de sortie du LLM à du JSON valide. Cela garantit que :

- La réponse est parsable sans post-traitement fragile (regex, strip de markdown, etc.)
- Les champs `enriched_description`, `material`, `care_instructions`, `style`, `seo_keywords` sont toujours présents
- Pas de texte parasite avant/après le JSON

Alternative écartée : parser manuellement avec regex — trop fragile face aux variations de sortie des petits modèles.

### Pourquoi `requests.Session()` et pas le client Python `ollama` ?

- **Prédictibilité** : le client Python `ollama` ajoute une couche d'abstraction opaque (retries, streaming, state management). Avec `requests`, on maîtrise exactement ce qui est envoyé et le comportement en cas d'erreur.
- **Keep-alive** : `requests.Session()` (`client.py:9`) réutilise les connexions TCP, évitant le handshake TLS/TCP à chaque requête — gain de ~50-100ms par appel.
- **Dépendance zéro** : `requests` est déjà dans `requirements.txt`. Le client `ollama` ajouterait une dépendance supplémentaire pour une API REST triviale.
- **Timeout explicite** : contrôle fin du timeout par modèle (30s vs 120s), difficile à paramétrer avec le client officiel.
- **Mode JSON** : le paramètre `format: "json"` est passé directement dans le payload brut, sans wrapping par une librairie qui pourrait le transformer.
