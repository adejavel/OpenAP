import subprocess
from uuid import getnode as get_mac
import logging
from logging.handlers import RotatingFileHandler
import requests
import json
import netifaces
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('policies.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info("Running apply policies script!")


try:
    with open('/root/deviceInfo.json') as json_data:
        d = json.load(json_data)
        OPENAP_HOST=d["apiEndPoint"]
except:
    OPENAP_HOST="https://staging-api.openap.io/"

def getMac():
    logger.info("Getting mac")
    mac = str(netifaces.ifaddresses('eth0')[netifaces.AF_LINK][0]["addr"]).upper()
    logger.info("Mac is {}".format(mac))
    return mac

try:
    headers = {
        'Content-Type': "application/json",
        'Mac-Adress': getMac(),
    }
    url = "{}devices/getDevicePolicies".format(OPENAP_HOST)
    response = requests.request("GET", url, headers=headers)
    policy = json.loads(response.text)
    logger.info("Policies downloaded, applying")
    os.system("ebtables --flush")
    for client in policy["parameters"]["clients"]:
        os.system("ebtables -A FORWARD -s {} -j DROP".format(client["mac_address"]))

except:
    logger.exception("Error")