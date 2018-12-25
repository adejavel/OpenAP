#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask,jsonify,after_this_request,request
import logging
from logging.handlers import RotatingFileHandler
from uuid import getnode as get_mac
import socket
import os
import shutil
import time
import json
import subprocess
import netifaces
from crontab import CronTab

app = Flask(__name__)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('agent.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info("Running main script!")


DEFAULT_PARAMETERS=["wpa","wpa_key_mgmt","wpa_pairwise","rsn_pairwise","ieee80211n","ht_capab","ctrl_interface","ctrl_interface_group"]
HOSTAPD_DEFAULT_CONFIG={
    "bridge":"br0",
    "country_code":"US",
    "ignore_broadcast_ssid":"0",
    "macaddr_acl":"0",
    "wmm_enabled":"1",
    "ctrl_interface":"/var/run/hostapd",
    "ctrl_interface_group":"0"
}

@app.route('/getConfig',methods=["POST"])
def get_config():
    resp = getConfig(request)
    logger.info(resp)
    return jsonify(resp)


@app.route('/getUSBStructure',methods=["GET"])
def getStructureUSB():
    try:
        data = os.popen("tree -JfsD /media/pi")
        jsonData = json.loads(data.read())[0]["contents"]
        newData=[]
        for elem in jsonData:
            logger.info(elem)
            if elem["type"] == "directory":
                elem["contents"] = getMimeType(elem["contents"])
                newData.append(elem)
            elif elem["type"] == "file":
                elem["mime_type"] = os.popen("file -b --mime-type {}".format(elem["name"])).read().replace("\n","")
                newData.append(elem)
        logger.info(jsonData)
        logger.info("##################")
        logger.info("##################")
        logger.info("##################")
        logger.info(newData)
        return jsonify(newData)
    except:
        logger.exception("Error")
        return jsonify({"error":True})

def getMimeType(content):
    for elem in content:
        #logger.info(elem)
        if elem["type"]=="directory":
            elem["contents"]=getMimeType(elem["contents"])
        elif elem["type"]=="file":
            elem["mime_type"]=os.popen("file -b --mime-type {}".format(elem["name"].replace(" ","\ ").encode('utf-8'))).read()
    return content


def checkIWConfig():
    wlanResult = os.popen("iwconfig | grep wlan")
    wlanResult = wlanResult.read()
    wlanList=[]
    for line in wlanResult.split('\n'):
        if "wlan" in line.split(" ")[0]:
            wlanList.append(line.split(" ")[0])
    logger.info(wlanList)
    globalResult={}
    globalInterObj={}
    for wlanInt in wlanList:
        output = os.popen("iw {} info".format(wlanInt))
        output = output.read()
        #logger.info(output)
        wlan = 0
        for line in output.split('\n'):
            if "phy" in line:
                logger.info("Found phy interface")
                wlan = line.split()[1]
        logger.info(wlan)
        output2 = subprocess.check_output('iw phy{} info'.format(wlan), shell=True)
        obj = {
            "bgn": [],
            "a": []
        }
        inBand1 = False
        inBand2 = False
        inFreq = False
        for line in output2.split('\n'):
            #logger.info(line)
            raw = repr(line)
            line2 = line.replace(" ", "")
            leading_spaces = len(line2) - len(line2.lstrip())
            if inFreq:
                if leading_spaces != 3:
                    inFreq = False
                else:
                    if not "radar detection" in raw and not "disabled" in raw:
                        fr = (line.split("[")[1]).split("]")[0]
                        if inBand1:
                            obj["bgn"].append(int(fr))
                        elif inBand2:
                            obj["a"].append(int(fr))
            if "Band 1" in line:
                inBand1 = True
                inBand2 = False
                inFreq = False
            elif "Band 2" in line:
                inBand1 = False
                inBand2 = True
                inFreq = False
            if "Frequencies" in line:
                inFreq = True

        finalObject = {
            "bgn": obj["bgn"],
            "a": {
                "40": [],
                "20": []
            }
        }
        interObj = {
            "bgn": obj["bgn"],
            "a": {
                "40": {},
                "20": []
            }
        }
        for channel in obj["a"]:
            if ((channel - 4) in obj["a"] and (channel - 2) in obj["a"]):
                if not channel in finalObject["a"]["40"]:
                    finalObject["a"]["40"].append(channel)
                if str(channel) in interObj["a"]["40"]:
                    interObj["a"]["40"][str(channel)] = "+-"
                else:
                    interObj["a"]["40"][str(channel)] = "-"
            if ((channel + 4) in obj["a"] and (channel + 2) in obj["a"]):
                if not channel in finalObject["a"]["40"]:
                    finalObject["a"]["40"].append(channel)
                if str(channel) in interObj["a"]["40"]:
                    interObj["a"]["40"][str(channel)] = "+-"
                else:
                    interObj["a"]["40"][str(channel)] = "+"
            if not channel in finalObject["a"]["20"]:
                finalObject["a"]["20"].append(channel)
            if not channel in interObj["a"]["20"]:
                interObj["a"]["20"].append(channel)
        logger.info(finalObject)
        # print interObj

        #finalObject["interface"]=wlanInt
        globalResult[wlanInt]=finalObject
        globalInterObj[wlanInt] = interObj
        #globalResult.append(finalObject)
    with open('hostapd_available_config.json', 'w') as fp:
        json.dump({"configs": globalInterObj, "time": time.time()}, fp)
    return globalResult



@app.route('/checkConfigHostapd',methods=["GET"])
def checkConfigHostapd():
    logger.info("Trying to parse hostapd configuration")
    try:
        finalobj = checkIWConfig()
        return jsonify({"status": False,"parsedConfig":finalobj})

    except:
        logger.exception("Failer to parse hotapd config")
        return jsonify({"status":False})



def getConfig(request):
    logger.info("Executing getConfig action")
    logger.info(request.json)
    try:
        data = request.json
        policy_config=data["policy_config"]
        applyPolicyConfig(policy_config)
        if "applied_config" in data:
            config = data["applied_config"]
            interface=config["parameters"]["interface"]
            ip = getIP()
            mac = getMac()
            hostapdConfig = parseHostapdConfig()
            if config["type"]=="AP":
                logger.info("Comparing config")
                finalobj={}
                configH = parseHostapdConfig()
                try:
                    finalobj = checkIWConfig()
                except:
                    pass
                if not compareConfig(configH,config["parameters"]):
                    logger.info("Not in SYNC")
                    try:
                        os.system("killall hostapd")
                    except:
                        pass
                    applyConfiguration(config)
                    try:
                        os.system("killall hostapd")
                    except:
                        pass
                    logger.info("Not same config")
                    applyConfiguration(config)
                    logger.info("Config applied, trying to reboot")
                    start = restartHostapd()
                    if not start:
                        logger.info("not started")
                        try:
                            with open('hostapd_available_config.json') as f2:
                                channel = getFieldHostapdConfig("channel")
                                data = json.load(f2)
                                avai = data["configs"][interface]["a"]["40"][channel]
                                logger.info(avai)
                                ht_capab = getFieldHostapdConfig("ht_capab")
                                if ht_capab is not None:
                                    logger.info(ht_capab)
                                    if ht_capab == "[HT40-][SHORT-GI-40]" and "+" in avai:
                                        logger.info("trying 40 +")
                                        setParameterHostapdConfig("ht_capab", "[HT40+][SHORT-GI-40]")
                                    elif ht_capab == "[HT40+][SHORT-GI-40]" and "-" in avai:
                                        logger.info("trying 40 -")
                                        setParameterHostapdConfig("ht_capab", "[HT40-][SHORT-GI-40]")
                                start = restartHostapd()
                        except:
                            logger.exception("error")
                            pass
                    if not start:
                        logger.info("not started")
                        try:
                            with open('hostapd_available_config.json') as f2:
                                channel = getFieldHostapdConfig("channel")
                                data = json.load(f2)
                                avai = data["configs"][interface]["a"]["40"][channel]
                                logger.info(avai)
                                ht_capab = getFieldHostapdConfig("ht_capab")
                                if ht_capab is not None:
                                    logger.info(ht_capab)
                                    logger.info("trying 20")
                                    setParameterHostapdConfig("ht_capab", None)
                                start = restartHostapd()
                        except:
                            logger.exception("error")
                            pass

                    if start:
                        logger.info("started!")
                        return {"status": True, "inSync": True,
                                "config": {"ip_address": ip, "hostapd_config": hostapdConfig, "mac_address": mac,
                                           "checked_hostapd_config": finalobj}}

                    else:
                        logger.info("not started!")
                        return {"status": False, "inSync": False,
                                "config": {"ip_address": ip, "hostapd_config": hostapdConfig, "mac_address": mac,
                                           "checked_hostapd_config": finalobj}}

                else:
                    logger.info("In sync!")
                    #logger.info(hostapdConfig)
                    return {"status": True, "inSync": True,"config": {"ip_address": ip, "hostapd_config": hostapdConfig, "mac_address": mac,"checked_hostapd_config":finalobj}}
            else:
                return {"status":False}
        else:
            logger.info("no applied config")
            return {"status": True}
    except:
        logger.exception("Error while getting config")
        return {"status": False}


def compareConfig(deviceConfig,appliedConfig):
    toIgnore=["wpa","wpa_key_mgmt","wpa_pairwise","rsn_pairwise","ieee80211n","ht_capab","width"]
    for key in deviceConfig:
        if key not in toIgnore:
            if key in appliedConfig:
                if deviceConfig[key]!=appliedConfig[key]:
                    return False
            else:
                return False
    for key in appliedConfig:
        if key not in toIgnore:
            if key in deviceConfig:
                if deviceConfig[key]!=appliedConfig[key]:
                    return False
            else:
                return False
    return True


def parseHostapdConfig():
    logger.info("Parsing hostapd config")
    try:
        hostapdConfig={}
        with open("/etc/hostapd/hostapd.conf") as config:
            for line in config:
                if not line.startswith("#"):
                    words = line.split("=")
                    # if words[0]=="ht_capab":
                    #     hostapdConfig["width"]="40"
                    if not words[0] in HOSTAPD_DEFAULT_CONFIG and not words[0] in DEFAULT_PARAMETERS:
                        if len(words)>2:
                            value = "=".join(words[1:])
                        else:
                            value = words[1]
                        value = str.replace(value,"\n","")
                        hostapdConfig[translateFromPiToServer(words[0])] = value
        return hostapdConfig
    except:
        logger.exception("Error while paring hostapd config")
        return {}


def getFieldHostapdConfig(field):
    logger.info("trying to get {}".format(field))
    try:
        toRet = None
        with open("/etc/hostapd/hostapd.conf") as config:
            for line in config:
                if not line.startswith("#"):
                    words = line.split("=")
                    if words[0] == field:
                        toRet= words[1].rstrip()
        return toRet
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
    logger.info("Getting mac")
    mac = str(netifaces.ifaddresses('eth0')[netifaces.AF_LINK][0]["addr"]).upper()
    logger.info("Mac is {}".format(mac))
    return mac
    # try:
    #     mac = get_mac()
    #     mac=':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
    #     return str(mac)
    # except:
    #     return ""


def applyPolicyConfig(policy_config):
    cron = CronTab(user=True)
    cron.remove_all(command="OpenAP/OpenAP/code/applyPolicies.py")
    for client in policy_config["parameters"]["clients"]:
        if not client["always"]:
            from_hour = client["from"].split(":")[0]
            from_min = client["from"].split(":")[1]
            to_hour = client["to"].split(":")[0]
            to_min = client["to"].split(":")[1]
            job = cron.new(command='python /root/OpenAP/OpenAP/code/applyPolicies.py')
            job.setall("{} {} * * *".format(from_min,from_hour))
            job2 = cron.new(command='python /root/OpenAP/OpenAP/code/applyPolicies.py')
            job2.setall("{} {} * * *".format(to_min, to_hour))
    cron.write()
    os.system("python /root/OpenAP/OpenAP/code/applyPolicies.py")


@app.route('/applyConfig',methods=["POST"])
def applyConfig():
    try:

        config = json.loads(request.data, strict=False)
        #logger.info(config)
        policy_config= config["policy_config"]
        applyPolicyConfig(policy_config)
        config=config["network_config"]
        logger.info(config)
        if config["type"]=="AP":
            logger.info("Configuring AP")
            Hconf = parseHostapdConfig()
            if not compareConfig(config["parameters"],Hconf):
                try:
                    os.system("killall hostapd")
                except:
                    pass
                logger.info("Not same config")
                applyConfiguration(config)
                try:
                    interface=config["parameters"]["interface"]
                except:
                    interface="wlan0"
                logger.info("Config applied, trying to reboot")
                start = restartHostapd()
                if not start:
                    logger.info("not started")
                    try:
                        with open('hostapd_available_config.json') as f2:
                            channel = getFieldHostapdConfig("channel")
                            data = json.load(f2)
                            avai = data["configs"][interface]["a"]["40"][channel]
                            #logger.info(avai)
                            ht_capab = getFieldHostapdConfig("ht_capab")
                            if ht_capab is not None:
                                #logger.info(ht_capab)
                                if ht_capab == "[HT40-][SHORT-GI-40]" and "+" in avai:
                                    logger.info("trying 40 +")
                                    setParameterHostapdConfig("ht_capab", "[HT40+][SHORT-GI-40]")
                                elif ht_capab == "[HT40+][SHORT-GI-40]" and "-" in avai:
                                    logger.info("trying 40 -")
                                    setParameterHostapdConfig("ht_capab", "[HT40-][SHORT-GI-40]")
                            start = restartHostapd()
                    except:
                        logger.exception("error")
                        pass
                if not start:
                    logger.info("not started")
                    try:
                        with open('hostapd_available_config.json') as f2:
                            channel = getFieldHostapdConfig("channel")
                            data = json.load(f2)
                            avai = data["configs"][interface]["a"]["40"][channel]
                            #logger.info(avai)
                            ht_capab = getFieldHostapdConfig("ht_capab")
                            if ht_capab is not None:
                                #logger.info(ht_capab)
                                logger.info("trying 20")
                                setParameterHostapdConfig("ht_capab", None)
                            start = restartHostapd()
                    except:
                        logger.exception("error")
                        pass

                if start:
                    logger.info("started!")
                    return jsonify({"status": True, "inSync": True})
                else:
                    logger.info("not started!")
                    return jsonify({"status": False, "inSync": False})

            else:
                return jsonify({"status": True,"inSync":True})
        return jsonify({"status": False, "inSync": False})

    except:
        logger.exception("error while applying config")
        return jsonify({"status": False})

@app.route('/pingDevice',methods=["GET"])
def testConnection():
    return jsonify({"status":True})

@app.route('/reboot',methods=["GET"])
def reboot():
    @after_this_request
    def reboot(test):
        time.sleep(1)
        os.system('sudo shutdown -r now')
        return jsonify({"status": True})

    return jsonify({"status": True})


def applyConfiguration(config):
    if config["type"] == "AP":
        shutil.move("/etc/hostapd/hostapd.conf", "/etc/hostapd/hostapd.old.conf")
        os.system("touch /etc/hostapd/hostapd.conf")
        try:
            interface = config["parameters"]["interface"]
        except:
            interface = "wlan0"
        logger.info("Interface is {}".format(interface))
        for param in HOSTAPD_DEFAULT_CONFIG:
            setParameterHostapdConfig(param, HOSTAPD_DEFAULT_CONFIG[param])
        for param in config["parameters"]:
            if param != "width":
                param2 = translateFromServerToPi(param)
                if param2 == "wpa_passphrase":
                    setParameterHostapdConfig("wpa", "2")
                    setParameterHostapdConfig("wpa_key_mgmt", "WPA-PSK")
                    setParameterHostapdConfig("wpa_pairwise", "TKIP")
                    setParameterHostapdConfig("rsn_pairwise", "CCMP")
                if param2=="hw_mode" and config["parameters"][param]=="a":
                    logger.info("Trying to set a mode for wifi")
                    if "width" in config["parameters"] and config["parameters"]["width"]=="40":
                        logger.info("Trying to set 40 width")
                        try:
                            with open('hostapd_available_config.json') as f:
                                data = json.load(f)
                                avai = data["configs"][interface]["a"]["40"][config["parameters"]["channel"]]
                                logger.info("Avai:")
                                logger.info(avai)
                                if "+" in avai:
                                    setParameterHostapdConfig("ht_capab", "[HT40+][SHORT-GI-40]")
                                elif "-" in avai:
                                    setParameterHostapdConfig("ht_capab", "[HT40-][SHORT-GI-40]")
                        except:
                            logger.exception("Error")
                            pass
                    setParameterHostapdConfig("ieee80211n", "1")

                setParameterHostapdConfig(param2, config["parameters"][param])
        return True
    return False


def translateFromServerToPi(param):
    if param == "wifimode":
        param2 = "hw_mode"
    elif param == "password":
        param2 = "wpa_passphrase"
    else:
        param2 = param
    return param2

def translateFromPiToServer(param):
    if param == "hw_mode":
        param2 = "wifimode"
    elif param == "wpa_passphrase":
        param2 = "password"
    else:
        param2 = param
    return param2


def setParameterHostapdConfig(param,value):
    logger.info("Setting parameter {} as {} in hostapd config".format(param,value))
    try:

        with open("newconfig.conf", 'w') as new_file:
            with open("/etc/hostapd/hostapd.conf") as old_file:
                found = False
                for line in old_file:
                    if line.startswith(param):
                        if value is not None:
                            found=True
                            new_file.write("{}={}\n".format(param,value))
                    else:
                        new_file.write(line)
                if not found and value is not None:
                    new_file.write("{}={}\n".format(param, value))

        os.remove("/etc/hostapd/hostapd.conf")
        shutil.move("newconfig.conf", "/etc/hostapd/hostapd.conf")
        return {"status": True}
    except:
        logger.exception("Error while modifying hostapd config")
        return {"status": False}


def popen_timeout(command, timeout):
    p = subprocess.Popen(command,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for t in xrange(timeout):
        time.sleep(1)
        if p.poll() is not None:
            return p.communicate()
    p.kill()
    return False

def restartHostapd():
    try:
        os.system("killall hostapd")
        time.sleep(1)
    except:
        pass
    try:

        os.system("hostapd -B /etc/hostapd/hostapd.conf")
        #output = popen_timeout("hostapd /etc/hostapd/hostapd.conf",1)
        time.sleep(1)
        ps = os.popen("ps -A").read()
        #logger.info(ps)
        if "hostapd" in ps:
            try:
                os.system("killall hostapd")
                time.sleep(1)
            except:
                pass
            subprocess.Popen("hostapd /etc/hostapd/hostapd.conf", shell=True)
            return True
        else:
            return False
    except:
        logger.exception("error")
        return False

if __name__ == '__main__':
    app.run(port=80,host="0.0.0.0")