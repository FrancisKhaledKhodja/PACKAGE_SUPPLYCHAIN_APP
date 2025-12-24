import os
import shutil
import time
from supplychain_app.constants import (path_exit,
                                            folder_gestion_pr,  
                                            path_exit_parquet,
                                            path_datan, 
                                            folder_name_app,
                                            CONSO_OFFER_SRC_DIR,
                                            CONSO_OFFER_PARQUET_DIR)
import polars as pl
from supplychain_app.excel_csv_to_dataframe import read_excel
from supplychain_app.my_loguru import logger

SRC_STOCK_554_SUPPLYCHAIN_APP = path_exit
NAME_FILE_554 = "554 - (STK SPD TPS REEL) - STOCK TEMPS REEL SUPPLYCHAIN_APP.xlsx"

last_update_summary: dict | None = None


def _latest_excel_in_dir(directory: str) -> str | None:
    try:
        names = [
            f for f in os.listdir(directory)
            if f.lower().endswith((".xlsx", ".xls"))
        ]
        if not names:
            return None

        preferred = [
            f for f in names
            if f.lower().startswith(("offre_consommable", "offre_consommables"))
        ]
        candidates = preferred if preferred else names

        def _key(fname: str):
            try:
                mtime = os.path.getmtime(os.path.join(directory, fname))
            except Exception:
                mtime = 0
            return (mtime, fname.lower())

        best = max(candidates, key=_key)
        return os.path.join(directory, best)
    except Exception:
        return None


