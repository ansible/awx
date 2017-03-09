FROM gcr.io/ansible-tower-engineering/tower_devel:latest

# For UI tests
RUN yum install -y bzip2 gcc-c++

RUN npm set progress=false

WORKDIR "/tower_devel"

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["bash"]
