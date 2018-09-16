import subprocess
output = subprocess.Popen('iw wlan0 info', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
for line in output.stdout.readlines():
    if "phy" in line:
        wlan = line.split()[1]
print wlan
output2 = subprocess.Popen('iw phy{} info'.format(wlan), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
obj={
    "bgn":[],
    "a":[]
}
inBand1=False
inBand2=False
inFreq=False
for line in output2.stdout.readlines():
    raw= repr(line)
    line2 = line.replace(" ","")
    leading_spaces = len(line2) - len(line2.lstrip())
    if inFreq:
        if leading_spaces != 3:
            inFreq=False
        else:
            if not "(radar detection)" in raw and not "(disabled)" in raw:
                fr = (line.split("[")[1]).split("]")[0]
                if inBand1:
                    obj["bgn"].append(int(fr))
                elif inBand2:
                    obj["a"].append(int(fr))
    if "Band 1" in line:
        inBand1=True
        inBand2 = False
        inFreq = False
    elif "Band 2" in line:
        inBand1=False
        inBand2 = True
        inFreq = False
    if "Frequencies" in line:
        inFreq=True

finalObject={
    "bgn":obj["bgn"],
    "a":{
        "40":[],
        "20":[]
    }
}
interObj={
    "bgn":obj["bgn"],
    "a":{
        "40":{},
        "20":[]
    }
}
for channel in obj["a"]:
    if ((channel-4) in obj["a"] and (channel-2) in obj["a"]):
        finalObject["a"]["40"].append(channel)
        if str(channel) in interObj["a"]["40"]:
            interObj["a"]["40"][str(channel)] = "+-"
        else:
            interObj["a"]["40"][str(channel)] = "-"
    if ((channel+4) in obj["a"] and (channel+2) in obj["a"]):
        finalObject["a"]["40"].append(channel)
        if str(channel) in interObj["a"]["40"]:
            interObj["a"]["40"][str(channel)] = "+-"
        else:
            interObj["a"]["40"][str(channel)]="+"
    finalObject["a"]["20"].append(channel)
print finalObject
print interObj

