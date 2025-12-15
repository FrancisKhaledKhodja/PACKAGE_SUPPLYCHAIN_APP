import os
import shutil
import datetime as dt
import polars as pl

from package_pudo_api.constants import (path_exit, 
                                            file_name_521, 
                                            sheet_names_521,
                                            path_input, 
                                            file_name_531, 
                                            path_output, 
                                            sheet_name_531, 
                                            path_exit_parquet)

from package_pudo_api.miscellaneous_functions import get_date_creation_file, copy_file, make_folder
from package_pudo_api.excel_csv_to_dataframe import read_excel
from package_pudo_api.my_loguru import logger



class Items():
    
    def __init__(self, folder_path: str, file_name: str, sheet_names: list[str]):
        """
        Initializes the Items class.

        Makes the following operations:
        - read the Excel file
        - identify the OC and OL articles
        - Create a dataframe containing the manufacturers and their reference article
        - Create a dictionary containing the items and their manufacturers
        - Remove the columns manufacturer and reference article from the main dataframe
        - Remove the duplicate rows
        - Merge the dataframe containing the items dimensions with the main dataframe
        - Remove the duplicate columns
        - Rename certain columns
        """

        for sheet_name in sheet_names:
            match sheet_name:
                case "ARTICLES PIM":
                    self.items_df = read_excel(folder_path, file_name, sheet_name)
                case "ARTICLES PIM - TRANSPORT":
                    self.transport_df = read_excel(folder_path, file_name, sheet_name)
                case "FABRICANT":
                    self.manufacturer_df = read_excel(folder_path, file_name, sheet_name)
                case "EQUIVALENT":
                    self.equivalent_df = read_excel(folder_path, file_name, sheet_name)

        self._merge_dataframes()
        self._rename_specific_columns()
        self._convert_type_pump()
        self._create_column_oc_ol_identifier()
        self._making_dictionnary()

    def _convert_type_pump(self):
        self.items_df = self.items_df.with_columns(pl.col("pump").cast(pl.Float32))
        self.items_df = self.items_df.with_columns(pl.col("prix_achat_prev").cast(pl.Float32))

    def _merge_dataframes(self):
        """
        Merge the dataframe containing the items dimensions with the main dataframe.

        This method merge the dataframe containing the items dimensions with the main dataframe
        on the "code_article" column. After the merge, the dataframe containing the items dimensions
        is deleted.

        """
        self.items_df = self.items_df.join(self.transport_df, how="left", on="code_article")
        columns_to_remove = ['libelle_court_article_right', 'feuille_du_catalogue_right', 'type_article_right', 
                             'statut_abrege_article_right', 'categorie_inv_accounting_right', 'criticite_pim_right', 
                             'catalogue_consommable_right', 'delai_approvisionnement_right']
        self.items_df = self.items_df.drop(columns_to_remove)


    def _rename_specific_columns(self):
        dict_columns_name = {"proprietaire_article_champs_calcule": "proprietaire_article", 
                             "pump_valeur_actuelle": "pump"}
        self.items_df = self.items_df.rename(dict_columns_name)


    def _create_column_oc_ol_identifier(self):
        """
        Identify OC or OL items
        """
        self.items_df = (
            self.items_df
            .with_columns(
                pl.col("feuille_du_catalogue")
                .map_elements(
                    lambda x: "OC" if x == "EMI.AM.OC" else("OL" if x == "EMI.AM.OL" else None), return_dtype=pl.String
                    )
                .alias("est_oc_ou_ol")
                )
            )


    def _making_dictionnary(self):
        items_manufacturer_dictionnary = {}
        for row in self.manufacturer_df.iter_rows(named=True):
            item_code = row["code_article"]
            if item_code not in items_manufacturer_dictionnary:
                items_manufacturer_dictionnary[item_code] = []
            items_manufacturer_dictionnary[item_code].append(
                {
                    "nom_fabricant": row["nom_fabricant"],
                    "reference_article_fabricant": row["reference_article_fabricant"]
                }
            )

        items_equivalent_dictionnary = {}
        for row in self.equivalent_df.iter_rows(named=True):
            item_code = row["code_article"]
            if item_code not in items_equivalent_dictionnary:
                items_equivalent_dictionnary[item_code] = []
            items_equivalent_dictionnary[item_code].append(
                {
                    "code_article_equivalent": row["code_article_correspondant"], 
                    "type_de_relation": row["type_de_relation"]
                }
            )

        self.items_dictionnary = {row["code_article"]: row for row in self.items_df.iter_rows(named=True)}
        for item_code in self.items_dictionnary:
            if item_code in items_manufacturer_dictionnary:
                self.items_dictionnary[item_code]["fabricants"] = items_manufacturer_dictionnary[item_code]
            if item_code in items_equivalent_dictionnary:
                self.items_dictionnary[item_code]["equivalent"] = items_equivalent_dictionnary[item_code]


    def _write_parquet(self, folder_path):
        self.items_df.write_parquet(os.path.join(folder_path, "items.parquet"))
        self.equivalent_df.write_parquet(os.path.join(folder_path, "equivalents.parquet"))
        self.manufacturer_df.write_parquet(os.path.join(folder_path, "manufacturers.parquet"))


