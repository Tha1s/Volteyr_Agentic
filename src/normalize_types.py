import duckdb
import re
import csv
import os
from db import DB_PATH

NORMALIZE_MAP = {
    'Pantalon': 'Pantalons',
    'Pants': 'Pantalons',
    'Trouser': 'Pantalons',
    'T-Shirt': 'T-Shirts',
    'T-shirt': 'T-Shirts',
    'T Shirt': 'T-Shirts',
    'TEE SHIRT': 'T-Shirts',
    'Tees': 'T-Shirts',
    'Tshirts': 'T-Shirts',
    'Veste': 'Vestes',
    'Jacket': 'Vestes',
    'JACKET': 'Vestes',
    'JACKETS': 'Vestes',
    'Coats': 'Vestes',
    'Suit jackets': 'Vestes',
    'Manteau': 'Manteaux',
    'Pull': 'Pulls',
    'PULL': 'Pulls',
    'Pullovers': 'Pulls',
    'Sweaters': 'Pulls',
    'Turtleneck Sweaters': 'Pulls',
    'Pulls Col Rond': 'Pulls',
    'Pulls Col Roulé': 'Pulls',
    'Pulls Col V': 'Pulls',
    'Pulls Cols Ronds': 'Pulls',
    'Bague': 'Bagues',
    'Bracelet': 'Bracelets',
    'Bracelets Et Joncs': 'Bracelets',
    'Créoles': "Boucles D'Oreilles",
    'Mono boucle': "Boucles D'Oreilles",
    "Boucles d'Oreilles": "Boucles D'Oreilles",
    "Boucles d'oreilles": "Boucles D'Oreilles",
    'Boucles D\u2019Oreilles': "Boucles D'Oreilles",
    'Chemises & Tops': 'Chemises Et Tops',
    'Chemises Et Top': 'Chemises Et Tops',
    'Chemises / Blouses': 'Chemises',
    'Blouses Et Chemises': 'Chemises',
    'Chemises Et T-Shirts': 'Chemises Et Tops',
    'T-Shirts Et Chemises': 'Chemises Et Tops',
    'SHIRT': 'Chemises',
    'Shirts': 'Chemises',
    'Chemise': 'Chemises',
    'CARDIGAN': 'Cardigans',
    'Wrap cardigans': 'Cardigans',
    'SWEATSHIRT': 'Sweats',
    'Sweatshirt': 'Sweats',
    'Sweatshirts': 'Sweats',
    'Hoodies': 'Sweats',
    'Sweat-shirt': 'Sweats',
    'ROBE': 'Robes',
    'Dress': 'Robes',
    'Midi dresses': 'Robes',
    'Short dresses': 'Robes',
    'Gowns': 'Robes',
    'JUPE': 'Jupes',
    'Jupe': 'Jupes',
    'Midi Skirts': 'Jupes',
    'Mini Skirts': 'Jupes',
    'Skirts and shorts': 'Jupes Et Shorts',
    'Jupes et Shorts': 'Jupes Et Shorts',
    'Jupes Et Robes': 'Robes Et Jupes',
    'TOP': 'Tops',
    'Top': 'Tops',
    'Long Sleeved Top': 'Tops',
    'Short Sleeved Top': 'Tops',
    'Sleeveless Top': 'Tops',
    'Tops et T-Shirts': 'Tops',
    'Tops & Chemises': 'Tops',
    'Baskets Homme': 'Baskets',
    'SNEAKERS SIMONE': 'Sneakers',
    'DERBIES': 'Derbies',
    'SANDALES PLATES': 'Sandales',
    'Sandals': 'Sandales',
    'Chausson Espadrille': 'Espadrilles',
    'Bottes Et Bottines': 'Bottes',
    'Bottes de randonnée': 'Bottes',
    'Mules Et Sandales': 'Mules',
    'Chaussures De Ville': 'Chaussures',
    'Zapatilla': 'Chaussures',
    'SHOES': 'Chaussures',
    'Talons Moyens': 'Chaussures',
    'TALONS HAUT': 'Chaussures',
    'Bain': 'Maillots De Bain',
    'Beachwear': 'Maillots De Bain',
    'SWIMWEAR': 'Maillots De Bain',
    'Bikini Bottoms': 'Maillots De Bain',
    'Maillots de bain': 'Maillots De Bain',
    'Maillots 1 Pièce': 'Maillots De Bain',
    'Maillots 1 piÃ¨ce': 'Maillots De Bain',
    'Maillots De Bain 1 Pièce': 'Maillots De Bain',
    'Maillots De Bain Femme': 'Maillots De Bain',
    'Hauts De Maillot': 'Maillots De Bain',
    'Hauts De Maillots': 'Maillots De Bain',
    'Maille': 'Maille Et Sweats',
    'Mailles Et Sweats': 'Maille Et Sweats',
    'Knitwear': 'Maille Et Sweats',
    'LINGERIE': 'Lingerie',
    'Bodies Et Lingerie': 'Lingerie',
    'Soutiens-Gorge Ampliformes': 'Lingerie',
    'Brassières': 'Lingerie',
    'Briefs': 'Lingerie',
    'Boxers': 'Lingerie',
    'Caleçons': 'Lingerie',
    'Strings': 'Lingerie',
    'Tangas': 'Lingerie',
    'Hauts De Lingerie': 'Lingerie',
    'Bodies & Pyjamas': 'Pyjamas',
    'Body Et Combinaisons': 'Combinaisons',
    'Bodies Et Combinaisons': 'Combinaisons',
    'Sacs & Accessoires': 'Sacs',
    'Sacs Et Accessoires': 'Sacs',
    'Sacs Et Maroquinerie': 'Sacs',
    'Sacs Et Pochettes': 'Sacs',
    'Sacs Pepa': 'Sacs',
    'Sac hobo Femme': 'Sacs',
    'Handbags': 'Sacs',
    'Tote Bags': 'Sacs',
    'tote': 'Sacs',
    'Sac à Dos': 'Sacs',
    'Shoulder bags': 'Sacs À Bandoulière',
    'Sacs Bandoulière': 'Sacs À Bandoulière',
    'Sacs Et Bandoulières': 'Sacs À Bandoulière',
    'Sac à Bandoulière': 'Sacs À Bandoulière',
    'Sacs A Main': 'Sacs À Main',
    'Pochettes Et Trousses': 'Pochettes',
    'Pochettes Et Sachets Ramasse-Crottes': 'Pochettes',
    'Housses Et Trousses': 'Trousses',
    'MAROQUINERIE': 'Maroquinerie',
    'Chaussettes Et Collants': 'Chaussettes',
    'Bottoms': 'Bas',
    'Bas lingerie': 'Bas',
    'Culottes': 'Bas',
    'Culottes Et Bas': 'Bas',
    'Belts': 'Ceintures',
    'Accessoires Et Chaussures': 'Accessoires',
    'ACCESSORIES MEN': 'Accessoires',
    'WOMEN ACCESSORIES': 'Accessoires',
    'Boîtes À Bijoux': 'Accessoires',
    'Casques': 'Accessoires',
    'Masques': 'Accessoires',
    'Shorts & Bermuda Shorts': 'Shorts',
    'Bermudas': 'Shorts',
    'Bootcut Jeans': 'Jeans',
    'Jeans & Pantalons': 'Jeans',
    'Jeans Et Pantalons': 'Jeans',
    'Blazers': 'Vestes',
    'Vestes & Manteaux, Homme': 'Vestes Et Manteaux',
    'Manteaux Et Vestes': 'Vestes Et Manteaux',
    'Manteaux/Veste - Bébé - Mixte': 'Vestes Et Manteaux',
    'Manteaux/Veste': 'Vestes & Manteaux',
    'GILET': 'Gilets',
    'LUMINAIRE': 'Luminaires',
    'Néon LED à forme': 'Luminaires',
    'Lampes À Poser': 'Luminaires',
    'Lunettes De Vue': 'Lunettes',
    'Bébé Garçon': 'Bébé',
    'Nouveau Né': 'Bébé',
    'Enfant Fille': 'Enfant',
    'Fille': 'Enfant',
    'Enfant Garçon': 'Enfant',
    'ACCESSOIRES': 'Accessoires',
    'CHEMISE': 'Chemises',
    'TSHIRTS & TOPS': 'Tops',
    'T-Shirts & Tops': 'Tops',
    'JUMPER': 'Pulls',
    'DENIM': 'Jeans',
    'Joggers': 'Joggings',
    'Maillot': 'Maillots',
    'Doudounes': 'Vestes',
    'Parkas': 'Vestes',
    'Softshells': 'Vestes',
    'Escarpins': 'Chaussures',
    'Ballerines': 'Chaussures',
    'Pumps': 'Chaussures',
    'Sabots': 'Chaussures',
    'Tongs': 'Chaussures',
    'Slides': 'Chaussures',
    'Bateaux': 'Chaussures',
    'Pulls & Gilets': 'Pulls',
    'Pulls Et Sweats': 'Pulls',
    'Leggings': 'Bas',
    'Cyclistes': 'Bas',
    'Manchette': 'Bracelets',
    'Fonds De Robes': 'Robes',
    'Robe mi-longue': 'Robes',
    'Jupe mi-longue': 'Jupes',
    'Teddies': 'Pulls',
    'Combinaisons & Robes': 'Combinaisons',
    'Nightwear': 'Pyjamas',
    'Nuit': 'Pyjamas',
    'Bras': 'Bijoux',
    'Anses': 'Sacs',
    'wallet': 'Portefeuilles',
    'Porte-Chéquiers': 'Petite Maroquinerie',
    'Porte-Passeports': 'Petite Maroquinerie',
    # V3 — genres
    'Femme': 'Autres',
    'Ensembles': 'Autres',
    # V3 — sous-types chaussures
    'Mocassins': 'Chaussures',
    'Espadrilles': 'Chaussures',
    'Running': 'Chaussures',
    'Boots': 'Chaussures',
    'Derbies': 'Chaussures',
    # V3 — singletons accessoires
    'Chapeaux': 'Accessoires',
    'Bonnets': 'Accessoires',
    'Casquettes': 'Accessoires',
    'Foulards': 'Accessoires',
    'Écharpes': 'Accessoires',
    'Mitaines': 'Accessoires',
    'Cravates': 'Accessoires',
    'Parapluies': 'Accessoires',
    'Trousses': 'Accessoires',
    'Hats': 'Accessoires',
    # V3 — bijoux
    'Broches': 'Bijoux',
    'Pendentifs': 'Bijoux',
    # V3 — vêtements divers
    'Polos': 'T-Shirts',
    'Kimonos': 'Vestes',
    'Ponchos': 'Vestes',
    'Tuniques': 'Chemises',
    'Chaussons Bébés': 'Chaussures',
    'Pulls & Cardigans': 'Pulls',
    'Pulls & Sweats': 'Pulls',
    'T-Shirts Et Tops': 'Tops',
    'Culottes Menstruelles': 'Lingerie',
    'Bloomer/Culotte': 'Bébé',
    'Ensembles Pour Bébés Et Tout-Petits': 'Bébé',
    'Chaussures - Chaussures': 'Chaussures',
    # V3 — doublons

    'Sacs À Main': 'Sacs',
    'Portefeuilles': 'Petite Maroquinerie',

    'Pantalons Et Jupes': 'Pantalons',
    'Pantalons Et Joggings': 'Pantalons',
    'Pantalons Et Combinaisons': 'Pantalons',
    'Pantalons Et Jeans': 'Pantalons',
    'Pantalons & Leggings': 'Pantalons',
    'Sets De Valises': 'Valises Long Séjour',
    'Lingerie Bas': 'Lingerie',
    'Peignoirs': 'Lingerie',
    'Peinture Par Numéros': 'Autres',
    # V4 — fusion agressive 61 → 14 catégories
    # T-Shirts unification → Hauts
    'T-shirts': 'T-Shirts',
    'T-shirts & Polos': 'T-Shirts',
    'T-Shirts': 'Hauts',
    # Hauts/Tops/Shirts

    'Chemises Et Tops': 'Hauts',
    'Chemises': 'Hauts',
    'Blouses': 'Hauts',
    'Tops': 'Hauts',
    # Pulls & Maille
    'Maille Et Sweats': 'Pulls & Maille',
    'Sweats': 'Pulls & Maille',
    'Cardigans': 'Pulls & Maille',
    'Pulls Et Gilets': 'Pulls & Maille',
    'Gilets': 'Pulls & Maille',
    'Pulls': 'Pulls & Maille',
    # Vestes & Manteaux
    'Vestes Et Manteaux': 'Vestes & Manteaux',
    'Manteaux': 'Vestes & Manteaux',
    'Vestes': 'Vestes & Manteaux',
    # Robes & Jupes
    'Robes Et Combinaisons': 'Robes & Jupes',
    'Robes Et Jupes': 'Robes & Jupes',
    'Combinaisons': 'Robes & Jupes',
    'Jupes Et Shorts': 'Robes & Jupes',
    'Jupes': 'Robes & Jupes',
    'Robes': 'Robes & Jupes',
    # Chaussures
    'Baskets': 'Chaussures',
    'Sneakers': 'Chaussures',
    'Sandales': 'Chaussures',
    'Bottes': 'Chaussures',
    'Bottines': 'Chaussures',
    'Mules': 'Chaussures',
    'Chaussures Et Accessoires': 'Chaussures',
    # Pantalons & Shorts
    'Jeans': 'Pantalons & Shorts',
    'Shorts': 'Pantalons & Shorts',
    'Joggings': 'Pantalons & Shorts',
    'Bas': 'Pantalons & Shorts',
    'Pantalons Et Shorts': 'Pantalons & Shorts',
    'Pantalons': 'Pantalons & Shorts',
    'Chaussettes': 'Pantalons & Shorts',
    # Sacs & Maroquinerie
    'Sacs À Bandoulière': 'Sacs & Maroquinerie',
    'Maroquinerie': 'Sacs & Maroquinerie',
    'Petite Maroquinerie': 'Sacs & Maroquinerie',
    'Pochettes': 'Sacs & Maroquinerie',
    'Sacs': 'Sacs & Maroquinerie',
    # Bijoux
    'Bagues': 'Bijoux',
    'Bracelets': 'Bijoux',
    'Colliers': 'Bijoux',
    "Boucles D'Oreilles": 'Bijoux',
    # Accessoires
    'Ceintures': 'Accessoires',
    'Lunettes': 'Accessoires',
    'Accessoires Iphones 12': 'Accessoires',
    # Maillots
    'Maillots': 'Maillots De Bain',
    # Enfant/Bébé
    'Bébé': 'Bébé & Enfant',
    'Enfant': 'Bébé & Enfant',
}

