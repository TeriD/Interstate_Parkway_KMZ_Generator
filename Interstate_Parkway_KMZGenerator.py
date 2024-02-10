#
# =====================================================================================================
# Name:        Interstate_Parkway_KMZGenerator.PY
# Purpose:     To create KMZ files requested by Highway Design.
# Description: This script was derived from an ArcMap model export of preformatted layerfiles to KMZ 
#               files for each district into a subfolder on N:\BRMaint\Mapping.
# Author:      Teri Dowdy
# Created:     2023-10-03
# Modified:    2023-12-14
# License:     Advanced
# Python Version: 3.x
# Copyright: (c) Kentucky Transportation Cabinet @2023.
# =====================================================================================================
#
""" Notes:  This script performs the following tasks in order:
        1.  Delete old local working folders.
        2.  Create folder based on today's date
        3.  Process KMZs from layerfiles
        4.  Copy KMZ folder to both local working folder and N:\EVERYONE\GIS\KMZ_Files
        5.  Email completion failure sent to GIS Team SDE Administrators.
"""
#
# -----------------------------------------------------------------------------------------------------
# MODULES
# -----------------------------------------------------------------------------------------------------
import arcpy
import json
import logging
import os
import os.path
import shutil
from shutil import copytree, ignore_patterns
import datetime, time
import subprocess
import smtplib
import sys
import traceback

# -----------------------------------------------------------------------------------------------------
# DEFINE CONSTANTS
# -----------------------------------------------------------------------------------------------------
ERROR_SUBJECT = "Interstate_Parkway KMZ Generator ETL TST Error"
ERROR_BODY = "\n\n================================================================================= \
            \n\nThe weekly ETL for generating KMZs for Interstates and Parkways has failed. \
            \n\n Please check the log file for errors. \
            \n\n================================================================================= "
            
SUCCESS_SUBJECT = "Interstate_Parkway KMZ Generator ETL TST Success"
SUCCESS_BODY = "\n\n================================================================================= \
            \n\nThe weekly ETL for generating KMZs for Interstates and Parkways has completed successfully. \
            \n\n================================================================================= "
            
# ----------------------------------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------------------------------

def delete_files_in_directory(export_dir):
   try:
     files = os.listdir(export_dir)
     for file in files:
       file_path = os.path.join(export_dir, file)
       if os.path.isfile(file_path):
         os.remove(file_path)
     logging.info("All files deleted successfully.")
   except Exception as e:
       tb = traceback.format_exc()
       error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
       logging.error("Error occurred on line {error_line} while deleting files: {str(e)}\n{tb}")
       sendEmail(ERROR_SUBJECT, ERROR_BODY)
       sys.exit(1)   
    
def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

