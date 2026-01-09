import click
import subprocess
from typing import Callable, Optional
import importlib.util
import os
from supplychain_app.constants import (
    path_pudo,
    folder_gestion_pr,
    folder_chronopost,
    path_input,
    file_name_545,
    path_lmline,
)
from package_pudo.my_loguru import logger
try:
    import package_pudo.lm2s.etl_lm2s as _lm2s_for_bundle
except Exception:
    _lm2s_for_bundle = None

def _safe_call(progress_cb: Callable[[str], None], label: str, fn: Optional[Callable]=None):
    try:
        progress_cb(label)
        if fn:
            return fn()
    except Exception as exc:
        progress_cb(f"[WARN] Étape ignorée: {label} -> {exc}")
    return None

def run_etl(progress_cb: Callable[[str], None] = print):
    """Orchestre le pipeline PUDO sans lancer de sous-processus.
    Retourne le chemin du dernier fichier annuaire PR généré, si disponible.
    """
    def _progress(msg: str) -> None:
        try:
            progress_cb(msg)
        except Exception:
            pass
        try:
            logger.info(msg)
        except Exception:
            pass

    _progress("[START] Pipeline PUDO")
    # Étape 0: mails Chronopost (récupération CSV)
    try:
        from package_pudo.chronopost.step_0_mails_chronopost_recovery import get_mail_chronopost
        _safe_call(_progress, "Récupération mails Chronopost…", get_mail_chronopost)
    except Exception as exc:
        _progress(f"[WARN] Étape 0 non disponible: {exc}")

    # Étapes Chronopost 1..4: n'exécuter que celles présentes pour éviter des warnings inutiles
    chronopost_steps = [
        "package_pudo.chronopost.step_1_transform_from_csv_to_xlsx",
        "package_pudo.chronopost.step_2_merge_C9_and_C13_xlsx",
        "package_pudo.chronopost.step_3_add_gps_coordinate",
        "package_pudo.chronopost.step_4_creation_notebook_chronopost",
    ]
    existing_steps = [m for m in chronopost_steps if importlib.util.find_spec(m) is not None]
    for idx, modpath in enumerate(existing_steps, start=1):
        module = __import__(modpath, fromlist=['run'])
        fn = getattr(module, 'run', None)
        label = f"Étape Chronopost {idx}: {modpath.split('.')[-1]}…"
        if callable(fn):
            _safe_call(_progress, label, fn)
        else:
            step_name = modpath.split('.')[-1]
            fallback = None
            if step_name == 'step_1_transform_from_csv_to_xlsx':
                try:
                    from package_pudo.chronopost.step_1_transform_from_csv_to_xlsx import transform_csv_to_excel
                    from package_pudo.chronopost.constants import path_datan, folder_pudo, folder_chronopost, FOLDER_C9_C13_CSV, FOLDER_C9_C13_EXCEL
                    def fallback():
                        import os
                        transform_csv_to_excel(os.path.join(path_datan, folder_pudo, folder_chronopost, FOLDER_C9_C13_CSV),
                                               os.path.join(path_datan, folder_pudo, folder_chronopost, FOLDER_C9_C13_EXCEL))
                except Exception:
                    fallback = None
            elif step_name == 'step_2_merge_C9_and_C13_xlsx':
                try:
                    from package_pudo.chronopost.step_2_merge_C9_and_C13_xlsx import make_merge_xlsx_c9_c13
                    from package_pudo.chronopost.constants import path_datan, folder_pudo, folder_chronopost, FOLDER_C9_C13_EXCEL, FOLDER_C9_C13_FUSION_EXCEL
                    def fallback():
                        import os
                        make_merge_xlsx_c9_c13(os.path.join(path_datan, folder_pudo, folder_chronopost, FOLDER_C9_C13_EXCEL),
                                               os.path.join(path_datan, folder_pudo, folder_chronopost, FOLDER_C9_C13_FUSION_EXCEL))
                except Exception:
                    fallback = None
            elif step_name == 'step_3_add_gps_coordinate':
                try:
                    from package_pudo.chronopost.step_3_add_gps_coordinate import get_gps_coordinate_pudo, add_gps_coordinates_in_file
                    def fallback():
                        get_gps_coordinate_pudo()
                        add_gps_coordinates_in_file()
                except Exception:
                    fallback = None
            elif step_name == 'step_4_creation_notebook_chronopost':
                try:
                    from package_pudo.chronopost.step_4_creation_notebook_chronopost import construire_table_carnet_chronopost
                    def fallback():
                        construire_table_carnet_chronopost()
                except Exception:
                    fallback = None
            _safe_call(_progress, label, fallback)

    # Étape LM2S (si run() existe) - éviter l'import dynamique par nom de chaîne
    try:
        mod = _lm2s_for_bundle
        if mod is None:
            import package_pudo.lm2s.etl_lm2s as mod  # type: ignore
        fn = getattr(mod, 'run', None)
        _safe_call(_progress, "Récupération annuaire PUDO LM2S…", fn)
    except Exception as exc:
        _progress(f"[WARN] Récupération annuaire PUDO LM2S non disponible: {exc}")

    # Rapport des fichiers disponibles avant fusion finale
    _report_inputs(_progress)

    # Merge final + sauvegarde annuaire PR
    from package_pudo.pudo.pudo import merge_pudo_files, save_in_excel_pudo_directory
    _progress("Fusion finale des fichiers PUDO…")
    df = merge_pudo_files()
    _progress("Sauvegarde de l'annuaire PR…")
    save_in_excel_pudo_directory(df)

    # Retourner le chemin du dernier fichier (pour copie éventuelle effectuée côté app)
    try:
        last_file = os.listdir(os.path.join(path_pudo, folder_gestion_pr, 'ANNUAIRE_PR'))[-1]
        out = os.path.join(path_pudo, folder_gestion_pr, 'ANNUAIRE_PR', last_file)
        _progress(f"[DONE] Pipeline PUDO terminé -> {out}")
        return out
    except Exception:
        _progress("[DONE] Pipeline PUDO terminé")
        return None

