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
    nomenclatures = pl.read_parquet(os.path.join(path_datan, folder_name_app, "nomenclatures.parquet"))
    manufacturers = pl.read_parquet(os.path.join(path_datan, folder_name_app, "manufacturers.parquet"))
    equivalents = pl.read_parquet(os.path.join(path_datan, folder_name_app, "equivalents.parquet"))
    stats_exit = pl.read_parquet(os.path.join(path_datan, folder_name_app, "stats_exit.parquet"))
    try:
        stats_exit = stats_exit.with_columns(pl.col("date_mvt").dt.year().alias("annee"))
    except Exception:
        # si la colonne date_mvt n'existe pas ou n'est pas de type date/temps, on laisse stats_exit tel quel
        pass
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
    try:
        stats_exit = pl.read_parquet(os.path.join(path_datan, folder_name_app, "stats_exit.parquet"))
        try:
            stats_exit = stats_exit.with_columns(pl.col("date_mvt").dt.year().alias("annee"))
        except Exception:
            # si la colonne date_mvt n'existe pas ou n'est pas de type date/temps, on laisse stats_exit tel quel
            pass
    except FileNotFoundError:
        stats_exit = pl.DataFrame()

# Dictionnaires utiles (magasins/helios)
dico_stores = {row["code_magasin"]: row for row in stores.iter_rows(named=True)} if 'stores' in locals() else {}
dico_helios = {row["code_ig"]: row for row in helios.iter_rows(named=True)} if 'helios' in locals() else {}


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


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
    if not code_ig:
        return None
    code = code_ig.strip().upper()
    row = dico_helios.get(code)
    if not row:
        return None
    lat = row.get("latitude")
    lon = row.get("longitude")
    if lat is None or lon is None:
        return None
    label = row.get("code_ig", code)
    libelle_long = row.get("libelle_long_ig")
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
        wanted = {t.strip().lower() for t in types}
        df = df.filter(pl.col("type_de_depot").str.to_lowercase().is_in(list(wanted)))

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
    results: list[dict] = []
    if 'stores' not in locals() and 'stores' not in globals():
        return results
    q = (query or "").strip().lower()
    types_set = {t.strip().lower() for t in depot_types} if depot_types else None
    count = 0
    for row in stores.iter_rows(named=True):
        if types_set is not None:
            tval = str(row.get("type_de_depot", "")).lower()
            if tval not in types_set:
                continue
        code = row.get("code_magasin") or row.get("code") or row.get("id")
        if code is None:
            continue
        contact_name = row.get("contact")
        equipe = row.get("equipe")
        responsable = row.get("nom_responsable")

        phone = row.get("tel_contact")
        email = row.get("email_contact")
        ville = row.get("ville")
        adr1 = row.get("adresse1")

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
    try:
        results.sort(key=lambda x: (x.get("label") or "").casefold())
    except Exception:
        pass
    return results


def get_store_types() -> list[str]:
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
        s = set()
        for row in stores.iter_rows(named=True):
            v = row.get("type_de_depot")
            if v is not None:
                s.add(str(v))
        return sorted(s)


def get_manufacturers_for(code_article: str) -> list[dict]:
    out: list[dict] = []
    #if 'manufacturers' not in globals() or manufacturers.is_empty():
        #return out
    key_cols = [c for c in ["code_article"] if c in manufacturers.columns]
    if not key_cols:
        return out
    try:
        norm = str(code_article).strip().upper()
        df = manufacturers.filter(pl.any_horizontal([
            pl.col(c) == norm
            for c in key_cols
        ]))
        out = [r for r in df.iter_rows(named=True)]
    except Exception:
        out = []
    return out


def get_item_by_code(code_article: str) -> dict | None:
    if 'items' not in globals() or items.is_empty():
        return None
    key_cols = [c for c in ["code_article", "code", "id_article"] if c in items.columns]
    if not key_cols:
        return None
    try:
        norm = str(code_article).strip().upper()
        df = items.filter(pl.any_horizontal([
            pl.col(c).cast(pl.Utf8).str.strip().str.to_uppercase() == norm
            for c in key_cols
        ]))
        if df.height == 0:
            return None
        return df.row(0, named=True)
    except Exception:
        return None


