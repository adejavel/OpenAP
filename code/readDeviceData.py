import speedtest
from uuid import getnode as get_mac
import logging
from logging.handlers import RotatingFileHandler
import requests
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('deviceData.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info("Running read device script!")

def getSpeedTest():

    servers = []
    # If you want to test against a specific server
    # servers = [1234]

    s = speedtest.Speedtest()
    s.get_servers(servers)
    s.get_best_server()
    s.download()
    s.upload()
    s.results.share()

    results_dict = s.results.dict()



    results_speed_dict = {}
    results_speed_dict['download']=results_dict['download']
    results_speed_dict['upload']=results_dict['upload']
    results_speed_dict['ping']=results_dict['ping']

    return results_speed_dict



print(getSpeedTest())

def getMac():
    #logger.info("Getting mac")
    try:
        mac = get_mac()
        mac = ':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
        return str(mac)
    except:
        return ""


print(getMac())



payload = getSpeedTest()
headers = {
    'Content-Type': "application/json",
    'Mac-Adress': getMac(),
    }

url = "https://api.openap.io/devices/postDeviceData"


response = requests.request("POST", url, json=payload, headers=headers)