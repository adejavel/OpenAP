#!/usr/bin/python
import socket
from uuid import getnode as get_mac
import os
import requests
import time
import json
import logging
import subprocess
from logging.handlers import RotatingFileHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('autoboot.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info("Running autoboot script!")

#Updating system

try:
    update_filename = '/root/.index_update.json'
    try:
        with open(update_filename, 'r') as f:
            content = json.load(f)
    except:
        logger.exception("no json")
        content = {}

    with open('OpenAP/OpenAP/code/.update.json') as f2:
        updates = json.load(f2)

    if content.get("update_index") is None or not isinstance(content.get("update_index"), int):
        content = {
            "update_index": -1
        }
    index = content.get("update_index")
    for i, update in enumerate(updates):
        if index < i :
            index = i 
            os.system(update)

    content["update_index"] = index
    os.remove(update_filename)

    with open(update_filename, 'w') as f:
        json.dump(content, f, indent=4)

except:
    logger.exception("Error")


while True:
    try:

        subprocess.Popen("python OpenAP/OpenAP/code/main.py", shell=True)
        break
    except:
        time.sleep(5)