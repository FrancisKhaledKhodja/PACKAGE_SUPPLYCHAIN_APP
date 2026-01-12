import os
import shutil
import datetime as dt
import polars as pl

from package_pudo.chronopost.constants import (
    path_datan,
    path_pudo, 
    folder_pudo, 
    FOLDER_C9_C13_EXCEL, 
    FOLDER_C9_C13_FUSION_EXCEL, 
    folder_chronopost, 
    path_exit_pr
    )



def correct_c9_c13_with_eligibility_chronopost(df):
    
    folder_eliginility_chronopost = r"R:\24-DPR\11-Applications\04-Gestion_Des_Points_Relais\Data\CHRONOPOST\ELIGIBILITE"
    file_name_eligbilty = "OZCA Mai 2025 TDF.xlsx"
    
    eligibility_df = pl.read_excel(os.path.join(folder_eliginility_chronopost, file_name_eligbilty))
    eligibility_df = eligibility_df.with_columns(pl.col("CP") + 100000)
    eligibility_df = eligibility_df.with_columns(pl.col("CP").cast(pl.String).str.slice(1, 5))
    
    dico_eligibility = {row["CP"]: row["Couverture C9"] for row in eligibility_df.iter_rows(named=True)}
    
    eligibility_check = pl.col("code_postal").map_elements(lambda x: dico_eligibility.get(x, None) == "NON", return_dtype=pl.Boolean)
    
    expression = (
        pl.when(pl.col("code_postal").is_in(list(dico_eligibility.keys())) & eligibility_check)
        .then(pl.lit("C13"))
        .otherwise(pl.col("categorie_pr_chronopost"))
        .cast(pl.String)
    )
    
    df = df.with_columns(expression.alias("categorie_pr_chronopost"))
    
    return df
    
    


def merge_file_xlsx_c9_c13(path_file: str, name_file_1: str, name_file_2: str, date_file: dt):
    col = ["code_point_relais", "enseigne", "adresse_1", "adresse_2"]
    col.extend(["adresse_3", "code_postal", "ville", "horaires_lundi", "horaires_mardi", "horaires_mercredi"])
    col.extend(["horaires_jeudi", "horaires_vendredi", "horaires_samedi"])
    col.extend(["debut_absence_1", "fin_absence_1", "debut_absence_2", "fin_absence_2", "debut_absence_3"])
    col.extend(["fin_absence_3", "categorie_pr_chronopost", "latitude", "longitude"])

    if "C9" in name_file_1:
        df_c9 = pl.read_excel(os.path.join(path_file, name_file_1), schema_overrides={"code_postal": pl.String})
        df_c13 = pl.read_excel(os.path.join(path_file, name_file_2), schema_overrides={"code_postal": pl.String})
    else:
        df_c9 = pl.read_excel(os.path.join(path_file, name_file_2), schema_overrides={"code_postal": pl.String})
        df_c13 = pl.read_excel(os.path.join(path_file, name_file_1), schema_overrides={"code_postal": pl.String})

    df_c9 = df_c9.with_columns(pl.lit(None).alias("latitude"))
    df_c9 = df_c9.with_columns(pl.lit(None).alias("longitude"))
    df_c9 = df_c9.drop(pl.col("nom"))
    df_c13 = df_c13.with_columns(pl.col("debut_absence_1", "fin_absence_1").cast(pl.String))

    code_pr_c9 = set(df_c9.select(pl.col("code_point_relais")).to_series().to_list())
    code_pr_c13 = set(df_c13.select(pl.col("code_point_relais")).to_series().to_list())
    # Identification des groupes C9-C13, des purs C9 et des purs C13
    code_pr_c9_c13 = code_pr_c9.intersection(code_pr_c13)
    code_pr_c9_without_c13 = code_pr_c9.difference(code_pr_c13)
    code_pr_c13_without_c9 = code_pr_c13.difference(code_pr_c9)
    # Construction de la nouvelle table des points relais
    df_c9_c13 = df_c9.filter(pl.col("code_point_relais").is_in(list(code_pr_c9_c13)))
    df_c9_c13 = df_c9_c13.with_columns(pl.lit("C9_C13").alias("categorie_pr_chronopost"))
    df_c9_without_c13 = df_c9.filter(pl.col("code_point_relais").is_in(list(code_pr_c9_without_c13)))
    df_c13_without_c9 = df_c13.filter(pl.col("code_point_relais").is_in(list(code_pr_c13_without_c9)))

    df = pl.concat([df_c9_c13.select(pl.col(col)), df_c9_without_c13.select(pl.col(col)), df_c13_without_c9.select(pl.col(col))], how="diagonal_relaxed")
    df = df.select(pl.col(col))
    df = df.sort(pl.col("code_point_relais"))
    
    df = clean_columns(df)
    
    df = define_column_absence_to_use(df, date_file)
    
    df = df.with_columns(pl.col("periode_absence_a_utiliser").map_elements(lambda x: get_status_pudo(x, date_file), skip_nulls=False, return_dtype=pl.String).alias("statut"))

    return df


