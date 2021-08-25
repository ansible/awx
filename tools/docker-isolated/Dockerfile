ARG VERSION

FROM ${VERSION}

ENV UID=1000
ENV HOMEDIR=ansible

USER 0

RUN dnf install -y gcc python39-devel openssh-server
RUN python3.9 -m ensurepip && pip3.9 install psutil "virtualenv < 20" "ansible-runner == 2.0.2"

RUN dnf remove -y gcc python39-devel && dnf clean all && rm -rf /var/cache/dnf && \
    alternatives --set python /usr/bin/python3 && alternatives --set python3 /usr/bin/python3.9

RUN rm -f /etc/ssh/*_key
RUN ssh-keygen -q -A -N ""
RUN sed -i "s/UsePAM.*/UsePAM yes/g" /etc/ssh/sshd_config && echo "Port 2022" >> /etc/ssh/sshd_config

RUN useradd -u ${UID} -d /home/${HOMEDIR} awx && \
    mkdir /home/${HOMEDIR}/.ssh && \
    chmod 700 /home/${HOMEDIR}/.ssh && \
    chown awx:awx /home/${HOMEDIR}/.ssh && \
    mkdir /var/lib/awx/.ansible && \
    chown awx:awx /var/lib/awx/.ansible

RUN rm -rf /run/nologin

EXPOSE 2022

ENTRYPOINT ["tini", "--"]
CMD ["/usr/sbin/sshd", "-D", "-e"]
