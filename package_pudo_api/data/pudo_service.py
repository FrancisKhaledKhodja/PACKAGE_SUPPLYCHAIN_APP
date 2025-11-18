import os

from math import radians, sin, cos, sqrt, atan2
import polars as pl
from package_pudo_api.data.pudo_etl import update_data

from package_pudo_api.constants import path_output, folder_bdd_python, path_datan, folder_name_app

try:
    
    pudos = pl.read_parquet(os.path.join(path_datan, folder_name_app, "pudo_directory.parquet"))
    stores = pl.read_parquet(os.path.join(path_datan, folder_name_app, "stores.parquet"))
    helios = pl.read_parquet(os.path.join(path_datan, folder_name_app, "helios.parquet"))
    items = pl.read_parquet(os.path.join(path_datan, folder_name_app, "items.parquet"))
    items_son_buildings = pl.read_parquet(os.path.join(path_datan, folder_name_app, "items_son_buildings.parquet"))
    items_parent_buildings = pl.read_parquet(os.path.join(path_datan, folder_name_app, "items_parent_buildings.parquet"))
    nomenclatures = pl.read_parquet(os.path.join(path_datan, folder_name_app, "nomenclatures.parquet"))
    manufacturers = pl.read_parquet(os.path.join(path_datan, folder_name_app, "manufacturers.parquet"))
    equivalents = pl.read_parquet(os.path.join(path_datan, folder_name_app, "equivalents.parquet"))
except FileNotFoundError:
    update_data()
    try:
        pudos = pl.read_parquet(os.path.join(path_datan, folder_name_app, "pudo_directory.parquet"))
    except FileNotFoundError:
        pudos = pl.DataFrame()
    try:
        stores = pl.read_parquet(os.path.join(path_datan, folder_name_app, "stores.parquet"))
    except FileNotFoundError:
        stores = pl.DataFrame()
    try:
        helios = pl.read_parquet(os.path.join(path_datan, folder_name_app, "helios.parquet"))
    except FileNotFoundError:
        helios = pl.DataFrame()
    try:
        items = pl.read_parquet(os.path.join(path_datan, folder_name_app, "items.parquet"))
    except FileNotFoundError:
        items = pl.DataFrame()
    try:
        items_son_buildings = pl.read_parquet(os.path.join(path_datan, folder_name_app, "items_son_buildings.parquet"))
    except FileNotFoundError:
        items_son_buildings = pl.DataFrame()
    try:
        items_parent_buildings = pl.read_parquet(os.path.join(path_datan, folder_name_app, "items_parent_buildings.parquet"))
    except FileNotFoundError:
        items_parent_buildings = pl.DataFrame()
    try:
        nomenclatures = pl.read_parquet(os.path.join(path_datan, folder_name_app, "nomenclatures.parquet"))
    except FileNotFoundError:
        nomenclatures = pl.DataFrame()
    try:
        manufacturers = pl.read_parquet(os.path.join(path_datan, folder_name_app, "manufacturers.parquet"))
    except FileNotFoundError:
        manufacturers = pl.DataFrame()
    try:
        equivalents = pl.read_parquet(os.path.join(path_datan, folder_name_app, "equivalents.parquet"))
    except FileNotFoundError:
        equivalents = pl.DataFrame()

# Dictionnaires utiles (magasins/helios)
dico_stores = {row["code_magasin"]: row for row in stores.iter_rows(named=True)} if 'stores' in locals() else {}
dico_helios = {row["code_ig"]: row for row in helios.iter_rows(named=True)} if 'helios' in locals() else {}

def get_items_son_buildings_df() -> pl.DataFrame:
    """Retourne le DataFrame complet items_son_buildings ou un DF vide s'il est indisponible.

    Ce parquet est chargé depuis path_datan/folder_name_app/items_son_buildings.parquet
    et pourra être utilisé notamment pour le Parc Helios par article.
    """
    if 'items_son_buildings' not in globals():
        return pl.DataFrame()
    return items_son_buildings


