import socket
from uuid import getnode as get_mac
import os
import requests
import time
import json
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('autoboot.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def getMac():
    logger.info("Getting mac")
    try:
        mac = get_mac()
        mac=':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
        return str(mac)
    except:
        return ""

while True:
    try:
        logger.info("Trying to activate ngrok...")
        resp = os.popen('./ngrok http 80 > /root/test.log &').read()
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
                pass
        logger.info("Found tunnel {}".format(tunnel))
        logger.info("Running main code")
        os.system("python OpenAP/OpenAP/code/main.py &")
        logger.info("Done, sleeping 2 sec")
        time.sleep(2)
        logger.info("Registering to server")
        url = "https://api.openap.io/devices/register"

        payload = {
            "http_tunnel":tunnel
        }
        headers = {
            'Content-Type': "application/json",
            'Mac-Adress': getMac(),
            }

        response = requests.request("POST", url, json=payload, headers=headers)
        logger.info("Done!")

        print(response.text)

        exit()
        break
    except:
        time.sleep(5)