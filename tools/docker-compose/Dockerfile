FROM ubuntu:14.04

RUN locale-gen en_US.UTF-8  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8  
RUN apt-get update && apt-get install -y software-properties-common python-software-properties curl
RUN add-apt-repository -y ppa:chris-lea/redis-server; add-apt-repository -y ppa:chris-lea/zeromq; add-apt-repository -y ppa:chris-lea/node.js; add-apt-repository -y ppa:ansible/ansible; add-apt-repository -y ppa:jal233/proot;
RUN curl -sL https://deb.nodesource.com/setup_0.12 | bash -
RUN curl -sL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main" | tee /etc/apt/sources.list.d/postgres-9.4.list
RUN apt-get update && apt-get install -y openssh-server ansible mg vim tmux git mercurial subversion python-dev python-psycopg2 make postgresql-client libpq-dev nodejs python-psutil libxml2-dev libxslt-dev lib32z1-dev libsasl2-dev libldap2-dev libffi-dev libzmq-dev proot python-pip libxmlsec1-dev swig redis-server libgss-dev libkrb5-dev && apt-get autoremove --purge -y && rm -rf /var/lib/apt/lists/*
RUN pip install flake8 pytest pytest-pythonpath pytest-django pytest-cov pytest-mock dateutils django-debug-toolbar==1.4 pyflakes==1.0.0 virtualenv
RUN /usr/bin/ssh-keygen -q -t rsa -N "" -f /root/.ssh/id_rsa
RUN mkdir -p /etc/tower
RUN mkdir -p /data/db
ADD license /etc/awx/license
ADD license /etc/tower/license
RUN pip2 install honcho
RUN wget https://github.com/Yelp/dumb-init/releases/download/v1.0.1/dumb-init_1.0.1_amd64.deb
RUN dpkg -i dumb-init_*.deb
RUN rm -rf /dumb-init_*.deb
ADD ansible-tower.egg-link /tmp/ansible-tower.egg-link
ADD tower-manage /usr/local/bin/tower-manage
ADD ansible_tower.egg-info /tmp/ansible_tower.egg-info
RUN ln -s /tower_devel/tools/docker-compose/start_development.sh /start_development.sh

EXPOSE 8013 8080 22
ENTRYPOINT ["/usr/bin/dumb-init"]
CMD /start_development.sh
