REVISION=588429
CHROMIUM_URL="https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/${REVISION}/chrome-linux.zip"

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
