import requests
import zipfile
import os
import time

while True:
    try:
        r = requests.get("http://192.168.43.213:8080/getConfig")
        with open("code.zip", "wb") as code:
            code.write(r.content)

        with zipfile.ZipFile("code.zip","r") as zip_ref:
            zip_ref.extractall("")

        os.remove("code.zip")
        os.system("python code/main.py")
        break
    except:
        time.sleep(5)