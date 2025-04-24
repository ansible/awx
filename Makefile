-include awx/ui/Makefile

PYTHON := $(notdir $(shell for i in python3.11 python3; do command -v $$i; done|sed 1q))
SHELL := bash
DOCKER_COMPOSE ?= docker compose
OFFICIAL ?= no
NODE ?= node
NPM_BIN ?= npm
KIND_BIN ?= $(shell which kind)
CHROMIUM_BIN=/tmp/chrome-linux/chrome
GIT_REPO_NAME ?= $(shell basename `git rev-parse --show-toplevel`)
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
MANAGEMENT_COMMAND ?= awx-manage
VERSION ?= $(shell $(PYTHON) tools/scripts/scm_version.py 2> /dev/null)

# ansible-test requires semver compatable version, so we allow overrides to hack it
COLLECTION_VERSION ?= $(shell $(PYTHON) tools/scripts/scm_version.py | cut -d . -f 1-3)
# args for the ansible-test sanity command
COLLECTION_SANITY_ARGS ?= --docker
# collection unit testing directories
COLLECTION_TEST_DIRS ?= awx_collection/test/awx
# collection integration test directories (defaults to all)
COLLECTION_TEST_TARGET ?=
# args for collection install
COLLECTION_PACKAGE ?= awx
COLLECTION_NAMESPACE ?= awx
COLLECTION_INSTALL = $(HOME)/.ansible/collections/ansible_collections/$(COLLECTION_NAMESPACE)/$(COLLECTION_PACKAGE)
COLLECTION_TEMPLATE_VERSION ?= false

# NOTE: This defaults the container image version to the branch that's active
COMPOSE_TAG ?= $(GIT_BRANCH)
MAIN_NODE_TYPE ?= hybrid
# If set to true docker-compose will also start a pgbouncer instance and use it
PGBOUNCER ?= false
# If set to true docker-compose will also start a splunk instance
SPLUNK ?= false
# If set to true docker-compose will also start a prometheus instance
PROMETHEUS ?= false
# If set to true docker-compose will also start a grafana instance
GRAFANA ?= false
# If set to true docker-compose will also start a hashicorp vault instance
VAULT ?= false
# If set to true docker-compose will also start a hashicorp vault instance with TLS enabled
VAULT_TLS ?= false
# If set to true docker-compose will also start an OpenTelemetry Collector instance
OTEL ?= false
# If set to true docker-compose will also start a Loki instance
LOKI ?= false
# If set to true docker-compose will install editable dependencies
EDITABLE_DEPENDENCIES ?= false
# If set to true, use tls for postgres connection
PG_TLS ?= false

VENV_BASE ?= /var/lib/awx/venv

DEV_DOCKER_OWNER ?= ansible
# Docker will only accept lowercase, so github names like Paul need to be paul
DEV_DOCKER_OWNER_LOWER = $(shell echo $(DEV_DOCKER_OWNER) | tr A-Z a-z)
DEV_DOCKER_TAG_BASE ?= ghcr.io/$(DEV_DOCKER_OWNER_LOWER)
DEVEL_IMAGE_NAME ?= $(DEV_DOCKER_TAG_BASE)/$(GIT_REPO_NAME)_devel:$(COMPOSE_TAG)
IMAGE_KUBE_DEV=$(DEV_DOCKER_TAG_BASE)/$(GIT_REPO_NAME)_kube_devel:$(COMPOSE_TAG)
IMAGE_KUBE=$(DEV_DOCKER_TAG_BASE)/$(GIT_REPO_NAME):$(COMPOSE_TAG)

# Common command to use for running ansible-playbook
ANSIBLE_PLAYBOOK ?= ansible-playbook -e ansible_python_interpreter=$(PYTHON)

RECEPTOR_IMAGE ?= quay.io/ansible/receptor:devel

