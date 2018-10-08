import subprocess
from uuid import getnode as get_mac
import logging
from logging.handlers import RotatingFileHandler
import requests
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('readClients.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info("Running read client script!")

def getMac():
    logger.info("Getting mac")
    try:
        mac = get_mac()
        mac=':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
        return str(mac)
    except:
        return ""

def getIP(mac_address):
    output = subprocess.check_output("arp -a", shell=True)
    for line in output.split('\n'):
        if mac_address in line:
            return line.split("(")[1].split(")")[0]
    return None


output2 = subprocess.check_output("iw dev wlan0 station dump", shell=True)
clients={}
currentDevice = None
for line in output2.split('\n'):
    words = line.split(" ")
    if line !="":
        if words[0]=="Station":
            currentDevice=words[1]
            clients[currentDevice]={}
            clients[currentDevice]["ip_address"]=getIP(currentDevice)
        elif currentDevice!=None:
            values = line.split(":")
            values = [w.replace("\t","") for w in values]
            if values[0] in ["inactive time","rx bytes","tx bytes","rx packets","tx packets","tx retries","tx failed","rx drop misc","signal", "signal avg","tx bitrate","rx bitrate","connected time"]:
                vals =values[1].split()
                while "" in vals: vals.remove("")
                while " " in vals: vals.remove(" ")
                val=vals[0]
                print val
                clients[currentDevice][values[0].replace(" ", "_")] = int(float(val))
            else:
                clients[currentDevice][values[0].replace(" ","_")]=values[1]


print clients
payload = {
    "clients":clients
}
headers = {
    'Content-Type': "application/json",
    'Mac-Adress': getMac(),
    }

url = "https://api.openap.io/devices/postClientsData"


response = requests.request("POST", url, json=payload, headers=headers)