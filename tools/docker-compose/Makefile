COMPOSE_UP_OPTS ?=
COMPOSE_OPTS ?=
CONTROL_PLANE_NODE_COUNT ?= 1
EXECUTION_NODE_COUNT ?= 0
MINIKUBE_CONTAINER_GROUP ?= false
MINIKUBE_SETUP ?= false
EXTRA_SOURCES_ANSIBLE_OPTS ?=

# Build the list of compose files from the base + active overrides.
# `docker-compose-sources` activates every enabled override into
# _sources/overrides/: static ones (splunk, prometheus, grafana, otel, loki,
# minikube) are copied from tools/docker-compose/overrides/, dynamic ones
# (vault, pgbouncer, execution-nodes, editable-deps) are rendered from J2
# templates. The wildcard picks up whatever the last sources run activated,
# so enabled-service state is remembered between make invocations — exactly
# like the old monolithic rendered docker-compose.yml.
# Uses = (not :=) so $(wildcard) is evaluated at use-time, after
# docker-compose-sources has rendered the files.
COMPOSE_FILES = -f tools/docker-compose/_sources/docker-compose.yml
COMPOSE_FILES += $(patsubst %,-f %,$(sort $(wildcard tools/docker-compose/_sources/overrides/*.yml)))

ifneq ($(ADMIN_PASSWORD),)
	EXTRA_SOURCES_ANSIBLE_OPTS := -e admin_password=$(ADMIN_PASSWORD) $(EXTRA_SOURCES_ANSIBLE_OPTS)
endif

.PHONY: docker-compose-sources docker-compose docker-compose-up docker-compose-down \
	docker-compose-credential-plugins docker-compose-test docker-compose-runtest \
	docker-compose-build-schema docker-compose-clean docker-compose-container-group-clean \
	docker-compose-build docker-compose-buildx docker-clean docker-clean-volumes \
	docker-refresh docker-compose-container-group docker-compose-logstash Dockerfile.dev

docker-compose-sources: $(GIT_COMMON_DIR)/hooks/pre-commit
	@if [ $(MINIKUBE_CONTAINER_GROUP) = true ]; then\
	    $(ANSIBLE_PLAYBOOK) -i tools/docker-compose/inventory -e minikube_setup=$(MINIKUBE_SETUP) tools/docker-compose-minikube/deploy.yml; \
	fi;

	$(ANSIBLE_PLAYBOOK) -i tools/docker-compose/inventory tools/docker-compose/ansible/sources.yml \
	    -e awx_image=$(DEV_DOCKER_TAG_BASE)/$(GIT_REPO_NAME)_devel \
	    -e awx_image_tag=$(COMPOSE_TAG) \
	    -e receptor_image=$(RECEPTOR_IMAGE) \
	    -e control_plane_node_count=$(CONTROL_PLANE_NODE_COUNT) \
	    -e execution_node_count=$(EXECUTION_NODE_COUNT) \
	    -e minikube_container_group=$(MINIKUBE_CONTAINER_GROUP) \
	    -e enable_pgbouncer=$(PGBOUNCER) \
	    -e enable_splunk=$(SPLUNK) \
	    -e enable_prometheus=$(PROMETHEUS) \
	    -e enable_grafana=$(GRAFANA) \
	    -e enable_vault=$(VAULT) \
	    -e vault_tls=$(VAULT_TLS) \
	    -e enable_otel=$(OTEL) \
	    -e enable_loki=$(LOKI) \
	    -e install_editable_dependencies=$(EDITABLE_DEPENDENCIES) \
	    -e pg_tls=$(PG_TLS) \
	    $(EXTRA_SOURCES_ANSIBLE_OPTS)

docker-compose: awx/projects docker-compose-sources
	ansible-galaxy install --ignore-certs -r tools/docker-compose/ansible/requirements.yml;
	$(ANSIBLE_PLAYBOOK) -i tools/docker-compose/inventory tools/docker-compose/ansible/initialize_containers.yml \
	    -e enable_vault=$(VAULT) \
	    -e vault_tls=$(VAULT_TLS); \
	$(MAKE) docker-compose-up

docker-compose-up:
	$(if $(GIT_IS_WORKTREE),SETUPTOOLS_SCM_PRETEND_VERSION="$(VERSION)") $(DOCKER_COMPOSE) $(COMPOSE_FILES) $(COMPOSE_OPTS) up $(COMPOSE_UP_OPTS) --remove-orphans

docker-compose-down:
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) $(COMPOSE_OPTS) down --remove-orphans

docker-compose-credential-plugins: awx/projects docker-compose-sources
	echo -e "\033[0;31mTo generate a CyberArk Conjur API key: docker exec -it tools_conjur_1 conjurctl account create quick-start\033[0m"
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) -f tools/docker-compose/overrides/credential-plugins.yml up --no-recreate awx_1 --remove-orphans

docker-compose-test: awx/projects docker-compose-sources
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) run --rm --service-ports awx_1 /bin/bash

docker-compose-runtest: awx/projects docker-compose-sources
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) run --rm --service-ports awx_1 /start_tests.sh

docker-compose-build-schema: awx/projects docker-compose-sources
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) run --rm --service-ports --no-deps awx_1 make genschema

docker-compose-clean: awx/projects
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) rm -sf

docker-compose-container-group-clean:
	@if [ -f "tools/docker-compose-minikube/_sources/minikube" ]; then \
	    tools/docker-compose-minikube/_sources/minikube delete; \
	fi
	rm -rf tools/docker-compose-minikube/_sources/

## Generate Dockerfile.dev for awx_devel image
Dockerfile.dev: tools/ansible/roles/dockerfile/templates/Dockerfile.j2
	$(ANSIBLE_PLAYBOOK) tools/ansible/dockerfile.yml \
		-e dockerfile_name=Dockerfile.dev \
		-e build_dev=True \
		-e receptor_image=$(RECEPTOR_IMAGE)

## Build awx_devel image for docker compose development environment
docker-compose-build: Dockerfile.dev
	DOCKER_BUILDKIT=1 docker build \
		--ssh default=$(SSH_AUTH_SOCK) \
		-f Dockerfile.dev \
		-t $(DEVEL_IMAGE_NAME) \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		$(DOCKER_DEVEL_CACHE_FLAG) .

## Build awx_devel image for docker compose development environment for multiple architectures
docker-compose-buildx: Dockerfile.dev
	- docker buildx create --name docker-compose-buildx
	docker buildx use docker-compose-buildx
	docker buildx build \
		--ssh default=$(SSH_AUTH_SOCK) \
		--push \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		$(DOCKER_DEVEL_CACHE_FLAG) \
		--platform=$(PLATFORMS) \
		--tag $(DEVEL_IMAGE_NAME) \
		-f Dockerfile.dev .
	- docker buildx rm docker-compose-buildx

docker-clean:
	-$(foreach container_id,$(shell docker ps -f name=tools_awx -aq && docker ps -f name=tools_receptor -aq),docker stop $(container_id); docker rm -f $(container_id);)
	-$(foreach image_id,$(shell docker images --filter=reference='*/*/*awx_devel*' --filter=reference='*/*awx_devel*' --filter=reference='*awx_devel*' -aq),docker rmi --force $(image_id);)

docker-clean-volumes: docker-compose-clean docker-compose-container-group-clean
	docker volume rm -f tools_var_lib_awx tools_awx_db tools_awx_db_15 tools_vault_1 tools_grafana_storage tools_prometheus_storage $(shell docker volume ls --filter name=tools_redis_socket_ -q)

docker-refresh: docker-clean docker-compose

docker-compose-container-group:
	MINIKUBE_CONTAINER_GROUP=true $(MAKE) docker-compose

docker-compose-logstash: awx/projects docker-compose-sources
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) -f tools/docker-compose/overrides/logstash.yml $(COMPOSE_OPTS) up $(COMPOSE_UP_OPTS) --remove-orphans
