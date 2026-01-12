import os
import subprocess
import sys
import runpy
import contextlib
import traceback
from datetime import datetime

from flask import jsonify, request, session
from urllib.parse import quote
import requests
import re

from supplychain_app.constants import (
    folder_bdd_python,
    folder_chronopost,
    folder_gestion_pr,
    folder_pudo,
    path_datan,
)

from . import bp


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _run_module_in_process(mod: str, log_f, env: dict) -> dict:
    """Exécute un module Python comme si on faisait `python -m <mod>`.

    Important pour les binaires PyInstaller (onefile) : `sys.executable` pointe sur l'EXE,
    donc un `subprocess` ne peut pas relancer un interpréteur Python classique.
    """
    t0 = datetime.now().isoformat()

    com_inited = False

    # Propager l'environnement (proxy, chemins, etc.) au process courant.
    old_env = os.environ.copy()
    try:
        os.environ.update(env or {})

        old_argv = sys.argv[:]
        sys.argv = ["-m", mod]
        try:
            # When running inside the Flask request thread (and especially in frozen mode),
            # win32com requires COM to be initialized in the current thread.
            try:
                import pythoncom  # type: ignore

                pythoncom.CoInitialize()
                com_inited = True
            except Exception:
                com_inited = False

            # Some pywin32 setups (notably frozen builds) may require this module to be present.
            try:
                import win32timezone  # type: ignore  # noqa: F401
            except Exception:
                pass

            with contextlib.redirect_stdout(log_f), contextlib.redirect_stderr(log_f):
                runpy.run_module(mod, run_name="__main__")
            return {"module": mod, "ok": True, "started_at": t0, "ended_at": datetime.now().isoformat()}
        except SystemExit as e:
            code = int(getattr(e, "code", 0) or 0)
            ok = code == 0
            return {
                "module": mod,
                "ok": ok,
                "started_at": t0,
                "ended_at": datetime.now().isoformat(),
                "returncode": code,
            }
        except Exception as e:
            traceback.print_exc(file=log_f)
            return {
                "module": mod,
                "ok": False,
                "started_at": t0,
                "ended_at": datetime.now().isoformat(),
                "error": f"{e.__class__.__name__}: {e}",
            }
        finally:
            sys.argv = old_argv
            if com_inited:
                try:
                    import pythoncom  # type: ignore

                    pythoncom.CoUninitialize()
                except Exception:
                    pass
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def _required_directories() -> list[str]:
    base = os.path.join(path_datan, folder_bdd_python)
    pudo_base = os.path.join(base, folder_pudo)

    # Dossiers racine
    dirs = [
        base,
        pudo_base,
        os.path.join(pudo_base, folder_chronopost),
        os.path.join(pudo_base, folder_gestion_pr),
        os.path.join(pudo_base, "LM2S"),
    ]

    # Sous-arborescence CHRONOPOST (d'après le document)
    dirs.extend([
        os.path.join(pudo_base, folder_chronopost, "0_C9_C13_CSV"),
        os.path.join(pudo_base, folder_chronopost, "1_C9_C13_EXCEL"),
        os.path.join(pudo_base, folder_chronopost, "2_C9_C13_EXCEL_FUSION"),
        os.path.join(pudo_base, folder_chronopost, "ELIGIBILITE"),
    ])

    # Sous-arborescence GESTION_PR (d'après le document)
    dirs.extend([
        os.path.join(pudo_base, folder_gestion_pr, "ANALYSES"),
        os.path.join(pudo_base, folder_gestion_pr, "ANNUAIRE_PR"),
        os.path.join(pudo_base, folder_gestion_pr, "CARNET_CHRONOPOST"),
    ])

    return dirs


def _check_directories() -> dict:
    required = _required_directories()
    missing = [p for p in required if not os.path.isdir(p)]
    return {
        "base": os.path.join(path_datan, folder_bdd_python),
        "required_dirs": required,
        "missing_dirs": missing,
        "ok": len(missing) == 0,
    }


