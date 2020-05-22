REVISION=588429
CHROMIUM_URL="https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/${REVISION}/chrome-linux.zip"

wget ${CHROMIUM_URL} -w 30 -t 6 -O /tmp/chrome-linux.zip
unzip -o -d /tmp /tmp/chrome-linux.zip
