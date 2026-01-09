import os
import shutil
import datetime as dt
import time
import polars as pl

from package_pudo.chronopost.constants import (
    path_backup_address_gps, 
    file_name_backup_addresses, 
    path_pudo, 
    path_exit_pr, 
    folder_chronopost
    )
from package_pudo.chronopost.constants import FOLDER_C9_C13_FUSION_EXCEL
from package_pudo.api_address_gps import get_cleaning_address, get_latitude_and_longitude
from package_pudo.my_loguru import logger



def get_gps_coordinate_pudo():
    last_file = sorted(os.listdir(os.path.join(path_pudo, "CHRONOPOST", FOLDER_C9_C13_FUSION_EXCEL)))[-1]
    df = pl.read_excel(os.path.join(path_pudo, "CHRONOPOST", FOLDER_C9_C13_FUSION_EXCEL, last_file))

    backup_path = os.path.join(path_backup_address_gps, file_name_backup_addresses)
    if os.path.exists(backup_path):
        backup_addresses = pl.read_parquet(backup_path)
    else:
        os.makedirs(path_backup_address_gps, exist_ok=True)
        backup_addresses = pl.DataFrame({"adresse": [], "address": [], "latitude": [], "longitude": []})

    dico_backup_addresses = {row.get("adresse"): row for row in backup_addresses.iter_rows(named=True) if row.get("adresse")}
    logger.info(f"Backup GPS avant: {len(dico_backup_addresses)} adresse(s)")

    missing = df.filter(pl.col("latitude").is_null()).height
    logger.info(f"Fichier {last_file}: {missing} ligne(s) sans latitude")
    

    last_heartbeat = time.time()
    new_queries = 0
    for i, row in enumerate(df.filter(pl.col("latitude").is_null()).iter_rows(named=True), start=1):
        address = f"{row.get('adresse_1', '')} {row.get('code_postal', '')}, {row.get('ville', '')}"
        address = get_cleaning_address(address)
        if address not in dico_backup_addresses:
            new_queries += 1
            if new_queries <= 3 or (new_queries % 25 == 0):
                logger.info(f"Nouvelle requête geocodage #{new_queries} (i={i}) -> '{address}'")
            t_call = time.time()
            response = get_latitude_and_longitude(address)
            dt_call = time.time() - t_call
            if dt_call >= 10:
                logger.info(f"Geocoding lent ({dt_call:.1f}s) pour: '{address}'")
            if response and response.get("latitude") is not None and response.get("longitude") is not None:
                response["adresse"] = address
                dico_backup_addresses[address] = response

        if i % 50 == 0:
            logger.info(f"Geocoding en cours: {i} adresse(s) traitée(s) (lat null initial)")

        # Heartbeat to avoid 'silent' periods between multiples of 50.
        now = time.time()
        if (now - last_heartbeat) >= 30:
            logger.info(f"Geocoding en cours (heartbeat): {i} adresse(s) traitée(s)")
            last_heartbeat = now
    
    logger.info(f"Backup GPS après: {len(dico_backup_addresses)} adresse(s)")
    backup_addresses = pl.from_dicts([v for _, v in dico_backup_addresses.items()])
    logger.info(f"Backup parquet shape: {backup_addresses.shape}")
    logger.info("Écriture backup parquet...")
    backup_addresses.write_parquet(backup_path)
    logger.info("Écriture backup parquet OK")


def add_gps_coordinates_in_file():
    last_file = os.listdir(os.path.join(path_pudo, "CHRONOPOST", FOLDER_C9_C13_FUSION_EXCEL))[-1]
    df = pl.read_excel(os.path.join(path_pudo, "CHRONOPOST", FOLDER_C9_C13_FUSION_EXCEL, last_file))
    df = df.with_columns(pl.concat_str(pl.col("adresse_1", "code_postal", "ville"), separator=" ").map_elements(lambda x: get_cleaning_address(x), return_dtype=pl.String).alias("adresse_nettoyee"))

    backup_path = os.path.join(path_backup_address_gps, file_name_backup_addresses)
    if os.path.exists(backup_path):
        backup_addresses = pl.read_parquet(backup_path)
    else:
        backup_addresses = pl.DataFrame({"adresse": [], "latitude": [], "longitude": []})

    backup_map = {
        row.get("adresse"): (row.get("latitude"), row.get("longitude"))
        for row in backup_addresses.iter_rows(named=True)
        if row.get("adresse")
    }

    expression = (
        pl.when(pl.col("latitude").is_null())
        .then(pl.col("adresse_nettoyee").map_elements(lambda x: float(backup_map.get(x, (None, None))[0]) if backup_map.get(x, (None, None))[0] is not None else None, return_dtype=pl.Float32))
        .otherwise(pl.col("latitude"))
    )
    df = df.with_columns(expression.alias("latitude"))

    expression = (
        pl.when(pl.col("longitude").is_null())
        .then(pl.col("adresse_nettoyee").map_elements(lambda x: float(backup_map.get(x, (None, None))[1]) if backup_map.get(x, (None, None))[1] is not None else None, return_dtype=pl.Float32))
        .otherwise(pl.col("longitude"))
    )
    df = df.with_columns(expression.alias("longitude"))
    
    out_xlsx = os.path.join(path_pudo, "CHRONOPOST", FOLDER_C9_C13_FUSION_EXCEL, last_file)
    logger.info(f"Écriture Excel: {out_xlsx}")
    df.write_excel(out_xlsx)
    logger.info("Écriture Excel OK")

    null_after = df.filter(pl.col("latitude").is_null() | pl.col("longitude").is_null()).height
    logger.info(f"Fichier {last_file}: reste {null_after} ligne(s) sans GPS après remplissage")
    
    
def run():
    get_gps_coordinate_pudo()
    add_gps_coordinates_in_file()

if __name__ == "__main__":
    logger.info("Call of the script step_3_add_gps_coordinate")
    
    today = dt.datetime.now().date().strftime("%Y%m%d")
    get_gps_coordinate_pudo()
    add_gps_coordinates_in_file()
    
    for name_file in sorted(os.listdir(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_FUSION_EXCEL)), reverse=True):
        if today in name_file:
            shutil.copyfile(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_FUSION_EXCEL, name_file), 
                            os.path.join(path_exit_pr, folder_chronopost, FOLDER_C9_C13_FUSION_EXCEL, name_file))
            break
        
    logger.info("End of call of the script step_3_add_gps_coordinate")
    
    