AUTRES = {
    '#N/A', 'A definir', 'A définir', 'ACC LLG', 'AQUAHERO',
    'CIVIL', 'Element', 'JAC', 'PAP', 'Prix', 'Silhouette',
    'Mini', 'Nouveautés salon', 'OVERSHIRT', 'Col Rond',
    'Removable straps',
    'Bonpoint', 'Chanel', 'Gucci', 'Hermès', 'Prada', 'Vans',
    'Birkenstock', 'Golden Goose', 'Hugo Boss', 'Hartford',
    'Jimmy Choo', 'Reiko', 'Sessùn', 'Tartine & Chocolat',
    'Band Of Outsiders', 'Anaki', 'IKKS', 'PS by PAUL SMITH',
    'Petit Bateau', 'Air Jordan',
    'Men, KNITWEAR, LMTS0194', 'Women, DRESSES, 7028I77-2135',
    'Women, KNITWEAR, WA296C12519A', 'Women, TOP, 030-2WBET',
    'Women, TOP, T0001FQ23', 'RTW CLOTHING', 'KEYRING & CHARM',
    'SURFWEAR GIRLS', 'SURFWEAR MEN',
    'Peinture Par Numéros', 'Affiches', 'Coffrets',
    'Complément Alimentaire Peau', 'Vitamines et compléments alimentaires',
    'Soin | Visage', 'Teint', 'Beauté Des Mains & Pieds',
    'Faux Ongles', 'Protections Solaires', 'Hygiène', 'Produits Corps',
    'Poubelle tri sélectif', "Plantes D'Intérieur", 'Jardin',
    'Art De La Table', 'Assiettes', 'Coupelles', 'Couverts',
    'Plats', 'Vases', 'Tables', 'Chaises', 'Assises', 'Poufs',
    'Petit Mobilier', 'SIEGE SUR MESURE',
    'Paniers', 'Cables', 'Isothermes', 'Bavoirs', 'Boutchou',
    'CÉRÉMONIE', 'MEN', 'WOVEN',     'Homme', 'Bras', 'Corps',
    # V3 — non-mode
    'Tapis', 'Décoration', 'Arts De La Table', 'Linge De Lit',
    'Draps Plats', 'Parure De Couette', "Taies D'Oreiller",
    'Linge De Bain', 'Serviettes', 'Linge De Maison',
    'COUSSIN ET PLAID', 'Plaids', 'Valises Long Séjour',
    'Maison', 'Prêt-À-Porter', 'Prêt-à-porter', 'Vêtements',
    'Costumes & Smokings',
    # V4
    'Luminaires', 'Zyne',
}


