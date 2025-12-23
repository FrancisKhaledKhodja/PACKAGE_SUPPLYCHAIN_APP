import os
import datetime
import re
from math import radians, sin, cos, sqrt, atan2
import polars as pl
from supplychain_app.constants import (
    path_datan,
    folder_bdd_python,
    folder_pudo,
    folder_name_app,
    CHOIX_PR_TECH_DIR,
    CHOIX_PR_TECH_FILE,
)

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

try:
    items_parent_buildings = pl.read_parquet(os.path.join(path_datan, folder_name_app, "items_parent_buildings.parquet"))
except FileNotFoundError:
    items_parent_buildings = pl.DataFrame()

try:
    items_son_buildings = pl.read_parquet(os.path.join(path_datan, folder_name_app, "items_son_buildings.parquet"))
except FileNotFoundError:
    items_son_buildings = pl.DataFrame()

# Dictionnaires utiles (magasins/helios)
dico_stores = {row["code_magasin"]: row for row in stores.iter_rows(named=True)} if 'stores' in locals() else {}
dico_helios = {row["code_ig"]: row for row in helios.iter_rows(named=True)} if 'helios' in locals() else {}

# Cache en mémoire pour certaines listes calculées une fois
_ol_igs_cache: list[dict] | None = None

_distance_tech_pr_df: pl.DataFrame | None = None
_distance_tech_pr_mtime: float | None = None


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


def _get_col_name(df: pl.DataFrame, candidates: list[str]) -> str | None:
    if df is None:
        return None
    cols = list(df.columns)
    lower_map = {str(c).strip().lower(): str(c) for c in cols}
    for cand in candidates:
        key = str(cand).strip().lower()
        if key in lower_map:
            return lower_map[key]
    return None


def _load_distance_tech_pr_df(force: bool = False) -> pl.DataFrame | None:
    global _distance_tech_pr_df, _distance_tech_pr_mtime
    path = os.path.join(path_datan, folder_name_app, "distance_tech_pr.parquet")
    if not os.path.exists(path):
        alt = os.path.join(path_datan, folder_bdd_python, folder_pudo, "GESTION_PR", "ANALYSES", "distance_tech_pr.parquet")
        if os.path.exists(alt):
            path = alt
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        _distance_tech_pr_df = pl.DataFrame()
        _distance_tech_pr_mtime = None
        return _distance_tech_pr_df

    if (not force) and _distance_tech_pr_df is not None and _distance_tech_pr_mtime == mtime:
        return _distance_tech_pr_df

    try:
        _distance_tech_pr_df = pl.read_parquet(path)
        _distance_tech_pr_mtime = mtime
        return _distance_tech_pr_df
    except Exception:
        _distance_tech_pr_df = pl.DataFrame()
        _distance_tech_pr_mtime = mtime
        return _distance_tech_pr_df


def get_distance_tech_pr_for_store(code_magasin: str, code_pr: str | None = None, limit: int | None = None) -> pl.DataFrame:
    df = _load_distance_tech_pr_df(force=False)
    if df is None or df.is_empty():
        return pl.DataFrame()

    store_col = _get_col_name(df, ["code_magasin", "store", "magasin", "code_store", "code_tech", "technicien", "tech"])
    if not store_col:
        return pl.DataFrame()

    sub = df
    try:
        sub = sub.filter(pl.col(store_col).cast(pl.Utf8).str.strip_chars() == str(code_magasin).strip())
    except Exception:
        return pl.DataFrame()

    if code_pr:
        pr_col = _get_col_name(df, ["code_point_relais", "code_pr", "pr", "code_pudo", "code_pointrelais"])
        if pr_col:
            try:
                sub = sub.filter(pl.col(pr_col).cast(pl.Utf8).str.strip_chars() == str(code_pr).strip())
            except Exception:
                pass

    sort_col = _get_col_name(sub, ["distance", "distance_m", "distance_km", "distance_kilometres", "km"])
    if sort_col:
        try:
            sub = sub.sort(pl.col(sort_col).cast(pl.Float64), descending=False, nulls_last=True)
        except Exception:
            try:
                sub = sub.sort(pl.col(sort_col), descending=False)
            except Exception:
                pass

    if limit is not None:
        try:
            lim = int(limit)
        except Exception:
            lim = None
        if lim is not None and lim > 0:
            sub = sub.head(lim)

    return sub