def get_status_pudo(beginning_and_end_of_absence_date: str, date_file: dt):

    if isinstance(beginning_and_end_of_absence_date, str):
        beginning_absence_date, end_of_absence_date = beginning_and_end_of_absence_date.split("|")
        beginning_absence_date = dt.datetime.strptime(beginning_absence_date, "%Y-%m-%d").date()
        end_of_absence_date = dt.datetime.strptime(end_of_absence_date, "%Y-%m-%d").date()
        if date_file < beginning_absence_date or date_file > end_of_absence_date:
            return "ouvert"
        elif date_file >= beginning_absence_date and date_file <= end_of_absence_date:
            return "ferme"
        else:
            return "ouvert"
    else:
        return "ouvert"


def get_expression_compute_absence(name_column_beginning_absence, name_column_end_of_absence, date_file: dt):
    expression = (
        pl.when(
            (date_file <= pl.col(name_column_beginning_absence)) 
            | ((date_file > pl.col(name_column_beginning_absence)) & (date_file <= pl.col(name_column_end_of_absence)))
            )
        .then((pl.col(name_column_beginning_absence) - date_file).dt.total_days())
        .otherwise(None)
        )
    return expression


def create_columns_absence(df):
    df = df.with_columns(pl.concat_str(pl.col("debut_absence_1", "fin_absence_1"), separator="|").alias('periode_absence_1'))
    df = df.with_columns(pl.concat_str(pl.col("debut_absence_2", "fin_absence_2"), separator="|").alias('periode_absence_2'))
    df = df.with_columns(pl.concat_str(pl.col("debut_absence_3", "fin_absence_3"), separator="|").alias('periode_absence_3'))
    for name_col in ("debut_absence_1",	"fin_absence_1", "debut_absence_2", "fin_absence_2", "debut_absence_3", "fin_absence_3"):
        df = df.drop(pl.col(name_col))
    return df

def analyze_dates_absence(dates, date_file):

    beginning_absence, end_of_absence = dates.split("|")
    beginning_absence, end_of_absence = dt.datetime.strptime(beginning_absence, "%Y-%m-%d").date(), dt.datetime.strptime(end_of_absence, "%Y-%m-%d").date()
    if date_file <= beginning_absence or (date_file > beginning_absence and date_file <= end_of_absence):
        return dates


def define_column_absence_to_use(df, date_file):
    expression = (
        pl.when(pl.col("periode_absence_1").is_not_null())
        .then(pl.col("periode_absence_1").map_elements(lambda x: analyze_dates_absence(x, date_file), return_dtype=pl.String))
    )
    
    df = df.with_columns(expression.alias("periode_absence_a_utiliser"))
    
    expression = (
        pl.when((pl.col("periode_absence_2").is_not_null()) & (pl.col("periode_absence_a_utiliser").is_null()))
        .then(pl.col("periode_absence_2").map_elements(lambda x: analyze_dates_absence(x, date_file), return_dtype=pl.String))
        .otherwise(pl.col("periode_absence_a_utiliser"))
    )
    
    df = df.with_columns(expression.alias("periode_absence_a_utiliser"))
    
    expression = (
        pl.when((pl.col("periode_absence_3").is_not_null()) & (pl.col("periode_absence_a_utiliser").is_null()))
        .then(pl.col("periode_absence_3").map_elements(lambda x: analyze_dates_absence(x, date_file), return_dtype=pl.String))
        .otherwise(pl.col("periode_absence_a_utiliser"))
    )
    
    df = df.with_columns(expression.alias("periode_absence_a_utiliser"))
    
    return df
    