_CHILD_SUFFIX = re.compile(r'\s*-\s*(?:Bébé|Enfant|Fille|Garçon|Mixte|Homme|Femme).*$', re.IGNORECASE)


def normalize_product_type(name: str) -> str:
    if not name or not name.strip():
        return "Autres"
    cleaned = _CHILD_SUFFIX.sub('', name).strip()
    if cleaned != name:
        name = cleaned
    while name in NORMALIZE_MAP:
        name = NORMALIZE_MAP[name]
    if name in AUTRES:
        return "Autres"
    return name


def add_category_column(db_path: str | None = None) -> None:
    path = db_path or DB_PATH
    conn = duckdb.connect(path)

    CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products.csv")

    conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR")

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        updates = {}
        for row in reader:
            pid = int(row["product_id"].strip())
            raw_type = row["product_type"].strip() if row["product_type"] else ""
            updates[pid] = raw_type

    changed = 0
    for pid, raw_type in updates.items():
        category = normalize_product_type(raw_type)
        conn.execute(
            "UPDATE products SET product_type = ?, category = ? WHERE product_id = ?",
            [raw_type, category, pid],
        )
        changed += 1

    conn.commit()
    print(f"✅ Migration terminée : {changed} produits mis à jour (product_type restauré, category ajoutée)")
    counts = conn.execute(
        "SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY COUNT(*) DESC"
    ).fetchall()
    print(f"📊 Catégories après migration : {len(counts)} distinctes")
    for cat, cnt in counts:
        print(f"   {cat}: {cnt}")
    conn.close()


if __name__ == "__main__":
    add_category_column()
