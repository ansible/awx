FROM centos:7

RUN yum install -y epel-release

RUN yum install -y \
    bzip2 \
    gcc-c++ \
    git \
    make \
    nodejs \
    npm

WORKDIR /awx

COPY awx/ui/package.json awx/ui/package.json

RUN npm --prefix=awx/ui install

COPY awx/ui/test/e2e awx/ui/test/e2e

ENTRYPOINT ["npm", "--prefix=awx/ui", "run", "e2e", "--", "--env=cluster"]
