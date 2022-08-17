# docker-compose container image variables
DEV_DOCKER_TAG_BASE ?= ghcr.io/ansible
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
COMPOSE_TAG ?= $(GIT_BRANCH)
DEVEL_IMAGE_NAME ?= $(DEV_DOCKER_TAG_BASE)/awx_devel:$(COMPOSE_TAG)
RECEPTOR_IMAGE ?= quay.io/ansible/receptor:devel

# docker-compose awx configurations
MAIN_NODE_TYPE ?= hybrid
# If set to true docker-compose will also start a keycloak instance
KEYCLOAK ?= false
# If set to true docker-compose will also start an ldap instance
LDAP ?= false
# If set to true docker-compose will also start a splunk instance
SPLUNK ?= false
# If set to true docker-compose will also start a prometheus instance
PROMETHEUS ?= false
# If set to true docker-compose will also start a grafana instance
GRAFANA ?= false

COMPOSE_UP_OPTS ?=
COMPOSE_OPTS ?=
CONTROL_PLANE_NODE_COUNT ?= 1
EXECUTION_NODE_COUNT ?= 2
MINIKUBE_CONTAINER_GROUP ?= false

DEV_RELOAD_COMMAND ?= supervisorctl restart tower-processes:*
MANAGEMENT_COMMAND ?= awx-manage

# ------------------------------------------------------------------------------#
# Targets used inside of awx docker-compose development environment             #
# ------------------------------------------------------------------------------#

## Start auto-reload watcher in the docker-compose development environment
awx-autoreload:
	@/awx_devel/tools/docker-compose/awx-autoreload /awx_devel/awx "$(DEV_RELOAD_COMMAND)"

## Start daphne in docker-compose development environment
daphne:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	daphne -b 127.0.0.1 -p 8051 awx.asgi:channel_layer

## Start controller broadcast websocket in docker-compose development environment
wsbroadcast:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_wsbroadcast

## Start task dispatcher in docker-compose development environment
dispatcher:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_dispatcher

## Start callback receiver in docker-compose development environment
receiver:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_callback_receiver

## Start nginx mode in docker-compose development environment
nginx:
	nginx -g "daemon off;"

## Start jupyter notebook for docker-compose development environment
jupyter:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(MANAGEMENT_COMMAND) shell_plus --notebook

## Start supervsiord in docker-compose development environment
supervisor:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	supervisord --pidfile=/tmp/supervisor_pid -n

## Start uwsgi in docker-compose development environment
uwsgi: collectstatic
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	uwsgi -b 32768 \
	    --socket 127.0.0.1:8050 \
	    --module=awx.wsgi:application \
	    --home=/var/lib/awx/venv/awx \
	    --chdir=/awx_devel/ \
	    --vacuum \
	    --processes=5 \
	    --harakiri=120 --master \
	    --no-orphans \
	    --max-requests=1000 \
	    --stats /tmp/stats.socket \
	    --lazy-apps \
	    --logformat "%(addr) %(method) %(uri) - %(proto) %(status)"

## Create database tables and apply any new migrations.
migrate:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(MANAGEMENT_COMMAND) migrate --noinput

## Create Django superuser.
adduser:
	$(MANAGEMENT_COMMAND) createsuperuser

## Run after making changes to the models to create a new migration.
dbchange:
	$(MANAGEMENT_COMMAND) makemigrations

## Run django management command to collects static files
collectstatic:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	mkdir -p awx/public/static && $(PYTHON) manage.py collectstatic --clear --noinput > /dev/null 2>&1

## Create /var/lib/awx/.awx_version
version_file:
	mkdir -p /var/lib/awx/; \
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) -c "import awx; print(awx.__version__)" > /var/lib/awx/.awx_version; \

# ------------------------------------------------------------------------------#
# Targets used for building awx docker-compose development environment          #
# ------------------------------------------------------------------------------#

# NOTE: This directory is bind-mounted inside of the development container and
# needs to be pre-created for permissions to be set correctly. Otherwise,
# Docker will create this directory as root.
## Pre-create awx/projects directory that will be bind-mounted into the dev container
awx/projects:
	@mkdir -p $@

