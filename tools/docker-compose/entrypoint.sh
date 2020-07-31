#!/bin/bash

if [ `id -u` -ge 500 ] || [ -z "${CURRENT_UID}" ]; then

cat << EOF > /etc/passwd
root:x:0:0:root:/root:/bin/bash
awx:x:`id -u`:`id -g`:,,,:/var/lib/awx:/bin/bash
EOF

cat <<EOF > /etc/subuid
awx:100000:50001
EOF

cat <<EOF > /etc/subgid
awx:100000:50001
EOF

fi

# Required to get rootless podman working after
# writing out the sub*id files above
podman system migrate

exec $@
