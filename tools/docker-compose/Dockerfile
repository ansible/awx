FROM centos:7

ARG UID=0

RUN yum -y update && yum -y install epel-release

# sync with installer/roles/image_build/templates/Dockerfile.j2
RUN yum -y install acl \
  ansible \
  bubblewrap \
  curl \
  cyrus-sasl \
  cyrus-sasl-devel \
  gcc \
  gcc-c++ \
  git \
  krb5-devel \
  krb5-libs \
  krb5-workstation \
  libcurl-devel \
  libffi-devel \
  libselinux-python \
  libstdc++.so.6 \
  libtool-ltdl-devel \
  libxml2-devel \
  libxslt-devel \
  make \
  mercurial \
  mg \
  nginx \
  nodejs \
  openldap-devel \
  openssh-server \
  postgresql-devel \
  python-devel \
  python-pip \
  python-pip \
  python-psutil \
  python-psycopg2 \
  python-setuptools \
  python36-devel \
  python36-setuptools \
  rsync \
  setools-libs \
  subversion \
  sudo \
  swig \
  tmux \
  unzip \
  vim \
  xmlsec1 \
  xmlsec1-devel \
  xmlsec1-openssl \
  xmlsec1-openssl-devel \
  yum-utils

ADD https://github.com/krallin/tini/releases/download/v0.14.0/tini /tini
RUN chmod +x /tini

RUN /usr/bin/ssh-keygen -q -t rsa -N "" -f /root/.ssh/id_rsa
RUN mkdir -p /data/db

ADD tools/docker-compose/awx.egg-link /tmp/awx.egg-link
ADD tools/docker-compose/awx-manage /usr/local/bin/awx-manage
ADD tools/docker-compose/awx.egg-info /tmp/awx.egg-info

RUN ln -Ffs /awx_devel/tools/docker-compose/nginx.conf /etc/nginx/nginx.conf
RUN ln -Ffs /awx_devel/tools/docker-compose/nginx.vh.default.conf /etc/nginx/conf.d/nginx.vh.default.conf
RUN ln -s /awx_devel/tools/docker-compose/start_development.sh /start_development.sh
RUN ln -s /awx_devel/tools/docker-compose/start_tests.sh /start_tests.sh
RUN ln -s /awx_devel/tools/docker-compose/bootstrap_development.sh /bootstrap_development.sh

RUN openssl req -nodes -newkey rsa:2048 -keyout /etc/nginx/nginx.key -out /etc/nginx/nginx.csr -subj "/C=US/ST=North Carolina/L=Durham/O=Ansible/OU=AWX Development/CN=awx.localhost"
RUN openssl x509 -req -days 365 -in /etc/nginx/nginx.csr -signkey /etc/nginx/nginx.key -out /etc/nginx/nginx.crt

RUN python3 -m ensurepip && pip3 install virtualenv
RUN pip install supervisor

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
RUN n 8.15.0
ENV PATH /usr/bin:/usr/local/n/versions/node/8.15.0/bin:$PATH

RUN yum -y remove cyrus-sasl-devel \
  gcc \
  gcc-c++ \
  krb5-devel \
  libtool-ltdl-devel \
  libxml2-devel \
  libxslt-devel \
  openldap-devel \
  postgresql-devel \
  python-devel \
  python36-devel \
  nodejs \
  xmlsec1-devel \
  xmlsec1-openssl-devel

RUN yum -y clean all

RUN rm -rf /root/.cache

RUN localedef -c -i en_US -f UTF-8 en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

WORKDIR /

EXPOSE 8043 8013 8080 22

ENTRYPOINT ["/tini", "--"]
CMD /start_development.sh

# Pre-create things that we need to write to
RUN for dir in /var/lib/awx/ /var/log/tower/ /projects /.ansible /var/log/nginx /var/lib/nginx /.local; \
  do mkdir -p $dir; chmod -R g+rwx $dir; chgrp -R root $dir; done

RUN for file in /etc/passwd /etc/supervisord.conf \
  /venv/awx/lib/python3.6/site-packages/awx.egg-link /var/run/nginx.pid; \
  do touch $file; chmod -R g+rwx $file; chgrp -R root $file; done
