import subprocess
output = subprocess.Popen('iw wlan0 info', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
for line in output.stdout.readlines():
    if "phy" in line:
        wlan = line.split()[1]
print wlan
output2 = subprocess.Popen('iw wlan0 info', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
for line in output2.stdout.readlines():
    print line