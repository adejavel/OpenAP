import subprocess
from uuid import getnode as get_mac
import datetime
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
    logger.info(policy)
    logger.info("ebtables --flush")
    os.system("ebtables --flush")
    if policy["parameters"]["policy_type"]=="blacklist":
        key_word = "DROP"
        #logger.info("ebtables -P FORWARD ACCEPT")
        #os.system("ebtables -P FORWARD ACCEPT")
    if policy["parameters"]["policy_type"]=="whitelist":
        key_word = "ACCEPT"
        #logger.info("ebtables -P FORWARD DROP")
        #os.system("ebtables -P FORWARD DROP")
    for client in policy["parameters"]["clients"]:
        if client["always"]:
            logger.info("ebtables -A FORWARD -s {} -j {}".format(client["mac_address"],key_word))
            os.system("ebtables -A FORWARD -s {} -j {}".format(client["mac_address"],key_word))
        else:
            date_from = datetime.datetime.strptime(client["from"],'%H:%M')
            date_to = datetime.datetime.strptime(client["to"], '%H:%M')
            date_now = datetime.datetime.now()
            if date_from.time() > date_to.time():
                if (date_now.time()<=date_from.time() and date_now.time()<=date_to.time()) or (date_now.time()>=date_from.time() and date_now.time()>=date_to.time()):
                    logger.info("ebtables -A FORWARD -s {} -j {}".format(client["mac_address"], key_word))
                    os.system("ebtables -A FORWARD -s {} -j {}".format(client["mac_address"],key_word))
            else:
                if date_now.time()>=date_from.time() and date_now.time()<=date_to.time():
                    logger.info("ebtables -A FORWARD -s {} -j {}".format(client["mac_address"], key_word))
                    os.system("ebtables -A FORWARD -s {} -j {}".format(client["mac_address"],key_word))
    logger.info("ebtables -P FORWARD {}".format(key_word))
    os.system("ebtables -P FORWARD {}".format(key_word))



except:
    logger.exception("Error")