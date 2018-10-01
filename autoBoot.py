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



while True:
    try:
        subprocess.Popen("python OpenAP/OpenAP/code/main.py", shell=True)
        break
    except:
        time.sleep(5)