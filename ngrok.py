#!/usr/bin/python
import socket
from uuid import getnode as get_mac
import os
import requests
import time
import json
import logging
import subprocess
import psutil
from logging.handlers import RotatingFileHandler
import netifaces

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('ngrok.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info("Running ngrok script!")

try:
    with open('/root/deviceInfo.json') as json_data:
        d = json.load(json_data)
        OPENAP_HOST=d["apiEndPoint"]
except:
    OPENAP_HOST="https://staging-api.openap.io/"

def getMac():
    logger.info("Getting mac")
    logger.info(netifaces.interfaces())
    logger.info(netifaces.ifaddresses('eth0')[netifaces.AF_LINK])
    mac = str(netifaces.ifaddresses('eth0')[netifaces.AF_LINK][0]["addr"]).upper()
    logger.info("Mac is {}".format(mac))
    return mac
    # try:
    #     mac = get_mac()
    #     mac=':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
    #     return str(mac)
    # except:
    #     return ""

def getIP():
    logger.info("Getting IP address")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('192.0.0.8', 1027))
        except socket.error:
            return None
        return str(s.getsockname()[0])
    except:
        logger.exception("Error while getting IP address")


while True:
    try:
        for proc in psutil.process_iter():
            if "ngrok" in proc.name():
                proc.kill()
        time.sleep(2)
        logger.info("Trying to activate ngrok...")
        resp = os.popen('./ngrok http 80 > /test.log &').read()
        logger.info("...Success => waiting 5 sec")
        time.sleep(5)
        logger.info("Getting tunnel")
        for i in range(8):
            try:
                resp = requests.get("http://localhost:404{}/api/tunnels".format(i))
                j = json.loads(resp.text)
                tunnel = j["tunnels"][0]["public_url"]
                break
            except:
                logger.exception("test")
                pass
        logger.info("Found tunnel {}".format(tunnel))
        logger.info("Running main code")
        logger.info("Done, sleeping 2 sec")
        time.sleep(2)
        logger.info("Registering to server")
        url = "{}devices/register".format(OPENAP_HOST)
        ip= getIP()
        payload = {
            "http_tunnel":tunnel,
            "ip_address":ip
        }
        headers = {
            'Content-Type': "application/json",
            'Mac-Adress': getMac(),
            }

        response = requests.request("POST", url, json=payload, headers=headers)
        logger.info("Done!")

        logger.info(response.text)

        break
    except:
        logger.exception("Error")
        time.sleep(5)