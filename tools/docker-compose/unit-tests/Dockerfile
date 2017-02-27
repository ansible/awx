FROM gcr.io/ansible-tower-engineering/tower_devel:latest

RUN yum install -y bzip2 gcc-c++

# We need to install dependencies somewhere other than /ansible-tower.
# Anything in /ansible-tower will be overwritten by the bind-mount.
# We switch the WORKDIR to /ansible-tower further down.
WORKDIR "/tmp/"

# Build front-end deps

# https://github.com/npm/npm/issues/9863
RUN cd $(npm root -g)/npm \
  && npm install fs-extra \
  && sed -i -e s/graceful-fs/fs-extra/ -e s/fs\.rename/fs.move/ ./lib/utils/rename.js

RUN npm install -g npm@3.10.7

COPY awx/ui/package.json awx/ui/

RUN npm set progress=false

# Copy __init__.py so the Makefile can retrieve `awx.__version__`
COPY awx/__init__.py awx/
RUN make ui-deps

WORKDIR "/tower_devel"

# This entrypoint script takes care of moving the node_modules
# into the bind-mount, then exec's to whatever was passed as the CMD.
ADD tools/docker-compose/unit-tests/entrypoint /usr/bin/
RUN chmod +x /usr/bin/entrypoint

ENTRYPOINT ["entrypoint"]
CMD ["bash"]
