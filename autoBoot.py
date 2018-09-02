import socket
from uuid import getnode as get_mac
import os
import requests
import time
import json

def getMac():
    try:
        mac = get_mac()
        mac=':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
        return str(mac)
    except:
        return ""

def getIP():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('192.0.0.8', 1027))
        except socket.error:
            return None
        return str(s.getsockname()[0])
    except:
        pass

def parseHostapdConfig():
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
        pass



while True:
    try:
        resp = os.popen('./ngrok http 80 > /root/test.log &').read()
        time.sleep(5)
        for i in range(8):
            try:
                resp = requests.get("http://localhost:404{}/api/tunnels".format(i))
                j = json.loads(resp.text)
                tunnel = j["tunnels"][0]["public_url"]
                break
            except:
                pass


        url = "https://api-openap.projects.jcloud.fr/devices/register"

        payload = {
            "ip":getIP(),
            "http_tunnel":tunnel,
            "hostapd_config":parseHostapdConfig()
        }
        headers = {
            'Content-Type': "application/json",
            'Mac-Adress': getMac(),
            }

        response = requests.request("POST", url, json=payload, headers=headers)

        print(response.text)
        os.system("python code/main.py")
        break
    except:
        time.sleep(5)