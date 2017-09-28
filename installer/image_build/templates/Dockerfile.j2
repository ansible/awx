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
ADD ansible.repo /etc/yum.repos.d/ansible.repo
ADD RPM-GPG-KEY-ansible-release /etc/pki/rpm-gpg/RPM-GPG-KEY-ansible-release
# OS Dependencies
WORKDIR /tmp
RUN mkdir -p /var/lib/awx/public/static
RUN chgrp -Rf root /var/lib/awx && chmod -Rf g+w /var/lib/awx
RUN yum -y install epel-release && \
    yum -y localinstall http://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-centos96-9.6-3.noarch.rpm && \
    yum -y update && \
    yum -y install ansible git mercurial subversion curl python-psycopg2 python-pip python-setuptools libselinux-python setools-libs yum-utils sudo acl make postgresql-devel nginx python-psutil libxml2-devel libxslt-devel libstdc++.so.6 gcc cyrus-sasl-devel cyrus-sasl openldap-devel libffi-devel python-pip xmlsec1-devel swig krb5-devel xmlsec1-openssl xmlsec1 xmlsec1-openssl-devel libtool-ltdl-devel bubblewrap gcc-c++ python-devel krb5-workstation krb5-libs && \
    pip install virtualenv supervisor && \
    VENV_BASE=/var/lib/awx/venv make requirements_ansible && \
    VENV_BASE=/var/lib/awx/venv make requirements_awx && \
    yum -y remove gcc postgresql-devel libxml2-devel libxslt-devel cyrus-sasl-devel openldap-devel xmlsec1-devel krb5-devel xmlsec1-openssl-devel libtool-ltdl-devel gcc-c++ python-devel && \
    yum -y clean all && \
    rm -rf /root/.cache

RUN mkdir -p /var/log/tower
RUN mkdir -p /etc/tower
COPY {{ awx_sdist_file }} /tmp/{{ awx_sdist_file }}
RUN OFFICIAL=yes pip install /tmp/{{ awx_sdist_file }}

RUN echo "{{ awx_version }}" > /var/lib/awx/.tower_version
ADD nginx.conf /etc/nginx/nginx.conf
ADD supervisor.conf /supervisor.conf
ADD supervisor_task.conf /supervisor_task.conf
ADD launch_awx.sh /usr/bin/launch_awx.sh
ADD launch_awx_task.sh /usr/bin/launch_awx_task.sh
RUN chmod +rx /usr/bin/launch_awx.sh && chmod +rx /usr/bin/launch_awx_task.sh
ADD settings.py /etc/tower/settings.py
RUN chmod g+w /etc/passwd
RUN chmod -R 777 /var/log/nginx && chmod -R 777 /var/lib/nginx
USER 1000
EXPOSE 8052
WORKDIR /var/lib/awx
ENTRYPOINT ["/tini", "--"]
CMD /usr/bin/launch_awx.sh
