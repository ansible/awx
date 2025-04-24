#!/bin/bash

if [ `id -u` -ge 500 ] || [ -z "${CURRENT_UID}" ]; then

cat << EOF > /etc/passwd
root:x:0:0:root:/root:/bin/bash
awx:x:`id -u`:`id -g`:,,,:/var/lib/awx:/bin/bash
nginx:x:`id -u nginx`:`id -g nginx`:Nginx web server:/var/lib/nginx:/sbin/nologin
EOF

cat <<EOF >> /etc/group
awx:x:`id -u`:awx
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

export SDB_NOTIFY_HOST=$(ip route | head -n1 | awk '{print $3}')


exec $@