def get_items_parent_buildings_df() -> pl.DataFrame:
    """Retourne le DataFrame complet items_parent_buildings ou un DF vide s'il est indisponible.

    Ce parquet est chargé depuis path_datan/folder_name_app/items_parent_buildings.parquet
    et est utilisé pour calculer la quantité en production et le nombre de sites actifs
    pour un article donné.
    """
    if 'items_parent_buildings' not in globals():
        return pl.DataFrame()
    return items_parent_buildings


def get_helios_quantity_for_item(code_article: str) -> float:
    """Retourne la quantité totale du parc Helios pour un article donné.

    - Filtre strictement items_son_buildings sur la colonne code_article
      (valeur normalisée en majuscules, trim).
    - Cherche une colonne de quantité (nom contenant 'quant' ou 'qte') et en fait la somme.
    - Si aucune ligne ou aucune quantité trouvée, retourne 0.0.
    """
    if 'items_son_buildings' not in globals() or items_son_buildings.is_empty():
        return 0.0
    df = items_son_buildings
    if "code_article" not in df.columns:
        return 0.0
    try:
        norm = str(code_article).strip().upper()
        filtered = df.filter(
            pl.col("code_article").cast(pl.Utf8).str.strip().str.to_uppercase() == norm
        )
        if filtered.is_empty():
            return 0.0
        # Chercher une colonne de quantité
        qty_cols = [
            c for c in filtered.columns
            if "quant" in c.lower() or "qte" in c.lower()
        ]
        if not qty_cols:
            return 0.0
        col = qty_cols[0]
        try:
            s = filtered[col].cast(pl.Float64, strict=False)
            val = s.sum()
            return float(val) if val is not None else 0.0
        except Exception:
            return 0.0
    except Exception:
        return 0.0


def get_helios_production_summary_for_item(code_article: str) -> dict:
    """Retourne une synthèse du parc en production pour un article donné à partir
    de items_parent_buildings.parquet.

    La synthèse contient :
      - code: code article normalisé
      - quantity_active: somme de quantite_fils_actif (>0)
      - active_sites: nombre de codes IG uniques où le matériel est actif
    """
    result = {
        "code": (code_article or "").strip().upper(),
        "quantity_active": 0.0,
        "active_sites": 0,
    }
    try:

        required_cols = {"code_article_fils", "quantite_fils_actif", "code_ig"}
        if not required_cols.issubset(items_parent_buildings.columns):
            return result

        norm = result["code"]
        filtered = items_parent_buildings.filter(
            (pl.col("code_article_fils") == norm)
            & (pl.col("quantite_fils_actif").cast(pl.Float64, strict=False) > 0)
        )
        if filtered.is_empty():
            return result

        grouped = (
            filtered
            .group_by(pl.col("code_article_fils"))
            .agg(
                pl.col("quantite_fils_actif").cast(pl.Float64, strict=False).sum().alias("quantity_active"),
                pl.col("code_ig").n_unique().alias("active_sites"),
            )
        )
        if grouped.height == 0:
            return result
        row = grouped.row(0, named=True)
        qa = row.get("quantity_active")
        ns = row.get("active_sites")
        result["quantity_active"] = float(qa) if qa is not None else 0.0
        result["active_sites"] = int(ns) if ns is not None else 0
        return result
    except Exception:
        return result