# Python packages to install only from source (not from binary wheels)
# Comma separated list
SRC_ONLY_PKGS ?= cffi,pycparser,psycopg,twilio
# These should be upgraded in the AWX and Ansible venv before attempting
# to install the actual requirements
VENV_BOOTSTRAP ?= pip==21.2.4 setuptools==70.3.0 setuptools_scm[toml]==8.1.0 wheel==0.45.1 cython==3.0.11

NAME ?= awx

# TAR build parameters
SDIST_TAR_NAME=$(NAME)-$(VERSION)

SDIST_COMMAND ?= sdist
SDIST_TAR_FILE ?= $(SDIST_TAR_NAME).tar.gz

I18N_FLAG_FILE = .i18n_built

## PLATFORMS defines the target platforms for  the manager image be build to provide support to multiple
PLATFORMS ?= linux/amd64,linux/arm64  # linux/ppc64le,linux/s390x

# Set up cache variables for image builds, allowing to control whether cache is used or not, ex:
# DOCKER_CACHE=--no-cache make docker-compose-build
ifeq ($(DOCKER_CACHE),)
 DOCKER_DEVEL_CACHE_FLAG=--cache-from=$(DEVEL_IMAGE_NAME)
 DOCKER_KUBE_DEV_CACHE_FLAG=--cache-from=$(IMAGE_KUBE_DEV)
 DOCKER_KUBE_CACHE_FLAG=--cache-from=$(IMAGE_KUBE)
else
 DOCKER_DEVEL_CACHE_FLAG=$(DOCKER_CACHE)
 DOCKER_KUBE_DEV_CACHE_FLAG=$(DOCKER_CACHE)
 DOCKER_KUBE_CACHE_FLAG=$(DOCKER_CACHE)
endif

.PHONY: awx-link clean clean-tmp clean-venv requirements requirements_dev \
	develop refresh adduser migrate dbchange \
	receiver test test_unit test_coverage coverage_html \
	sdist \
	VERSION PYTHON_VERSION docker-compose-sources \
	.git/hooks/pre-commit

clean-tmp:
	rm -rf tmp/

clean-venv:
	rm -rf venv/

clean-dist:
	rm -rf dist

clean-schema:
	rm -rf swagger.json
	rm -rf schema.json
	rm -rf reference-schema.json

clean-languages:
	rm -f $(I18N_FLAG_FILE)
	find ./awx/locale/ -type f -regex '.*\.mo$$' -delete

## Remove temporary build files, compiled Python files.
clean: clean-api clean-awxkit clean-dist
	rm -rf awx/public
	rm -rf awx/lib/site-packages
	rm -rf awx/job_status
	rm -rf awx/job_output
	rm -rf reports
	rm -rf tmp
	rm -rf $(I18N_FLAG_FILE)
	mkdir tmp

clean-api:
	rm -rf build $(NAME)-$(VERSION) *.egg-info
	rm -rf .tox
	find . -type f -regex ".*\.py[co]$$" -delete
	find . -type d -name "__pycache__" -delete
	rm -f awx/awx_test.sqlite3*
	rm -rf requirements/vendor
	rm -rf awx/projects

