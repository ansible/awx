FROM ubuntu:14.04

RUN locale-gen en_US.UTF-8  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8  
RUN apt-get update && apt-get install -y software-properties-common python-software-properties curl
RUN add-apt-repository -y ppa:chris-lea/zeromq; add-apt-repository -y ppa:chris-lea/node.js; add-apt-repository ppa:ansible/ansible
RUN curl -sL https://deb.nodesource.com/setup_0.12 | bash -
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10 && apt-key adv --fetch-keys http://www.postgresql.org/media/keys/ACCC4CF8.asc
RUN echo "deb http://repo.mongodb.org/apt/ubuntu "$(lsb_release -sc)"/mongodb-org/3.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.0.list && echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main" | tee /etc/apt/sources.list.d/postgres-9.4.list
RUN apt-get update
RUN apt-get install -y openssh-server ansible mg vim tmux git mercurial subversion python-dev python-psycopg2 make postgresql-client libpq-dev nodejs python-psutil libxml2-dev libxslt-dev lib32z1-dev libsasl2-dev libldap2-dev libffi-dev libzmq-dev proot python-pip libxmlsec1-dev swig && rm -rf /var/lib/apt/lists/*
RUN /usr/bin/ssh-keygen -q -t rsa -N "" -f /root/.ssh/id_rsa
RUN mkdir -p /etc/tower
RUN mkdir -p /data/db
ADD license /etc/awx/license
ADD license /etc/tower/license
RUN pip2 install honcho
ADD start_development.sh /start_development.sh

EXPOSE 8013 8080 22
CMD /start_development.sh