def get_available_pudo(lat, long, radius, enseignes: list[str] | None = None):
    pudos_filtered = pudos.filter(pl.col("latitude").is_not_null())
    pudos_filtered = (
        pudos_filtered
        .with_columns(
            pl.struct(["latitude", "longitude"]).map_elements(
                lambda row: haversine_distance(
                    float(lat),
                    float(long),
                    float(row["latitude"]),
                    float(row["longitude"]),
                ),
                return_dtype=pl.Float32,
            ).alias("distance")
        )
        .filter(pl.col("distance") <= float(radius))
    )

    df = pl.DataFrame()
    if enseignes:
        # Normaliser les valeurs demandées (insensible à la casse)
        wanted = {e.strip().lower() for e in enseignes if e}

        # Préparer des colonnes en minuscules pour les comparaisons texte
        pudos_lc = pudos_filtered.with_columns([
            pl.col("categorie_pr_chronopost").cast(pl.Utf8).str.to_lowercase().alias("_cat_lc"),
            pl.col("nom_prestataire").cast(pl.Utf8).str.to_lowercase().alias("_prest_lc"),
        ])

        if "chronopost 9h00" in wanted:
            df = pl.concat([
                df,
                pudos_lc.filter(pl.col("_cat_lc").is_in(["c9", "c9_c13"]))
            ])
        if "chronopost 13h00" in wanted:
            df = pl.concat([
                df,
                pudos_lc.filter(pl.col("_cat_lc").is_in(["c9_c13", "c13"]))
            ])
        if "lm2s" in wanted:
            df = pl.concat([
                df,
                pudos_lc.filter(pl.col("_prest_lc") == "lm2s")
            ])
        if "tdf" in wanted:
            df = pl.concat([
                df,
                pudos_lc.filter(pl.col("_prest_lc") == "tdf")
            ])

        if not df.is_empty():
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
        # Ne conserver que les magasins avec statut == 0
        statut = row.get("statut")
        if statut is not None:
            try:
                if int(statut) != 0:
                    continue
            except (TypeError, ValueError):
                # Si le statut n'est pas convertible en entier, on l'exclut par sécurité
                continue
        code = row.get("code_magasin") or row.get("code") or row.get("id")
        if code is None:
            continue
        libelle_magasin = row.get("libelle_magasin")
        contact_name = row.get("contact") or row.get("nom_contact") or row.get("personne_contact")
        equipe = row.get("equipe")
        responsable = row.get("nom_responsable")

        phone = row.get("tel_contact")
        email = row.get("email_contact")
        ville = row.get("ville")
        adr1 = row.get("adresse1")

        if q:
            hay = " ".join([
                str(code), str(libelle_magasin or ''), str(contact_name or ''), str(ville or ''), str(phone or ''), str(email or ''), str(adr1 or '')
            ]).lower()
            if q not in hay:
                continue

        parts = [str(code)]
        if libelle_magasin:
            parts.append(str(libelle_magasin))

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