def get_helios_active_sites_for_item(code_article: str) -> list[dict]:
    """Retourne la liste des sites IG où l'article est actif (quantite_fils_actif > 0).

    Étapes :
      - filtre items_parent_buildings sur code_article_fils == code (exact) et quantite_fils_actif > 0
      - récupère les code_ig uniques
      - joint avec le DF helios (sur code_ig) pour enrichir avec les infos site
    """
    out: list[dict] = []
    try:
        norm = (code_article or "").strip().upper()
        if not norm:
            return out
        if 'items_parent_buildings' not in globals() or items_parent_buildings.is_empty():
            return out
        if 'helios' not in globals() or helios.is_empty():
            return out

        required_cols = {"code_article_fils", "quantite_fils_actif", "code_ig"}
        if not required_cols.issubset(items_parent_buildings.columns):
            return out

        parents_building = items_parent_buildings
        filtered = parents_building.filter(
            (pl.col("code_article_fils") == norm)
            & (pl.col("quantite_fils_actif").cast(pl.Float64, strict=False) > 0)
        )
        if filtered.is_empty():
            return out

        # Quantité active par site (code_ig)
        per_site = (
            filtered
            .group_by(pl.col("code_ig"))
            .agg(pl.col("quantite_fils_actif").cast(pl.Float64, strict=False).sum().alias("quantity_active"))
        )
        if per_site.is_empty():
            return out

        # Joindre avec helios sur code_ig (on laisse toutes les colonnes disponibles
        # pour pouvoir utiliser libelle_long_ig, adresse, code_postal, etc.)
        joined = per_site.join(helios, how="left", on="code_ig")
        for row in joined.iter_rows(named=True):
            out.append(row)
        return out
    except Exception:
        return out

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance à vol d'oiseau entre deux points GPS en kilomètres.
    
    lat1, lon1 : latitude et longitude du point 1 (en degrés décimaux)
    lat2, lon2 : latitude et longitude du point 2 (en degrés décimaux)
    """
    # Rayon moyen de la Terre en km
    R = 6371.0
    
    # Conversion des degrés en radians
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    
    # Formule du haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance

def get_available_pudo(lat, long, radius, enseignes: list[str] | None = None):
    pudos_filtered = pudos.filter(pl.col("latitude").is_not_null())
    pudos_filtered = (
        pudos_filtered
        .with_columns(
            pl.struct(["latitude", "longitude"]).map_elements(
                lambda row: haversine_distance(lat, long, row["latitude"], row["longitude"]),
                return_dtype=pl.Float32,
            ).alias("distance")
        )
        .filter(pl.col("distance") <= radius)
    )


    df = pl.DataFrame()
    if enseignes:
        if "Chronopost 9H00" in enseignes:
            df = pl.concat([df, pudos_filtered.filter(pl.col("categorie_pr_chronopost").is_in(["C9", "C9_C13"]))])
        if "Chronopost 13H00" in enseignes:
            df = pl.concat([df, pudos_filtered.filter(pl.col("categorie_pr_chronopost").is_in(["C9_C13", "C13"]))])
        if "LM2S" in enseignes:
            df = pl.concat([df, pudos_filtered.filter(pl.col("nom_prestataire") == "lm2s")])
        if "TDF" in enseignes:
            df = pl.concat([df, pudos_filtered.filter(pl.col("nom_prestataire") == "TDF")])
            
        df = df.select(pl.col("code_point_relais", "enseigne", "adresse_1", "code_postal", "ville", "categorie_pr_chronopost", "nom_prestataire", "distance", "latitude", "longitude"))

        return df
    

def get_coords_for_ig(code_ig: str):
    """
    Retourne un dict {address, latitude, longitude} pour un code IG si présent
    dans dico_helios, sinon None.
    """
    if not code_ig:
        return None
    code = code_ig.strip().upper()
    row = dico_helios.get(code)
    if not row:
        return None
    # Hypothèse: le parquet helios contient 'latitude' et 'longitude'
    lat = row.get("latitude")
    lon = row.get("longitude")
    if lat is None or lon is None:
        return None
    # Labels et adresse si disponibles
    label = row.get("code_ig", code)
    libelle_long = row.get("libelle_long_ig")
    # Utiliser strictement les colonnes demandées pour l'adresse postale
    addr1 = row.get("adresse")
    cp = row.get("code_postal")
    ville = row.get("commune")
    postal_address = None
    parts = [p for p in [addr1, cp, ville] if p]
    if parts:
        postal_address = " ".join(map(str, parts))
    return {
        "address": label,
        "latitude": float(lat),
        "longitude": float(lon),
        "libelle_long_ig": libelle_long,
        "postal_address": postal_address,
    }


def get_nearby_stores(lat: float, lon: float, radius_km: float, types: list[str] | None = None):
    """
    Retourne un DataFrame des magasins à proximité d'un point (lat, lon),
    filtrés par rayon et par type_de_depot si fourni (pied de site / laboratoire).
    Colonnes retournées: code_magasin, type_de_depot, adresse_1, adresse_2,
    code_postal, ville, distance, latitude_rigt, longitude_right
    """
    if 'stores' not in locals() and 'stores' not in globals():
        return None
    df = stores.filter(
        pl.col("latitude_right").is_not_null() & pl.col("longitude_right").is_not_null()
    ).with_columns(
        pl.struct(["latitude_right", "longitude_right"]).map_elements(
            lambda row: haversine_distance(lat, lon, float(row["latitude_right"]), float(row["longitude_right"])) ,
            return_dtype=pl.Float32,
        ).alias("distance")
    ).filter(pl.col("distance") <= float(radius_km))

    if types:
        # filtrage insensible à la casse et aux accents éventuels
        wanted = {t.strip().lower() for t in types}
        df = df.filter(pl.col("type_de_depot").str.to_lowercase().is_in(list(wanted)))

    # Normalize address columns if alternative names exist
    if "adresse_1" not in df.columns and "adresse1" in df.columns:
        df = df.with_columns(pl.col("adresse1").alias("adresse_1"))
    if "adresse_2" not in df.columns and "adresse2" in df.columns:
        df = df.with_columns(pl.col("adresse2").alias("adresse_2"))

    cols = [
        "code_magasin",
        "type_de_depot",
        "adresse_1",
        "adresse_2",
        "code_postal",
        "ville",
        "distance",
        "latitude_right",
        "longitude_right",
    ]
    existing = [c for c in cols if c in df.columns]
    return df.select(existing)


def get_store_contacts(max_items: int | None = None, query: str | None = None, depot_types: list[str] | None = None) -> list[dict]:
    """
    Construit une liste de contacts à partir de la table stores.
    Chaque élément: {"value": code_magasin, "label": "<nom/contact> - <ville> (<telephone>)"}
    Champs utilisés si présents: code_magasin, contact, nom_contact, personne_contact,
    telephone, tel, email, ville, adresse_1.
    Filtres: recherche plein texte (query) et type_de_depot (depot_types).
    """
    results: list[dict] = []
    if 'stores' not in locals() and 'stores' not in globals():
        return results
    # Normalize filters
    q = (query or "").strip().lower()
    types_set = {t.strip().lower() for t in depot_types} if depot_types else None
    # Iterate rows but cap if requested
    count = 0
    for row in stores.iter_rows(named=True):
        # Filter by type if requested
        if types_set is not None:
            tval = str(row.get("type_de_depot", "")).lower()
            if tval not in types_set:
                continue
        code = row.get("code_magasin") or row.get("code") or row.get("id")
        if code is None:
            continue
        # Try to infer contact name and phone
        contact_name = row.get("contact")
        equipe = row.get("equipe")
        responsable = row.get("nom_responsable")

        phone = row.get("tel_contact")
        email = row.get("email_contact")
        ville = row.get("ville")
        adr1 = row.get("adresse1")

        # Free text query filter across a few fields
        if q:
            hay = " ".join([
                str(code), str(contact_name or ''), str(ville or ''), str(phone or ''), str(email or ''), str(adr1 or '')
            ]).lower()
            if q not in hay:
                continue

        parts = [str(code)]
        if contact_name:
            parts.append(str(contact_name))
        if equipe:
            parts.append(str(equipe))

        label = " - ".join(parts) if parts else str(code)
        results.append({"value": str(code), "label": label})
        count += 1
        if max_items is not None and count >= max_items:
            break
    # Sort alphabetically by label
    try:
        results.sort(key=lambda x: (x.get("label") or "").casefold())
    except Exception:
        pass
    return results


def get_store_types() -> list[str]:
    """Retourne la liste triée des valeurs distinctes de type_de_depot."""
    if 'stores' not in locals() and 'stores' not in globals():
        return []
    try:
        vals = (
            stores
            .select(pl.col("type_de_depot").drop_nulls().unique())
            .to_series()
            .to_list()
        )
        return sorted([str(v) for v in vals])
    except Exception:
        # Fallback simple
        s = set()
        for row in stores.iter_rows(named=True):
            v = row.get("type_de_depot")
            if v is not None:
                s.add(str(v))
        return sorted(s)

def get_manufacturers_for(code_article: str) -> list[dict]:
    """Retourne la liste des fabricants liés à un code article si le parquet est disponible.
    Cherche une colonne de jointure plausible parmi: code_article, code, id_article.
    """
    out: list[dict] = []
    if 'manufacturers' not in globals() or manufacturers.is_empty():
        return out
    key_candidates = [
        "code_article",
        "code",
        "id_article",
        "code_article_client",
        "code_article_tdf",
        "reference",
        "ref",
        "code_fournisseur",
        "id",
    ]
    key_cols = [c for c in key_candidates if c in manufacturers.columns]
    if not key_cols:
        return out
    try:
        norm = str(code_article).strip().upper()
        seen: set[tuple] = set()
        results: list[dict] = []
        for col in key_cols:
            try:
                df = manufacturers.filter(
                    pl.col(col).cast(pl.Utf8).str.strip().str.to_uppercase() == norm
                )
                for r in df.iter_rows(named=True):
                    key = tuple(sorted(r.items()))
                    if key in seen:
                        continue
                    seen.add(key)
                    r["__matched_by"] = col
                    results.append(r)
            except Exception:
                continue
        out = results
    except Exception:
        out = []
    return out


def get_item_by_code(code_article: str) -> dict | None:
    """Retourne la ligne d'item pour un code article donné si disponible.

    La version précédente dépendait d'une liste fixe de noms de colonnes.
    Ici, on cherche dans *toutes* les colonnes en normalisant en texte/majuscule,
    ce qui permet de retrouver l'article même si la colonne a un nom différent
    (CODE_ARTICLE, code_article_tdf, reference, etc.).
    """
    if 'items' not in globals() or items.is_empty():
        return None
    try:
        norm = str(code_article).strip().upper()

        # 1) Tentative d'égalité stricte sur chaque colonne (comme avant)
        for col in items.columns:
            try:
                df = items.filter(
                    pl.col(col).cast(pl.Utf8).str.strip().str.to_uppercase() == norm
                )
                if df.height > 0:
                    row = df.row(0, named=True)
                    row["__matched_by"] = col
                    return row
            except Exception:
                continue

        # 2) Fallback: recherche plein texte (contains) sur la concat de toutes les colonnes,
        #    pour retrouver la même ligne que la recherche globale.
        try:
            df = items
            exprs = [
                pl.col(c).cast(pl.Utf8).fill_null("").str.to_uppercase()
                for c in df.columns
            ]
            hay = pl.concat_str(exprs, separator=" ").alias("__haystack")
            df2 = (
                df.with_columns(hay)
                  .filter(pl.col("__haystack").str.contains(norm))
            )
            if df2.height > 0:
                row = df2.drop("__haystack").row(0, named=True)
                row["__matched_by"] = "__haystack_contains__"
                return row
        except Exception:
            pass

        return None
    except Exception:
        return None


def get_equivalents_for(code_article: str) -> list[dict]:
    """Retourne la liste des équivalences liées à un code article si le parquet est disponible.

    Version robuste : on cherche le code normalisé dans *toutes* les colonnes du DF
    `equivalents`, en égalité stricte (après cast en texte / strip / upper).
    """
    out: list[dict] = []
    if 'equivalents' not in globals() or equivalents.is_empty():
        return out
    try:
        norm = str(code_article).strip().upper()
        seen: set[tuple] = set()
        results: list[dict] = []
        for col in equivalents.columns:
            try:
                df = equivalents.filter(
                    pl.col(col).cast(pl.Utf8).str.strip().str.to_uppercase() == norm
                )
                for r in df.iter_rows(named=True):
                    key = tuple(sorted(r.items()))
                    if key in seen:
                        continue
                    seen.add(key)
                    r["__matched_by"] = col
                    results.append(r)
            except Exception:
                continue
        out = results
    except Exception:
        out = []
    return out
    


def get_store_details(code_magasin: str) -> dict | None:
    """
    Retourne un dictionnaire de détails pour un magasin demandé.
    Clés retournées: code_magasin, libelle_magasin, equipe, responsable, contact,
    telephone, pr_principal, pr_backup, pr_hors_normes.
    Les valeurs sont récupérées depuis les colonnes disponibles avec des fallbacks.
    """
    if not code_magasin:
        return None
    row = dico_stores.get(code_magasin) if 'dico_stores' in globals() else None
    if row is None:
        # tentative de récupération via DF
        try:
            match = stores.filter(pl.col("code_magasin") == code_magasin)
            if match.height == 0:
                return None
            row = match.row(0, named=True)
        except Exception:
            return None

    def pick(keys: list[str]):
        for k in keys:
            v = row.get(k)
            if v is not None and v != "":
                return v
        return None

    resp_nom = pick(["nom_responsable"]) or ""
    resp_prenom = pick(["prenom_responsable"]) or ""
    responsable_val = ", ".join([p for p in [resp_nom, resp_prenom] if p])

    adr1 = pick(["adresse1"]) or ""
    cp = pick(["code_postal"]) or ""
    ville = pick(["ville"]) or ""
    adresse_val = " ".join([p for p in [adr1, cp, ville] if p]).strip()

    details = {
        "code_magasin": pick(["code_magasin"]),
        "libelle_magasin": pick(["libelle_magasin"]),
        "equipe": pick(["equipe"]),
        "responsable": responsable_val,
        "email_responsable": pick(["mail_responsable"]),
        "contact": pick(["contact"]),
        "telephone": pick(["tel_contact"]),
        "email": pick(["email_contact"]),
        "adresse": adresse_val,
        "code_ig": pick(["code_ig_du_tiers_emplacement"]),
        "pr_principal": pick(["pr_principal"]),
        "pr_backup": pick(["pr_backup"]),
        "pr_hors_normes": pick(["pr_hors_norme"]),
    }
    code_ig_val = details.get("code_ig")
    if code_ig_val and 'dico_helios' in globals():
        hrow = dico_helios.get(code_ig_val)
        if hrow:
            adr = hrow.get("adresse") or ""
            cp = hrow.get("code_postal") or ""
            com = hrow.get("commune") or ""
            details["adresse_ig"] = (f"{adr} {cp} {com}").strip()

    return details


def get_pudo_details(code_point_relais: str) -> dict | None:
    if not code_point_relais:
        return None
    try:
        match = pudos.filter(pl.col("code_point_relais") == code_point_relais)
        if match.height == 0:
            return None
        row = match.row(0, named=True)
    except Exception:
        return None

    def pick(keys: list[str]):
        for k in keys:
            v = row.get(k)
            if v is not None and v != "":
                return v
        return None

    return {
        "code_point_relais": pick(["code_point_relais"]),
        "enseigne": pick(["enseigne", "nom_point_relais"]),
        "adresse_1": pick(["adresse_1", "adresse1"]),
        "code_postal": pick(["code_postal"]),
        "ville": pick(["ville"]),
        "categorie": pick(["categorie_pr_chronopost", "categorie_de_point_relais"]),
        "prestataire": pick(["nom_prestataire", "code_transporteur"]),
        "statut": pick(["statut", "flag_actif"]),
        "latitude": float(pick(["latitude"])) if pick(["latitude"]) is not None else None,
        "longitude": float(pick(["longitude"])) if pick(["longitude"]) is not None else None,
    }


def list_technician_pudo_assignments() -> list[dict]:
    """Retourne une liste à plat des attributions PR par technicien.
    Une ligne par point relais associé (principal, backup, hors normes).

    Colonnes: code_magasin, technicien (si dispo), type_de_depot, pr_role,
              code_point_relais, enseigne, adresse_postale, statut
    """
    rows: list[dict] = []
    if 'stores' not in globals():
        return rows
    # Itérer sur tous les magasins/techniciens
    for srow in stores.iter_rows(named=True):
        code_magasin = srow.get("code_magasin")
        type_de_depot = srow.get("type_de_depot")
        # Nom du technicien/contact si dispo
        technicien = srow.get("contact") or srow.get("nom_contact") or srow.get("personne_contact")
        # Rôles de PR potentiels (gérer variations de noms de colonnes)
        pr_principal = srow.get("pr_principal")
        pr_backup = srow.get("pr_backup")
        pr_hn = srow.get("pr_hors_normes") if "pr_hors_normes" in srow else srow.get("pr_hors_norme")

        def add_pr(role: str, code_pr: str | None):
            if not code_pr:
                return
            p = get_pudo_details(str(code_pr))
            if not p:
                return
            adresse_postale = " ".join([str(p.get("adresse_1") or ""), str(p.get("code_postal") or ""), str(p.get("ville") or "")] ).strip()
            rows.append({
                "code_magasin": code_magasin,
                "technicien": technicien,
                "type_de_depot": type_de_depot,
                "pr_role": role,
                "code_point_relais": p.get("code_point_relais"),
                "enseigne": p.get("enseigne"),
                "adresse_postale": adresse_postale,
                "statut": p.get("statut"),
            })

        add_pr("principal", pr_principal)
        add_pr("backup", pr_backup)
        add_pr("hors_normes", pr_hn)
    return rows


def search_items(query: str | None, max_rows: int = 200) -> pl.DataFrame | None:
    """
    Recherche plein texte dans la table items (items.parquet) sur l'ensemble des colonnes.
    - query: texte recherché (insensible à la casse)
    - max_rows: limite de lignes retournées
    Retourne un DataFrame Polars (éventuellement vide) ou None si items indisponible.
    """
    if 'items' not in globals():
        return None
    q = (query or '').strip().lower()
    if not q:
        return pl.DataFrame()
    df = items
    try:
        exprs = [pl.col(c).cast(pl.Utf8).fill_null("").str.to_lowercase() for c in df.columns]
        hay = pl.concat_str(exprs, separator=" ").alias("__haystack")
        out = (
            df.with_columns(hay)
              .filter(pl.col("__haystack").str.contains(q))
              .drop("__haystack")
              .head(max_rows)
        )
        return out
    except Exception:
        # Fallback très simple: pas de filtre, retourne vide
        return pl.DataFrame()


def get_items_columns() -> list[str]:
    """Retourne la liste des colonnes disponibles dans items, ou une liste vide."""
    if 'items' not in globals():
        return []
    try:
        return list(items.columns)
    except Exception:
        return []


def search_items_advanced(global_query: str | None, col_filters: dict[str, str] | None, max_rows: int = 300) -> pl.DataFrame | None:
    """
    Recherche avancée dans items:
      - global_query: recherche plein texte sur toutes les colonnes (insensible case)
      - col_filters: dict {col -> valeur} appliqué par 'contains' insensible case, ignoré si valeur vide
    """
    if 'items' not in globals():
        return None
    df = items
    try:
        # Build filter expressions
        filters = []
        gq = (global_query or '').strip().lower()
        if gq:
            exprs = [pl.col(c).cast(pl.Utf8).fill_null("").str.to_lowercase() for c in df.columns]
            hay = pl.concat_str(exprs, separator=" ").alias("__haystack")
            df = df.with_columns(hay)
            filters.append(pl.col("__haystack").str.contains(gq))
        if col_filters:
            for col, val in col_filters.items():
                if not val:
                    continue
                if col in df.columns:
                    filters.append(
                        pl.col(col).cast(pl.Utf8).fill_null("").str.to_lowercase().str.contains(val.strip().lower())
                    )
        if filters:
            combined = filters[0]
            for f in filters[1:]:
                combined = combined & f
            df = df.filter(combined)
        if "__haystack" in df.columns:
            df = df.drop("__haystack")
        return df.head(max_rows)
    except Exception:
        return pl.DataFrame()
