import subprocess
output = subprocess.Popen('iw wlan0 info', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
for line in output.stdout.readlines():
    if "phy" in line:
        wlan = line.split()[1]
print wlan
output2 = subprocess.Popen('iw list', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
obj={
    "bgn":[],
    "a":[]
}
inBand1=False
inBand2=False
inFreq=False
for line in output2.stdout.readlines():
    raw= repr(line)
    print line
    if "Band 1" in line:
        print "BAND 1"
        inBand1=True
        inBand2 = False
        inFreq = False
    elif "Band 2" in line:
        print "BAND 2"
        inBand1=False
        inBand2 = True
        inFreq = False
    if "Frequencies" in line:
        print "FREQ"
        inFreq=True
    if inFreq:
        if not raw.startswith("'\t\t\t"):
            inFreq=False
        else:
            print "GOOD STARTTTTT"
            if inBand1:
                obj["bgn"].append(line)
            elif inBand2:
                obj["a"].append(line)



print obj