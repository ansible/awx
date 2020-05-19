#!/bin/bash

REVISION=588429
CHROMIUM_URL="https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/${REVISION}/chrome-linux.zip"
CHROMIUM_DOWNLOAD_DIR="/tmp/chrome-linux"

mkdir -p ${CHROMIUM_DOWNLOAD_DIR}

interval=30
retries=6
status=1
until [ $retries -eq 0 ] || [ $status -eq 0 ]; do
  wget ${CHROMIUM_URL} -O /tmp/chrome-linux.zip
  status=$?
  sleep $interval
  ((retries--))
done

unzip -o -d /tmp /tmp/chrome-linux.zip

