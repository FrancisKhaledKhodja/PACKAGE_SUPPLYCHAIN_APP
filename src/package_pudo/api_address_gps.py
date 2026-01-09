import os
import requests
import re
import sys
import getpass
from string import punctuation
from urllib.parse import quote

import unidecode


_CACHED_PROXY_LOGIN = None
_CACHED_PROXY_PASSWORD = None
PROXY_TDF = "fproxy-vip.tdf.fr:8080"

def _get_proxy_credentials_from_user() -> tuple[str | None, str | None]:
    global _CACHED_PROXY_LOGIN
    global _CACHED_PROXY_PASSWORD

    if _CACHED_PROXY_LOGIN is not None or _CACHED_PROXY_PASSWORD is not None:
        return _CACHED_PROXY_LOGIN, _CACHED_PROXY_PASSWORD

    login = os.getenv("PROXY_LOGIN") or os.getenv("login")
    password = os.getenv("PROXY_PASSWORD") or os.getenv("password")

    if login and password:
        _CACHED_PROXY_LOGIN = login
        _CACHED_PROXY_PASSWORD = password
        return login, password

    if sys.stdin is not None and sys.stdin.isatty():
        login = login or input("Login proxy (Windows): ").strip() or None
        password = password or getpass.getpass("Mot de passe proxy (Windows): ").strip() or None

    _CACHED_PROXY_LOGIN = login
    _CACHED_PROXY_PASSWORD = password
    return login, password

def get_datagouv_response_gps_for_address(address: str) -> dict:
    URL_DATA_GOUV = "https://data.geopf.fr/geocodage/search/"
    address = get_cleaning_address(address)
    params = {"q": address, "limit": 5}
    # Prefer proxy already configured by the webapp (HTTP_PROXY/http_proxy).
    proxy_from_env = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    proxies = None

    if proxy_from_env:
        proxies = {"http": proxy_from_env, "https": proxy_from_env}
    else:
        # Fallback for CLI usage only: build proxy from credentials if available.
        login, password = _get_proxy_credentials_from_user()
        if login and password:
            enc_login = quote(login, safe="")
            enc_password = quote(password, safe="")
            proxy_url = f"http://{enc_login}:{enc_password}@{PROXY_TDF}"
            os.environ["http_proxy"] = proxy_url
            os.environ["https_proxy"] = proxy_url
            proxies = {"http": proxy_url, "https": proxy_url}
    try:
        # connect timeout, read timeout
        resp = requests.get(URL_DATA_GOUV, params=params, proxies=proxies, timeout=(5, 20))
        resp.raise_for_status()
        results = resp.json()
    except Exception:
        return None
    
    if "features"in results and results["features"]:
        result = sorted(results["features"], key=lambda row: row["properties"]["score"], reverse=True)[0]
        return result


def get_cleaning_address(*address):
    cleaned_address = []
    address_pretreatment = [] 
    for i, element in enumerate(address):
        if i == 0:
            address_pretreatment.append(element)
        elif i != 0 and element != address[i - 1]:
            address_pretreatment.append(element)
    for element in address_pretreatment:
        for punct in punctuation:
            if element is not None and punct in element:
                element = element.replace(punct, " ")
        if element is not None and "n°" in element:
            element = element.replace("n°", "numero")
        if element is not None:
            cleaned_address.append(unidecode.unidecode(element.lower().strip()))
    cleaned_address = " ".join(cleaned_address)
    cleaned_address = re.sub(r"\s+", r" ", cleaned_address)
    cleaned_address = cleaned_address.lower()
    return cleaned_address


def get_latitude_and_longitude(address: str):
    result = get_datagouv_response_gps_for_address(address)
    if result:
        label = result["properties"]["label"]
        longitude, latitude = result["geometry"]["coordinates"]
        return {"address": label, "latitude": latitude, "longitude": longitude}
    else:
        return {"address": None, "latitude": None, "longitude": None}




