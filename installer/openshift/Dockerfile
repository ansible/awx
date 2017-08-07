FROM centos:7

# Do we need this?
#RUN locale-gen en_US.UTF-8
#ENV LANG en_US.UTF-8
#ENV LANGUAGE en_US:en
#ENV LC_ALL en_US.UTF-8

USER root

# Init System
ADD https://github.com/krallin/tini/releases/download/v0.14.0/tini /tini
RUN chmod +x /tini

ADD Makefile /tmp/Makefile
RUN mkdir /tmp/requirements
ADD requirements/requirements_ansible.txt \
    requirements/requirements_ansible_uninstall.txt \
    requirements/requirements_ansible_git.txt \
    requirements/requirements.txt \
    requirements/requirements_tower_uninstall.txt \
    requirements/requirements_git.txt \
    /tmp/requirements/

# OS Dependencies
RUN yum -y install epel-release && yum -y localinstall http://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-centos96-9.6-3.noarch.rpm && yum -y update && yum -y install ansible git curl python-psycopg2 python-pip python-setuptools libselinux-python setools-libs yum-utils sudo acl make postgresql-devel nginx python-psutil libxml2-devel libxslt-devel libstdc++.so.6 gcc cyrus-sasl-devel cyrus-sasl openldap-devel libffi-devel python-pip xmlsec1-devel swig krb5-devel xmlsec1-openssl xmlsec1 xmlsec1-openssl-devel libtool-ltdl-devel bubblewrap gcc-c++ python-devel
RUN pip install virtualenv supervisor
WORKDIR /tmp
RUN mkdir -p /var/lib/awx/public/static

RUN mkdir -p /var/log/tower
RUN mkdir -p /etc/tower
RUN echo "awxsecret" > /etc/tower/SECRET_KEY
RUN VENV_BASE=/var/lib/awx/venv make requirements_ansible && VENV_BASE=/var/lib/awx/venv make requirements_awx
COPY dist/awx-{{ version }}.tar.gz /tmp/awx-{{ version }}.tar.gz
RUN OFFICIAL=yes pip install /tmp/awx-{{ version }}.tar.gz

RUN echo "{{ version }}" > /var/lib/awx/.tower_version
ADD installer/openshift/nginx.conf /etc/nginx/nginx.conf
ADD installer/openshift/supervisor.conf /supervisor.conf
ADD installer/openshift/supervisor_task.conf /supervisor_task.conf
ADD installer/openshift/launch_awx.sh /usr/bin/launch_awx.sh
ADD installer/openshift/launch_awx_task.sh /usr/bin/launch_awx_task.sh
ADD installer/openshift/settings.py /etc/tower/settings.py
RUN yum -y remove gcc postgresql-devel libxml2-devel libxslt-devel cyrus-sasl-devel openldap-devel xmlsec1-devel krb5-devel xmlsec1-openssl-devel libtool-ltdl-devel gcc-c++ python-devel && yum -y clean all
RUN rm -rf /root/.cache
RUN chmod g+w /etc/passwd
RUN chgrp -Rf root /var/lib/awx && chmod -Rf g+w /var/lib/awx
RUN chmod -R 777 /var/log/nginx && chmod -R 777 /var/lib/nginx
USER 1000
EXPOSE 8052
WORKDIR /var/lib/awx
ENTRYPOINT ["/tini", "--"]
CMD /usr/bin/launch_awx.sh
