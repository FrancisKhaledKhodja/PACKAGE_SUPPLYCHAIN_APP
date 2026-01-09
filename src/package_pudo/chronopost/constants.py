import os

PATH_ONEDRIVE = r"R:\24-DPR\11-Applications\04-Gestion_Des_Points_Relais\Data"
FOLDER_C9_C13_CSV= "0_C9_C13_CSV"
FOLDER_C9_C13_EXCEL = "1_C9_C13_EXCEL"
FOLDER_C9_C13_FUSION_EXCEL = "2_C9_C13_EXCEL_FUSION"
FOLDER_1 = "Boîte de réception"
EMAIL_INBOX = "referentiel_logistique"
FILE_NAME_HEADER_C13  = "CHRONO_RELAIS_C13_DETAILS_CHRONOS"
SUBJECT = "Points relais CHRONOPOST pour TDF"
SENDER_EMAIL = "chrexp@ediserv.chronopost.fr"
FOLDER_BACKUP_GPS_ADDRESS = "API_ADRESSE"
NAME_FILE_BACKUP_GPS_ADDRESS = "SAUVEGARDE_REQUETE_API.json"

folder_input = "data_input"
folder_output = "data_output"
folder_bdd_python = "bdd_app_python"
folder_excel_output = "excel_files_output"
folder_gestion_pr = "GESTION_PR"
path_datan = r"D:\Datan"
folder_pudo = "PUDO"
folder_chronopost = "CHRONOPOST"
folder_notebook_chronopost = "CARNET_CHRONOPOST"
path_exit = r"\\apps\Vol1\Data\011-BO_XI_entrees\07-DOR_DP\Sorties"
path_exit_pr = os.path.join(path_exit, r"GESTION_PR")
path_output = os.path.join(path_datan, folder_bdd_python, folder_output)
path_pudo = os.path.join(path_datan, folder_bdd_python, folder_pudo)
file_name_backup_addresses = "backup_addresses.parquet"
path_backup_address_gps = os.path.join(path_datan, folder_bdd_python,  "backup_addresses")