# TODO: make rest of the automation actually use Dockerfile.docker-compose
## Generate Dockerfile for docker-compose development environment container image
Dockerfile.docker-compose: tools/ansible/roles/dockerfile/templates/Dockerfile.j2
	ansible-playbook tools/ansible/dockerfile.yml -e receptor_image=$(RECEPTOR_IMAGE)

## Build docker-compose development environment container image
docker-compose/image-build:
	ansible-playbook tools/ansible/dockerfile.yml -e build_dev=True -e receptor_image=$(RECEPTOR_IMAGE)
	DOCKER_BUILDKIT=1 docker build -t $(DEVEL_IMAGE_NAME) \
	    --build-arg BUILDKIT_INLINE_CACHE=1 \
	    --cache-from=$(DEV_DOCKER_TAG_BASE)/awx_devel:$(COMPOSE_TAG) .

## Push docker-compose development environment container image
docker-compose/image-push:
	docker push $(DEVEL_IMAGE_NAME)

.PHONY: tools/docker-compose/_sources
# NOTE: tools/docker-compose/_sources should always be regenerated
## Build tools/docker-compose/_sources for docker-compose development environment
tools/docker-compose/_sources: .git/hooks/pre-commit
	@if [ $(MINIKUBE_CONTAINER_GROUP) = true ]; then\
	    ansible-playbook -i tools/docker-compose/inventory tools/docker-compose-minikube/deploy.yml; \
	fi;

	ansible-playbook -i tools/docker-compose/inventory tools/docker-compose/ansible/sources.yml \
	    -e awx_image=$(DEV_DOCKER_TAG_BASE)/awx_devel \
	    -e awx_image_tag=$(COMPOSE_TAG) \
	    -e receptor_image=$(RECEPTOR_IMAGE) \
	    -e control_plane_node_count=$(CONTROL_PLANE_NODE_COUNT) \
	    -e execution_node_count=$(EXECUTION_NODE_COUNT) \
	    -e minikube_container_group=$(MINIKUBE_CONTAINER_GROUP) \
	    -e enable_keycloak=$(KEYCLOAK) \
	    -e enable_ldap=$(LDAP) \
	    -e enable_splunk=$(SPLUNK) \
	    -e enable_prometheus=$(PROMETHEUS) \
	    -e enable_grafana=$(GRAFANA)

# ------------------------------------------------------------------------------#
# Targets used for running awx docker-compose development environment           #
# ------------------------------------------------------------------------------#

## Start docker-composed based awx development environment
docker-compose: awx/projects tools/docker-compose/_sources
	docker-compose \
	    -f tools/docker-compose/_sources/docker-compose.yml $(COMPOSE_OPTS) \
	    up $(COMPOSE_UP_OPTS) --remove-orphans

## Run docker-compose development environment without starting services
docker-compose/bash:
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports awx_1 /bin/bash

## Run AWX API test in docker-compose development environment
docker-compose/test: awx/projects tools/docker-compose/_sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports awx_1 /start_tests.sh

## Run swagger test in docker-compose development environment
docker-compose/swagger: awx/projects tools/docker-compose/_sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports --no-deps awx_1 /start_tests.sh swagger

## Docker Development Environment with Elastic Stack Connected
docker-compose/elk: awx/projects tools/docker-compose/_sources
	docker-compose \
	    -f tools/docker-compose/_sources/docker-compose.yml \
	    -f tools/elastic/docker-compose.logstash-link.yml \
	    -f tools/elastic/docker-compose.elastic-override.yml \
	    up --no-recreate

## Deploy docker-compose development environment with Elastic stack with logstash cluster
docker-compose/elk-cluster: awx/projects tools/docker-compose/_sources
	docker-compose \
	    -f tools/docker-compose/_sources/docker-compose.yml \
	    -f tools/elastic/docker-compose.logstash-link-cluster.yml \
	    -f tools/elastic/docker-compose.elastic-override.yml \
	    up --no-recreate

## Deploy docker-compose development environment minikube container group
docker-compose/container-group:
	MINIKUBE_CONTAINER_GROUP=true make docker-compose

