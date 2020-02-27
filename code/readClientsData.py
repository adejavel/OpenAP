import subprocess
from uuid import getnode as get_mac
import logging
from logging.handlers import RotatingFileHandler
import requests
import json
import netifaces
from threading import Timer
import ipaddress
import time
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('readClients.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info("Running read client script!")

try:
    with open('/root/deviceInfo.json') as json_data:
        d = json.load(json_data)
        OPENAP_HOST=d["apiEndPoint"]
except:
    OPENAP_HOST="https://staging-api.openap.io/"

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

def getIP(mac_address):
    print ""
    print "Trying to get ip for {}".format(mac_address)
    print ""
    output = subprocess.check_output("arp -a", shell=True)
    for line in output.split('\n'):
        print line
        if mac_address.lower() in line.lower():
            print "MAC FOUND"
            return line.split("(")[1].split(")")[0]
    return None

## PINGING Broadcaast to get get mac - ip correlation

ip_addresses = ipaddress.IPv4Network(ipaddress.ip_network(u'{}/{}'.format(netifaces.ifaddresses('br0')[netifaces.AF_INET][0].get("addr"),netifaces.ifaddresses('br0')[netifaces.AF_INET][0].get("netmask")), strict=False))
logger.info(ip_addresses)
for ip_addr in ip_addresses:
    print(ip_addr)
    cmd = "ping {} -w 2".format(ip_addr)
    ping = os.system(cmd)



time.sleep(5)

interface = ""
with open("/etc/hostapd/hostapd.conf") as config:
    for line in config:
        if not line.startswith("#"):
            words = line.split("=")
            if words[0]=="interface":
                interface=str.replace(words[1],"\n","")
logger.info("interface is {}".format(interface))
output2 = subprocess.check_output("iw dev {} station dump".format(interface), shell=True)
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

url = "{}devices/postClientsData".format(OPENAP_HOST)


response = requests.request("POST", url, json=payload, headers=headers)