@click.group()
def cli():
    pass

@cli.command()
def etl_pudos():
    # Fallback CLI: utilise l'orchestrateur interne
    run_etl(print)
    

def _report_inputs(progress_cb: Callable[[str], None]):
    try:
        fusion_dir = os.path.join(path_pudo, folder_chronopost, '2_C9_C13_EXCEL_FUSION')
        chrono = [f for f in os.listdir(fusion_dir) if f.lower().endswith(('.xlsx', '.xls'))] if os.path.exists(fusion_dir) else []
        n = len(chrono)
        head = ', '.join(sorted(chrono)[-3:]) if n else 'aucun'
        progress_cb(f"Chronopost fusion: {n} fichier(s) dans {fusion_dir} -> {head}")
    except Exception as e:
        progress_cb(f"[WARN] Vérif Chronopost: {e}")

    try:
        lm2s_dir = path_lmline
        lm2s = [f for f in os.listdir(lm2s_dir) if f.lower().endswith(('.xlsx', '.xls'))] if os.path.exists(lm2s_dir) else []
        n = len(lm2s)
        head = ', '.join(sorted(lm2s)[-3:]) if n else 'aucun'
        progress_cb(f"LM2S: {n} fichier(s) dans {lm2s_dir} -> {head}")
    except Exception as e:
        progress_cb(f"[WARN] Vérif LM2S: {e}")

    try:
        quotidien_dir = os.path.join(path_input, 'QUOTIDIEN')
        folders = [f for f in os.listdir(quotidien_dir) if os.path.isdir(os.path.join(quotidien_dir, f))] if os.path.exists(quotidien_dir) else []
        last_folder = sorted(folders)[-1] if folders else None
        if last_folder:
            xls_path = os.path.join(quotidien_dir, last_folder, file_name_545)
            exists = os.path.exists(xls_path)
            progress_cb(f"SPEED: dernier dossier '{last_folder}', fichier attendu {'présent' if exists else 'absent'}: {xls_path}")
        else:
            progress_cb("SPEED: aucun sous-dossier dans QUOTIDIEN")
    except Exception as e:
        progress_cb(f"[WARN] Vérif SPEED: {e}")