## Deploy docker-compose development environment with credential plugin
docker-compose/credential-plugins: awx/projects tools/docker-compose/_sources
	@echo "\033[0;31mGenerate a CyberArk Conjur API key: docker exec -it tools_conjur_1 conjurctl account create quick-start\033[0m"
	docker-compose \
		-f tools/docker-compose/_sources/docker-compose.yml \
		-f tools/docker-credential-plugins-override.yml \
		up --no-recreate --remove-orphans awx_1

# ------------------------------------------------------------------------------#
# Targets used for cleanup awx docker-compose development environment           #
# ------------------------------------------------------------------------------#

## Remove docker-compose development environment
docker-compose/remove: awx/projects
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml rm -sf

## Cleanup docker-compose development environment and minikube container group
docker-compose/container-group/remove:
	@if [ -f "tools/docker-compose-minikube/_sources/minikube" ]; then \
	    tools/docker-compose-minikube/_sources/minikube delete; \
	fi
	rm -rf tools/docker-compose-minikube/_sources/

## Cleanup volumes for docker-compose development environment
docker-compose/clean-volumes: docker-compose-clean docker-compose-container-group-clean
	docker volume rm -f tools_awx_db tools_grafana_storage tools_prometheus_storage $(docker volume ls --filter name=tools_redis_socket_ -q)

## Force remove all tools_awx and tools_receptor container and awx_devel images
docker-compose/force-clean-images:
	$(foreach container_id,$(shell docker ps -f name=tools_awx -aq && docker ps -f name=tools_receptor -aq),docker stop $(container_id); docker rm -f $(container_id);)
	@if [ "$(shell docker images | grep awx_devel)" ]; then \
	  docker images | grep awx_devel | awk '{print $$3}' | xargs docker rmi --force; \
	fi

## Stop and remove all elk containers for docker-compose development environment
docker-compose/elk/remove:
	@docker stop tools_kibana_1 || true
	@docker stop tools_logstash_1 || true
	@docker stop tools_elasticsearch_1 || true
	@docker rm tools_logstash_1 || true
	@docker rm tools_elasticsearch_1 || true
	@docker rm tools_kibana_1 || true

## Remove all container for docker-compose development environment
docker-compose/remove-all: docker-compose/remove docker-compose/elk/remove docker-compose/container-group/remove

## Clean all containers volumes and images for docker-compose development environment
docker-compose/clean-all: docker-compose/remove-all docker-compose/clean-volumes docker-compose/force-clean-images

## Refresh docker-compose development environment
docker-compose/refresh: docker-compose/clean-all docker-compose

# ------------------------------------------------------------------------------#
# Targets used for awx kubernetes development environment                       #
# ------------------------------------------------------------------------------#

## Generate Dockerfile for kubernetes development environment container image
Dockerfile.kube-dev: tools/ansible/roles/dockerfile/templates/Dockerfile.j2
	ansible-playbook tools/ansible/dockerfile.yml \
	    -e dockerfile_name=Dockerfile.kube-dev \
	    -e kube_dev=True \
	    -e template_dest=_build_kube_dev \
	    -e receptor_image=$(RECEPTOR_IMAGE)

## Build kubernetes development environment container image
kube-dev/image-build: Dockerfile.kube-dev
	DOCKER_BUILDKIT=1 docker build -f Dockerfile.kube-dev \
	    --build-arg BUILDKIT_INLINE_CACHE=1 \
	    --cache-from=$(DEV_DOCKER_TAG_BASE)/awx_kube_devel:$(COMPOSE_TAG) \
	    -t $(DEV_DOCKER_TAG_BASE)/awx_kube_devel:$(COMPOSE_TAG) .

## Push kubernetes development environment container image
kube-dev/image-push:
	docker push $(DEV_DOCKER_TAG_BASE)/awx_kube_devel:$(COMPOSE_TAG)

# ------------------------------------------------------------------------------#
# Unused targets ¯\_(ツ)_/¯                                                     #
# ------------------------------------------------------------------------------#
## Run Postgres 12 in docker container ¯\_(ツ)_/¯
psql-container:
	docker run -it --net tools_default --rm postgres:12 sh -c 'exec psql -h "postgres" -p "5432" -U postgres'

