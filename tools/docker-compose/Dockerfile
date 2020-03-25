FROM centos:8

ARG UID=0

# Add ansible-devel so that we get collections!
ADD tools/docker-compose/ansible_nightly.repo /etc/yum.repos.d/ansible_nightly.repo

# sync with installer/roles/image_build/templates/Dockerfile.j2
RUN dnf -y update && \
  dnf -y install epel-release 'dnf-command(config-manager)' && \
  dnf module -y enable 'postgresql:10' && \
  dnf config-manager --set-enabled PowerTools && \
  dnf -y install acl \
  ansible \
  bubblewrap \
  curl \
  diffutils \
  dnf-utils \
  gcc \
  gcc-c++ \
  gettext \
  git-core \
  glibc-langpack-en \
  krb5-workstation \
  libcurl-devel \
  libffi-devel \
  libstdc++.so.6 \
  libtool-ltdl-devel \
  libcgroup-tools \
  make \
  mercurial \
  nginx \
  nmap-ncat \
  nodejs \
  nss \
  openldap-devel \
  openssh-server \
  patch \
  @postgresql:10 \
  postgresql-devel \
  python3-devel \
  python3-libselinux \
  python3-pip \
  python3-psycopg2 \
  python3-setuptools \
  python3-pycurl \
  rsync \
  subversion \
  strace \
  sudo \
  swig \
  tcpdump \
  tmux \
  unzip \
  vim \
  which \
  xmlsec1 \
  xmlsec1-devel \
  xmlsec1-openssl \
  xmlsec1-openssl-devel

# UI tests only, do not put in installer/roles/image_build/templates/Dockerfile.j2
RUN dnf -y install \
  gtk3 \
  alsa-lib \
  libX11-xcb \
  libXScrnSaver

ENV PATH="/usr/pgsql-10/bin:${PATH}"

RUN dnf install -y https://github.com/krallin/tini/releases/download/v0.18.0/tini_0.18.0.rpm

RUN /usr/bin/ssh-keygen -q -t rsa -N "" -f /root/.ssh/id_rsa
RUN mkdir -p /data/db

ADD tools/docker-compose/awx.egg-link /tmp/awx.egg-link
ADD tools/docker-compose/awx-manage /usr/local/bin/awx-manage
ADD tools/docker-compose/awx.egg-info /tmp/awx.egg-info

RUN openssl req -nodes -newkey rsa:2048 -keyout /etc/nginx/nginx.key -out /etc/nginx/nginx.csr -subj "/C=US/ST=North Carolina/L=Durham/O=Ansible/OU=AWX Development/CN=awx.localhost"
RUN openssl x509 -req -days 365 -in /etc/nginx/nginx.csr -signkey /etc/nginx/nginx.key -out /etc/nginx/nginx.crt
RUN chmod 640 /etc/nginx/nginx.{csr,key,crt}

RUN python3 -m ensurepip && pip3 install "virtualenv < 20" flake8
RUN pip3 install supervisor

ADD Makefile /tmp/Makefile
RUN mkdir /tmp/requirements
ADD requirements/requirements.txt \
  requirements/requirements_git.txt \
  requirements/requirements_ansible.txt \
  requirements/requirements_ansible_git.txt \
  requirements/requirements_dev.txt \
  requirements/requirements_ansible_uninstall.txt \
  requirements/requirements_tower_uninstall.txt \
  /tmp/requirements/
RUN mkdir -p /venv && chmod g+w /venv
RUN cd /tmp && VENV_BASE="/venv" make requirements_dev

# Use the distro provided npm to bootstrap our required version of node
RUN npm install -g n
RUN n 10.15.0

# Install OpenShift CLI
RUN cd /usr/local/bin && \
    curl -L https://github.com/openshift/origin/releases/download/v3.9.0/openshift-origin-client-tools-v3.9.0-191fece-linux-64bit.tar.gz | \
    tar -xz --strip-components=1 --wildcards --no-anchored 'oc'

ADD tools/docker-compose/google-cloud-sdk.repo /etc/yum.repos.d/
RUN dnf install -y kubectl

RUN dnf -y remove nodejs

RUN dnf -y clean all

RUN rm -rf /root/.cache

# https://github.com/ansible/awx/issues/5224
RUN chmod u+s /usr/bin/bwrap

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ADD tools/docker-compose/nginx.conf /etc/nginx/nginx.conf
ADD tools/docker-compose/nginx.vh.default.conf /etc/nginx/conf.d/nginx.vh.default.conf
ADD tools/docker-compose/launch_awx.sh /usr/bin/launch_awx.sh
ADD tools/docker-compose/start_tests.sh /start_tests.sh
ADD tools/docker-compose/bootstrap_development.sh /usr/bin/bootstrap_development.sh

EXPOSE 8043 8013 8080 22

ADD tools/docker-compose/entrypoint.sh /
ADD tools/scripts/awx-python /usr/bin/awx-python
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]

# Pre-create things that we need to write to
RUN for dir in /var/lib/awx/ /var/log/tower/ /var/lib/awx/projects /.ansible /var/log/nginx /var/lib/nginx /.local; \
  do mkdir -p $dir; chmod -R g+rwx $dir; chgrp -R root $dir; done

RUN for file in /etc/passwd /etc/supervisord.conf \
  /venv/awx/lib/python3.6/site-packages/awx.egg-link /var/run/nginx.pid; \
  do touch $file; chmod -R g+rwx $file; chgrp -R root $file; done

ENV HOME /var/lib/awx

ENV PATH=/usr/local/n/versions/node/10.15.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