def get_equivalents_for(code_article: str) -> list[dict]:
    """Retourne les lignes d'équivalence pour un code article.

    Règle métier simple :
      - filtrer equivalents sur la colonne "code_article" == code_article fourni
      - renvoyer les lignes telles quelles (plus un champ __matched_by pour info)
    """
    if 'equivalents' not in globals() or equivalents.is_empty():
        return []

    try:
        df = equivalents.filter(pl.col("code_article") == code_article)
    except Exception:
        return []

    # Enrichir avec le libellé de chaque code_article_correspondant depuis items
    try:
        if 'items' in globals() and not items.is_empty() and "code_article_correspondant" in df.columns:
            if "code_article" in items.columns and "libelle_court_article" in items.columns:
                df_items = items.select(
                    [
                        pl.col("code_article").alias("code_article_correspondant"),
                        pl.col("libelle_court_article").alias("libelle_court_article_correspondant"),
                    ]
                )
                df = df.join(df_items, on="code_article_correspondant", how="left")
    except Exception:
        # en cas de problème de join, on garde df tel quel
        pass

    results: list[dict] = []
    seen: set[tuple] = set()

    for r in df.iter_rows(named=True):
        key = tuple(sorted(r.items()))
        if key in seen:
            continue
        seen.add(key)
        r["__matched_by"] = "code_article"
        results.append(r)

    return results


def get_store_details(code_magasin: str) -> dict | None:
    if not code_magasin:
        return None
    row = dico_stores.get(code_magasin) if 'dico_stores' in globals() else None
    if row is None:
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
            # Exposer le libellé long IG pour l'affichage dans le frontend technicien
            details["libelle_long_ig"] = hrow.get("libelle_long_ig")

    return details


def list_technician_pudo_assignments() -> list[dict]:
    rows: list[dict] = []
    if 'stores' not in globals():
        return rows
    for srow in stores.iter_rows(named=True):
        code_magasin = srow.get("code_magasin")
        type_de_depot = srow.get("type_de_depot")
        technicien = srow.get("contact") or srow.get("nom_contact") or srow.get("personne_contact")
        equipe = srow.get("equipe")
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
                "equipe": equipe,
                "technicien": technicien,
                "type_de_depot": type_de_depot,
                "pr_role": role,
                "code_point_relais": p.get("code_point_relais"),
                "enseigne": p.get("enseigne"),
                "adresse_postale": p.get("adresse_postale") if p.get("adresse_postale") else adresse_postale,
                "statut": p.get("statut"),
                "categorie": p.get("categorie"),
                "prestataire": p.get("prestataire"),
            })

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

        add_pr("principal", pr_principal)
        add_pr("backup", pr_backup)
        add_pr("hors_normes", pr_hn)
    return rows


def search_items(query: str | None, max_rows: int = 200) -> pl.DataFrame | None:
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
        return pl.DataFrame()


def get_items_columns() -> list[str]:
    if 'items' not in globals():
        return []
    try:
        return list(items.columns)
    except Exception:
        return []


def search_items_advanced(global_query: str | None, col_filters: dict[str, str] | None, max_rows: int = 300) -> pl.DataFrame | None:
    if 'items' not in globals():
        return None
    df = items

    # Intégrer les informations fournisseurs dans la recherche globale si disponibles
    try:
        if 'manufacturers' in globals() and not manufacturers.is_empty() and "code_article" in manufacturers.columns and "code_article" in df.columns:
            mf = manufacturers
            text_cols = [c for c in mf.columns if c != "code_article"]
            if text_cols:
                mf_tmp = mf.select(
                    [
                        pl.col("code_article"),
                        *[pl.col(c).cast(pl.Utf8).fill_null("").str.to_lowercase().alias(c) for c in text_cols],
                    ]
                )
                mf_tmp = mf_tmp.with_columns(
                    pl.concat_str([pl.col(c) for c in text_cols], separator=" ").alias("__mf_text")
                )
                mf_agg = (
                    mf_tmp
                    .group_by("code_article")
                    .agg(pl.col("__mf_text").str.concat(" "))
                    .select(["code_article", pl.col("__mf_text").alias("__mf_text_suppliers")])
                )
                df = df.join(mf_agg, on="code_article", how="left")
    except Exception:
        pass
    try:
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


def stats_exit_items(item_code: str, type_exit: str | list[str] | None = None) -> pl.DataFrame:
    if 'stats_exit' not in globals():
        return pl.DataFrame()
    df = stats_exit
    try:
        expr = pl.col("code_article") == item_code
        if type_exit is not None:
            if isinstance(type_exit, list):
                values = [v for v in type_exit if v is not None]
            else:
                values = [type_exit]
            if values:
                expr = expr & pl.col("lib_motif_mvt").is_in(values)
        out = (
            df.filter(expr)
              .group_by(pl.col("annee"))
              .agg(pl.col("qte_mvt").sum())
              .sort(pl.col("annee"))
        )
        return out
    except Exception:
        return pl.DataFrame()
