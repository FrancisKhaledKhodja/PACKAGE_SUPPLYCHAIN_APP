import os

from dotenv import load_dotenv

load_dotenv()

STORES_CLOSED = ["1301", "3301", "8803", "4102", "1316"]
UPSTREAM_STORE_TYPES = ["FOURNISSEURS", "NATIONAL", "RESERVE", "LOCAL", "PIED DE SITE", 
                        "REPARATEUR INTERNE", "REPARATEUR EXTERNE", "DTOM", "DIVERS"]
UPSTREAM_STORES = ["MBZL", "MBAL", "35BS"]

path_datan = r"D:\Datan"
folder_bdd_python = "bdd_app_python"
folder_excel_output = "excel_files_output"
path_excel_output = os.path.join(path_datan, folder_bdd_python, folder_excel_output)
folder_input = "data_input"
folder_output = "data_output"

path_exit = r"\\apps\Vol1\Data\011-BO_XI_entrees\07-DOR_DP\Sorties"
path_input = os.path.join(path_datan, folder_bdd_python, folder_input)
path_output = os.path.join(path_datan, folder_bdd_python, folder_output)
folder_chronopost = "CHRONOPOST"
folder_notebook_chronopost = "CARNET_CHRONOPOST"
folder_pudo = "PUDO"
folder_mvt_speed = r"MVT\SPEED"
folder_mvt_oracle = r"MVT\ORACLE"
folder_gestion_pr = "GESTION_PR"
path_lmline = os.path.join(path_datan, folder_bdd_python, folder_pudo, "LM2S")


path_exit_lmline = os.path.join(path_exit, r"GESTION_PR\LM2S")
path_backup_address_gps = os.path.join(path_datan, folder_bdd_python,  "backup_addresses")

path_pudo = os.path.join(path_datan, folder_bdd_python, folder_pudo)
folder_donation_equipment = "donation_equipment"
folder_database_application = r"./databases/database_application"
file_name_database_application = "database_application.db"

path_photo_input = r"\\apps\Vol1\Data\35-Recherche_Stock\Photos"
folder_database_photo = r"./databases/database_photo"
file_name_database_photo = r"database_photo.db"

path_exit_parquet = os.path.join(path_exit, "FICHIERS_ANALYSES_SUPPLY_CHAIN", "FICHIERS_PARQUET")

folder_tracking_logistic = "SUIVI_ENCOURS_STOCK_EMBARQUES"
path_tracking_logistic = os.path.join(path_exit, folder_tracking_logistic)


# Choix PR technicien (overrides administration)
CHOIX_PR_TECH_DIR = os.path.join(path_exit, folder_gestion_pr, "CHOIX_PR_TECH")
CHOIX_PR_TECH_FILE = "choix_pr_tech.parquet"

# referential items
file_name_521 = "521 - (PIM) - REFERENTIEL ARTICLES V2.xlsx"
sheet_names_521 = ["ARTICLES PIM", "ARTICLES PIM - TRANSPORT", "EQUIVALENT", "FABRICANT"]

# nomenclature items
file_name_531 = "531 - Nomenclature Equipement.xlsx"
sheet_name_531 = "Nomenclature Fils"

# projects
file_name_551 = "551 - (RAP SIP) - PROJET PE.xlsx"
file_name_552 = "552 - (RAP SIP) - PROJET PJ.xlsx"

# Min mMax stores
file_name_532 = "532 - (SPD TPS REEL) - MIN MAX MAGASINS.xlsx"

# referential Helios
file_name_515 = "515 - (IG) - SITES IG HELIOS.xlsx"
file_name_560 = "560 - (HELIOS) - IG PS SLA CCO EQUIP V2.xlsx"
sheet_name_560 = "IG_PNO_EQUIP"
sheet_name_560_pop = "POP"
sheet_name_560_pno = "PNO"
sheet_name_560_sla = "SLA"
sheet_name_560_cco = "CCO"

# Referential stores and pudo
file_name_545 = "545 - (STK TIERS SIP) - ANNUAIRE MAGASINS ET POINT RELAIS.xlsx"
sheet_name_545_stores = "LISTE MAG PR"
sheet_name_545_pudo = "LISTE PR"

# Stock real time
file_name_554 = "554 - (STK SPD TPS REEL) - STOCK TEMPS REEL.xlsx"

# Stock min max
file_name_532 = "532 - (SPD TPS REEL) - MIN MAX MAGASINS.xlsx"

# Movements stock
file_name_510 = "510 - (STK SPD TPS REEL) - MOUVEMENT STOCK.csv"

file_name_506 = "506 - (STK SPD TPS REEL) - TRACKING ALLER RETOUR V2 ENTRE 2 DATES.xlsx"
sheet_name_506 = "TRACKING ALLER"

# Transco file store code oracle speed
file_name_file_transco_store_code = "TRANSCO MAG AU 20200722.xlsx"

# bu repartition
file_name_bu_sheet_distribution = "cle_repartition_bu_v2.xlsx"

# project bu repartion 
file_name_bu_project_distribution = "transco_libelle_programme_pe_v2.xlsx"

# Correspondence between movement label oracle and speed
file_name_correspondence_mvt_label_oracle_speed = "Liste des transcodifications des mouvements.xlsx"

# Correspondence between store code oracle and store code speed
file_name_correspondence_store_code_oracle_speed = "TRANSCO MAG AU 20200722.xlsx"

# Bt
file_name_559 = "559 - BT.csv"

# DPI
file_name_572 = "572 - (BOOST DPI TPS REEL) - PORTEFEUILLE DPI.xlsx"
sheet_name_572 =  "dde pce + dde liv ou transfert"

# Correspondance user_dpi
file_name_correspondance_user_dpi = "correspondance_user_cdp_deploiement.xlsx"

file_name_500 = "500 - (STK SPD SIP) - ETAT DES STOCKS (POWERBI).csv"
file_name_backup_addresses = "backup_addresses.parquet"
file_name_backup_origin_destination = "backup_origin_destination.parquet"

folder_name_app = "supply_chain_app" 

LOGIN_LMLINE = os.environ.get("login_lmline", "")
PASSWORD_LMLINE = os.environ.get("password_lmline", "")
LOGIN_URL_LMLINE = os.environ.get("login_url_lmline", "http://lmline.lm2s.fr/login")
DOWNLOAD_URL_LMLINE = os.environ.get("download_url_lmline", "http://lmline.lm2s.fr/export/pudo")
PROXY_TDF = os.environ.get("proxy_tdf", "fproxy-vip.tdf.fr:8080")


path_supply_chain_app = r"D:\Datan\supply_chain_app"
path_photos_local = os.path.join(path_supply_chain_app, "photos")
path_photos_network = os.path.join(path_exit, "PHOTOS")
 
CONSO_OFFER_SRC_DIR = os.environ.get("SCAPP_CONSO_OFFER_SRC_DIR", r"\\apps\Vol1\Data\011-BO_XI_entrees\07-DOR_DP\Sorties\FICHIERS_REFERENTIEL_ARTICLE\OFFRE_CATALOGUE_CONSOMMABLES")
CONSO_OFFER_PARQUET_DIR = os.environ.get("SCAPP_CONSO_OFFER_PARQUET_DIR", os.path.join(path_supply_chain_app, "offre_consommables"))
CONSO_OFFER_DIR = CONSO_OFFER_PARQUET_DIR
