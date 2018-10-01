#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask,jsonify,after_this_request,request
import logging
from logging.handlers import RotatingFileHandler
from uuid import getnode as get_mac
import requests
import sys

app = Flask(__name__)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('clients.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info("Running connection script!")

logger.info(str(sys.argv))

mac_address = sys.argv[1]
def getMac():
    logger.info("Getting mac")
    try:
        mac = get_mac()
        mac=':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
        return str(mac)
    except:
        return ""

payload = {
    "mac_address":mac_address
}
headers = {
    'Content-Type': "application/json",
    'Mac-Adress': getMac(),
    }

if sys.argv[3]=="True":
    url = "https://api.openap.io/devices/connectDevice"

elif sys.argv[3]=="False":
    url = "https://api.openap.io/devices/disconnectDevice"
else:
    url=""

response = requests.request("POST", url, json=payload, headers=headers)