def clean_columns(df):
    df = df.with_columns(pl.lit(None).alias("nombre_jours_avant_debut_conges"))
    df = df.with_columns(pl.lit(None).alias("nombre_jours_avant_fin_conges"))
    df = df.with_columns(pl.lit(None).alias("statut"))
    
    for name_column in ("debut_absence_1",	"fin_absence_1", "debut_absence_2", "fin_absence_2", "debut_absence_3", "fin_absence_3"):
        expression = (
            pl.when((pl.col(name_column) == "") | (pl.col(name_column) == "-"))
            .then(None)
            .otherwise(pl.col(name_column))
        )
        df = df.with_columns(expression.alias(name_column))
    
    for name_column in ("debut_absence_1",	"fin_absence_1", "debut_absence_2", "fin_absence_2", "debut_absence_3", "fin_absence_3"):
        expression = (
            pl.when((pl.col(name_column).is_not_null()) & (pl.col(name_column).str.contains("/")))
            .then(pl.col(name_column).map_elements(lambda x: "".join(x.split("/")[::-1]), return_dtype=pl.String))
            .otherwise(pl.col(name_column))
        )
        df = df.with_columns(expression.alias(name_column))

    
    for name_column in ("debut_absence_1",	"fin_absence_1", "debut_absence_2", "fin_absence_2", "debut_absence_3", "fin_absence_3"):
        expression = (
            pl.when((pl.col(name_column).is_not_null()) & (pl.col(name_column).str.len_chars() == 8))
            .then(pl.col(name_column).str.to_datetime(format="%Y%m%d").dt.date())
            .otherwise(pl.col(name_column))
        )
        df = df.with_columns(expression.alias(name_column))
        df = df.with_columns(pl.col(name_column).cast(pl.Date))
        
    df = create_columns_absence(df)
    
    return df
    

def make_merge_xlsx_c9_c13(path_folder_excel, path_folder_fusion_excel):
    print(path_folder_fusion_excel)
    list_files_fusion_excel = os.listdir(path_folder_fusion_excel)
    list_files_excel = os.listdir(path_folder_excel)

    dates_fichiers = sorted(list(set([x.split(".")[0][-8:] for x in list_files_excel])))
    dates_fichiers.reverse()

    for date in dates_fichiers:
        list_files_with_date_selected = list(filter(lambda x: date in x, list_files_excel))
        if len(list_files_with_date_selected) == 2:
            list_file_with_date_selected =  list(filter(lambda x: date in x, list_files_fusion_excel))
            if len(list_file_with_date_selected) == 0:
                print("Traitement des fichiers du: " + date)
                date_file = dt.datetime.strptime(date, "%Y%m%d").date()
                df = merge_file_xlsx_c9_c13(path_folder_excel, list_files_with_date_selected[0], list_files_with_date_selected[1], date_file)
                df = correct_c9_c13_with_eligibility_chronopost(df)
                df = df.filter(pl.col("enseigne").is_not_null())
                df = df.with_columns(pl.lit("chronopost").alias("nom_prestataire"))      
                df.write_excel(os.path.join(path_folder_fusion_excel, "CHRONO_RELAIS_C9_C13_DETAILS_CHRONOS_{}.xlsx".format(date)))


if __name__ == "__main__":
    
    today = dt.datetime.now().date().strftime("%Y%m%d")
    make_merge_xlsx_c9_c13(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_EXCEL), 
                           os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_FUSION_EXCEL))
    

    for name_file in sorted(os.listdir(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_FUSION_EXCEL)), reverse=True):
        if today in name_file:
            shutil.copyfile(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_FUSION_EXCEL, name_file), 
                            os.path.join(path_exit_pr, folder_chronopost, FOLDER_C9_C13_FUSION_EXCEL, name_file))
            break

    