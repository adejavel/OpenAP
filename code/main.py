# -*- coding: utf-8 -*-
import requests
import json
import time
import os
import socket
import zipfile
import shutil
import logging
from logging.handlers import RotatingFileHandler
from uuid import getnode as get_mac

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('agent.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#__BASE__URL__="http://192.168.43.213:8080"

with open('.config.json') as f:
    data = json.load(f)
    __BASE__URL__ = data["__BASE__URL__"]

def getActions():
    url = "{}/getActions".format(__BASE__URL__)
    response = requests.request("GET", url)
    return json.loads(response.text)

def answerAction(id, result):
    print "answering action"
    logger.info("Answering action id {} at {}".format(id,time.time()))
    try:
        url = "{}/answerAction".format(__BASE__URL__)
        payload = {
            "id": id,
            "result": result
        }
        headers = {
            'Content-Type': "application/json",
        }
        requests.request("POST", url, data=json.dumps(payload), headers=headers)
        logger.info("Action {} answered".format(id))
    except:
        logger.exception("An error occured while answering action")

def executeActions(actions):
    reboot = False
    logger.info("Executing {} actions".format(len(actions)))
    try:
        for action in actions:
            try:
                if action["type"]=="ping":
                    logger.info("Found ping action")
                    answer = ping(action["parameters"])
                    logger.info("ping method executed successfully")
                    answerAction(action["_id"]["$oid"],answer)
                elif action["type"]=="reboot":
                    logger.info("Found reboot action")
                    answer = {"status":True}
                    answerAction(action["_id"]["$oid"], answer)
                    reboot=True
                elif action["type"] == "get_config":
                    logger.info("Found get_config action")
                    answer = getConfig()
                    logger.info("getConfig method executed successfully")
                    answerAction(action["_id"]["$oid"], answer)
                elif action["type"]== "reload_code":
                    logger.info("Found reload_code action")
                    answer = reloadCode()
                    logger.info("reloadCode method executed successfully")
                    answerAction(action["_id"]["$oid"], answer)
                    os.system("python code/main.py")
                    exit()
                elif action["type"]=="rename_ssid":
                    logger.info("Found rename_ssid action")
                    answer= renameSSID(action["parameters"])
                    logger.info("renameSSID method executed successfully")
                    answerAction(action["_id"]["$oid"], answer)
                    reboot = True
            except:
                logger.exception("An error occured while executing 1 action")
        if reboot:
            os.system('sudo shutdown -r now')
    except:
        logger.exception("Error occured while executing actions")

def ping(parameters):
    logger.info("Executing ping action")
    try:
        print "pinging"
        address = parameters["address"]
        response = os.system("ping -c 1 {}".format(address))
        if response==0:
            return {"status":True}
        else:
            return {"status": False}
    except:
        logger.exception("Error while pinging")
        return {"status": False}

def getConfig():
    logger.info("Executing getConfig action")
    try:
        ip = getIP()
        mac = getMac()
        hostapdConfig = parseHostapdConfig()
        return {"status":True,"config":{"ip_address":ip,"hostapd_config":hostapdConfig,"mac_address":mac}}
    except:
        logger.exception("Error while getting config")
        return {"status": False}

def parseHostapdConfig():
    logger.info("Parsing hostapd config")
    try:
        hostapdConfig={}
        with open("/etc/hostapd/hostapd.conf") as config:
            for line in config:
                if not line.startswith("#"):
                    words = line.split("=")
                    if len(words)>2:
                        value = "=".join(words[1:])
                    else:
                        value = words[1]
                    value = str.replace(value,"\n","")
                    hostapdConfig[words[0]] = value
        return hostapdConfig
    except:
        logger.exception("Error while paring hostapd config")


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

def getMac():
    logger.info("Trying to get mac address")
    try:
        mac = get_mac()
        mac=':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
        return mac
    except:
        logger.exception("Error while getting mac address")
        return ""

def reloadCode():
    logger.info("Reloading code")
    try:
        r = requests.get("{}/getConfig".format(__BASE__URL__))
        shutil.rmtree("code")
        with open("code.zip", "wb") as code:
            code.write(r.content)

        with zipfile.ZipFile("code.zip", "r") as zip_ref:
            zip_ref.extractall("")

        os.remove("code.zip")

        return {"status": True}
    except:
        logger.exception("Error while reloading the code")
        return {"status": False}

def renameSSID(parameters):
    logger.info("Renaming SSID action")
    try:
        ssid = parameters["name"]
        answer = setParameterHostapdConfig("ssid",ssid)
        os.system("service hostapd restart")
        return answer
    except:
        logger.exception("Error while renaming SSID")
        return {"status": False}

def setParameterHostapdConfig(param,value):
    logger.info("Setting parameter {} as {} in hostapd config".format(param,value))
    try:
        with open("newconfig.conf", 'w') as new_file:
            with open("/etc/hostapd/hostapd.conf") as old_file:
                for line in old_file:
                    if line.startswith(param):
                        new_file.write("{}={}\n".format(param,value))
                    else:
                        new_file.write(line)
        os.remove("/etc/hostapd/hostapd.conf")
        shutil.move("newconfig.conf", "/etc/hostapd/hostapd.conf")
        return {"status": True}
    except:
        logger.exception("Error while modifying hostapd config")
        return {"status": False}

while True:
    try:
        print "Checking for actions"
        actions = getActions()
        print actions
        if len(actions)!=0:
            executeActions(actions)
        time.sleep(10)
    except:
        logger.exception("Error while checking for actions")