def get_ol_technicians() -> list[dict]:
    """Retourne la liste des techniciens éligibles pour l'OL mode dégradé.

    Source : stores.parquet
    Filtre : type_de_depot ∈ {"REO", "EMBARQUE", "EXPERT"}
    """
    results: list[dict] = []
    if "stores" not in globals() and "stores" not in locals():
        return results

    allowed_types = {"reo", "embarque", "expert"}

    # On agrège par code_magasin pour avoir une entrée par technicien
    seen: dict[str, dict] = {}
    for row in stores.iter_rows(named=True):
        # Ne conserver que les techniciens dont le magasin a statut == 0
        statut = row.get("statut")
        if statut is not None:
            try:
                if int(statut) != 0:
                    continue
            except (TypeError, ValueError):
                # Si le statut n'est pas convertible en entier, on l'exclut par sécurité
                continue

        ttype = str(row.get("type_de_depot") or "").strip().lower()
        if ttype not in allowed_types:
            continue

        code_magasin = row.get("code_magasin")
        if not code_magasin:
            continue

        contact = row.get("contact") or row.get("nom_contact") or row.get("personne_contact")
        tel = row.get("tel_contact")
        email = row.get("email_contact")
        libelle_magasin = row.get("libelle_magasin")
        equipe = row.get("equipe")

        adr1 = row.get("adresse1") or ""
        cp = row.get("code_postal") or ""
        ville = row.get("ville") or ""
        adresse = " ".join([str(adr1), str(cp), str(ville)]).strip()

        code_ig = row.get("code_ig_du_tiers_emplacement")
        pr_principal = row.get("pr_principal")
        pr_backup = row.get("pr_backup")
        pr_hn = row.get("pr_hors_normes") if "pr_hors_normes" in row else row.get("pr_hors_norme")

        # Code tiers Daher du technicien (si colonne disponible dans le parquet)
        code_tiers = row.get("code_tiers_daher") or row.get("code_tiers") or None

        key = str(code_magasin)
        if key not in seen:
            seen[key] = {
                "code_magasin": code_magasin,
                "libelle_magasin": libelle_magasin,
                "type_de_depot": row.get("type_de_depot"),
                "contact": contact,
                "telephone": tel,
                "email": email,
                "adresse": adresse,
                "equipe": equipe,
                "code_ig": code_ig,
                "pr_principal": pr_principal,
                "pr_backup": pr_backup,
                "pr_hors_normes": pr_hn,
                "code_tiers_daher": code_tiers,
            }

    results = list(seen.values())
    try:
        results.sort(key=lambda r: (str(r.get("contact") or "") + " " + str(r.get("code_magasin") or "")).casefold())
    except Exception:
        pass
    return results


def get_pudo_postal_address(code_point_relais: str) -> dict | None:
    """Retourne l'adresse postale d'un point relais identifié par son code.

    La réponse contient au minimum : code_point_relais, enseigne, adresse_postale.
    """
    if not code_point_relais:
        return None
    if "pudos" not in globals() and "pudos" not in locals():
        return None
    try:
        df = pudos
        match = df.filter(pl.col("code_point_relais") == code_point_relais)
        if match.height == 0:
            return None
        row = match.row(0, named=True)

        def pick(keys: list[str]):
            for k in keys:
                if k in row:
                    v = row.get(k)
                    if v is not None and v != "":
                        return v
            return None

        adr1 = pick(["adresse_postale", "adresse_1", "adresse1"]) or ""
        cp = pick(["code_postal"]) or ""
        ville = pick(["ville"]) or ""
        adresse_postale = " ".join([str(adr1), str(cp), str(ville)]).strip()

        return {
            "code_point_relais": pick(["code_point_relais"]),
            "enseigne": pick(["enseigne", "nom_point_relais"]),
            "adresse_postale": adresse_postale,
        }
    except Exception:
        return None


def get_ol_igs() -> list[dict]:
    """Retourne la liste des codes IG utilisables pour l'OL mode dégradé.

    Source : helios.parquet (via la variable globale helios / dico_helios).
    """
    global _ol_igs_cache

    # Si déjà calculé, on renvoie directement le cache
    if _ol_igs_cache is not None:
        return _ol_igs_cache

    results: list[dict] = []
    if "helios" not in globals() and "helios" not in locals():
        return results
    try:
        df = helios
    except Exception:
        return results

    try:
        for row in df.iter_rows(named=True):
            code_ig = row.get("code_ig") or row.get("code_ig_du_tiers_emplacement")
            if not code_ig:
                continue
            libelle = row.get("libelle_long_ig") or row.get("libelle_ig") or ""
            adr = row.get("adresse") or ""
            cp = row.get("code_postal") or ""
            com = row.get("commune") or row.get("ville") or ""
            adresse_postale = " ".join([str(adr), str(cp), str(com)]).strip()
            results.append({
                "code_ig": code_ig,
                "libelle_long_ig": libelle,
                "adresse_postale": adresse_postale,
            })
        try:
            results.sort(key=lambda r: str(r.get("code_ig") or "").casefold())
        except Exception:
            pass
        _ol_igs_cache = results
        return results
    except Exception:
        return []


