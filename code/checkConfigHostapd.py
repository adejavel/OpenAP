import os
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('check_config.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
import shutil
import traceback
import subprocess
import json
import time
import requests
from uuid import getnode as get_mac

HOSTAPD_DEFAULT_CONFIG={
    "bridge":"br0",
    "country_code":"FR",
    "ignore_broadcast_ssid":"0",
    "interface":"wlan0",
    "macaddr_acl":"0",
    "wmm_enabled":"1",
}

begin = time.time()

def getMac():
    logger.info("Getting mac")
    try:
        mac = get_mac()
        mac=':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
        return str(mac)
    except:
        traceback.print_exc()
        return ""

def setParameterHostapdConfig(param,value):
    #slogger.info("Setting parameter {} as {} in hostapd config".format(param,value))
    try:

        with open("newconfig_check_config.conf", 'w') as new_file:
            with open("/etc/hostapd/hostapd_check_conf.conf") as old_file:
                found = False
                for line in old_file:
                    if line.startswith(param):
                        found=True
                        new_file.write("{}={}\n".format(param,value))
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

logger.info("Beginning check action")

try:
    os.system("killall hostapd")
except:
    pass


try:
    os.remove("hostapd_available_config.json")
except:
    pass

workingConfigs=[]
checked=[]

for wifimode in ["b","g"]:
    #for country in ["FR", "US", "CA", "RU", "CN"]:
    for country in ["FR"]:
        channels=[]
        widths=[]
        if wifimode in ["b","g"]:
            channels=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,123]
            widths = ["20"]
        elif wifimode in ["a"]:
            channels=[32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,68,96,100,102,104,108,110,112,114,116,118,120,122,124,126,128,132,134,136,138,140,142,144,149,151,153,155,157,159,161,165]
            widths = ["20","40"]
        else:
            channels=[]
            widths=[]
        for channel in channels:
            for width in widths:
                if width == "40":
                    for ht_c in ["[HT40-][SHORT-GI-40]","[HT40+][SHORT-GI-40]"]:
                        print("Trying config: mode: {} // channel: {} // width: {} // ht_capab: {} // country: {}".format(wifimode,channel,width,ht_c,country))
                        try:
                            os.system("killall hostapd")
                            time.sleep(0.1)
                        except:
                            pass
                        try:

                            try:
                                os.remove("/etc/hostapd/hostapd_check_conf.conf")
                            except:
                                pass
                            open("/etc/hostapd/hostapd_check_conf.conf", 'a').close()
                            for param in HOSTAPD_DEFAULT_CONFIG:
                                setParameterHostapdConfig(param,HOSTAPD_DEFAULT_CONFIG[param])
                            setParameterHostapdConfig("ssid","test")
                            setParameterHostapdConfig("country_code", country)
                            setParameterHostapdConfig("hw_mode", wifimode)
                            setParameterHostapdConfig("channel", str(channel))
                            if wifimode in ["a"]:
                                setParameterHostapdConfig("ieee80211n", "1")
                            setParameterHostapdConfig("ht_capab", ht_c)

                            #out = os.system("hostapd /etc/hostapd/hostapd_check_conf.conf &")

                            #logger.info(ps)
                            #logger.info(out)
                            #os.system("hostapd /etc/hostapd/hostapd_check_conf.conf")
                            #output = subprocess.check_output("hostapd /etc/hostapd/hostapd_check_conf.conf", shell=True)
                            #output = subprocess.Popen("/usr/sbin/hostapd /etc/hostapd/hostapd_check_conf.conf")
                            cmd = ['hostapd', '/etc/hostapd/hostapd_check_conf.conf']
                            #output = subprocess.call("hostapd /etc/hostapd/hostapd_check_conf.conf",shell=True)
                            output = subprocess.Popen('/usr/sbin/hostapd /etc/hostapd/hostapd_check_conf.conf', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            output.wait(0.5)
                            # with open("/etc/hostapd/hostapd_check_conf.conf") as old_file:
                            #     for line in old_file:
                            #         logger.info(line)
                            logger.info(output.returncode)
                            for line in output.stdout.readlines():
                                logger.info(line)
                            #logger.info(output)
                            ps = os.popen("ps -A").read()
                            logger.info(ps)
                            #output = subprocess.run("hostapd /etc/hostapd/hostapd_check_conf.conf",timeout=0.2)
                            #print(output)
                            print("It didn't worked!")


                        except subprocess.TimeoutExpired:
                            logger.exception("Error")
                            traceback.print_exc()
                            print("It worked")
                            workingConfigs.append(
                                {
                                    "wifimode":wifimode,
                                    "channel":channel,
                                    "width":width,
                                    "ht_capab":ht_c,
                                    "country":country
                                }
                            )
                            pass
                        except:
                            ps = os.popen("ps -A").read()
                            #logger.info(ps)
                            logger.exception("Error")
                            logger.info("last exception")
                            traceback.print_exc()
                            print("It didn't work!")


                        checked.append({
                                    "wifimode":wifimode,
                                    "channel":channel,
                                    "width":width,
                                    "ht_capab":ht_c,
                                    "country":country
                                })
                        logger.info({
                                    "wifimode":wifimode,
                                    "channel":channel,
                                    "width":width,
                                    "ht_capab":ht_c,
                                    "country":country
                                })
                else:
                    print(
                    "Trying config: mode: {} // channel: {} // width: {} // country: {}".format(wifimode, channel, width,country))
                    try:
                        os.system("killall hostapd")
                        time.sleep(0.1)
                    except:
                        pass
                    try:

                        try:
                            os.remove("/etc/hostapd/hostapd_check_conf.conf")
                        except:
                            pass
                        open("/etc/hostapd/hostapd_check_conf.conf", 'a').close()
                        for param in HOSTAPD_DEFAULT_CONFIG:
                            setParameterHostapdConfig(param, HOSTAPD_DEFAULT_CONFIG[param])
                        setParameterHostapdConfig("ssid", "test")
                        setParameterHostapdConfig("country_code", country)
                        setParameterHostapdConfig("hw_mode", wifimode)
                        setParameterHostapdConfig("channel", str(channel))
                        if wifimode in ["a"]:
                            setParameterHostapdConfig("ieee80211n", "1")

                        #out = os.system("hostapd /etc/hostapd/hostapd_check_conf.conf &")
                        #ps = os.popen("ps -A").read()
                        # output = subprocess.call("hostapd /etc/hostapd/hostapd_check_conf.conf",shell=True)

                        output = subprocess.Popen('/usr/sbin/hostapd /etc/hostapd/hostapd_check_conf.conf', shell=True,
                                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        #output.wait(0.2)
                        time.sleep(0.1)

                        logger.info("######################################")
                        logger.info("Begin")
                        logger.info(output.returncode)
                        ps = os.popen("ps -A").read()
                        #logger.info(ps)
                        logger.info({
                            "wifimode": wifimode,
                            "channel": channel,
                            "width": width,
                            "country": country
                        })

                        output.kill()
                        time.sleep(0.5)
                        for line in output.stdout.readlines():
                            logger.info(line)
                        logger.info(output.returncode)
                        logger.info("end")
                        logger.info("######################################")
                        #logger.info(output)
                        #
                        #output = subprocess.check_output("hostapd -B /etc/hostapd/hostapd_check_conf.conf", shell=True)
                        #output = subprocess.Popen("/usr/sbin/hostapd /etc/hostapd/hostapd_check_conf.conf")
                        cmd = ['hostapd', '/etc/hostapd/hostapd_check_conf.conf']
                        #output = subprocess.run("hostapd /etc/hostapd/hostapd_check_conf.conf", timeout=0.2)
                        # print(output)

                        print("It didn't worked!")


                    # except subprocess.TimeoutExpired:
                    #     logger.exception("Error")
                    #     traceback.print_exc()
                    #     print("It worked")
                    #     workingConfigs.append(
                    #         {
                    #             "wifimode": wifimode,
                    #             "channel": channel,
                    #             "width": width,
                    #             "country":country
                    #         }
                    #     )
                    #     pass
                    # except:
                    #     #ps = os.popen("ps -A").read()
                    #     #logger.info(ps)
                    #     logger.info("last exception")
                    #     logger.exception("Error")
                    #     traceback.print_exc()
                    #     print("It didn't work!")
                    #
                    #     try:
                    #         os.system("killall hostapd")
                    #     except:
                    #         pass
                    except:
                        logger.exception("Error bordel")
                    checked.append({
                        "wifimode": wifimode,
                        "channel": channel,
                        "width": width,
                        "country":country
                    })

with open('hostapd_available_config.json', 'w') as fp:
    json.dump({"configs":workingConfigs,"time":time.time()}, fp)

logger.info("Ended in {}".format(time.time()-begin))
url = "https://api.openap.io/devices/postCheckedHostapdConfig"

finalConfigs=[]
for working in workingConfigs:
    found=False
    for conf in finalConfigs:
        if conf["wifimode"]==working["wifimode"] and conf["channel"]==working["channel"] and conf["width"]==working["width"]:
            found=True
    if not found:
        finalConfigs.append(
            {
                "wifimode":working["wifimode"],
                "channel":working["channel"],
                "width":working["width"]
            }
        )

payload = {
    "checked_hostapd_config":finalConfigs,
}
headers = {
    'Content-Type': "application/json",
    'Mac-Adress': getMac(),
    }

print(headers)
response = requests.request("POST", url, json=payload, headers=headers)
print(response.text)
# print("Executed in {}sec".format(time.time()-begin))
# for check in checked:
#     print(checked)
# print(len(checked))