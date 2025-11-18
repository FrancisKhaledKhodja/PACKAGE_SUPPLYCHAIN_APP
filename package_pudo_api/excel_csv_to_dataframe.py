import os
import unidecode
import polars as pl
from string import punctuation
import re
import openpyxl
#from package_supply_chain.my_loguru import logger



def transform_string(label: str) -> str:
    '''
    Transform the string in lowercase, remove the punctuation 
    and replace the spaces by an underscore 
    '''
    #logger.debug(f"Transforming string: {label}")
    label = label.lower().strip()
    label = unidecode.unidecode(label)
    
    # First replace special characters
    for punc in punctuation:
        if punc == "+":
            label = label.replace(punc, " et ")
        elif punc == "<":
            label = label.replace(punc, " inf ")
        elif punc == ">":
            label = label.replace(punc, " sup ")
        elif punc != "_":
            label = label.replace(punc, " ")

    # Nettoyer les espaces et les underscores
    label = re.sub(r"\s+", "_", label)
    label = re.sub(r"_+", "_", label)
    label = label.strip("_")

    # Remplacer "ndeg" par "n" s'il est présent
    if "ndeg" in label:
        label = label.replace("ndeg", "n")

    #logger.debug(f"Transformed string: {label}")
    return label


def transform_columns_name(dataframe: pl.DataFrame) -> pl.DataFrame:
    '''
    Transform the header of the dataframe with transform_string function 
    '''
    #logger.debug(f"Transforming columns names: {dataframe.columns}")
    name_columns = [transform_string(label) for label in dataframe.columns]
    #logger.debug(f"Transformed columns names: {name_columns}")
    name_columns_to_replace = []
    for i, name_col in enumerate(name_columns):
        if name_columns.count(name_col) > 1:
            name_columns_to_replace.append(name_col) 
    
    for name_col in name_columns_to_replace:
        count = 0
        flag = 1
        for i, name_col_2 in enumerate(name_columns):
            if flag and name_col_2 == name_col:
                flag = 0
            elif name_col_2 == name_col:
                name_columns[i] = "{}_{}".format(name_col_2, count)
                count += 1

    dataframe.columns = name_columns

    return dataframe


def read_excel(folder_path: str, file_name: str, sheet_name: str=None) -> pl.DataFrame:
    '''
    Read an Excel file and return a PolarsDataFrame.

    Args:
        folder_path (str): Path folder containing the Excel file
        file_name (str): Name of the Excel file
        sheet_name (str, optional): name of the sheet to read

    Returns:
        pl.DataFrame: Polars DataFrame containing the data of the sheet
    '''
    #logger.info(f"Reading Excel file and sheetname: {folder_path}\{file_name}, {sheet_name}")
    if not (file_name.endswith(".xlsx") or file_name.endswith(".xls")):
        raise Exception("Ce fichier n'est pas un fichier Excel")

    file_path = os.path.join(folder_path, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")

    try:
        # Lecture du classeur avec openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb[sheet_name] if sheet_name else wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            df = pl.DataFrame()
        else:
            headers = [str(h) if h is not None else "" for h in rows[0]]
            data_rows = rows[1:]
            records = [dict(zip(headers, r)) for r in data_rows]
            df = pl.DataFrame(records)
    except Exception as e:
        raise Exception(f"Erreur lors de la lecture du fichier Excel: {str(e)}")

    df = transform_columns_name(df)
    #logger.info(f"End reading Excel file: {folder_path}/{file_name}, {sheet_name}")

    return df


def read_csv(folder_path: str, file_name: str) -> pl.DataFrame:
    #logger.info(f"Reading Csv file: {folder_path}\{file_name}")
    if not file_name.endswith(".csv"):
        raise Exception("Ce fichier n'est pas un fichier Csv")
    
    file_path = os.path.join(folder_path, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
    
    try:
        df = pl.read_csv(file_path, separator=";", infer_schema_length=0)
    except Exception as e:
        raise Exception(f"Erreur lors de la lecture du fichier Excel: {str(e)}")

    df = transform_columns_name(df)
    #logger.info(f"End reading Csv file: {folder_path}/{file_name}")

    return df
    