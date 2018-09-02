from flask import Flask,jsonify,after_this_request,request
import logging
from logging.handlers import RotatingFileHandler
from uuid import getnode as get_mac
import socket
import os
import shutil
import time
import json

app = Flask(__name__)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('agent.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

@app.route('/getConfig')
def get_config():
    return jsonify(getConfig())



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
@app.route('/applyConfig',methods=["POST"])
def applyConfig():
    try:
        config = json.loads(request.data, strict=False)
	logger.info(config)
        if config["type"]=="AP":
            for param in config["parameters"]:
                if param=="wifimode":
                    param2="hw_mode"
                elif param=="password":
                    param2="wpa_passphrase"
                else:
                    param2=param
                setParameterHostapdConfig(param2, config["parameters"][param])
            @after_this_request
            def reboot(test):
                time.sleep(1)
                os.system('sudo shutdown -r now')
                return test
            return jsonify({"status":True})
        else:
            return jsonify({"status": False})
    except:
	logger.info(request)
	logger.info(request.data)
	logger.info(request.json)
        logger.exception("error while applying config")
        return jsonify({"status": False})


def setParameterHostapdConfig(param,value):
    logger.info("Setting parameter {} as {} in hostapd config".format(param,value))
    try:

        with open("newconfig.conf", 'w') as new_file:
            with open("/etc/hostapd/hostapd.conf") as old_file:
                found = False
                for line in old_file:
                    if line.startswith(param):
                        found=True
                        new_file.write("{}={}\n".format(param,value))
                    else:
                        new_file.write(line)
                if not found:
                    new_file.write("{}={}\n".format(param, value))

        os.remove("/etc/hostapd/hostapd.conf")
        shutil.move("newconfig.conf", "/etc/hostapd/hostapd.conf")
        return {"status": True}
    except:
        logger.exception("Error while modifying hostapd config")
        return {"status": False}

if __name__ == '__main__':
    app.run(port=80,host="0.0.0.0")