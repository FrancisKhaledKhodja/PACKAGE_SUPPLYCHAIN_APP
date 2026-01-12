import os
import shutil
import datetime as dt
from io import StringIO
import requests
import sys
import getpass
from urllib.parse import quote, urljoin
import re
import glob

import pandas as pd
import polars as pl

from supplychain_app.constants import (
    path_lmline,
    path_exit_lmline,
    path_backup_address_gps, 
    file_name_backup_addresses, 
    LOGIN_LMLINE,
    PASSWORD_LMLINE,
    LOGIN_URL_LMLINE,
    DOWNLOAD_URL_LMLINE,
    PROXY_TDF, 
    )
from package_pudo.api_address_gps import get_cleaning_address, get_latitude_and_longitude
from package_pudo.my_loguru import logger


_CACHED_PROXY_LOGIN = None
_CACHED_PROXY_PASSWORD = None


def _get_proxy_credentials_from_user() -> tuple[str | None, str | None]:
    """Même mécanisme que package_pudo.api_address_gps._get_proxy_credentials_from_user."""
    global _CACHED_PROXY_LOGIN
    global _CACHED_PROXY_PASSWORD

    if _CACHED_PROXY_LOGIN is not None or _CACHED_PROXY_PASSWORD is not None:
        return _CACHED_PROXY_LOGIN, _CACHED_PROXY_PASSWORD

    # Priorité: variables explicites propagées par l'app (treatments/routes.py)
    login = os.getenv("PROXY_LOGIN") or os.getenv("login")
    password = os.getenv("PROXY_PASSWORD") or os.getenv("password")

    if login and password:
        _CACHED_PROXY_LOGIN = login
        _CACHED_PROXY_PASSWORD = password
        return login, password

    allow_prompt = str(os.getenv("SCAPP_ALLOW_PROXY_PROMPT", "0")).strip() in {"1", "true", "True", "yes", "YES"}
    if allow_prompt and sys.stdin is not None and sys.stdin.isatty():
        login = login or input("Login proxy (Windows): ").strip() or None
        password = password or getpass.getpass("Mot de passe proxy (Windows): ").strip() or None

    _CACHED_PROXY_LOGIN = login
    _CACHED_PROXY_PASSWORD = password
    return login, password


