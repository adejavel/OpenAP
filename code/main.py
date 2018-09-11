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
import traceback
from threading import Thread
app = Flask(__name__)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('agent.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)



DEFAULT_PARAMETERS=["wpa","wpa_key_mgmt","wpa_pairwise","rsn_pairwise","ieee80211n","ht_capab"]
HOSTAPD_DEFAULT_CONFIG={
    "bridge":"br0",
    "country_code":"FR",
    "ignore_broadcast_ssid":"0",
    "interface":"wlan0",
    "macaddr_acl":"0",
    "wmm_enabled":"1",
}


@app.route('/getConfig',methods=["POST"])
def get_config():
    resp = getConfig(request)
    logger.info(resp)
    return jsonify(resp)


def setParameterHostapdConfigCheck(param, value):
    logger.info("Setting parameter {} as {} in hostapd config".format(param, value))
    try:

        with open("newconfig_check_config.conf", 'w') as new_file:
            with open("/etc/hostapd/hostapd_check_conf.conf") as old_file:
                found = False
                for line in old_file:
                    if line.startswith(param):
                        found = True
                        new_file.write("{}={}\n".format(param, value))
                    else:
                        new_file.write(line)
                if not found:
                    new_file.write("{}={}\n".format(param, value))

        os.remove("/etc/hostapd/hostapd_check_conf.conf")
        shutil.move("newconfig_check_config.conf", "/etc/hostapd/hostapd_check_conf.conf")
        return {"status": True}
    except:
        logger.exception("Error while modifying hostapd config")
        return {"status": False}

@app.route('/checkConfigHostapd',methods=["GET"])
def checkConfigHostapd():
    begin = time.time()



    logger.info("Beginning check action")

    try:
        os.system("killall hostapd")
    except:
        pass

    try:
        os.remove("hostapd_available_config.json")
    except:
        pass

    workingConfigs = []
    checked = []

    for wifimode in ["b", "g", "a"]:
        channels = []
        widths = []
        if wifimode in ["b", "g"]:
            channels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
            widths = ["20"]
        elif wifimode in ["a"]:
            channels = [32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62, 64, 68, 96, 100, 102, 104, 108,
                        110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 132, 134, 136, 138, 140, 142, 144, 149, 151,
                        153, 155, 157, 159, 161, 165]
            widths = ["20", "40"]
        else:
            channels = []
            widths = []
        for channel in channels:
            for width in widths:
                if width == "40":
                    for ht_c in ["[HT40-][SHORT-GI-40]", "[HT40+][SHORT-GI-40]"]:
                        print(
                        "Trying config: mode: {} // channel: {} // width: {} // ht_capab: {}".format(wifimode, channel,
                                                                                                     width, ht_c))
                        try:
                            try:
                                os.remove("/etc/hostapd/hostapd_check_conf.conf")
                            except:
                                pass
                            open("/etc/hostapd/hostapd_check_conf.conf", 'a').close()
                            for param in HOSTAPD_DEFAULT_CONFIG:
                                setParameterHostapdConfigCheck(param, HOSTAPD_DEFAULT_CONFIG[param])
                            setParameterHostapdConfigCheck("ssid", "test")
                            setParameterHostapdConfigCheck("hw_mode", wifimode)
                            setParameterHostapdConfigCheck("channel", str(channel))
                            if wifimode in ["a"]:
                                setParameterHostapdConfigCheck("ieee80211n", "1")
                            setParameterHostapdConfigCheck("ht_capab", ht_c)

                            # os.system("hostapd /etc/hostapd/hostapd_check_conf.conf")
                            # output = subprocess.check_output("hostapd /etc/hostapd/hostapd_check_conf.conf", shell=True)
                            # output = subprocess.Popen("hostapd /etc/hostapd/hostapd_check_conf.conf")
                            cmd = ['hostapd', '/etc/hostapd/hostapd_check_conf.conf', '/dev/null']
                            output = subprocess.run(cmd, timeout=0.5)
                            # print(output)
                            print("It didn't worked!")


                        except subprocess.TimeoutExpired:
                            traceback.print_exc()
                            print("It worked")
                            workingConfigs.append(
                                {
                                    "wifimode": wifimode,
                                    "channel": channel,
                                    "width": width,
                                    "ht_capab": ht_c
                                }
                            )
                            pass
                        except:
                            traceback.print_exc()
                            print("It didn't work!")

                            try:
                                os.system("killall hostapd")
                            except:
                                pass
                        checked.append({
                            "wifimode": wifimode,
                            "channel": channel,
                            "width": width,
                            "ht_capab": ht_c
                        })
                else:
                    print(
                        "Trying config: mode: {} // channel: {} // width: {}".format(wifimode, channel, width))
                    try:
                        try:
                            os.remove("/etc/hostapd/hostapd_check_conf.conf")
                        except:
                            pass
                        open("/etc/hostapd/hostapd_check_conf.conf", 'a').close()
                        for param in HOSTAPD_DEFAULT_CONFIG:
                            setParameterHostapdConfigCheck(param, HOSTAPD_DEFAULT_CONFIG[param])
                        setParameterHostapdConfigCheck("ssid", "test")
                        setParameterHostapdConfigCheck("hw_mode", wifimode)
                        setParameterHostapdConfigCheck("channel", str(channel))
                        if wifimode in ["a"]:
                            setParameterHostapdConfigCheck("ieee80211n", "1")

                        # os.system("hostapd /etc/hostapd/hostapd_check_conf.conf")
                        # output = subprocess.check_output("hostapd /etc/hostapd/hostapd_check_conf.conf", shell=True)
                        # output = subprocess.Popen("hostapd /etc/hostapd/hostapd_check_conf.conf")
                        cmd = ['hostapd', '/etc/hostapd/hostapd_check_conf.conf', '/dev/null']
                        output = subprocess.run(cmd, timeout=0.5)
                        # print(output)
                        print("It didn't worked!")


                    except subprocess.TimeoutExpired:
                        traceback.print_exc()
                        print("It worked")
                        workingConfigs.append(
                            {
                                "wifimode": wifimode,
                                "channel": channel,
                                "width": width
                            }
                        )
                        pass
                    except:
                        traceback.print_exc()
                        print("It didn't work!")

                        try:
                            os.system("killall hostapd")
                        except:
                            pass
                    checked.append({
                        "wifimode": wifimode,
                        "channel": channel,
                        "width": width,
                    })
    tm = time.time()
    with open('hostapd_available_config.json', 'w') as fp:
        json.dump({"configs": workingConfigs, "time": tm}, fp)

    logger.info("Ended in {}".format(time.time() - begin))
    return {"status": True}



def getConfig(request):
    logger.info("Executing getConfig action")
    try:
        data = request.json
        config = data["applied_config"]
        ip = getIP()
        mac = getMac()
        hostapdConfig = parseHostapdConfig()
        if config["type"]=="AP":
            logger.info("Comparing config")
            configH = parseHostapdConfig()
            if not compareConfig(configH,config["parameters"]):
                logger.info("Not in SYNC")
                try:
                    os.system("killall hostapd")
                except:
                    pass
                applyConfiguration(config)
                @after_this_request
                def reboot(test):
                    time.sleep(1)
                    os.system('sudo shutdown -r now')
                    return {"status": True, "inSync": False, "config": {"ip_address": ip, "hostapd_config": hostapdConfig, "mac_address": mac}}
                return {"status":True,"inSync":False,"config":{"ip_address":ip,"hostapd_config":hostapdConfig,"mac_address":mac}}
            else:
                logger.info("In sync!")
                logger.info(hostapdConfig)
                return {"status": True, "inSync": True,"config": {"ip_address": ip, "hostapd_config": hostapdConfig, "mac_address": mac}}
        else:
            return {"status":False}
    except:
        logger.exception("Error while getting config")
        return {"status": False}


def compareConfig(deviceConfig,appliedConfig):
    toIgnore=["wpa","wpa_key_mgmt","wpa_pairwise","rsn_pairwise","ieee80211n","ht_capab"]
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
            logger.info("Configuring AP")
            Hconf = parseHostapdConfig()
            if not compareConfig(config["parameters"],Hconf):
                try:
                    os.system("killall hostapd")
                except:
                    pass
                logger.info("Not same config")
                applyConfiguration(config)
                logger.info("Config applied, trying to reboot")

                @after_this_request
                def reboot(test):
                    time.sleep(1)
                    os.system('sudo shutdown -r now')
                    return jsonify({"status":True,"inSync":False})
                return jsonify({"status":True,"inSync":False})
            else:
                return jsonify({"status": True,"inSync":True})
        return jsonify({"status": False, "inSync": False})

    except:
        logger.info(request)
        logger.info(request.data)
        logger.info(request.json)
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
        for param in HOSTAPD_DEFAULT_CONFIG:
            setParameterHostapdConfig(param, HOSTAPD_DEFAULT_CONFIG[param])
        for param in config["parameters"]:
            param2 = translateFromServerToPi(param)
            if param2 == "wpa_passphrase":
                setParameterHostapdConfig("wpa", "2")
                setParameterHostapdConfig("wpa_key_mgmt", "WPA-PSK")
                setParameterHostapdConfig("wpa_pairwise", "TKIP")
                setParameterHostapdConfig("rsn_pairwise", "CCMP")
            if param2=="hw_mode" and config["parameters"][param]=="a":
                setParameterHostapdConfig("ieee80211n", "1")
                setParameterHostapdConfig("ht_capab","[HT40-][SHORT-GI-40]")
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