import subprocess
output = subprocess.Popen('iw wlan0 info', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
for line in output.stdout.readlines():
    if "phy" in line:
        wlan = line.split()[1]
print wlan
output2 = subprocess.Popen('iw list', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
obj={
    "2.4":[],
    "5":[]
}
inBand1=False
inBand2=False
inFreq=False
for line in output2.stdout.readlines():
    raw= repr(line)
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
    if inFreq:
        if not raw.startswith("\t\t\t"):
            inFreq=False
        else:
            if inBand1:
                obj["2.4"].append(line)
            elif inBand2:
                obj["5"].append(line)



print obj