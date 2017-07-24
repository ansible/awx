FROM centos/systemd
RUN yum clean all

ADD Makefile /tmp/Makefile
RUN mkdir /tmp/requirements
ADD requirements/requirements_ansible.txt requirements/requirements_ansible_git.txt requirements/requirements_ansible_uninstall.txt requirements/requirements_isolated.txt /tmp/requirements/
RUN yum -y update && yum -y install curl epel-release
RUN curl --silent --location https://rpm.nodesource.com/setup_6.x | bash -
RUN yum -y update && yum -y install openssh-server ansible mg vim tmux git python-devel python-psycopg2 make python-psutil libxml2-devel libxslt-devel libstdc++.so.6 gcc cyrus-sasl-devel cyrus-sasl openldap-devel libffi-devel zeromq-devel python-pip xmlsec1-devel swig krb5-devel xmlsec1-openssl xmlsec1 xmlsec1-openssl-devel libtool-ltdl-devel bubblewrap zanata-python-client gettext gcc-c++
RUN pip install virtualenv
WORKDIR /tmp
RUN make requirements_ansible
RUN make requirements_isolated
RUN localedef -c -i en_US -f UTF-8 en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
WORKDIR /
EXPOSE 22
ADD tools/docker-isolated/awx-expect /usr/local/bin/awx-expect

RUN rm -f /etc/ssh/ssh_host_ecdsa_key /etc/ssh/ssh_host_rsa_key
RUN ssh-keygen -q -N "" -t dsa -f /etc/ssh/ssh_host_ecdsa_key
RUN ssh-keygen -q -N "" -t rsa -f /etc/ssh/ssh_host_rsa_key
RUN sed -i "s/#UsePrivilegeSeparation.*/UsePrivilegeSeparation no/g" /etc/ssh/sshd_config
RUN sed -i "s/UsePAM.*/UsePAM yes/g" /etc/ssh/sshd_config
RUN ssh-keygen -A
RUN mkdir -p /root/.ssh
RUN touch /root/.ssh/authorized_keys

CMD ["/usr/sbin/init"]
