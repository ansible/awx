FROM centos:7

# RUN locale-gen en_US.UTF-8
# ENV LANG en_US.UTF-8
# ENV LANGUAGE en_US:en
# ENV LC_ALL en_US.UTF-8
ADD Makefile /tmp/Makefile
RUN mkdir /tmp/requirements
ADD requirements/requirements.txt requirements/requirements_ansible.txt requirements/requirements_dev.txt requirements/requirements_jenkins.txt /tmp/requirements/
RUN yum -y update && yum -y install curl epel-release
RUN curl --silent --location https://rpm.nodesource.com/setup_6.x | bash -
RUN yum -y localinstall http://download.postgresql.org/pub/repos/yum/9.4/redhat/rhel-6-x86_64/pgdg-centos94-9.4-3.noarch.rpm
ADD tools/docker-compose/proot.repo /etc/yum.repos.d/proot.repo
RUN yum -y update && yum -y install openssh-server ansible mg vim tmux git mercurial subversion python-devel python-psycopg2 make postgresql postgresql-devel nodejs python-psutil libxml2-devel libxslt-devel libstdc++.so.6 gcc cyrus-sasl-devel cyrus-sasl openldap-devel libffi-devel zeromq-devel proot python-pip xmlsec1-devel swig krb5-devel xmlsec1-openssl xmlsec1 xmlsec1-openssl-devel libtool-ltdl-devel
RUN pip install flake8 pytest==2.9.2 pytest-pythonpath pytest-django pytest-cov pytest-mock dateutils django-debug-toolbar==1.4 pyflakes==1.0.0 virtualenv
RUN /usr/bin/ssh-keygen -q -t rsa -N "" -f /root/.ssh/id_rsa
RUN mkdir -p /etc/tower
RUN mkdir -p /data/db
ADD tools/docker-compose/license /etc/tower/license
RUN pip2 install honcho
RUN curl -LO https://github.com/Yelp/dumb-init/releases/download/v1.1.3/dumb-init_1.1.3_amd64 && chmod +x ./dumb-init_1.1.3_amd64 && mv ./dumb-init_1.1.3_amd64 /usr/bin/dumb-init
ADD tools/docker-compose/ansible-tower.egg-link /tmp/ansible-tower.egg-link
ADD tools/docker-compose/tower-manage /usr/local/bin/tower-manage
ADD tools/docker-compose/awx-manage /usr/local/bin/awx-manage
ADD tools/docker-compose/ansible_tower.egg-info /tmp/ansible_tower.egg-info
RUN ln -s /tower_devel/tools/docker-compose/start_development.sh /start_development.sh
WORKDIR /tmp
RUN SWIG_FEATURES="-cpperraswarn -includeall -D__`uname -m`__ -I/usr/include/openssl" VENV_BASE="/venv" make requirements_dev
WORKDIR /
EXPOSE 8013 8080 22
ENTRYPOINT ["/usr/bin/dumb-init"]
CMD /start_development.sh