def _redact_proxy_credentials(text: str | None) -> str:
    if not text:
        return ""
    # Redact http(s) proxy URLs of the form http://user:pass@host
    return re.sub(r"(https?://[^\s:/]+:)([^@\s]+)(@)", r"\1***\3", text)


@bp.post("/proxy-test")
def proxy_test():
    body = request.get_json(silent=True) or {}
    url = (body.get("url") or "http://example.com/").strip() or "http://example.com/"
    timeout_s = body.get("timeout_s", 8)
    try:
        timeout_s = float(timeout_s)
    except Exception:
        timeout_s = 8.0
    timeout_s = max(2.0, min(timeout_s, 30.0))

    proxy_login = session.get("proxy_login")
    proxy_password = session.get("proxy_password")
    proxy_tdf = os.environ.get("proxy_tdf") or os.environ.get("PROXY_TDF") or "fproxy-vip.tdf.fr:8080"
    if not (proxy_login and proxy_password):
        return jsonify({
            "ok": False,
            "error": "missing_proxy_credentials",
            "hint": "Connectez-vous via la page de login de l'application (menu).",
        }), 401

    enc_login = quote(str(proxy_login), safe="")
    enc_password = quote(str(proxy_password), safe="")
    proxy_url = f"http://{enc_login}:{enc_password}@{proxy_tdf}"
    proxies = {"http": proxy_url, "https": proxy_url}

    s = requests.Session()
    s.trust_env = False
    try:
        r = s.get(url, proxies=proxies, timeout=(3, timeout_s), allow_redirects=False, verify=False)
        status = int(getattr(r, "status_code", 0) or 0)
        ok = 200 <= status < 400
        return jsonify({
            "ok": ok,
            "status": status,
            "url": url,
            "proxy_host": proxy_tdf,
            "proxy_login": str(proxy_login),
        }), 200 if ok else 502
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"{e.__class__.__name__}: {e}",
            "url": url,
            "proxy_host": proxy_tdf,
            "proxy_login": str(proxy_login),
        }), 502