def search_ol_igs(query: str | None = None, limit: int = 50) -> list[dict]:
    """Recherche d'IG pour l'OL mode dégradé, avec filtrage texte et limite.

    La recherche s'effectue sur le code IG et le libellé long, en insensible à la casse.
    Les données de base proviennent de get_ol_igs() et donc du cache en mémoire.
    """
    rows = get_ol_igs() or []
    try:
        lim = int(limit)
    except Exception:
        lim = 50
    if lim <= 0:
        lim = 1
    if lim > 500:
        lim = 500

    q = (query or "").strip().lower()
    if not q:
        return rows[:lim]

    out: list[dict] = []
    for r in rows:
        code = str(r.get("code_ig") or "").lower()
        lib = str(r.get("libelle_long_ig") or "").lower()
        if q in code or q in lib:
            out.append(r)
            if len(out) >= lim:
                break
    return out


def get_ol_stores() -> list[dict]:
    """Retourne les magasins éligibles pour l'expédition OL (type NATIONAL ou LOCAL).

    Chaque entrée contient au minimum : code_magasin, type_de_depot, adresse_postale.
    """
    results: list[dict] = []
    if "stores" not in globals() and "stores" not in locals():
      return results

    allowed = {"national", "local"}
    try:
        for row in stores.iter_rows(named=True):
            tdep = str(row.get("type_de_depot") or "").strip().lower()
            if tdep not in allowed:
                continue
            code_magasin = row.get("code_magasin")
            if not code_magasin:
                continue

            def pick(keys: list[str]):
                for k in keys:
                    if k in row:
                        v = row.get(k)
                        if v is not None and v != "":
                            return v
                return None

            adr1 = pick(["adresse_postale", "adresse_1", "adresse1", "adresse"]) or ""
            adr2 = pick(["adresse_2", "adresse2"]) or ""
            cp = pick(["code_postal"]) or ""
            ville = pick(["ville"]) or ""
            adresse_postale = " ".join([str(adr1), str(cp), str(ville)]).strip()

            # Code tiers Daher (si colonne disponible dans le parquet)
            code_tiers = row.get("code_tiers_daher") or row.get("code_tiers") or None

            results.append({
                "code_magasin": code_magasin,
                "libelle_magasin": row.get("libelle_magasin"),
                "type_de_depot": row.get("type_de_depot"),
                "adresse_postale": adresse_postale,
                "adresse1": adr1,
                "adresse2": adr2,
                "code_postal": cp,
                "ville": ville,
                "statut": row.get("statut"),
                "code_tiers_daher": code_tiers,
            })
        # dédoublonnage par code_magasin
        uniq: dict[str, dict] = {}
        for r in results:
            uniq[str(r.get("code_magasin"))] = r
        results = list(uniq.values())
        try:
            results.sort(key=lambda r: str(r.get("code_magasin") or "").casefold())
        except Exception:
            pass
        return results
    except Exception:
        return []


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
    try:
        norm = str(code_article).strip().upper()

        if "code_article" in items.columns:
            try:
                df = items.filter(pl.col("code_article").cast(pl.Utf8).str.strip_chars().str.to_uppercase() == norm)
                if df.height > 0:
                    row = df.row(0, named=True)
                    row["__matched_by"] = "code_article"
                    return row
            except Exception:
                pass

        # 1) Tentative d'égalité stricte sur toutes les colonnes
        for col in items.columns:
            try:
                if col == "code_article":
                    continue
                df = items.filter(
                    pl.col(col).cast(pl.Utf8).str.strip_chars().str.to_uppercase() == norm
                )
                if df.height > 0:
                    row = df.row(0, named=True)
                    row["__matched_by"] = col
                    return row
            except Exception:
                continue

        # 2) Fallback: recherche plein texte (contains) sur concat de toutes les colonnes
        try:
            df = items
            exprs = [
                pl.col(c).cast(pl.Utf8).fill_null("").str.to_uppercase()
                for c in df.columns
            ]
            hay = pl.concat_str(exprs, separator=" ").alias("__haystack")
            df2 = df.with_columns(hay).filter(pl.col("__haystack").str.contains(norm))
            if df2.height > 0:
                row = df2.drop("__haystack").row(0, named=True)
                row["__matched_by"] = "__haystack_contains__"
                return row
        except Exception:
            pass

        return None
    except Exception:
        return None


