import os
import shutil
import datetime as dt
import polars as pl

from supplychain_app.constants import (
    path_output,
    folder_gestion_pr,
    path_input,
    folder_chronopost,
    path_exit,
    path_pudo,
    path_lmline,
    file_name_545,
    sheet_name_545_pudo,
    path_backup_address_gps,
    file_name_backup_addresses,
)
from package_pudo.api_address_gps import get_cleaning_address, get_latitude_and_longitude
from package_pudo.my_loguru import logger


path_exit_pr = os.path.join(path_exit, folder_gestion_pr)



def get_last_directory_pudo_from_speed():
    quotidien_dir = os.path.join(path_input, "QUOTIDIEN")
    if not os.path.exists(quotidien_dir):
        raise FileNotFoundError(f"Dossier QUOTIDIEN introuvable: {quotidien_dir}")
    folders = [f for f in os.listdir(quotidien_dir) if os.path.isdir(os.path.join(quotidien_dir, f))]
    if not folders:
        raise FileNotFoundError(f"Aucun sous-dossier dans {quotidien_dir}. Déposez un dossier quotidien contenant {file_name_545}.")
    last_folder = sorted(folders)[-1]
    xls_path = os.path.join(quotidien_dir, last_folder, file_name_545)
    if not os.path.exists(xls_path):
        raise FileNotFoundError(f"Fichier attendu introuvable: {xls_path}")
    df = pl.read_excel(xls_path, sheet_name=sheet_name_545_pudo)
    df = df.with_columns(pl.col("Flag actif").cast(pl.Int8))
    df = df.filter(pl.col("Flag actif") == 1)
    df = df.filter(
        (pl.col("Code point relais").str.starts_with("TDF")) 
        | (pl.col("Nom point relais").str.to_lowercase().str.contains("boks")) 
        | (pl.col("Code point relais").str.starts_with("PR")))
    df = df.with_columns(pl.lit("ouvert").alias("statut"))
    df = df.with_columns(pl.lit(None).alias("latitude"))
    df = df.with_columns(pl.lit(None).alias("longitude"))
    transco = {"Code point relais": "code_point_relais", 
               "Nom point relais": "enseigne", 
               "Adresse 1": "adresse_1", 
               "Adresse 2": "adresse_2", 
               "Adresse 3": "adresse_3", 
               "Code postal": "code_postal", 
               "Ville": "ville"}
    
    df = df.with_columns(pl.lit("TDF").alias("nom_prestataire"))
    df = df.rename(transco)
    
    df = df.select(pl.col("code_point_relais", "enseigne", "adresse_1", "adresse_2", "adresse_3", "code_postal", "ville", "statut", "nom_prestataire", "latitude", "longitude"))
                         
    return df


def get_last_directory_pudo_chronopost():
    fusion_dir = os.path.join(path_pudo, folder_chronopost, "2_C9_C13_EXCEL_FUSION")
    files = [f for f in os.listdir(fusion_dir) if f.lower().endswith((".xlsx", ".xls"))]
    if not files:
        raise FileNotFoundError(f"Aucun fichier Chronopost fusion trouvé dans {fusion_dir}")
    last_file_name = sorted(files)[-1]
    df = pl.read_excel(os.path.join(fusion_dir, last_file_name))
    return df


def get_last_directory_pudo_lm2s():
    lm2s_dir = path_lmline
    files = [f for f in os.listdir(lm2s_dir) if f.lower().endswith((".xlsx", ".xls"))]
    if not files:
        raise FileNotFoundError(f"Aucun fichier LM2S trouvé dans {lm2s_dir}")
    last_file_name = sorted(files)[-1]
    df = pl.read_excel(os.path.join(lm2s_dir, last_file_name))
    transco = {"Code DAH": "code_point_relais", 
               "Nom PUDO": "enseigne", 
               "Adresse1": "adresse_1", 
               "Adresse2": "adresse_2",  
               "CodePostal": "code_postal", 
               "Ville": "ville", 
               "PUDO XL": "pudo_xl"}
    df = df.with_columns(pl.lit(None).alias("adresse_3"))
    df = df.rename(transco)
    df = df.select(pl.col("code_point_relais", "enseigne", "adresse_1", "adresse_2", "adresse_3", "code_postal", "ville", "statut", "nom_prestataire", "latitude", "longitude", "pudo_xl"))
    return df


