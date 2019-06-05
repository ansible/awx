FROM centos:7

RUN yum install -y epel-release

RUN yum install -y bzip2 \
    gcc-c++ \
    gettext \
    git \
    make \
    nodejs \
    python36-setuptools

# Use the distro provided npm to bootstrap our required version of node
RUN npm install -g n
RUN n 10.15.0
RUN yum remove -y nodejs

ENV PATH=/usr/local/n/versions/node/10.15.0/bin:$PATH

WORKDIR "/awx"

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["make sdist"]