clean-awxkit:
	rm -rf awxkit/*.egg-info awxkit/.tox awxkit/build/*

## convenience target to assert environment variables are defined
guard-%:
	@if [ "$${$*}" = "" ]; then \
	    echo "The required environment variable '$*' is not set"; \
	    exit 1; \
	fi

virtualenv: virtualenv_awx

# flit is needed for offline install of certain packages, specifically ptyprocess
# it is needed for setup, but not always recognized as a setup dependency
# similar to pip, setuptools, and wheel, these are all needed here as a bootstrapping issues
virtualenv_awx:
	if [ "$(VENV_BASE)" ]; then \
		if [ ! -d "$(VENV_BASE)" ]; then \
			mkdir $(VENV_BASE); \
		fi; \
		if [ ! -d "$(VENV_BASE)/awx" ]; then \
			$(PYTHON) -m venv $(VENV_BASE)/awx; \
			$(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) $(VENV_BOOTSTRAP); \
		fi; \
	fi

## Install third-party requirements needed for AWX's environment.
# this does not use system site packages intentionally
requirements_awx: virtualenv_awx
	if [[ "$(PIP_OPTIONS)" == *"--no-index"* ]]; then \
	    cat requirements/requirements.txt requirements/requirements_local.txt | $(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) -r /dev/stdin ; \
	else \
	    cat requirements/requirements.txt requirements/requirements_git.txt | $(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) --no-binary $(SRC_ONLY_PKGS) -r /dev/stdin ; \
	fi
	$(VENV_BASE)/awx/bin/pip uninstall --yes -r requirements/requirements_tower_uninstall.txt

requirements_awx_dev:
	$(VENV_BASE)/awx/bin/pip install -r requirements/requirements_dev.txt

requirements: requirements_awx

requirements_dev: requirements_awx requirements_awx_dev

requirements_test: requirements

## "Install" awx package in development mode.
develop:
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    pip uninstall -y awx; \
	    $(PYTHON) setup.py develop; \
	else \
	    pip uninstall -y awx; \
	    $(PYTHON) setup.py develop; \
	fi

version_file:
	mkdir -p /var/lib/awx/; \
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) -c "import awx; print(awx.__version__)" > /var/lib/awx/.awx_version; \

## Refresh development environment after pulling new code.
refresh: clean requirements_dev version_file develop migrate

## Create Django superuser.
adduser:
	$(MANAGEMENT_COMMAND) createsuperuser

## Create database tables and apply any new migrations.
migrate:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(MANAGEMENT_COMMAND) migrate --noinput

## Run after making changes to the models to create a new migration.
dbchange:
	$(MANAGEMENT_COMMAND) makemigrations

collectstatic:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py collectstatic --clear --noinput > /dev/null 2>&1

uwsgi: collectstatic
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	uwsgi /etc/tower/uwsgi.ini

awx-autoreload:
	@/awx_devel/tools/docker-compose/awx-autoreload /awx_devel/awx

daphne:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	daphne -b 127.0.0.1 -p 8051 awx.asgi:channel_layer

## Run to start the background task dispatcher for development.
dispatcher:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_dispatcher

## Run to start the zeromq callback receiver
receiver:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_callback_receiver

nginx:
	nginx -g "daemon off;"

jupyter:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(MANAGEMENT_COMMAND) shell_plus --notebook

## Start the rsyslog configurer process in background in development environment.
run-rsyslog-configurer:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_rsyslog_configurer

## Start cache_clear process in background in development environment.
run-cache-clear:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_cache_clear

## Start the wsrelay process in background in development environment.
run-wsrelay:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_wsrelay

## Start the heartbeat process in background in development environment.
run-ws-heartbeat:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_ws_heartbeat

reports:
	mkdir -p $@

black: reports
	@command -v black >/dev/null 2>&1 || { echo "could not find black on your PATH, you may need to \`pip install black\`, or set AWX_IGNORE_BLACK=1" && exit 1; }
	@(set -o pipefail && $@ $(BLACK_ARGS) awx awxkit awx_collection | tee reports/$@.report)

.git/hooks/pre-commit:
	@echo "if [ -x pre-commit.sh ]; then" > .git/hooks/pre-commit
	@echo "    ./pre-commit.sh;" >> .git/hooks/pre-commit
	@echo "fi" >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit

genschema: reports
	$(MAKE) swagger PYTEST_ARGS="--genschema --create-db "
	mv swagger.json schema.json

swagger: reports
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	(set -o pipefail && py.test --cov --cov-report=xml --junitxml=reports/junit.xml $(PYTEST_ARGS) awx/conf/tests/functional awx/main/tests/functional/api awx/main/tests/docs | tee reports/$@.report)
	@if [ "${GITHUB_ACTIONS}" = "true" ]; \
	then \
	  echo 'cov-report-files=reports/coverage.xml' >> "${GITHUB_OUTPUT}"; \
	  echo 'test-result-files=reports/junit.xml' >> "${GITHUB_OUTPUT}"; \
	fi

check: black

api-lint:
	BLACK_ARGS="--check" $(MAKE) black
	flake8 awx
	yamllint -s .

## Run egg_info_dev to generate awx.egg-info for development.
awx-link:
	[ -d "/awx_devel/awx.egg-info" ] || $(PYTHON) /awx_devel/tools/scripts/egg_info_dev

TEST_DIRS ?= awx/main/tests/unit awx/main/tests/functional awx/conf/tests
PYTEST_ARGS ?= -n auto
## Run all API unit tests.
test:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	PYTHONDONTWRITEBYTECODE=1 py.test -p no:cacheprovider $(PYTEST_ARGS) $(TEST_DIRS)
	cd awxkit && $(VENV_BASE)/awx/bin/tox -re py3
	awx-manage check_migrations --dry-run --check  -n 'missing_migration_file'

live_test:
	cd awx/main/tests/live && py.test tests/

## Run all API unit tests with coverage enabled.
test_coverage:
	$(MAKE) test PYTEST_ARGS="--create-db --cov --cov-report=xml --junitxml=reports/junit.xml"
	@if [ "${GITHUB_ACTIONS}" = "true" ]; \
	then \
	  echo 'cov-report-files=awxkit/coverage.xml,reports/coverage.xml' >> "${GITHUB_OUTPUT}"; \
	  echo 'test-result-files=awxkit/report.xml,reports/junit.xml' >> "${GITHUB_OUTPUT}"; \
	fi

test_migrations:
	PYTHONDONTWRITEBYTECODE=1 py.test -p no:cacheprovider --migrations -m migration_test --create-db --cov=awx --cov-report=xml --junitxml=reports/junit.xml $(PYTEST_ARGS) $(TEST_DIRS)
	@if [ "${GITHUB_ACTIONS}" = "true" ]; \
	then \
	  echo 'cov-report-files=reports/coverage.xml' >> "${GITHUB_OUTPUT}"; \
	  echo 'test-result-files=reports/junit.xml' >> "${GITHUB_OUTPUT}"; \
	fi

## Runs AWX_DOCKER_CMD inside a new docker container.
docker-runner:
	docker run -u $(shell id -u) --rm -v $(shell pwd):/awx_devel/:Z $(AWX_DOCKER_ARGS) --workdir=/awx_devel $(DEVEL_IMAGE_NAME) $(AWX_DOCKER_CMD)

test_collection:
	rm -f $(shell ls -d $(VENV_BASE)/awx/lib/python* | head -n 1)/no-global-site-packages.txt
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi && \
	if ! [ -x "$(shell command -v ansible-playbook)" ]; then pip install ansible-core; fi
	ansible --version
	py.test $(COLLECTION_TEST_DIRS) --cov --cov-report=xml --junitxml=reports/junit.xml -v
	@if [ "${GITHUB_ACTIONS}" = "true" ]; \
	then \
	  echo 'cov-report-files=reports/coverage.xml' >> "${GITHUB_OUTPUT}"; \
	  echo 'test-result-files=reports/junit.xml' >> "${GITHUB_OUTPUT}"; \
	fi
	# The python path needs to be modified so that the tests can find Ansible within the container
	# First we will use anything expility set as PYTHONPATH
	# Second we will load any libraries out of the virtualenv (if it's unspecified that should be ok because python should not load out of an empty directory)
	# Finally we will add the system path so that the tests can find the ansible libraries

test_collection_all: test_collection

# WARNING: symlinking a collection is fundamentally unstable
# this is for rapid development iteration with playbooks, do not use with other test targets
symlink_collection:
	rm -rf $(COLLECTION_INSTALL)
	mkdir -p ~/.ansible/collections/ansible_collections/$(COLLECTION_NAMESPACE)  # in case it does not exist
	ln -s $(shell pwd)/awx_collection $(COLLECTION_INSTALL)

awx_collection_build: $(shell find awx_collection -type f)
	$(ANSIBLE_PLAYBOOK) -i localhost, awx_collection/tools/template_galaxy.yml \
	  -e collection_package=$(COLLECTION_PACKAGE) \
	  -e collection_namespace=$(COLLECTION_NAMESPACE) \
	  -e collection_version=$(COLLECTION_VERSION) \
	  -e '{"awx_template_version": $(COLLECTION_TEMPLATE_VERSION)}'
	ansible-galaxy collection build awx_collection_build --force --output-path=awx_collection_build

build_collection: awx_collection_build

install_collection: build_collection
	rm -rf $(COLLECTION_INSTALL)
	ansible-galaxy collection install awx_collection_build/$(COLLECTION_NAMESPACE)-$(COLLECTION_PACKAGE)-$(COLLECTION_VERSION).tar.gz

test_collection_sanity:
	rm -rf awx_collection_build/
	rm -rf $(COLLECTION_INSTALL)
	if ! [ -x "$(shell command -v ansible-test)" ]; then pip install ansible-core; fi
	ansible --version
	COLLECTION_VERSION=1.0.0 $(MAKE) install_collection
	cd $(COLLECTION_INSTALL) && \
		ansible-test sanity $(COLLECTION_SANITY_ARGS) --coverage --junit && \
		ansible-test coverage xml --requirements --group-by command --group-by version
	@if [ "${GITHUB_ACTIONS}" = "true" ]; \
	then \
	  echo cov-report-files="$$(find "$(COLLECTION_INSTALL)/tests/output/reports/" -type f -name 'coverage=sanity*.xml' -print0 | tr '\0' ',' | sed 's#,$$##')" >> "${GITHUB_OUTPUT}"; \
	  echo test-result-files="$$(find "$(COLLECTION_INSTALL)/tests/output/junit/" -type f -name '*.xml' -print0 | tr '\0' ',' | sed 's#,$$##')" >> "${GITHUB_OUTPUT}"; \
	fi

test_collection_integration: install_collection
	cd $(COLLECTION_INSTALL) && \
		ansible-test integration --coverage -vvv $(COLLECTION_TEST_TARGET) && \
		ansible-test coverage xml --requirements --group-by command --group-by version
	@if [ "${GITHUB_ACTIONS}" = "true" ]; \
	then \
	  echo cov-report-files="$$(find "$(COLLECTION_INSTALL)/tests/output/reports/" -type f -name 'coverage=integration*.xml' -print0 | tr '\0' ',' | sed 's#,$$##')" >> "${GITHUB_OUTPUT}"; \
	fi

test_unit:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	py.test awx/main/tests/unit awx/conf/tests/unit

## Output test coverage as HTML (into htmlcov directory).
coverage_html:
	coverage html

## Run API unit tests across multiple Python/Django versions with Tox.
test_tox:
	tox -v


DATA_GEN_PRESET = ""
## Make fake data
bulk_data:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) tools/data_generators/rbac_dummy_data_generator.py --preset=$(DATA_GEN_PRESET)

dist/$(SDIST_TAR_FILE):
	$(PYTHON) -m build -s
	ln -sf $(SDIST_TAR_FILE) dist/awx.tar.gz

sdist: dist/$(SDIST_TAR_FILE)
	echo $(HEADLESS)
	@echo "#############################################"
	@echo "Artifacts:"
	@echo dist/$(SDIST_TAR_FILE)
	@echo "#############################################"

# This directory is bind-mounted inside of the development container and
# needs to be pre-created for permissions to be set correctly. Otherwise,
# Docker will create this directory as root.
awx/projects:
	@mkdir -p $@

COMPOSE_UP_OPTS ?=
COMPOSE_OPTS ?=
CONTROL_PLANE_NODE_COUNT ?= 1
EXECUTION_NODE_COUNT ?= 0
MINIKUBE_CONTAINER_GROUP ?= false
MINIKUBE_SETUP ?= false # if false, run minikube separately
EXTRA_SOURCES_ANSIBLE_OPTS ?=

ifneq ($(ADMIN_PASSWORD),)
	EXTRA_SOURCES_ANSIBLE_OPTS := -e admin_password=$(ADMIN_PASSWORD) $(EXTRA_SOURCES_ANSIBLE_OPTS)
endif

docker-compose-sources: .git/hooks/pre-commit
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
	$(DOCKER_COMPOSE) -f tools/docker-compose/_sources/docker-compose.yml $(COMPOSE_OPTS) up $(COMPOSE_UP_OPTS) --remove-orphans

docker-compose-down:
	$(DOCKER_COMPOSE) -f tools/docker-compose/_sources/docker-compose.yml $(COMPOSE_OPTS) down --remove-orphans

docker-compose-credential-plugins: awx/projects docker-compose-sources
	echo -e "\033[0;31mTo generate a CyberArk Conjur API key: docker exec -it tools_conjur_1 conjurctl account create quick-start\033[0m"
	$(DOCKER_COMPOSE) -f tools/docker-compose/_sources/docker-compose.yml -f tools/docker-credential-plugins-override.yml up --no-recreate awx_1 --remove-orphans

docker-compose-test: awx/projects docker-compose-sources
	$(DOCKER_COMPOSE) -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports awx_1 /bin/bash

docker-compose-runtest: awx/projects docker-compose-sources
	$(DOCKER_COMPOSE) -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports awx_1 /start_tests.sh

docker-compose-build-swagger: awx/projects docker-compose-sources
	$(DOCKER_COMPOSE) -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports --no-deps awx_1 /start_tests.sh swagger

SCHEMA_DIFF_BASE_BRANCH ?= devel
detect-schema-change: genschema
	curl https://s3.amazonaws.com/awx-public-ci-files/$(SCHEMA_DIFF_BASE_BRANCH)/schema.json -o reference-schema.json
	# Ignore differences in whitespace with -b
	diff -u -b reference-schema.json schema.json

docker-compose-clean: awx/projects
	$(DOCKER_COMPOSE) -f tools/docker-compose/_sources/docker-compose.yml rm -sf

docker-compose-container-group-clean:
	@if [ -f "tools/docker-compose-minikube/_sources/minikube" ]; then \
	    tools/docker-compose-minikube/_sources/minikube delete; \
	fi
	rm -rf tools/docker-compose-minikube/_sources/

.PHONY: Dockerfile.dev
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

.PHONY: docker-compose-buildx
## Build awx_devel image for docker compose development environment for multiple architectures
docker-compose-buildx: Dockerfile.dev
	- docker buildx create --name docker-compose-buildx
	docker buildx use docker-compose-buildx
	- docker buildx build \
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

VERSION:
	@echo "awx: $(VERSION)"

PYTHON_VERSION:
	@echo "$(subst python,,$(PYTHON))"

.PHONY: version-for-buildyml
version-for-buildyml:
	@echo $(firstword $(subst +, ,$(VERSION)))
# version-for-buildyml prints a special version string for build.yml,
# chopping off the sha after the '+' sign.
# tools/ansible/build.yml was doing this: make print-VERSION | cut -d + -f -1
# This does the same thing in native make without
# the pipe or the extra processes, and now the pb does `make version-for-buildyml`
# Example:
# 	22.1.1.dev38+g523c0d9781 becomes 22.1.1.dev38

.PHONY: Dockerfile
## Generate Dockerfile for awx image
Dockerfile: tools/ansible/roles/dockerfile/templates/Dockerfile.j2
	$(ANSIBLE_PLAYBOOK) tools/ansible/dockerfile.yml \
		-e receptor_image=$(RECEPTOR_IMAGE) \
		-e headless=$(HEADLESS)

## Build awx image for deployment on Kubernetes environment.
awx-kube-build: Dockerfile
	DOCKER_BUILDKIT=1 docker build -f Dockerfile \
		--ssh default=$(SSH_AUTH_SOCK) \
		--build-arg VERSION=$(VERSION) \
		--build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$(VERSION) \
		--build-arg HEADLESS=$(HEADLESS) \
		$(DOCKER_KUBE_CACHE_FLAG) \
		-t $(IMAGE_KUBE) .

## Build multi-arch awx image for deployment on Kubernetes environment.
awx-kube-buildx: Dockerfile
	- docker buildx create --name awx-kube-buildx
	docker buildx use awx-kube-buildx
	- docker buildx build \
		--ssh default=$(SSH_AUTH_SOCK) \
		--push \
		--build-arg VERSION=$(VERSION) \
		--build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$(VERSION) \
		--build-arg HEADLESS=$(HEADLESS) \
		--platform=$(PLATFORMS) \
		$(DOCKER_KUBE_CACHE_FLAG) \
		--tag $(IMAGE_KUBE) \
		-f Dockerfile .
	- docker buildx rm awx-kube-buildx


.PHONY: Dockerfile.kube-dev
## Generate Docker.kube-dev for awx_kube_devel image
Dockerfile.kube-dev: tools/ansible/roles/dockerfile/templates/Dockerfile.j2
	$(ANSIBLE_PLAYBOOK) tools/ansible/dockerfile.yml \
	    -e dockerfile_name=Dockerfile.kube-dev \
	    -e kube_dev=True \
	    -e template_dest=_build_kube_dev \
	    -e receptor_image=$(RECEPTOR_IMAGE)

## Build awx_kube_devel image for development on local Kubernetes environment.
awx-kube-dev-build: Dockerfile.kube-dev
	DOCKER_BUILDKIT=1 docker build -f Dockerfile.kube-dev \
		--ssh default=$(SSH_AUTH_SOCK) \
	    --build-arg BUILDKIT_INLINE_CACHE=1 \
	     $(DOCKER_KUBE_DEV_CACHE_FLAG) \
	    -t $(IMAGE_KUBE_DEV) .

## Build and push multi-arch awx_kube_devel image for development on local Kubernetes environment.
awx-kube-dev-buildx: Dockerfile.kube-dev
	- docker buildx create --name awx-kube-dev-buildx
	docker buildx use awx-kube-dev-buildx
	- docker buildx build \
		--ssh default=$(SSH_AUTH_SOCK) \
		--push \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		$(DOCKER_KUBE_DEV_CACHE_FLAG) \
		--platform=$(PLATFORMS) \
		--tag $(IMAGE_KUBE_DEV) \
		-f Dockerfile.kube-dev .
	- docker buildx rm awx-kube-dev-buildx

kind-dev-load: awx-kube-dev-build
	$(KIND_BIN) load docker-image $(IMAGE_KUBE_DEV)

# Translation TASKS
# --------------------------------------

## generate API django .pot .po
messages:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py makemessages -l en_us --keep-pot

.PHONY: print-%
print-%:
	@echo $($*)

# HELP related targets
# --------------------------------------

HELP_FILTER=.PHONY

## Display help targets
help:
	@printf "Available targets:\n"
	@$(MAKE) -s help/generate | grep -vE "\w($(HELP_FILTER))"

## Display help for all targets
help/all:
	@printf "Available targets:\n"
	@$(MAKE) -s help/generate

## Generate help output from MAKEFILE_LIST
help/generate:
	@awk '/^[-a-zA-Z_0-9%:\\\.\/]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = $$1; \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			gsub("\\\\", "", helpCommand); \
			gsub(":+$$", "", helpCommand); \
			printf "  \x1b[32;01m%-35s\x1b[0m %s\n", helpCommand, helpMessage; \
		} else { \
			helpCommand = $$1; \
			gsub("\\\\", "", helpCommand); \
			gsub(":+$$", "", helpCommand); \
			printf "  \x1b[32;01m%-35s\x1b[0m %s\n", helpCommand, "No help available"; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST) | sort -u
	@printf "\n"

## Display help for ui targets
help/ui:
	@$(MAKE) -s help MAKEFILE_LIST="awx/ui/Makefile"
