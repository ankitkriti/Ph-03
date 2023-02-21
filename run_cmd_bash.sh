#!/bin/bash

wget -q --spider http://google.com

cicomid=$(git rev-parse HEAD)
cicomid=${cicomid:0:7}

if [[ $? -eq 0 ]]
 then
    cd /home/pi/Desktop/waterspcrc/Ph-03/
    git pull origin master
    cicomid_new=$(git rev-parse HEAD)
    cicomid_new=${cicomid_new:0:7}
    if [[ "$cicomid" != "$cicomid_new" ]]
    then
      cicomid=$cicomid_new
      sudo systemctl restart codetest.service
    else
      echo 'No changes'
    fi

else
    echo 'No Internet'

fi