@bp.post("/run")
def run_treatments():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()

    if not name:
        return jsonify({"error": "name_required"}), 400

    allowed = {"all", "annuaire_pr", "carnet_chronopost", "etl_lm2s"}
    if name not in allowed:
        return jsonify({
            "error": "unknown_treatment",
            "allowed": sorted(allowed),
        }), 400

    dir_check = _check_directories()
    if not dir_check.get("ok"):
        return jsonify({
            "ok": False,
            "error": "missing_directories",
            "treatment": name,
            **dir_check,
        }), 412

    pipelines: dict[str, list[str]] = {
        # Pipeline complet (ordre imposé)
        "all": [
            "package_pudo.chronopost.step_0_mails_chronopost_recovery",
            "package_pudo.chronopost.step_1_transform_from_csv_to_xlsx",
            "package_pudo.chronopost.step_2_merge_C9_and_C13_xlsx",
            "package_pudo.chronopost.step_3_add_gps_coordinate",
            "package_pudo.chronopost.step_4_creation_notebook_chronopost",
            "package_pudo.lm2s.etl_lm2s",
            "package_pudo.pudo.pudo",
        ],
        "etl_lm2s": [
            "package_pudo.lm2s.etl_lm2s",
        ],
        # Génération carnet Chronopost (sous-ensemble)
        "carnet_chronopost": [
            "package_pudo.chronopost.step_0_mails_chronopost_recovery",
            "package_pudo.chronopost.step_1_transform_from_csv_to_xlsx",
            "package_pudo.chronopost.step_2_merge_C9_and_C13_xlsx",
            "package_pudo.chronopost.step_3_add_gps_coordinate",
            "package_pudo.chronopost.step_4_creation_notebook_chronopost",
        ],
        # Génération annuaire PR: pipeline complet (car dépendances possibles)
        "annuaire_pr": [
            "package_pudo.chronopost.step_0_mails_chronopost_recovery",
            "package_pudo.chronopost.step_1_transform_from_csv_to_xlsx",
            "package_pudo.chronopost.step_2_merge_C9_and_C13_xlsx",
            "package_pudo.chronopost.step_3_add_gps_coordinate",
            "package_pudo.chronopost.step_4_creation_notebook_chronopost",
            "package_pudo.lm2s.etl_lm2s",
            "package_pudo.pudo.pudo",
        ],
    }

    modules = pipelines.get(name)
    if not modules:
        return jsonify({
            "error": "unknown_treatment",
            "allowed": sorted(pipelines.keys()),
        }), 400

    started_at = datetime.now().isoformat()
    results: list[dict] = []

    # Ensure child processes write logs to the same file as the webapp.
    log_path = os.environ.get("SCAPP_LOG_PATH", "application.log")
    base_env = os.environ.copy()
    base_env["SCAPP_LOG_PATH"] = log_path
    base_env.setdefault("PYTHONUNBUFFERED", "1")

    # Propager le proxy authentifié depuis le login utilisateur (session Flask)
    proxy_login = session.get("proxy_login")
    proxy_password = session.get("proxy_password")
    proxy_tdf = os.environ.get("proxy_tdf") or os.environ.get("PROXY_TDF") or "fproxy-vip.tdf.fr:8080"
    if proxy_tdf and proxy_login and proxy_password:
        enc_login = quote(str(proxy_login), safe="")
        enc_password = quote(str(proxy_password), safe="")
        proxy_url = f"http://{enc_login}:{enc_password}@{proxy_tdf}"
        # Compat: certains scripts historisent l'attente sur `login`/`password`
        base_env["login"] = str(proxy_login)
        base_env["password"] = str(proxy_password)
        base_env["PROXY_LOGIN"] = str(proxy_login)
        base_env["PROXY_PASSWORD"] = str(proxy_password)
        base_env["http_proxy"] = proxy_url
        base_env["https_proxy"] = proxy_url
        base_env["HTTP_PROXY"] = proxy_url
        base_env["HTTPS_PROXY"] = proxy_url

    for mod in modules:
        t0 = datetime.now().isoformat()
        try:
            with open(log_path, "a", encoding="utf-8", errors="ignore") as log_f:
                log_f.write(f"\n[SCAPP] START module={mod} started_at={t0}\n")
                log_f.flush()

                if _is_frozen():
                    step_res = _run_module_in_process(mod, log_f, base_env)
                    results.append(step_res)
                    if not step_res.get("ok"):
                        break
                    continue

                cmd = [sys.executable, "-m", mod]
                proc = subprocess.run(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=base_env,
                    check=False,
                    timeout=int(os.environ.get("SCAPP_TREATMENT_STEP_TIMEOUT", "1800")),
                )

                ended_at = datetime.now().isoformat()
                log_f.write(f"[SCAPP] END module={mod} ended_at={ended_at} returncode={proc.returncode}\n")
                log_f.flush()
        except subprocess.TimeoutExpired as e:
            results.append({
                "module": mod,
                "cmd": cmd,
                "started_at": t0,
                "returncode": None,
                "error": f"TimeoutExpired: {e}",
            })
            return jsonify({
                "ok": False,
                "treatment": name,
                "started_at": started_at,
                "failed_module": mod,
                "results": results,
            }), 504
        except Exception as e:
            results.append({
                "module": mod,
                "cmd": cmd,
                "started_at": t0,
                "returncode": None,
                "error": f"{e.__class__.__name__}: {e}",
            })
            return jsonify({
                "ok": False,
                "treatment": name,
                "started_at": started_at,
                "failed_module": mod,
                "results": results,
            }), 500

        step = {
            "module": mod,
            "cmd": cmd,
            "started_at": t0,
            "returncode": int(proc.returncode),
            "stdout": "",
            "stderr": "",
        }
        results.append(step)

        if proc.returncode != 0:
            return jsonify({
                "ok": False,
                "treatment": name,
                "started_at": started_at,
                "failed_module": mod,
                "results": results,
            }), 500

    return jsonify({
        "ok": True,
        "treatment": name,
        "started_at": started_at,
        "results": results,
    }), 200
