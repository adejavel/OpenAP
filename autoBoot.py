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

        os.system("python OpenAP/OpenAP/code/main.py")
        time.sleep(2)

        url = "https://api.openap.io/devices/register"

        payload = {
            "http_tunnel":tunnel
        }
        headers = {
            'Content-Type': "application/json",
            'Mac-Adress': getMac(),
            }

        response = requests.request("POST", url, json=payload, headers=headers)

        print(response.text)

        exit()
        break
    except:
        time.sleep(5)