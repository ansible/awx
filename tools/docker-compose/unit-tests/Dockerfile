# FROM gcr.io/ansible-tower-engineering/tower_devel:latest
FROM centos

RUN yum install -y epel-release

RUN yum install -y \
	bzip2 \
	python-pip \
	python-virtualenv \
	make \
	swig \
	git \
	libffi-devel \
	openssl-devel \
	libxml2-devel \
	xmlsec1-devel \
	xmlsec1-openssl-devel \
	gcc \
	gcc-c++ \
	/usr/bin/pg_config \
	openldap-devel \
	postgresql-devel \
    rabbitmq-server \
	libtool-ltdl-devel

# NOTE: The following steps work for tower-3.0.0
# RUN curl -LO https://rpm.nodesource.com/pub_0.12/el/7/x86_64/nodejs-0.12.9-1nodesource.el7.centos.x86_64.rpm
# RUN yum install -y nodejs-0.12.9-1nodesource.el7.centos.x86_64.rpm
# RUN rm nodejs-0.12.9-1nodesource.el7.centos.x86_64.rpm

# Remove the 2 lines below and uncomment the 3 lines above to build
# RPMs with the old JS build system.
RUN curl --silent --location https://rpm.nodesource.com/setup_6.x | bash -

RUN yum install -y nodejs

# https://github.com/npm/npm/issues/9863
RUN cd $(npm root -g)/npm \
  && npm install fs-extra \
  && sed -i -e s/graceful-fs/fs-extra/ -e s/fs\.rename/fs.move/ ./lib/utils/rename.js

RUN npm install -g npm@3.10.7

WORKDIR "/ansible-tower"

# Copy requirements files
# NOTE: '*' is not used as it invalidates docker caching
COPY requirements/requirements.txt requirements/
COPY requirements/requirements_ansible.txt requirements/
COPY requirements/requirements_dev.txt requirements/
COPY requirements/requirements_jenkins.txt requirements/


# Copy __init__.py so the Makefile can retrieve `awx.__version__`
COPY awx/__init__.py awx/

# Copy Makefile
COPY Makefile .

# Install tower runtime virtualenvs
ENV SWIG_FEATURES="-cpperraswarn -includeall -I/usr/include/openssl"
RUN make requirements

# Install tower test requirements 
ENV VENV_BASE=""
RUN make requirements_jenkins

# Build front-end deps
COPY awx/ui/package.json awx/ui/

RUN npm set progress=false

RUN make ui-deps

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["bash"]
