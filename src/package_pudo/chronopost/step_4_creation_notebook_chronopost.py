import os
import shutil
import datetime as dt
import polars as pl
from package_pudo.chronopost.constants import (
    path_output, 
    path_pudo, 
    folder_gestion_pr, 
    folder_notebook_chronopost, 
    path_exit_pr
    )
from package_pudo.my_loguru import logger


def construire_table_carnet_chronopost():
    """
    Contruire table de PR techniciens pour la mise à jour des données sur le site web chronopost 
    """
    today = dt.datetime.today().date().strftime("%Y%m%d")
    ordre_colonnes = "Nom;Prénom;Adresse;Suite adresse;Code porte;Code pays;Code postal;Ville;Téléphone;E-mail;Référence;Type;Raison sociale".split(";")

    last_folder = os.listdir(path_output)[-1]

    store_directory = pl.read_parquet(os.path.join(path_output, last_folder, "stores_final.parquet"))
    last_file_pudo_directory = os.listdir(os.path.join(path_pudo, folder_gestion_pr, "ANNUAIRE_PR"))[-1]
    pudo_directory = pl.read_excel(os.path.join(path_pudo, folder_gestion_pr, "ANNUAIRE_PR", last_file_pudo_directory))
    dico_pudo_directory = {row["code_point_relais"]: row for row in pudo_directory.iter_rows(named=True)}
    
    df = store_directory.filter(
        (pl.col("statut") == 0) 
        & (pl.col("pr_principal").is_not_null()) 
        & (pl.col("type_de_depot") != "PIED DE SITE"))
    #df = self.annuaire_magasin.table[self.annuaire_magasin.table["statut"] == 0]
    #df = df[df["pr_principal"].notnull()]
    #df = df[df["type_de_depot"] != "PIED DE SITE"]
    
    df = df.select(pl.col("contact", "pr_principal", "tel_contact", "email_contact"))
    liste_carnet_chrono = []
    for row in df.iter_rows(named=True):
        if row["pr_principal"] in dico_pudo_directory:
            dico = {}
            nom, prenom = row["contact"].split(",")
            dico["Téléphone"] = row["tel_contact"]
            dico["E-mail"] = row["email_contact"]
            dico["Nom"] = nom.strip()
            dico["Prénom"] = prenom.strip()
            
            #info_pr = self.annuaire_pr_speed.obtenir_info_point_relais(row["pr_principal"])
            info_pr = dico_pudo_directory[row["pr_principal"]]
            dico["Adresse"] = info_pr["adresse_1"]
            dico["Suite adresse"] = info_pr["adresse_2"]
            dico["Code postal"] = "{:05d}".format(int(info_pr["code_postal"]))
            dico["Ville"] = info_pr["ville"]
            dico["Raison sociale"] = info_pr["enseigne"]
            
            dico["Type"] = "destinataire"
            dico["Code porte"] = ""
            dico["Code pays"] = "FR"
            dico["Référence"] = ""
            
            liste_carnet_chrono.append(dico)
        else:
            print("Probleme", row["pr_principal"])
    
    carnet_chronopost = pl.DataFrame(liste_carnet_chrono)

    carnet_chronopost = carnet_chronopost.select([pl.col(col_name) for col_name in ordre_colonnes])
    carnet_chronopost = carnet_chronopost.sort(pl.col("Nom"))
    
    carnet_chronopost.write_csv(os.path.join(path_pudo, folder_gestion_pr, folder_notebook_chronopost, f"LISTE_MAJ_PORTAIL_CHRONO_{today}.csv"), separator=";")
    
def run():
    construire_table_carnet_chronopost()

if __name__ == "__main__":
    logger.info("Call of the script step_4_creation_notebook_chronopost")
    
    today = dt.datetime.now().date().strftime("%Y%m%d")
    construire_table_carnet_chronopost()
    
    for name_file in sorted(os.listdir(os.path.join(path_pudo, folder_gestion_pr, folder_notebook_chronopost)), reverse=True):
        if today in name_file:
            shutil.copyfile(os.path.join(path_pudo, folder_gestion_pr, folder_notebook_chronopost, name_file), 
                            os.path.join(path_exit_pr, "GESTION_PR", folder_notebook_chronopost, name_file))
            break
    
    logger.info("End of call of the script step_4_creation_notebook_chronopost")
    
        