def get_item_by_code_strict(code_article: str) -> dict | None:
    if 'items' not in globals() or items.is_empty():
        return None
    try:
        norm = str(code_article).strip().upper()
        if not norm:
            return None

        if "code_article" not in items.columns:
            return None

        df = items.filter(pl.col("code_article").cast(pl.Utf8).str.strip_chars().str.to_uppercase() == norm)
        if df.height <= 0:
            return None
        row = df.row(0, named=True)
        row["__matched_by"] = "code_article_strict"
        return row
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


def get_pudo_directory() -> list[dict]:
    """
    Retourne une liste de points relais pour alimenter les listes déroulantes.

    Chaque élément contient au minimum :
      - code_point_relais
      - enseigne
      - ville
      - label (code - enseigne - ville)
    """
    if "pudos" not in globals() or pudos.is_empty():
        return []

    cols = []
    for c in [
        "code_point_relais",
        "enseigne",
        "ville",
        "adresse_1",
        "code_postal",
        "statut",
        "categorie_pr_chronopost",
        "nom_prestataire",
        "latitude",
        "longitude",
    ]:
        if c in pudos.columns:
            cols.append(c)

    try:
        extra_cols = [c for c in pudos.columns if "fermet" in str(c).lower()]
        for c in extra_cols:
            if c not in cols:
                cols.append(c)
    except Exception:
        pass
    df = pudos.select(cols)

    rows: list[dict] = []
    for r in df.iter_rows(named=True):
        code = str(r.get("code_point_relais") or "").strip()
        if not code:
            continue
        enseigne = str(r.get("enseigne") or "")
        ville = str(r.get("ville") or "")
        label_parts = [code]
        if enseigne:
            label_parts.append(enseigne)
        if ville:
            label_parts.append(ville)
        r["label"] = " - ".join(label_parts)
        rows.append(r)
    return rows


def _ensure_choix_pr_dir():
    if not os.path.isdir(CHOIX_PR_TECH_DIR):
        os.makedirs(CHOIX_PR_TECH_DIR, exist_ok=True)


def _load_pr_overrides_df() -> pl.DataFrame:
    _ensure_choix_pr_dir()
    path = os.path.join(CHOIX_PR_TECH_DIR, CHOIX_PR_TECH_FILE)
    if not os.path.exists(path):
        return pl.DataFrame(
            schema={
                "code_magasin": pl.Utf8,
                "pr_role": pl.Utf8,
                "code_point_relais_override": pl.Utf8,
                "commentaire": pl.Utf8,
                "date_commentaire": pl.Utf8,
            }
        )
    try:
        return pl.read_parquet(path)
    except Exception:
        return pl.DataFrame(
            schema={
                "code_magasin": pl.Utf8,
                "pr_role": pl.Utf8,
                "code_point_relais_override": pl.Utf8,
                "commentaire": pl.Utf8,
                "date_commentaire": pl.Utf8,
            }
        )


def _save_pr_overrides_df(df: pl.DataFrame) -> None:
    _ensure_choix_pr_dir()
    path = os.path.join(CHOIX_PR_TECH_DIR, CHOIX_PR_TECH_FILE)
    df.write_parquet(path)


def get_pr_overrides_for_store(code_magasin: str) -> dict:
    if not code_magasin:
        return {"principal": None, "backup": None, "hors_normes": None}

    df = _load_pr_overrides_df()
    if df.is_empty():
        return {"principal": None, "backup": None, "hors_normes": None}

    try:
        sub = df.filter(pl.col("code_magasin") == str(code_magasin))
    except Exception:
        return {"principal": None, "backup": None, "hors_normes": None}

    out = {"principal": None, "backup": None, "hors_normes": None}
    for row in sub.iter_rows(named=True):
        role = str(row.get("pr_role") or "")
        if role not in out:
            continue
        out[role] = {
            "code": row.get("code_point_relais_override"),
            "commentaire": row.get("commentaire"),
            "date_commentaire": row.get("date_commentaire"),
        }
    return out


