import os
import shutil
import datetime as dt
from time import perf_counter

from supplychain_app.constants import (path_input, 
                                            path_output)


def get_execution_time(func):
    '''
    Calculate the execution time of a function
    '''
    def wrapper(*args, **kargs):        
        t0 = perf_counter()
        result = func(*args, **kargs)
        t1 = perf_counter()
        #logger.info("Temps d'execution: {} secondes".format(str(round(t1 - t0, 0))))
        return result
    return wrapper


def get_date_creation_file(name_folder, name_file):
    
    list_files = os.listdir(os.path.join(name_folder))
    if name_file in list_files:
        date_creation_file = os.path.getctime(os.path.join(name_folder, name_file))
        date_creation_file = dt.datetime.fromtimestamp(date_creation_file)
        
        return date_creation_file
    
    
def copy_file(name_folder_origin, name_file, name_folder_destination):
    shutil.copyfile(os.path.join(name_folder_origin, name_file), 
                    os.path.join(name_folder_destination, name_file))
    
def make_folder():
    today = dt.datetime.now().date()
    today_str = today.strftime("%Y%m%d")
    
    last_folders_input = os.listdir(os.path.join(path_input, "QUOTIDIEN"))
    last_folders_output = os.listdir(os.path.join(path_output))
    if today_str not in last_folders_input:
        os.mkdir(os.path.join(path_input, "QUOTIDIEN", today_str))
    if today_str not in last_folders_output:
        os.mkdir(os.path.join(path_output, today_str))
    
