#!/bin/bash

source .env

DEVICE="${1:-$DEVICE_UIFLOW_TOKEN}"

if [[ $DEVICE == "" ]];
then
    echo "Usage: upload.sh <device>"
    exit 1
fi

printf "Uploading to device: $DEVICE\n"

http https://api.m5stack.com/v1/${DEVICE}/root/flash/config.py @config.py
http https://api.m5stack.com/v1/${DEVICE}/root/flash/main.py @main.py
