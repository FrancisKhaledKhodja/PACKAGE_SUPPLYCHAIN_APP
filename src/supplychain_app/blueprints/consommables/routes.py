import os
from datetime import datetime

from flask import jsonify

from . import bp
from supplychain_app.constants import CONSO_OFFER_DIR
from supplychain_app.constants import CONSO_OFFER_SRC_DIR
from supplychain_app.constants import path_datan, folder_name_app
from supplychain_app.excel_csv_to_dataframe import read_excel


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


@bp.get("/offer")
def consommables_offer():
    offer_parquet_dir = (CONSO_OFFER_DIR or "").strip()
    offer_src_dir = (CONSO_OFFER_SRC_DIR or "").strip()

    latest_path = None
    offer_mode = None
    parquet_path = None

    if offer_parquet_dir and os.path.isdir(offer_parquet_dir):
        parquet_path = os.path.join(offer_parquet_dir, "offre_consommables.parquet")
        if os.path.exists(parquet_path):
            offer_mode = "parquet"
            latest_path = parquet_path

    if offer_mode is None:
        if not offer_src_dir:
            return jsonify({
                "available": False,
                "error": "offer_src_dir_not_configured",
                "rows": [],
            }), 200

        if not os.path.isdir(offer_src_dir):
            return jsonify({
                "available": False,
                "error": "offer_src_dir_not_found",
                "dir": offer_src_dir,
                "rows": [],
            }), 200

        latest_path = _latest_excel_in_dir(offer_src_dir)
        if not latest_path:
            return jsonify({
                "available": False,
                "error": "offer_file_not_found",
                "dir": offer_src_dir,
                "rows": [],
            }), 200
        offer_mode = "excel"

    try:
        if offer_mode == "parquet":
            import polars as pl
            df = pl.read_parquet(latest_path)
        else:
            df = read_excel(os.path.dirname(latest_path), os.path.basename(latest_path))
    except Exception as e:
        return jsonify({
            "available": False,
            "error": f"read_failed: {e.__class__.__name__}",
            "message": str(e),
            "file": os.path.basename(latest_path) if latest_path else None,
            "dir": os.path.dirname(latest_path) if latest_path else None,
            "rows": [],
        }), 200

    # Enrichissement stock: magasin MPLC, qualité GOOD, flag_stock_d_m = M
    try:
        import polars as pl
        import datetime

        if df is not None and "code_article" in df.columns:
            codes = (
                df.select(pl.col("code_article").cast(pl.Utf8).str.strip_chars().str.to_uppercase())
                .to_series()
                .drop_nulls()
                .unique()
                .to_list()
            )

            stock_parquet = os.path.join(path_datan, folder_name_app, "stock_554.parquet")
            if codes and os.path.exists(stock_parquet):
                stock = pl.read_parquet(stock_parquet)
                required = {"code_article", "code_magasin", "flag_stock_d_m", "code_qualite", "qte_stock"}
                if required.issubset(stock.columns):
                    stock_f = (
                        stock
                        .with_columns([
                            pl.col("code_article").cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias("code_article"),
                            pl.col("code_magasin").cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias("code_magasin"),
                            pl.col("flag_stock_d_m").cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias("flag_stock_d_m"),
                            pl.col("code_qualite").cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias("code_qualite"),
                            pl.col("qte_stock").cast(pl.Float64, strict=False).fill_null(0.0).alias("qte_stock"),
                        ])
                        .filter(pl.col("code_article").is_in(codes))
                        .filter(pl.col("qte_stock") > 0)
                        .filter(pl.col("code_magasin") == "MPLC")
                        .filter(pl.col("flag_stock_d_m") == "M")
                        .filter(pl.col("code_qualite") == "GOOD")
                        .group_by("code_article")
                        .agg(pl.col("qte_stock").sum().alias("stock_mplc_good_m"))
                    )

                    df = (
                        df.with_columns(
                            pl.col("code_article").cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias("code_article")
                        )
                        .join(stock_f, on="code_article", how="left")
                        .with_columns(pl.col("stock_mplc_good_m").fill_null(0.0))
                    )

            # Enrichissement sorties (consommation) : stats_exit.parquet, toutes années
            try:
                stats_parquet = os.path.join(path_datan, folder_name_app, "stats_exit.parquet")
                if codes and os.path.exists(stats_parquet):
                    stats = pl.read_parquet(stats_parquet)
                    required_s = {"code_article", "lib_motif_mvt", "qte_mvt"}
                    if required_s.issubset(stats.columns):
                        stats = stats.with_columns([
                            pl.col("code_article").cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias("code_article"),
                            pl.col("lib_motif_mvt").cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias("lib_motif_mvt"),
                            pl.col("qte_mvt").cast(pl.Float64, strict=False).fill_null(0.0).alias("qte_mvt"),
                        ])

                        expr = (
                            pl.col("code_article").is_in(codes)
                            & (pl.col("lib_motif_mvt") == "SORTIE CONSOMMATION")
                        )

                        sorties = (
                            stats
                            .filter(expr)
                            .group_by("code_article")
                            .agg(pl.col("qte_mvt").sum().alias("sorties_conso_total"))
                        )

                        df = (
                            df.join(sorties, on="code_article", how="left")
                            .with_columns([
                                pl.col("sorties_conso_total").fill_null(0.0),
                                # compat: ancien nom conservé
                                pl.col("sorties_conso_total").alias("sorties_conso_annee_en_cours"),
                            ])
                        )
            except Exception:
                pass

            # Enrichissement catégorie sortie : items_without_exit_final.parquet
            try:
                cat_parquet = os.path.join(path_datan, folder_name_app, "items_without_exit_final.parquet")
                if codes and os.path.exists(cat_parquet):
                    cat_df = pl.read_parquet(cat_parquet)
                    if {"code_article", "categorie_sans_sortie"}.issubset(cat_df.columns):
                        cat_df = (
                            cat_df.select([
                                pl.col("code_article").cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias("code_article"),
                                pl.col("categorie_sans_sortie").cast(pl.Utf8).alias("categorie_sortie"),
                            ])
                            .filter(pl.col("code_article").is_in(codes))
                        )
                        df = df.join(cat_df, on="code_article", how="left")
            except Exception:
                pass
    except Exception:
        pass

    try:
        rows = [r for r in df.iter_rows(named=True)] if df is not None else []
    except Exception:
        rows = []

    try:
        mtime = os.path.getmtime(latest_path)
        mtime_iso = datetime.fromtimestamp(mtime).isoformat()
    except Exception:
        mtime = None
        mtime_iso = None

    cols = list(df.columns) if df is not None else []

    return jsonify({
        "available": True,
        "mode": offer_mode,
        "dir": os.path.dirname(latest_path) if latest_path else None,
        "file": os.path.basename(latest_path),
        "mtime": mtime,
        "mtime_iso": mtime_iso,
        "columns": cols,
        "rows": rows,
    }), 200
