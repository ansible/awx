FROM gcr.io/ansible-tower-engineering/awx_devel:latest

# For UI tests
RUN yum install -y bzip2 gcc-c++

RUN npm set progress=false

WORKDIR "/awx_devel"

ADD tools/docker-compose/unit-tests/entrypoint.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
