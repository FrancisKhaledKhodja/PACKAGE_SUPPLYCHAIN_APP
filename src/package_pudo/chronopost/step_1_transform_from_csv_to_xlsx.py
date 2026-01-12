import os
import shutil
import datetime as dt
import polars as pl

from package_pudo.chronopost.constants import *


def transform_file_C13(path_folder, name_file):
    lib_col = {"column_3": "code_point_relais", "column_4": "enseigne", "column_7": "latitude", "column_8": "longitude", 
              "column_10": "adresse_1", "column_11": "adresse_2", "column_12": "adresse_3", "column_13": "code_postal", 
              "column_14": "ville", "column_56": "debut_absence_1", "column_57": "fin_absence_1",
           "column_59": "debut_absence_2", "column_60": "fin_absence_2", "column_62": "debut_absence_3", "column_63": "fin_absence_3"}

    df = pl.read_csv(os.path.join(path_folder, name_file), separator=";", has_header=False, encoding="ISO-8859-1")
    df = df.slice(1).head(df.height - 1)
    df = df.with_columns(pl.col("column_13").cast(pl.String))

    expression = (
        pl.when(pl.col("column_13").str.len_chars() < 5)
        .then(pl.concat_str(pl.lit("0"), pl.col("column_13")))
        .otherwise(pl.col("column_13"))
    )
    df = df = df.with_columns(expression.alias("column_13"))

    for i in range(22, 50):
        column_name = f"column_{i}"
        df = df.with_columns(pl.col(column_name).cast(pl.String))
        expression_1 = (
            pl.when(pl.col(column_name).str.len_chars() < 4)
            .then(pl.col(column_name).map_elements(lambda x: "0" * (4 - len(x)) + x, return_dtype=pl.String))
            .otherwise(pl.col(column_name))
        )
        df = df.with_columns(expression_1.alias(column_name))

    DAYS = "lundi,mardi,mercredi,jeudi,vendredi,samedi,dimanche"

    day_counter = 0
    for i in range(22, 50, 4):
        df = df.with_columns((pl.col(f"column_{i}") + ":" + pl.col(f"column_{i + 1}") + "-" + pl.col(f"column_{i + 2}") + ":" + pl.col(f"column_{i + 3}")).alias(f"horaires_{DAYS.split(",")[day_counter]}"))
        df = df.drop(pl.col(f"column_{i}", f"column_{i + 1}", f"column_{i + 2}", f"column_{i + 3}"))
        day_counter += 1


    df = df.with_columns(pl.lit("C13").alias("categorie_pr_chronopost"))
    df = df.rename(lib_col)

    return df


def transform_file_C9(path_folder, name_file):
    lib_col = {"Point Relais": "code_point_relais", "Enseigne": "enseigne", "Nom": "nom"}
    lib_col.update({"Adresse 1": "adresse_1", "Adresse 2": "adresse_2", "Adresse 3": "adresse_3"})
    lib_col.update({"Code Postal": "code_postal", "Horaires Lundi": "horaires_lundi"})
    lib_col.update({"Horaires Mardi": "horaires_mardi", "Horaires Mercredi": "horaires_mercredi"})
    lib_col.update({"Horaires Jeudi": "horaires_jeudi", "Horaires Vendredi": "horaires_vendredi"})
    lib_col.update({"Horaires Samedi": "horaires_samedi", "Horaires Dimanche": "horaires_dimanche"})
    lib_col.update({"Debut Absence": "debut_absence_1", "Fin Absence": "fin_absence_1"})
    lib_col.update({"Debut Absence_duplicated_0": "debut_absence_2", "Fin Absence_duplicated_0": "fin_absence_2"})
    lib_col.update({"Debut Absence_duplicated_1": "debut_absence_3", "Fin Absence_duplicated_1": "fin_absence_3", "Ville": "ville"})

    df= pl.read_csv(os.path.join(os.path.join(path_folder, name_file)), separator=";", encoding="ISO-8859-1")
    df = df.slice(1)
    
    df = df.with_columns(pl.col("Code Postal").cast(pl.String))
    
    expression = (
        pl.when(pl.col("Code Postal").str.len_chars() < 5)
        .then(pl.concat_str(pl.lit("0"), pl.col("Code Postal")))
        .otherwise(pl.col("Code Postal"))
    )
    df = df.with_columns(expression.alias("Code Postal"))
    df = df.rename(lib_col)
    df = df.with_columns(pl.lit("C9").alias("categorie_pr_chronopost"))
    return df

def transform_csv_to_excel(path_folder_origin, path_folder_destination):
    list_csv_files = os.listdir(os.path.join(path_folder_origin))
    list_excel_files = os.listdir(os.path.join(path_folder_destination))
    list_excel_files = [file_excel.split(".")[0] for file_excel in list_excel_files]

    for name_file in list_csv_files:
        if not(name_file.split(".")[0] in list_excel_files):
            if "csv" in name_file and "C9" in name_file:
                file = transform_file_C9(os.path.join(path_folder_origin), name_file)
            elif "csv" in name_file and "C13" in name_file:
                file = transform_file_C13(os.path.join(path_folder_origin), name_file)
            file.write_excel(os.path.join(path_folder_destination, name_file.split(".")[0] + ".xlsx"))


if __name__ == "__main__":
    
    today = dt.datetime.now().date().strftime("%Y%m%d")
    transform_csv_to_excel(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_CSV), 
                           os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_EXCEL))
    
    number_of_copy_files = 0
    for name_file in sorted(os.listdir(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_EXCEL)), reverse=True):
        if today in name_file:
            shutil.copyfile(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_EXCEL, name_file), 
                            os.path.join(path_exit_pr, folder_chronopost, FOLDER_C9_C13_EXCEL, name_file))
            number_of_copy_files += 1
            if number_of_copy_files == 2:
                break
            
    