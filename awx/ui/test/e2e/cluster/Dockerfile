FROM centos:7

RUN yum -y update && yum -y install epel-release && yum -y install https://centos7.iuscommunity.org/ius-release.rpm

RUN yum install -y \
    bzip2 \
    gcc-c++ \
    git2u \
    git2u-core \
    make \
    nodejs \
    npm

WORKDIR /awx

COPY awx/ui/package.json awx/ui/package.json

ARG NPM_REGISTRY=https://registry.npmjs.org
ENV NPM_REGISTRY=${NPM_REGISTRY}

RUN npm config set registry ${NPM_REGISTRY}

RUN npm --prefix=awx/ui install

COPY awx/ui/test/e2e awx/ui/test/e2e

ENTRYPOINT ["npm", "--prefix=awx/ui", "run", "e2e", "--", "--env=cluster"]