def _atomic_write_parquet(df: pl.DataFrame, dst_path: str) -> None:
    dst_dir = os.path.dirname(dst_path)
    os.makedirs(dst_dir, exist_ok=True)
    tmp_path = dst_path + ".tmp"
    try:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        df.write_parquet(tmp_path)
        os.replace(tmp_path, dst_path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

def _ensure_app_folder():
    folders_list = os.listdir(path_datan)
    if folder_name_app not in folders_list:
        os.mkdir(os.path.join(path_datan, folder_name_app))


def _mtime(path: str):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def get_update_status():
    annuaire_dir = os.path.join(path_exit, folder_gestion_pr, "ANNUAIRE_PR")

    src_annuaire = None
    try:
        if os.path.isdir(annuaire_dir):
            names = [n for n in os.listdir(annuaire_dir) if n and not n.startswith("~$")]
            if names:
                def _ann_key(fname: str):
                    try:
                        return os.path.getmtime(os.path.join(annuaire_dir, fname))
                    except Exception:
                        return 0

                last_file_annuaire = max(names, key=_ann_key)
                src_annuaire = os.path.join(annuaire_dir, last_file_annuaire)
    except Exception:
        src_annuaire = None
    dst_annuaire_parquet = os.path.join(path_datan, folder_name_app, "pudo_directory.parquet")

    src_stores = os.path.join(path_exit_parquet, "stores_final.parquet")
    dst_stores = os.path.join(path_datan, folder_name_app, "stores.parquet")

    src_helios = os.path.join(path_exit_parquet, "helios.parquet")
    dst_helios = os.path.join(path_datan, folder_name_app, "helios.parquet")

    # Items parquet used by the stock search tab
    src_items = os.path.join(path_exit_parquet, "items.parquet")
    dst_items = os.path.join(path_datan, folder_name_app, "items.parquet")

    src_items_wo_exit = os.path.join(path_exit_parquet, "items_without_exit_final.parquet")
    dst_items_wo_exit = os.path.join(path_datan, folder_name_app, "items_without_exit_final.parquet")
    
    src_items_parent_buildings = os.path.join(path_exit_parquet, "items_parent_buildings.parquet")
    dst_items_parent_buildings = os.path.join(path_datan, folder_name_app, "items_parent_buildings.parquet")
    
    src_nomenclatures = os.path.join(path_exit_parquet, "nomenclatures.parquet")
    dst_nomenclatures = os.path.join(path_datan, folder_name_app, "nomenclatures.parquet")
    
    src_manufacturers = os.path.join(path_exit_parquet, "manufacturers.parquet")
    dst_manufacturers = os.path.join(path_datan, folder_name_app, "manufacturers.parquet")
    
    src_equivalents = os.path.join(path_exit_parquet, "equivalents.parquet")
    dst_equivalents = os.path.join(path_datan, folder_name_app, "equivalents.parquet")

    src_minmax = os.path.join(path_exit_parquet, "minmax.parquet")
    dst_minmax = os.path.join(path_datan, folder_name_app, "minmax.parquet")

    src_stats_exit = os.path.join(path_exit_parquet, "stats_exit.parquet")
    dst_stats_exit = os.path.join(path_datan, folder_name_app, "stats_exit.parquet")

    src_stock_554 = SRC_STOCK_554_SUPPLYCHAIN_APP
    dst_stock_554 = os.path.join(path_datan, folder_name_app, "stock_554.parquet")

    src_stock_final = os.path.join(path_exit_parquet, "stock_final.parquet")
    dst_stock_final = os.path.join(path_datan, folder_name_app, "stock_final.parquet")

    src_distance_tech_pr = os.path.join(path_exit_parquet, "distance_tech_pr.parquet")
    dst_distance_tech_pr = os.path.join(path_datan, folder_name_app, "distance_tech_pr.parquet")

    conso_src_dir = (CONSO_OFFER_SRC_DIR or "").strip()
    conso_dst_dir = (CONSO_OFFER_PARQUET_DIR or "").strip()
    conso_src = None
    if conso_src_dir and os.path.isdir(conso_src_dir):
        conso_src = _latest_excel_in_dir(conso_src_dir)
    conso_dst = os.path.join(conso_dst_dir, "offre_consommables.parquet") if conso_dst_dir else None

    items = []
    if src_annuaire:
        items.append({
            "key": "pudo_directory",
            "src": src_annuaire,
            "dst": dst_annuaire_parquet,
            "src_mtime": _mtime(src_annuaire),
            "dst_mtime": _mtime(dst_annuaire_parquet),
        })
    items.append({
        "key": "stores",
        "src": src_stores,
        "dst": dst_stores,
        "src_mtime": _mtime(src_stores),
        "dst_mtime": _mtime(dst_stores),
    })
    items.append({
        "key": "helios",
        "src": src_helios,
        "dst": dst_helios,
        "src_mtime": _mtime(src_helios),
        "dst_mtime": _mtime(dst_helios),
    })
    items.append({
        "key": "items",
        "src": src_items,
        "dst": dst_items,
        "src_mtime": _mtime(src_items),
        "dst_mtime": _mtime(dst_items),
    })
    items.append({
        "key": "items_parent_buildings",
        "src": src_items_parent_buildings,
        "dst": dst_items_parent_buildings,
        "src_mtime": _mtime(src_items_parent_buildings),
        "dst_mtime": _mtime(dst_items_parent_buildings),
    })
    items.append({
        "key": "items_without_exit_final",
        "src": src_items_wo_exit,
        "dst": dst_items_wo_exit,
        "src_mtime": _mtime(src_items_wo_exit),
        "dst_mtime": _mtime(dst_items_wo_exit),
    })
    items.append({
        "key": "nomenclatures",
        "src": src_nomenclatures,
        "dst": dst_nomenclatures,
        "src_mtime": _mtime(src_nomenclatures),
        "dst_mtime": _mtime(dst_nomenclatures),
    })
    items.append({
        "key": "manufacturers",
        "src": src_manufacturers,
        "dst": dst_manufacturers,
        "src_mtime": _mtime(src_manufacturers),
        "dst_mtime": _mtime(dst_manufacturers),
    })
    items.append({
        "key": "equivalents",
        "src": src_equivalents,
        "dst": dst_equivalents,
        "src_mtime": _mtime(src_equivalents),
        "dst_mtime": _mtime(dst_equivalents),
    })
    items.append({
        "key": "minmax",
        "src": src_minmax,
        "dst": dst_minmax,
        "src_mtime": _mtime(src_minmax),
        "dst_mtime": _mtime(dst_minmax),
    })
    items.append({
        "key": "stats_exit",
        "src": src_stats_exit,
        "dst": dst_stats_exit,
        "src_mtime": _mtime(src_stats_exit),
        "dst_mtime": _mtime(dst_stats_exit),
    })
    items.append({
        "key": "stock_554",
        "src": src_stock_554,
        "dst": dst_stock_554,
        "src_mtime": _mtime(src_stock_554),
        "dst_mtime": _mtime(dst_stock_554),
    })
    items.append({
        "key": "stock_final",
        "src": src_stock_final,
        "dst": dst_stock_final,
        "src_mtime": _mtime(src_stock_final),
        "dst_mtime": _mtime(dst_stock_final),
    })
    items.append({
        "key": "distance_tech_pr",
        "src": src_distance_tech_pr,
        "dst": dst_distance_tech_pr,
        "src_mtime": _mtime(src_distance_tech_pr),
        "dst_mtime": _mtime(dst_distance_tech_pr),
    })

    if conso_src or conso_dst:
        items.append({
            "key": "conso_offer",
            "src": conso_src,
            "dst": conso_dst,
            "src_mtime": _mtime(conso_src) if conso_src else None,
            "dst_mtime": _mtime(conso_dst) if conso_dst else None,
        })

    for it in items:
        sm = it.get("src_mtime")
        dm = it.get("dst_mtime")
        it["needs_update"] = (sm is not None) and (dm is None or sm > dm)

    return items

@logger.catch(level="ERROR")
def update_data():
    logger.info("Update data")
    _ensure_app_folder()

    global last_update_summary
    status = get_update_status()

    # 1) Convert latest annuaire Excel to parquet if newer or missing
    annuaire_info = next((x for x in status if x["key"] == "pudo_directory"), None)
    if annuaire_info and annuaire_info["src"] and annuaire_info["needs_update"]:
        src_path = annuaire_info["src"]
        pudo_directory = read_excel(os.path.dirname(src_path), os.path.basename(src_path))
        pudo_directory.write_parquet(annuaire_info["dst"])

    # 2) Copy stores parquet if newer or missing
    stores_info = next((x for x in status if x["key"] == "stores"), None)
    if stores_info and stores_info["src_mtime"] is not None and stores_info["needs_update"]:
        shutil.copy(stores_info["src"], stores_info["dst"])

    # 3) Copy helios parquet if newer or missing
    helios_info = next((x for x in status if x["key"] == "helios"), None)
    if helios_info and helios_info["src_mtime"] is not None and helios_info["needs_update"]:
        shutil.copy(helios_info["src"], helios_info["dst"])

    # 4) Copy items parquet if newer or missing
    items_info = next((x for x in status if x["key"] == "items"), None)
    if items_info and items_info["src_mtime"] is not None and items_info["needs_update"]:
        shutil.copy(items_info["src"], items_info["dst"])

    # 5) Copy items_parent_buildings parquet if newer or missing
    items_parent_buildings_info = next((x for x in status if x["key"] == "items_parent_buildings"), None)
    if items_parent_buildings_info and items_parent_buildings_info["src_mtime"] is not None and items_parent_buildings_info["needs_update"]:
        shutil.copy(items_parent_buildings_info["src"], items_parent_buildings_info["dst"])

    items_wo_exit_info = next((x for x in status if x["key"] == "items_without_exit_final"), None)
    if items_wo_exit_info and items_wo_exit_info["src_mtime"] is not None and items_wo_exit_info["needs_update"]:
        shutil.copy(items_wo_exit_info["src"], items_wo_exit_info["dst"])

    nomenclatures_info = next((x for x in status if x["key"] == "nomenclatures"), None)
    if nomenclatures_info and nomenclatures_info["src_mtime"] is not None and nomenclatures_info["needs_update"]:
        shutil.copy(nomenclatures_info["src"], nomenclatures_info["dst"])
    
    manufacturers_info = next((x for x in status if x["key"] == "manufacturers"), None)
    if manufacturers_info and manufacturers_info["src_mtime"] is not None and manufacturers_info["needs_update"]:
        shutil.copy(manufacturers_info["src"], manufacturers_info["dst"])
    
    equivalents_info = next((x for x in status if x["key"] == "equivalents"), None)
    if equivalents_info and equivalents_info["src_mtime"] is not None and equivalents_info["needs_update"]:
        shutil.copy(equivalents_info["src"], equivalents_info["dst"])

    minmax_info = next((x for x in status if x["key"] == "minmax"), None)
    if minmax_info and minmax_info["src_mtime"] is not None and minmax_info["needs_update"]:
        shutil.copy(minmax_info["src"], minmax_info["dst"])

    stats_exit_info = next((x for x in status if x["key"] == "stats_exit"), None)
    if stats_exit_info and stats_exit_info["src_mtime"] is not None and stats_exit_info["needs_update"]:
        shutil.copy(stats_exit_info["src"], stats_exit_info["dst"])

    stock_554_info = next((x for x in status if x["key"] == "stock_554"), None)
    if stock_554_info:
        stock_554_df = read_excel(SRC_STOCK_554_SUPPLYCHAIN_APP, NAME_FILE_554)

        stores_df = pl.read_parquet(os.path.join(path_datan, folder_name_app, "stores.parquet"))
        items_df = pl.read_parquet(os.path.join(path_datan, folder_name_app, "items.parquet"))

        stock_554_df = stock_554_df.join(
            stores_df.select(pl.col("code_magasin", "libelle_magasin", "type_de_depot")),
            how="left",
            on="code_magasin",
        )

        stock_554_df = stock_554_df.join(
            items_df.select(pl.col("code_article", "libelle_court_article")),
            how="left",
            on="code_article",
        )
        
        stock_554_df = stock_554_df.select(pl.col("code_magasin", "libelle_magasin", "type_de_depot", "emplacement", "flag_stock_d_m", "code_article", "libelle_court_article", "code_qualite", "qte_stock"))

        stock_554_df.write_parquet(stock_554_info["dst"])

    stock_final_info = next((x for x in status if x["key"] == "stock_final"), None)
    if stock_final_info and stock_final_info["src_mtime"] is not None and stock_final_info["needs_update"]:
        shutil.copy(stock_final_info["src"], stock_final_info["dst"])

    distance_tech_pr_info = next((x for x in status if x["key"] == "distance_tech_pr"), None)
    if distance_tech_pr_info and distance_tech_pr_info["src_mtime"] is not None and distance_tech_pr_info["needs_update"]:
        shutil.copy(distance_tech_pr_info["src"], distance_tech_pr_info["dst"])

    conso_info = next((x for x in status if x["key"] == "conso_offer"), None)
    if conso_info and conso_info.get("src") and conso_info.get("dst") and conso_info.get("needs_update"):
        try:
            src_path = str(conso_info["src"])
            df_offer = read_excel(os.path.dirname(src_path), os.path.basename(src_path))
            _atomic_write_parquet(df_offer, str(conso_info["dst"]))
        except Exception:
            raise

    # Recompute after updates to report final state
    status_after = get_update_status()
    logger.info("Data updated successfully")

    has_changes = any(it.get("needs_update") for it in status)
    last_update_summary = {
        "has_changes": bool(has_changes),
        "timestamp": time.time(),
    }

    return {"before": status, "after": status_after}


def get_last_update_summary() -> dict:
    global last_update_summary
    if last_update_summary is None:
        return {"has_changes": False, "timestamp": None}
    return last_update_summary


def get_stock_summary(code_article: str) -> pl.DataFrame:
    """
    Retourne une synthèse de la situation des stocks pour un code_article
    à partir du parquet stock_554.parquet enrichi.
    """
    stock_parquet = os.path.join(path_datan, folder_name_app, "stock_554.parquet")

    if not os.path.exists(stock_parquet):
        raise FileNotFoundError(stock_parquet)

    stock = pl.read_parquet(stock_parquet)

    stock_filtered = (
        stock
        .filter(pl.col("code_article") == code_article)
        .pivot(
            index=["type_de_depot", "flag_stock_d_m"],
            on="code_qualite",
            values="qte_stock",
            aggregate_function="sum",
        )
        .sort(pl.col("type_de_depot"))
    )

    return stock_filtered


def get_stock_details(code_article: str) -> pl.DataFrame:
    """Retourne le détail de stock par magasin pour un code_article.

    Colonnes retournées :
      - code_magasin, libelle_magasin, type_de_depot, emplacement,
        flag_stock_d_m, code_qualite, qte_stock
    """
    stock_parquet = os.path.join(path_datan, folder_name_app, "stock_554.parquet")

    if not os.path.exists(stock_parquet):
        raise FileNotFoundError(stock_parquet)

    stock = pl.read_parquet(stock_parquet)

    stock_filtered = (
        stock
        .filter(pl.col("code_article") == code_article)
        .select(
            pl.col(
                "code_magasin",
                "libelle_magasin",
                "type_de_depot",
                "emplacement",
                "flag_stock_d_m",
                "code_qualite",
                "qte_stock",
            )
        )
    )

    return stock_filtered


def get_stock_final_details(code_article: str) -> pl.DataFrame:
    """Retourne un état de stock ultra détaillé pour un code_article.

    Source : stock_final.parquet
    Colonnes retournées :
      - code_magasin, libelle_magasin, type_de_depot, flag_stock_d_m, emplacement,
        code_article, libelle_court_article, n_lot, n_serie, qte_stock, qualite,
        n_colis_aller, n_colis_retour, n_cde_dpm_dpi, demandeur_dpi,
        code_projet, libelle_projet, statut_projet, responsable_projet,
        date_reception_corrigee, categorie_anciennete, categorie_sans_sortie,
        bu, date_stock
    """
    stock_parquet = os.path.join(path_datan, folder_name_app, "stock_final.parquet")

    if not os.path.exists(stock_parquet):
        raise FileNotFoundError(stock_parquet)

    stock = pl.read_parquet(stock_parquet)

    stock_filtered = (
        stock
        .filter(pl.col("code_article") == code_article)
        .filter(pl.col("qte_stock") > 0)
        .select(
            pl.col(
                "code_magasin",
                "libelle_magasin",
                "type_de_depot",
                "flag_stock_d_m",
                "emplacement",
                "code_article",
                "libelle_court_article",
                "n_lot",
                "n_serie",
                "qte_stock",
                "qualite",
                "n_colis_aller",
                "n_colis_retour",
                "n_cde_dpm_dpi",
                "demandeur_dpi",
                "code_projet",
                "libelle_projet",
                "statut_projet",
                "responsable_projet",
                "date_reception_corrigee",
                "categorie_anciennete",
                "categorie_sans_sortie",
                "bu",
                "date_stock",
            )
        )
    )

    return stock_filtered

