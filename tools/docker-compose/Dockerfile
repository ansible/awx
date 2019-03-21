FROM centos:7

ARG UID=0

ADD Makefile /tmp/Makefile

RUN mkdir /tmp/requirements

RUN yum -y update && yum -y install curl epel-release && yum -y install https://centos7.iuscommunity.org/ius-release.rpm
RUN yum -y localinstall https://download.postgresql.org/pub/repos/yum/9.4/redhat/rhel-6-x86_64/pgdg-centos94-9.4-3.noarch.rpm
RUN curl --silent --location https://rpm.nodesource.com/setup_8.x | bash -

RUN yum -y update && yum -y install openssh-server ansible mg vim tmux \
  git2u-core mercurial subversion python-devel python-pip python36 python36-devel python-psycopg2 make postgresql \
  postgresql-devel nginx nodejs python-psutil libxml2-devel libxslt-devel \
  libstdc++.so.6 gcc cyrus-sasl-devel cyrus-sasl openldap-devel libffi-devel \
  xmlsec1-devel swig krb5-devel xmlsec1-openssl xmlsec1 \
  xmlsec1-openssl-devel libtool-ltdl-devel rabbitmq-server bubblewrap \
  zanata-python-client gettext gcc-c++ libcurl-devel bzip2 \
  rsync

RUN ln -s /usr/bin/python36 /usr/bin/python3

RUN python36 -m ensurepip
RUN pip3 install virtualenv
RUN /usr/bin/ssh-keygen -q -t rsa -N "" -f /root/.ssh/id_rsa
RUN mkdir -p /data/db
RUN pip3 install honcho && pip install supervisor

ADD requirements/requirements.txt \
  requirements/requirements_git.txt \
  requirements/requirements_ansible.txt \
  requirements/requirements_ansible_git.txt \
  requirements/requirements_dev.txt \
  requirements/requirements_ansible_uninstall.txt \
  requirements/requirements_tower_uninstall.txt \
  /tmp/requirements/

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
WORKDIR /tmp

RUN mkdir -p /venv && chmod g+w /venv
RUN CFLAGS="-DXMLSEC_NO_SIZE_T" SWIG_FEATURES="-cpperraswarn -includeall -D__`uname -m`__ -I/usr/include/openssl" VENV_BASE="/venv" make requirements_dev
RUN localedef -c -i en_US -f UTF-8 en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ADD https://github.com/krallin/tini/releases/download/v0.14.0/tini /tini
RUN chmod +x /tini
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