def save_pr_overrides_for_store(code_magasin: str, payload: dict) -> dict:
    if not code_magasin:
        return {"error": "code_magasin is required"}

    df = _load_pr_overrides_df()
    try:
        df = df.filter(pl.col("code_magasin") != str(code_magasin))
    except Exception:
        df = pl.DataFrame(
            schema={
                "code_magasin": pl.Utf8,
                "pr_role": pl.Utf8,
                "code_point_relais_override": pl.Utf8,
                "commentaire": pl.Utf8,
                "date_commentaire": pl.Utf8,
            }
        )

    rows = []
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for role in ["principal", "backup", "hors_normes"]:
        conf = payload.get(role) if isinstance(payload, dict) else None
        if not conf:
            continue
        code = (conf.get("code") or "").strip()
        commentaire = (conf.get("commentaire") or "").strip()
        if not code and not commentaire:
            continue
        rows.append(
            {
                "code_magasin": str(code_magasin),
                "pr_role": role,
                "code_point_relais_override": code or None,
                "commentaire": commentaire or None,
                "date_commentaire": now_str,
            }
        )

    if rows:
        df_new = pl.DataFrame(rows)
        df = pl.concat([df, df_new], how="vertical")

    _save_pr_overrides_df(df)
    return get_pr_overrides_for_store(code_magasin)


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
    adr2 = pick(["adresse2"]) or ""
    cp = pick(["code_postal"]) or ""
    ville = pick(["ville"]) or ""
    adresse_val = " ".join([p for p in [adr1, adr2, cp, ville] if p]).strip()

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
        "pr_hors_normes": pick(["pr_hors_normes"]) if "pr_hors_normes" in row else pick(["pr_hors_norme"]),
    }
    code_ig_val = details.get("code_ig")
    if code_ig_val:
        norm_code_ig = str(code_ig_val).strip().upper()
        is_pudo_style = bool(re.fullmatch(r"S\d{4}", norm_code_ig))

        if is_pudo_style and ("pudos" in globals() or "pudos" in locals()):
            try:
                match = pudos.filter(pl.col("code_point_relais") == norm_code_ig)
                if match.height > 0:
                    prow = match.row(0, named=True)
                    def _pick_pr(keys: list[str]):
                        for k in keys:
                            v = prow.get(k)
                            if v is not None and v != "":
                                return v
                        return None

                    adr = _pick_pr(["adresse_postale", "adresse_1", "adresse1"]) or ""
                    cp = _pick_pr(["code_postal"]) or ""
                    ville = _pick_pr(["ville"]) or ""
                    details["adresse_ig"] = " ".join([str(x) for x in [adr, cp, ville] if x]).strip()
                    details["libelle_long_ig"] = _pick_pr(["enseigne", "raison_sociale", "nom_point_relais"]) or details.get("libelle_long_ig")
            except Exception:
                pass

        if "adresse_ig" not in details and 'dico_helios' in globals():
            hrow = dico_helios.get(norm_code_ig)
            if hrow:
                adr = hrow.get("adresse") or ""
                cp = hrow.get("code_postal") or ""
                com = hrow.get("commune") or ""
                details["adresse_ig"] = (f"{adr} {cp} {com}").strip()
                details["libelle_long_ig"] = hrow.get("libelle_long_ig")

        if "adresse_ig" not in details:
            details["adresse_ig"] = (
                f"Aucune adresse trouvée pour le code IG {norm_code_ig} (ce code n'existe pas ou n'existe plus)."
            )

    return details