class Nomenclatures():
    
    def __init__(self, folder_path, file_name, sheet_name=None):
        if "parquet" in file_name:
            self.df = pl.read_parquet(os.path.join(folder_path, file_name))
            self._making_nomenclature_dictionnary()
        else:
            if sheet_name is not None:
                self.df = read_excel(folder_path, file_name, sheet_name)
                self._clean_columns()
                self.nomenclature_dictionnary =  self._making_nomenclature_dictionnary()
                self._making_nomenclature_dictionnary()
            else:
                raise("Il manque le nom de la feuille excel")

    def _clean_columns(self):
        self.df = self.df.with_columns(pl.col("article").str.strip_chars())
        self.df = self.df.with_columns(pl.col("article_eqpt_article_fils").str.strip_chars())


    def _get_list_items_with_nomenclature(self) -> list[str]:
        """
        From the dataframe df, identify the items with a nomenclature:
        an item with at least one child item
        """
        list_items_with_nomenclature = (
            
            self.df.filter(
                (pl.col("art_et_art_fils_eqpt_quantite").is_not_null()) 
                & (pl.col("article") != pl.col("article_eqpt_article_fils"))
                & (pl.col("art_et_art_fils_eqpt_quantite") > 0)
                )
                .group_by("article")
                .agg(
                    pl.col("article_eqpt_article_fils").count()
                    )
                    .select(pl.col("article"))
                    .to_series()
                    .to_list()
                    )
        
        #logger.debug(f"Number of items with nomenclature: {len(list_items_with_nomenclature)}")
        #logger.debug(f"List of items with nomenclature: {list_items_with_nomenclature}")

        return sorted(list_items_with_nomenclature)


    def _making_nomenclature_dictionnary(self) -> dict:
        """
        Making a dictionnary with as key the 'father' article and in value
        a list of dictionnary with in key the 'son' article and in value
        the quantity.
        """
        self.nomenclature_dictionnary = {}
        list_items_with_nomenclature = self._get_list_items_with_nomenclature()
        for item in list_items_with_nomenclature:
            self.nomenclature_dictionnary[item] = []
            df_item = (
                self.df.filter(
                    (pl.col("article") == item) 
                    & ((pl.col("art_et_art_fils_eqpt_quantite").is_not_null()) 
                       & (pl.col("art_et_art_fils_eqpt_quantite") > 0)))
                       .iter_rows(named=True)
                       )
            for row in df_item:
                self.nomenclature_dictionnary[item].append({"code_article": row["article_eqpt_article_fils"], 
                                                            "quantite": row["art_et_art_fils_eqpt_quantite"]})

        #logger.debug(f"Number of items with nomenclature: {len(self.nomenclature_dictionnary)}")
        #logger.debug(f"List of items with nomenclature: {self.nomenclature_dictionnary}")


    def get_item_tree(self, item_code: str, item_parent: str=None, multiplying_factor: int=1, counter: int=None) -> dict:
        """
        return a dictionnary representing the hierarchy or nomenclature of the item
        
        """
        if counter is None:
            counter = 0
        counter += 1
        if counter > 10:
            return {}
        tree = {}
        tree["code_article"] = item_code
        if item_parent is not None:
            for row in self.nomenclature_dictionnary[item_parent]:
                if row["code_article"] == item_code:
                    tree["quantite"] = row["quantite"] * multiplying_factor
        else:
            tree["quantite"] = 1 * multiplying_factor
        if item_code in self.nomenclature_dictionnary:
            tree["code_article_fils"] = []
            for code_article_fils in self.nomenclature_dictionnary[item_code]:
                tree["code_article_fils"].append(self.get_item_tree(code_article_fils["code_article"], item_code, tree["quantite"], counter))
        
        #logger.info(f"item_code: {item_code}")
        #logger.info(f"counter: {counter}")
        #logger.info(f"nomenclature: {tree}")
        
        return tree


    def get_item_nomenclature(self, parent_item):

        tree = self.get_item_tree(parent_item)
        item_nomenclature = {}
        item_nomenclature["code_article_parent"] = parent_item
        item_nomenclature["code_article_fils"] = []
        if "code_article_fils" in tree:
            for row in tree["code_article_fils"]:
                if "code_article" in row:
                    item_nomenclature["code_article_fils"].append({"code_article": row["code_article"], "quantite": row["quantite"]})
                if "code_article_fils" in row:
                    tree_2 = self.get_item_tree(row["code_article"])
                    for row_2 in tree_2["code_article_fils"]:
                        if "code_article" in row_2:
                            item_nomenclature["code_article_fils"].append({"code_article": row_2["code_article"], "quantite": row_2["quantite"]})
        
        item_nomenclature["code_article_fils"] = sorted(item_nomenclature["code_article_fils"], key=lambda x: x["code_article"])

        dict_child_code = {}
        for i, row in enumerate(item_nomenclature["code_article_fils"]):
            if row["code_article"] not in dict_child_code:
                dict_child_code[row["code_article"]] = 0
            dict_child_code[row["code_article"]] += row["quantite"]
        list_child_code = []
        for code_art, qte in dict_child_code.items():
            list_child_code.append({"code_article": code_art, "quantite": qte})

        item_nomenclature["code_article_fils"] = list_child_code
        item_nomenclature["code_article_fils"] = sorted(item_nomenclature["code_article_fils"], key= lambda row: row["code_article"])

        #logger.info(f"{item_nomenclature}")
        return item_nomenclature



