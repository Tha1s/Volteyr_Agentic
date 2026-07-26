ENRICHMENT_SYSTEM = "Tu es un rédacteur e-commerce spécialisé dans les descriptions de mode. Réponds UNIQUEMENT en JSON, sans texte avant ni après."

ENRICHMENT_USER = """Enrichis cette description produit en français.
Type: {product_type}
Catégorie: {category}
Marque: {vendor}
Description originale: {description}

Règles:
- N'invente jamais d'information. Si inconnu, écris "Non précisé"
- Mentionne le type de produit dans la première phrase
- Ton chic et accessible

Réponds UNIQUEMENT au format JSON avec ces champs:
{{
  "enriched_description": "...",
  "material": "...",
  "care_instructions": "...",
  "style": "...",
  "seo_keywords": "..."
}}"""