def is_drive_mapped(drive_letter):
    result = subprocess.run(f'net use {drive_letter}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def map_network_drive(drive_letter, network_path):
    try:
        if not is_drive_mapped(drive_letter):
            subprocess.run(['net', 'use', drive_letter, network_path], check=True)
            logging.info(f"Drive {drive_letter} has been mapped to {network_path}")
    except subprocess.CalledProcessError as e:
        tb = traceback.format_exc()
        error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
        logging.error(f"An error occurred on line {error_line} while mapping the drive: {e}")
        sys.exit(1)
    
def unmap_network_drive(drive_letter):
    if is_drive_mapped(drive_letter):
        try:
            subprocess.run(f'net use {drive_letter} /delete', shell=True, check=True)
            logging.info(f'Drive {drive_letter} has been unmapped.')
        except subprocess.CalledProcessError:
            tb = traceback.format_exc()
            error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
            logging.error(f'Error occurred on line {error_line} while trying to unmap drive {drive_letter}.')
            sys.exit(1)
    else:
        logging.info(f'Drive {drive_letter} is not mapped.')
        
def sendEmail(esubject, eMessage):
    # Import modules necessary for sending email
    from email.message import EmailMessage
    # Generate email message
    msg = EmailMessage()
    msg['From'] = "noreply@ky.gov"
    msg['To'] = "teri.dowdy@ky.gov" # , emily.bartee@ky.gov"
    msg['CC'] = ""
    msg['Subject'] = esubject
    msg.set_content(eMessage)
    # Send email message via SMTP server
    smtpServer = smtplib.SMTP('SMTP.ky.gov',25)
    smtpServer.send_message(msg)
    smtpServer.quit()
    logging.info(f"Email sent to GIS Team SDE Administrators.")
# -----------------------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------------------------------  

# Get date for process documentation
today = datetime.date.today()

# Initiate config location and read parameters
try:
    # Open the config file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "config.json")

    with open(file_path, "r") as file:
        data = json.load(file)
    
        # Access the variables from the loaded JSON data
        working_dir = data["working_dir"]

        if not working_dir:
            raise ValueError("working_dir is not defined in the config file")

        log_file = os.path.join(working_dir, "logs", "app.log")
        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        logging.info(today)
        logging.info(f"Working directory imported from Config file: {working_dir}")

        # Retrieve other variables from config
        export_dir = working_dir + "\\KMZ_Exports"
        layer_dir = working_dir + "\\LayerFiles"
        sde_dir = data["sde_dir"]
        prd_conn = data["prd_conn"]
        j_drive = data.get("drive_mappings", {}).get('j_drive')
        n_drive = data.get("drive_mappings", {}).get('n_drive')
        logging.info(f"Other parameters imported from Config file.")
        
except json.JSONDecodeError as e:
    tb = traceback.format_exc()
    error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
    log_file_path = os.path.join(working_dir, "logs", "app.log")
    logging.error(f"Invalid JSON in config file on line {error_line}: {str(e)}")
    sendEmail(ERROR_SUBJECT, ERROR_BODY)
    sys.exit(1)
except Exception as e:
    tb = traceback.format_exc()
    error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
    log_file_path = os.path.join(working_dir, "logs", "app.log")
    logging.error(f"Unexpected error on line {error_line}: {str(e)}")
    sendEmail(ERROR_SUBJECT, ERROR_BODY)
    sys.exit(1)

# Delete old local working folders. This keeps the working folder clean.
try:
    dirs = [d for d in os.listdir(export_dir) if os.path.isdir(os.path.join(export_dir, d))]
    for d in dirs:
        path = os.path.join(export_dir, d)
        shutil.rmtree(path, ignore_errors=False)

    delete_files_in_directory(export_dir)
    logging.info(f"Old local working files deleted.")
except Exception as e:
    tb = traceback.format_exc()
    error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
    logging.error(f"Unexpected error on line {error_line}: {str(e)}")
    sendEmail(ERROR_SUBJECT, ERROR_BODY)
    sys.exit(1)

# Process KMZs from layerfiles
try:
    for fn in os.listdir(layer_dir):
        if fn.endswith('lyrx'):
            logging.info(f"     {fn}")
            layer_source = layer_dir + "\\" + fn
            layer_dest = fn[:-4] + 'kmz'
            kmzEXPORT = export_dir + "\\" + layer_dest
            logging.info(f"     {kmzEXPORT}")
        
            arcpy.LayerToKML_conversion(layer_source, kmzEXPORT, 0, "NO_COMPOSITE",
                                        "3854285.94004372 3350081.56140465 5994554.76153164 4302135.45716181",
                                        1024, 96, "CLAMPED_TO_GROUND")
    logging.info(f"KMZ files created.")
except Exception as e:
    tb = traceback.format_exc()
    error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
    logging.error(f"Unexpected error on line {error_line}: {str(e)}")
    sendEmail(ERROR_SUBJECT, ERROR_BODY)
    sys.exit(1)


# Copy KMZ folder to N:\Everyone\GIS\KMZ_Files
# Unmap J: network drive if exists
unmap_network_drive('J:')

# Map N: drive if it doesn't exist
map_network_drive('N:', n_drive)

root_src_dir = export_dir
root_dst_dir = r"N:\EVERYONE\GIS\KMZ_Files"

for src_dir, dirs, files in os.walk(root_src_dir):
    dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    for file_ in files:
        src_file = os.path.join(src_dir, file_)
        dst_file = os.path.join(dst_dir, file_)
        if os.path.exists(dst_file):
            # in case of the src and dst are the same file
            if os.path.samefile(src_file, dst_file):
                continue
            os.remove(dst_file)
        shutil.move(src_file, dst_dir)

# Validate that the KMZ files were created
#    If not, send email to GIS Team SDE Administrator Lead.
all_files_correct = True

for file in os.listdir(root_dst_dir):
    if file.endswith(".kmz"):
        filetime = datetime.datetime.fromtimestamp(os.path.getctime(root_dst_dir + '\\' + file))
        if filetime.date() == today:
            logging.info(f"File transfer was successful for {file} on: {filetime}")
        else:
            all_files_correct = False
            break

if not all_files_correct:
    sendEmail(ERROR_SUBJECT, ERROR_BODY)
    sys.exit(1)

# Reset network drive mapping
unmap_network_drive('N:')

map_network_drive('J:', r'\\eas.ds.ky.gov\dfs\HIS_Archives')

# Send email to GIS Team SDE Administrator Lead.
sendEmail(SUCCESS_SUBJECT, SUCCESS_BODY)

print("EOF - processing complete.")
logging.info(f"EOF - processing complete.")
# =====================================================================================================