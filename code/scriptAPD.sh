#!/bin/bash
if [[ $2 == "AP-STA-CONNECTED" ]]
then
  python /root/OpenAP/OpenAP/code/client.py $3 $1 True
  echo "someone has connected with mac id $3 on $1" >> /root/clientsLogs.log
fi

if [[ $2 == "AP-STA-DISCONNECTED" ]]
then
  python /root/OpenAP/OpenAP/code/client.py $3 $1 False
  echo "someone has disconnected with mac id $3 on $1" >> /root/clientsLogs.log
fi