def list_technician_pudo_assignments() -> list[dict]:
    rows: list[dict] = []
    if 'stores' not in globals():
        return rows

    overrides_df = _load_pr_overrides_df()

    for srow in stores.iter_rows(named=True):
        # Ne conserver que les magasins avec statut == 0
        statut = srow.get("statut")
        if statut is not None:
            try:
                if int(statut) != 0:
                    continue
            except (TypeError, ValueError):
                # Si le statut n'est pas convertible en entier, on l'exclut par sécurité
                continue
        code_magasin = srow.get("code_magasin")
        type_de_depot = srow.get("type_de_depot")
        technicien = srow.get("contact") or srow.get("nom_contact") or srow.get("personne_contact")
        equipe = srow.get("equipe")
        pr_principal = srow.get("pr_principal")
        pr_backup = srow.get("pr_backup")
        pr_hn = srow.get("pr_hors_normes") if "pr_hors_normes" in srow else srow.get("pr_hors_norme")

        override_map = {"principal": None, "backup": None, "hors_normes": None}
        if not overrides_df.is_empty() and code_magasin:
            try:
                sub = overrides_df.filter(pl.col("code_magasin") == str(code_magasin))
                for orow in sub.iter_rows(named=True):
                    role = str(orow.get("pr_role") or "")
                    if role not in override_map:
                        continue
                    code = (orow.get("code_point_relais_override") or "")
                    code = str(code).strip() if code is not None else ""
                    override_map[role] = code or None
            except Exception:
                override_map = {"principal": None, "backup": None, "hors_normes": None}

        def add_pr(role: str, code_pr: str | None):
            if not code_pr:
                return
 
            store_code_pr = str(code_pr)
            effective_code = override_map.get(role) or store_code_pr
 
            p = get_pudo_details(str(effective_code))
            adresse_postale = ""
            if p:
                adresse_postale = " ".join([
                    str(p.get("adresse_1") or ""),
                    str(p.get("code_postal") or ""),
                    str(p.get("ville") or ""),
                ]).strip()
            rows.append({
                "code_magasin": code_magasin,
                "equipe": equipe,
                "technicien": technicien,
                "type_de_depot": type_de_depot,
                "pr_role": role,
                "code_point_relais_store": store_code_pr,
                "code_point_relais": (p.get("code_point_relais") if p else str(effective_code)),
                "enseigne": (p.get("enseigne") if p else None),
                "adresse_postale": (p.get("adresse_postale") if p and p.get("adresse_postale") else adresse_postale) or None,
                "statut": (p.get("statut") if p else None),
                "categorie": (p.get("categorie") if p else None),
                "prestataire": (p.get("prestataire") if p else None),
                "periode_absence_a_utiliser": (p.get("periode_absence_a_utiliser") if p else None),
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
                "enseigne": pick(["enseigne", "raison_sociale", "raisonSociale", "nom_point_relais"]),
                "adresse_1": pick(["adresse_1", "adresse1"]),
                "code_postal": pick(["code_postal"]),
                "ville": pick(["ville"]),
                "categorie": pick(["categorie_pr_chronopost", "categorie_de_point_relais"]),
                "prestataire": pick(["nom_prestataire", "code_transporteur"]),
                "statut": pick(["statut", "flag_actif"]),
                "latitude": float(pick(["latitude"])) if pick(["latitude"]) is not None else None,
                "longitude": float(pick(["longitude"])) if pick(["longitude"]) is not None else None,
                "periode_absence_a_utiliser": pick(["periode_absence_a_utiliser"]),
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


def stats_exit_items_monthly(item_code: str, type_exit: str | list[str] | None = None) -> pl.DataFrame:
    if 'stats_exit' not in globals():
        return pl.DataFrame()
    df = stats_exit
    try:
        current_year = datetime.datetime.now().year
        if "mois" not in df.columns:
            try:
                df = df.with_columns(
                    pl.col("date_mvt").dt.month().alias("mois")
                )
            except Exception:
                return pl.DataFrame()

        expr = (pl.col("code_article") == item_code) & (pl.col("annee") == current_year)
        if type_exit is not None:
            if isinstance(type_exit, list):
                values = [v for v in type_exit if v is not None]
            else:
                values = [type_exit]
            if values:
                expr = expr & pl.col("lib_motif_mvt").is_in(values)

        out = (
            df.filter(expr)
              .group_by([pl.col("annee"), pl.col("mois")])
              .agg(pl.col("qte_mvt").sum())
        )

        # Construire un DataFrame avec les 12 mois de l'année courante
        full_months = pl.DataFrame({
            "annee": [current_year] * 12,
            "mois": list(range(1, 13)),
        })

        # Joindre pour garantir une ligne par mois, en remplissant les manquants à 0
        out = (
            full_months
            .join(out, on=["annee", "mois"], how="left")
            .with_columns(
                pl.col("qte_mvt").fill_null(0)
            )
            .sort([pl.col("annee"), pl.col("mois")])
        )

        return out
    except Exception:
        return pl.DataFrame()


