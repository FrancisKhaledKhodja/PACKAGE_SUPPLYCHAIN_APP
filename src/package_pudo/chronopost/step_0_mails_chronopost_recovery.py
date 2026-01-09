import os
import shutil
import datetime as dt

import win32com.client
from package_pudo.chronopost.constants import *
from package_pudo.my_loguru import logger


def get_file_attachment(email_inbox: str, sender_email: list, list_folders_outlook: list, backup_recovery: str, list_files_already_saved: list):
    """Save attached files in an outlook email

    Args:
        email_inbox (str): inbox to scan
        sender_email (list): list of emails to scan
        list_folders_outlook (list): list of folders to scan
        backup_recovery (str): absolute path to save the files
        list_files_already_saved (list): list of files that you do not want to save again
    """
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

    for folder in list_folders_outlook:
        inbox = outlook.Folders(email_inbox).Folders(folder)
        messages = inbox.items
        for message in messages:
            try:
                sender_name = getattr(message, "SenderName", None)
                if sender_name and message.SenderName in sender_email:
                    files_attachment_number = message.Attachments.Count
                    if files_attachment_number > 0:
                        for i in range(1, files_attachment_number + 1):
                            file_attachment_name = message.Attachments.item(i).FileName
                            print("Fichier joint trouvé: {}".format(file_attachment_name))
                            if file_attachment_name not in list_files_already_saved:
                                file_name_path = os.path.join(backup_recovery, file_attachment_name)
                                print("Sauvegarde du fichier: {}".format(file_attachment_name))
                                message.Attachments.item(i).SaveAsFile(file_name_path)
            except TypeError as e:
                print("Probleme detecte: ", e)
                continue


def get_body_email(email_inbox: str, sender_email: list, list_folders_outlook: list, subject: str, backup_recovery: str, file_name_header, list_files_already_saved: list):
    """Save body from an outlook email

    Args:
        email_inbox (str): inbox to scan
        sender_email (list): emails to scan
        list_folders_outlook (list): list of folders to scan
        subject (str): email's subject to select
        backup_recovery (str): absolute path to save the files
        file_name_header ([type]): file name header given to the email's body
        list_files_already_saved (list): list of files that you do not want to save again
    """
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

    for folder in list_folders_outlook:
        inbox = outlook.Folders(email_inbox).Folders(folder)
        messages = inbox.items
        for message in messages:
            try:
                sender_name = getattr(message, "SenderName", None)
                if sender_name and message.SenderName in sender_email:
                    if message.Subject == subject:
                        body = message.Body
                        received_time_date = message.ReceivedTime.strftime("%Y%m%d")
                        file_name = f"{file_name_header}_{received_time_date}.csv"
                        print("Fichier dans corps du message trouvé: {}".format(file_name))
                        if file_name not in list_files_already_saved:
                            file_name_path = os.path.join(backup_recovery, file_name)
                            print("Sauvegarde du fichier dans le corps du message: {}".format(file_name))
                            with open(file_name_path, "w") as f:
                                body = body.split("\r\n")
                                for row in body:
                                    f.write(row + "\n")
            except TypeError as e:
                print("Probleme detecte: ", e)
                continue



def ensure_pudo_dirs():
    """Ensure required directories exist for PUDO Chronopost and LM2S processing."""
    required_paths = [
        os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_CSV),
        os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_EXCEL),
        os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_FUSION_EXCEL),
        os.path.join(path_pudo, folder_chronopost, "ELIGIBILITE"),
        os.path.join(path_pudo, "GESTION_PR", "ANNUAIRE_PR"),
        os.path.join(path_pudo, "GESTION_PR", "CARNET_CHRONOPOST"),
        os.path.join(path_pudo, "LM2S"),
    ]
    for p in required_paths:
        if not os.path.exists(p):
            os.makedirs(p)


def get_mail_chronopost():
    ensure_pudo_dirs()
    pudo_files = os.listdir(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_CSV))
    get_file_attachment(EMAIL_INBOX, SENDER_EMAIL, [FOLDER_1], os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_CSV), pudo_files)
    get_body_email(EMAIL_INBOX, SENDER_EMAIL, [FOLDER_1], SUBJECT, os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_CSV), FILE_NAME_HEADER_C13, pudo_files)
    
    
if __name__ == "__main__":
    logger.info("Call of the script step_0_mails_chronopost_recovery")
    
    today = dt.datetime.now().date().strftime("%Y%m%d")
    get_mail_chronopost()
    
    number_of_copy_files = 0
    for name_file in sorted(os.listdir(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_CSV)), reverse=True):
        if today in name_file:
            shutil.copyfile(os.path.join(path_pudo, folder_chronopost, FOLDER_C9_C13_CSV, name_file), 
                            os.path.join(path_exit_pr, folder_chronopost, FOLDER_C9_C13_CSV, name_file))
            number_of_copy_files += 1
            if number_of_copy_files == 2:
                break
            
    logger.info("End of call of the script step_0_mails_chronopost_recovery")
