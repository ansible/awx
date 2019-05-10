#!/bin/bash

if [ `id -u` -ge 500 ] || [ -z "${CURRENT_UID}" ]; then

  cat << EOF > /tmp/passwd
root:x:0:0:root:/root:/bin/bash
awx:x:`id -u`:`id -g`:,,,:/tmp:/bin/bash
EOF

  cat /tmp/passwd > /etc/passwd
  rm /tmp/passwd
fi

exec $@
