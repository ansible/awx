FROM ubuntu:14.04

RUN locale-gen en_US.UTF-8  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8  
RUN apt-get update
RUN apt-get install -y software-properties-common python-software-properties
RUN add-apt-repository -y ppa:chris-lea/redis-server; add-apt-repository -y ppa:chris-lea/zeromq; add-apt-repository -y ppa:chris-lea/node.js; add-apt-repository ppa:ansible/ansible
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
RUN echo "deb http://repo.mongodb.org/apt/ubuntu "$(lsb_release -sc)"/mongodb-org/3.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.0.list
RUN apt-get update
RUN apt-get install -y openssh-server ansible mg vim tmux git mercurial subversion python-dev python-pip libyaml-dev python-yaml python-paramiko python-jinja2 make postgresql python-psycopg2 python-ldap nodejs redis-server python-gevent libzmq3 python-zmq python-netifaces mongodb-org python-psutil && rm -rf /var/lib/apt/lists/*
RUN git clone http://d7f73f8614295715a4777bf15f46d0d486ad0e21:x-oauth-basic@github.com/ansible/ansible-commander.git tower
RUN pip install Django==1.6.7 django-devserver django-debug-toolbar django-jenkins ipython pymongo==2.8 mongoengine psutil
RUN cd /tower ; make develop
RUN /etc/init.d/postgresql start ; su - postgres -c 'ansible -i "127.0.0.1," -c local -v -m postgresql_user -U postgres -a "name=awx-dev password=AWXsome1 login_user=postgres" all'; /etc/init.d/postgresql stop
RUN /etc/init.d/postgresql start ; su - postgres -c 'ansible -i "127.0.0.1," -c local -v -m postgresql_db -U postgres -a "name=awx-dev owner=awx-dev login_user=postgres" all'; /etc/init.d/postgresql stop
RUN /usr/bin/ssh-keygen -q -t rsa -N "" -f /root/.ssh/id_rsa
ADD local_settings.py /tower/awx/settings/local_settings.py
RUN mkdir -p /etc/tower
RUN mkdir -p /data/db
ADD license /etc/awx/license
ADD license /etc/tower/license
RUN /etc/init.d/postgresql start; cd /tower ; make migrate ; make init ; /etc/init.d/postgresql stop
ADD start_everything.sh /start_everything.sh
ADD start_development.sh /start_development.sh

EXPOSE 8013 8080 27017 22
CMD /start_development.sh