def merge_pudo_files():
    dfs = []
    errs = []
    try:
        dfs.append(get_last_directory_pudo_chronopost())
    except Exception as e:
        errs.append(f"Chronopost: {e}")
    try:
        dfs.append(get_last_directory_pudo_lm2s())
    except Exception as e:
        errs.append(f"LM2S: {e}")
    try:
        dfs.append(get_last_directory_pudo_from_speed())
    except Exception as e:
        errs.append(f"SPEED: {e}")

    if not dfs:
        raise FileNotFoundError("Aucune source PUDO disponible. " + " | ".join(errs))

    df = pl.concat(dfs, how="diagonal_relaxed")
    df = df.filter((pl.col("code_point_relais") != "FF"))
    
    df = add_columns_cleaned_address(df)
    df = get_latitude_longitude_for_pudo(df)
    
    return df

def add_columns_cleaned_address(df):
    df = df.with_columns(
        (
            pl.concat_str(pl.col("adresse_1", "adresse_2", "code_postal", "ville"), ignore_nulls=True,separator=" ")
            .map_elements(lambda x: get_cleaning_address(x), return_dtype=pl.String)
            .alias("adresse_nettoyee")
            )
        )
    
    return df


def save_in_excel_pudo_directory(df):
    today = dt.datetime.now().date().strftime("%Y%m%d")
    out_dir = os.path.join(path_pudo, folder_gestion_pr, "ANNUAIRE_PR")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    df.write_excel(os.path.join(out_dir, f"ANNUAIRE_PR_{today}.xlsx"))
    
    
def get_latitude_longitude_for_pudo(df):
    backup_addresses = pl.read_parquet(os.path.join(path_backup_address_gps, file_name_backup_addresses))
    dico_backup_addresses = {row["adresse"]: row for row in backup_addresses.iter_rows(named=True)}

    for row in df.filter(pl.col("latitude").is_null()).iter_rows(named="True"):
        if row["adresse_nettoyee"] not in dico_backup_addresses:
            response = get_latitude_and_longitude(row["adresse_nettoyee"])
            if response is not None and response["latitude"] is not None:
                response["adresse"] = row["adresse_nettoyee"]
                dico_backup_addresses[row["adresse_nettoyee"]] = response

    backup_addresses = pl.from_dicts([v for _, v in dico_backup_addresses.items()])
    backup_addresses.write_parquet(os.path.join(path_backup_address_gps, file_name_backup_addresses))
        
    expression = (
        pl.when(pl.col("latitude").is_null())
        .then(pl.col("adresse_nettoyee").map_elements(lambda x: dico_backup_addresses[x]["latitude"] if x in dico_backup_addresses else None, return_dtype=pl.Float32))
        .otherwise(pl.col("latitude"))
    )
    
    df = df.with_columns(expression.alias("latitude"))
    
    expression = (
        pl.when(pl.col("longitude").is_null())
        .then(pl.col("adresse_nettoyee").map_elements(lambda x: dico_backup_addresses[x]["longitude"] if x in dico_backup_addresses else None, return_dtype=pl.Float32))
        .otherwise(pl.col("longitude"))
    )
    
    df = df.with_columns(expression.alias("longitude"))
    
    return df


if __name__ == "__main__":
    logger.info("Creation pudo files")
    df = merge_pudo_files()
    save_in_excel_pudo_directory(df)
    
    last_file = os.listdir(os.path.join(path_pudo, folder_gestion_pr, "ANNUAIRE_PR"))[-1]
    
    shutil.copyfile(os.path.join(path_pudo, folder_gestion_pr, "ANNUAIRE_PR", last_file), 
                    os.path.join(path_exit_pr, folder_gestion_pr, "ANNUAIRE_PR", last_file))
    
    logger.info("End of creation pudo files")
    
