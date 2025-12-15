import os
import tempfile

import polars as pl
from flask import jsonify, send_file

from . import bp
from package_pudo_api.constants import path_r, folder_gestion_pr, path_lmline, path_datan, folder_name_app


CARNET_CHRONOPOST_DIR = r"R:\24-DPR\11-Applications\04-Gestion_Des_Points_Relais\Data\GESTION_PR\CARNET_CHRONOPOST"
CHRONO_FUSION_DIR = r"R:\24-DPR\11-Applications\04-Gestion_Des_Points_Relais\Data\CHRONOPOST\2_C9_C13_EXCEL_FUSION"


def _latest_file_in_dir(directory: str, pattern_ext: tuple = (".xlsx", ".xls", ".csv")):
    """Return the lexicographically largest file in directory matching given extensions."""
    try:
        names = [
            f for f in os.listdir(directory)
            if f.lower().endswith(pattern_ext)
        ]
        if not names:
            return None
        best = max(names, key=lambda s: s.lower())
        return os.path.join(directory, best)
    except Exception:
        return None


@bp.get("/")
def list_latest_files():
    """Return the latest available business files for download (no parquets)."""
    # Annuaire PR
    annuaire_dir = os.path.join(path_r, folder_gestion_pr, "ANNUAIRE_PR")
    latest_annuaire = _latest_file_in_dir(annuaire_dir)

    # LM2S
    latest_lm2s = _latest_file_in_dir(path_lmline)

    # Chronopost fusionné (nouveau répertoire dédié)
    latest_chrono = _latest_file_in_dir(CHRONO_FUSION_DIR)

    # Carnet Chronopost
    latest_carnet = _latest_file_in_dir(CARNET_CHRONOPOST_DIR)

    # Stock final parquet (pour export CSV)
    stock_final_parquet = os.path.join(path_datan, folder_name_app, "stock_final.parquet")
    latest_stock_final = stock_final_parquet if os.path.exists(stock_final_parquet) else None

    def _info(path: str | None):
        if not path:
            return {"available": False, "filename": None}
        return {"available": True, "filename": os.path.basename(path)}

    return jsonify({
        "annuaire_pr": _info(latest_annuaire),
        "chronopost_fusionne": _info(latest_chrono),
        "lm2s": _info(latest_lm2s),
        "carnet_chronopost": _info(latest_carnet),
        "stock_final_csv": _info(latest_stock_final),
    })


@bp.get("/annuaire_pr")
def download_annuaire_pr_api():
    annuaire_dir = os.path.join(path_r, folder_gestion_pr, "ANNUAIRE_PR")
    latest = _latest_file_in_dir(annuaire_dir)
    if not latest:
        return jsonify({"error": "not_found"}), 404
    return send_file(latest, as_attachment=True, download_name=os.path.basename(latest))


@bp.get("/stock_final_csv")
def download_stock_final_csv_api():
    stock_parquet = os.path.join(path_datan, folder_name_app, "stock_final.parquet")
    if not os.path.exists(stock_parquet):
        return jsonify({"error": "not_found"}), 404

    try:
        df = pl.read_parquet(stock_parquet)
    except Exception:
        return jsonify({"error": "read_failed"}), 500

    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        df.write_csv(tmp_path, separator=";")
    except Exception:
        return jsonify({"error": "export_failed"}), 500

    return send_file(
        tmp_path,
        as_attachment=True,
        download_name="stock_final.csv",
        mimetype="text/csv; charset=utf-8",
    )


@bp.get("/lm2s")
def download_lm2s_api():
    latest = _latest_file_in_dir(path_lmline)
    if not latest:
        return jsonify({"error": "not_found"}), 404
    return send_file(latest, as_attachment=True, download_name=os.path.basename(latest))


@bp.get("/chronopost")
def download_chronopost_api():
    latest = _latest_file_in_dir(CHRONO_FUSION_DIR)
    if not latest:
        return jsonify({"error": "not_found"}), 404
    return send_file(latest, as_attachment=True, download_name=os.path.basename(latest))


@bp.get("/carnet_chronopost")
def download_carnet_chronopost_api():
    latest = _latest_file_in_dir(CARNET_CHRONOPOST_DIR)
    if not latest:
        return jsonify({"error": "not_found"}), 404
    return send_file(latest, as_attachment=True, download_name=os.path.basename(latest))