if __name__ == "__main__":
    logger.info("Extract, transform and load file 521 (items) and 531 (nomenclatures)")
    today = dt.datetime.now().date()
    today_str = today.strftime("%Y%m%d")
        
    make_folder()
    
    # file 521
    date_creation_file = get_date_creation_file(os.path.join(path_input, "QUOTIDIEN", today_str), file_name_521)
    if date_creation_file is None or date_creation_file != today:
        copy_file(path_exit, file_name_521, os.path.join(path_input, "QUOTIDIEN", today_str))

    items = Items(os.path.join(path_input, "QUOTIDIEN", today_str), file_name_521, sheet_names_521)
    items._write_parquet(os.path.join(path_output, today_str))
    
    shutil.copyfile(os.path.join(path_output, today_str, "items.parquet"), 
                    os.path.join(path_exit_parquet, "items.parquet"))
    
    shutil.copyfile(os.path.join(path_output, today_str, "manufacturers.parquet"), 
                    os.path.join(path_exit_parquet, "manufacturers.parquet"))
    
    shutil.copyfile(os.path.join(path_output, today_str, "equivalents.parquet"), 
                    os.path.join(path_exit_parquet, "equivalents.parquet"))

    
    # file 531
    date_creation_file = get_date_creation_file(os.path.join(path_input, "QUOTIDIEN", today_str), file_name_531)
    if date_creation_file is None or date_creation_file != today:
        copy_file(path_exit, file_name_531, os.path.join(path_input, "QUOTIDIEN", today_str))
    
    nomenclatures = Nomenclatures(os.path.join(path_input, "QUOTIDIEN", today_str), file_name_531, sheet_name_531)
    nomenclatures.df.write_parquet(os.path.join(path_output, today_str, "nomenclatures.parquet"))
    
    shutil.copyfile(os.path.join(path_output, today_str, "nomenclatures.parquet"), 
                    os.path.join(path_exit_parquet, "nomenclatures.parquet"))
    
    logger.info("End of extract, transform and load file 521 (items) and 531 (nomenclatures)")
    
        