def get_lm2s_pudo_directory():
    print("LM2S: start get_lm2s_pudo_directory", flush=True)
    today = dt.datetime.now().date().strftime("%Y%m%d")

    HEADERS = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'If-None-Match': '"3d4fe96f781829347fce7fa7f3824cdd-gzip"',
                    'Referer': 'http://lmline.lm2s.fr/login',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
                }

    login_lmline = LOGIN_LMLINE
    password_lmline = PASSWORD_LMLINE
    login_url_lmline = LOGIN_URL_LMLINE
    download_url_lmline = DOWNLOAD_URL_LMLINE
    proxy_tdf = PROXY_TDF

    if not login_lmline or not password_lmline:
        raise RuntimeError(
            "LM2S: identifiants LMline manquants. "
            "Renseigner les variables d'environnement 'login_lmline' et 'password_lmline'."
        )

    login_windows, password_windows = _get_proxy_credentials_from_user()

    if login_windows and password_windows and proxy_tdf:
        os.environ["http_proxy"] = f"http://{login_windows}:{password_windows}@{proxy_tdf}"
        os.environ["https_proxy"] = f"http://{login_windows}:{password_windows}@{proxy_tdf}"
    
    session = requests.Session()
    session.trust_env = False
    if os.environ.get("http_proxy"):
        session.proxies.update({"http": os.environ["http_proxy"], "https": os.environ["http_proxy"]})
    

    # Auth via formulaire (/login -> POST /user_sessions) pour obtenir un cookie de session.
    login_url = login_url_lmline
    post_url = urljoin(login_url, "/user_sessions")

    logger.info(f"LM2S: ouverture page login -> {login_url}")
    session.get(url=login_url, headers=HEADERS, verify=False)

    logger.info(f"LM2S: POST login -> {post_url}")
    payload = {
        "user_session[login]": login_lmline,
        "user_session[password]": password_lmline,
        "commit": "Login",
    }
    session.post(url=post_url, data=payload, headers=HEADERS, allow_redirects=True, verify=False)

    print(f"LM2S: HTTP GET -> {download_url_lmline}", flush=True)
    logger.info(f"LM2S: téléchargement annuaire -> {download_url_lmline}")
    response = session.get(url=download_url_lmline, headers=HEADERS, verify=False)
    html_content = response.text or ""

    # Le site renvoie parfois une page HTML (200 OK) indiquant qu'on n'est pas connecté.
    # Dans ce cas, on stoppe avec un message clair plutôt que de parser un faux tableau.
    lowered = html_content.lower()
    if (
        "vous n'etes pas connect" in lowered
        or "vous n\u2019etes pas connect" in lowered
        or "vous n'avez pas acc" in lowered
        or "vous n\u2019avez pas acc" in lowered
        or "flash_error" in lowered
    ):
        raise RuntimeError(
            "LM2S: accès refusé ou session non authentifiée sur LMline (réponse HTML). "
            "Vérifier les identifiants LMline (login_lmline/password_lmline) et les droits, "
            "ainsi que l'accès réseau/proxy."
        )

    df = pd.read_html(StringIO(html_content))[0]
    df = pl.from_pandas(df)
    df = df.with_columns(pl.col("CodePostal") + 100000)
    df = df.with_columns(pl.col("CodePostal").cast(pl.String))
    df = df.with_columns(pl.col("CodePostal").str.slice(1,5))
    df = df.with_columns(pl.lit("lm2s").alias("nom_prestataire"))
    df = df.with_columns(pl.concat_str(pl.col("Adresse1", "CodePostal", "Ville"), separator=" ").map_elements(lambda x: get_cleaning_address(x), return_dtype=pl.String).alias("adresse_nettoyee"))


    backup_addresses = pl.read_parquet(os.path.join(path_backup_address_gps, file_name_backup_addresses))
    dico_backup_addresses = {row["adresse"]: row for row in backup_addresses.iter_rows(named=True)}

    missing = 0
    for row in df.iter_rows(named=True):
        address = row["adresse_nettoyee"]
        if address not in dico_backup_addresses:
            missing += 1
            if missing == 1 or missing % 50 == 0:
                logger.info(f"LM2S: géocodage adresses manquantes -> {missing}…")
            response = get_latitude_and_longitude(address)

            if response and response["latitude"] is not None:
                print(address, response)
                response["adresse"] = address
                dico_backup_addresses[address] = response

    backup_addresses = pl.from_dicts([v for _, v in dico_backup_addresses.items()])
    backup_addresses.write_parquet(os.path.join(path_backup_address_gps, file_name_backup_addresses))

    df = df.join(backup_addresses.select(pl.col("adresse", "latitude", "longitude")), how="left", left_on="adresse_nettoyee", right_on="adresse")

    df = df.with_columns(pl.lit("ouvert").alias("statut"))

    nom_fichier_lm2s = f"annuaire_lm2s_{today}.xlsx"
    df.write_excel(os.path.join(path_lmline, nom_fichier_lm2s))


def run():
    """Wrapper pour l'orchestrateur ETL."""
    get_lm2s_pudo_directory()


if __name__ == "__main__":
    logger.info("Extract, transform and load pudo lm2s directory")
    run()

    pattern = os.path.join(path_lmline, "annuaire_lm2s_*.xlsx")
    candidates = [p for p in glob.glob(pattern) if os.path.isfile(p)]
    if not candidates:
        raise FileNotFoundError(f"LM2S: aucun fichier trouvé (pattern={pattern})")

    last_path = max(candidates, key=lambda p: os.path.getmtime(p))
    last_file = os.path.basename(last_path)

    os.makedirs(path_exit_lmline, exist_ok=True)
    shutil.copyfile(last_path, os.path.join(path_exit_lmline, last_file))
    
    logger.info("End of extract, transform and load pudo lm2s directory")