import os
import requests
import re
import unidecode

from string import punctuation
from urllib.parse import quote
from flask import session

proxy_tdf = "fproxy-vip.tdf.fr:8080"

def get_datagouv_response_gps_for_address(address: str) -> dict:
    URL_DATA_GOUV = "https://data.geopf.fr/geocodage/search/"
    address = get_cleaning_address(address)
    params = {"q": address, "limit": 5}
    # Ensure proxy is configured at call time (credentials may be provided by the webapp session)
    proxy_from_env = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

    # Read potential credentials from session or environment
    login_val = session.get("proxy_login") or os.getenv("login")
    password_val = session.get("proxy_password") or os.getenv("password")

    # If we have credentials and proxy_tdf, always build an authenticated proxy URL
    if proxy_tdf and login_val and password_val:
        enc_login = quote(login_val, safe="")
        enc_password = quote(password_val, safe="")
        proxy_url = f"http://{enc_login}:{enc_password}@{proxy_tdf}"
        os.environ["http_proxy"] = proxy_url
        os.environ["https_proxy"] = proxy_url
        proxy_from_env = proxy_url
    proxies = {"http": proxy_from_env, "https": proxy_from_env} if proxy_from_env else None

    try:
        resp = requests.get(URL_DATA_GOUV, params=params, proxies=proxies, timeout=10)
        resp.raise_for_status()
        results = resp.json()
    except Exception:
        # En cas d'erreur réseau / proxy / JSON, on renvoie simplement None
        # pour laisser l'appelant gérer l'absence de coordonnées.
        return None

    if "features" in results and results["features"]:
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
        longitude, latitude = map(float, result["geometry"]["coordinates"])
        return {"address": label, "latitude": latitude, "longitude": longitude}
    else:
        return {"address": None, "latitude": None, "longitude": None}