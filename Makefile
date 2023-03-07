PYTHON ?= python3.9
DOCKER_COMPOSE ?= docker-compose
OFFICIAL ?= no
NODE ?= node
NPM_BIN ?= npm
CHROMIUM_BIN=/tmp/chrome-linux/chrome
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
MANAGEMENT_COMMAND ?= awx-manage
VERSION := $(shell $(PYTHON) tools/scripts/scm_version.py)

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
COLLECTION_INSTALL = ~/.ansible/collections/ansible_collections/$(COLLECTION_NAMESPACE)/$(COLLECTION_PACKAGE)
COLLECTION_TEMPLATE_VERSION ?= false

# NOTE: This defaults the container image version to the branch that's active
COMPOSE_TAG ?= $(GIT_BRANCH)
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

VENV_BASE ?= /var/lib/awx/venv

DEV_DOCKER_TAG_BASE ?= ghcr.io/ansible
DEVEL_IMAGE_NAME ?= $(DEV_DOCKER_TAG_BASE)/awx_devel:$(COMPOSE_TAG)

RECEPTOR_IMAGE ?= quay.io/ansible/receptor:devel

# Python packages to install only from source (not from binary wheels)
# Comma separated list
SRC_ONLY_PKGS ?= cffi,pycparser,psycopg2,twilio
# These should be upgraded in the AWX and Ansible venv before attempting
# to install the actual requirements
VENV_BOOTSTRAP ?= pip==21.2.4 setuptools==65.6.3 setuptools_scm[toml]==7.0.5 wheel==0.38.4

NAME ?= awx

# TAR build parameters
SDIST_TAR_NAME=$(NAME)-$(VERSION)

SDIST_COMMAND ?= sdist
SDIST_TAR_FILE ?= $(SDIST_TAR_NAME).tar.gz

I18N_FLAG_FILE = .i18n_built

.PHONY: awx-link clean clean-tmp clean-venv requirements requirements_dev \
	develop refresh adduser migrate dbchange \
	receiver test test_unit test_coverage coverage_html \
	sdist \
	ui-release ui-devel \
	VERSION PYTHON_VERSION docker-compose-sources \
	.git/hooks/pre-commit github_ci_setup github_ci_runner

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
	find ./awx/locale/ -type f -regex ".*\.mo$" -delete

## Remove temporary build files, compiled Python files.
clean: clean-ui clean-api clean-awxkit clean-dist
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

supervisor:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	supervisord --pidfile=/tmp/supervisor_pid -n

collectstatic:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py collectstatic --clear --noinput > /dev/null 2>&1

DEV_RELOAD_COMMAND ?= supervisorctl restart tower-processes:*

uwsgi: collectstatic
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	uwsgi /etc/tower/uwsgi.ini

awx-autoreload:
	@/awx_devel/tools/docker-compose/awx-autoreload /awx_devel/awx "$(DEV_RELOAD_COMMAND)"

daphne:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	daphne -b 127.0.0.1 -p 8051 awx.asgi:channel_layer

wsbroadcast:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_wsbroadcast

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
	(set -o pipefail && py.test $(PYTEST_ARGS) awx/conf/tests/functional awx/main/tests/functional/api awx/main/tests/docs --release=$(VERSION_TARGET) | tee reports/$@.report)

check: black

api-lint:
	BLACK_ARGS="--check" make black
	flake8 awx
	yamllint -s .

awx-link:
	[ -d "/awx_devel/awx.egg-info" ] || $(PYTHON) /awx_devel/tools/scripts/egg_info_dev
	cp -f /tmp/awx.egg-link /var/lib/awx/venv/awx/lib/$(PYTHON)/site-packages/awx.egg-link

TEST_DIRS ?= awx/main/tests/unit awx/main/tests/functional awx/conf/tests awx/sso/tests
PYTEST_ARGS ?= -n auto
## Run all API unit tests.
test:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	PYTHONDONTWRITEBYTECODE=1 py.test -p no:cacheprovider $(PYTEST_ARGS) $(TEST_DIRS)
	cd awxkit && $(VENV_BASE)/awx/bin/tox -re py3
	awx-manage check_migrations --dry-run --check  -n 'missing_migration_file'

## Login to Github container image registry, pull image, then build image.
github_ci_setup:
	# GITHUB_ACTOR is automatic github actions env var
	# CI_GITHUB_TOKEN is defined in .github files
	echo $(CI_GITHUB_TOKEN) | docker login ghcr.io -u $(GITHUB_ACTOR) --password-stdin
	docker pull $(DEVEL_IMAGE_NAME) || :  # Pre-pull image to warm build cache
	make docker-compose-build

## Runs AWX_DOCKER_CMD inside a new docker container.
docker-runner:
	docker run -u $(shell id -u) --rm -v $(shell pwd):/awx_devel/:Z --workdir=/awx_devel $(DEVEL_IMAGE_NAME) $(AWX_DOCKER_CMD)

## Builds image and runs AWX_DOCKER_CMD in it, mainly for .github checks.
github_ci_runner: github_ci_setup docker-runner

test_collection:
	rm -f $(shell ls -d $(VENV_BASE)/awx/lib/python* | head -n 1)/no-global-site-packages.txt
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi && \
	if ! [ -x "$(shell command -v ansible-playbook)" ]; then pip install ansible-core; fi
	ansible --version
	py.test $(COLLECTION_TEST_DIRS) -v
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
	ansible-playbook -i localhost, awx_collection/tools/template_galaxy.yml \
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
	COLLECTION_VERSION=1.0.0 make install_collection
	cd $(COLLECTION_INSTALL) && ansible-test sanity $(COLLECTION_SANITY_ARGS)

test_collection_integration: install_collection
	cd $(COLLECTION_INSTALL) && ansible-test integration $(COLLECTION_TEST_TARGET)

test_unit:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	py.test awx/main/tests/unit awx/conf/tests/unit awx/sso/tests/unit

## Run all API unit tests with coverage enabled.
test_coverage:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	py.test --create-db --cov=awx --cov-report=xml --junitxml=./reports/junit.xml $(TEST_DIRS)

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


# UI TASKS
# --------------------------------------

UI_BUILD_FLAG_FILE = awx/ui/.ui-built

clean-ui:
	rm -rf node_modules
	rm -rf awx/ui/node_modules
	rm -rf awx/ui/build
	rm -rf awx/ui/src/locales/_build
	rm -rf $(UI_BUILD_FLAG_FILE)
        # the collectstatic command doesn't like it if this dir doesn't exist.
	mkdir -p awx/ui/build/static

awx/ui/node_modules:
	NODE_OPTIONS=--max-old-space-size=6144 $(NPM_BIN) --prefix awx/ui --loglevel warn --force ci

$(UI_BUILD_FLAG_FILE):
	$(MAKE) awx/ui/node_modules
	$(PYTHON) tools/scripts/compilemessages.py
	$(NPM_BIN) --prefix awx/ui --loglevel warn run compile-strings
	$(NPM_BIN) --prefix awx/ui --loglevel warn run build
	touch $@

ui-release: $(UI_BUILD_FLAG_FILE)

ui-devel: awx/ui/node_modules
	@$(MAKE) -B $(UI_BUILD_FLAG_FILE)
	mkdir -p /var/lib/awx/public/static/css
	mkdir -p /var/lib/awx/public/static/js
	mkdir -p /var/lib/awx/public/static/media
	cp -r awx/ui/build/static/css/* /var/lib/awx/public/static/css
	cp -r awx/ui/build/static/js/* /var/lib/awx/public/static/js
	cp -r awx/ui/build/static/media/* /var/lib/awx/public/static/media

ui-devel-instrumented: awx/ui/node_modules
	$(NPM_BIN) --prefix awx/ui --loglevel warn run start-instrumented

ui-devel-test: awx/ui/node_modules
	$(NPM_BIN) --prefix awx/ui --loglevel warn run start

ui-lint:
	$(NPM_BIN) --prefix awx/ui install
	$(NPM_BIN) run --prefix awx/ui lint
	$(NPM_BIN) run --prefix awx/ui prettier-check

ui-test:
	$(NPM_BIN) --prefix awx/ui install
	$(NPM_BIN) run --prefix awx/ui test

ui-test-screens:
	$(NPM_BIN) --prefix awx/ui install
	$(NPM_BIN) run --prefix awx/ui pretest
	$(NPM_BIN) run --prefix awx/ui test-screens --runInBand

ui-test-general:
	$(NPM_BIN) --prefix awx/ui install
	$(NPM_BIN) run --prefix awx/ui pretest
	$(NPM_BIN) run --prefix awx/ui/ test-general --runInBand

HEADLESS ?= no
ifeq ($(HEADLESS), yes)
dist/$(SDIST_TAR_FILE):
else
dist/$(SDIST_TAR_FILE): $(UI_BUILD_FLAG_FILE)
endif
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
	    ansible-playbook -i tools/docker-compose/inventory -e minikube_setup=$(MINIKUBE_SETUP) tools/docker-compose-minikube/deploy.yml; \
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
	    -e enable_grafana=$(GRAFANA) $(EXTRA_SOURCES_ANSIBLE_OPTS)



docker-compose: awx/projects docker-compose-sources
	$(DOCKER_COMPOSE) -f tools/docker-compose/_sources/docker-compose.yml $(COMPOSE_OPTS) up $(COMPOSE_UP_OPTS) --remove-orphans

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

## Base development image build
docker-compose-build:
	ansible-playbook tools/ansible/dockerfile.yml -e build_dev=True -e receptor_image=$(RECEPTOR_IMAGE)
	DOCKER_BUILDKIT=1 docker build -t $(DEVEL_IMAGE_NAME) \
	    --build-arg BUILDKIT_INLINE_CACHE=1 \
	    --cache-from=$(DEV_DOCKER_TAG_BASE)/awx_devel:$(COMPOSE_TAG) .

docker-clean:
	-$(foreach container_id,$(shell docker ps -f name=tools_awx -aq && docker ps -f name=tools_receptor -aq),docker stop $(container_id); docker rm -f $(container_id);)
	-$(foreach image_id,$(shell docker images --filter=reference='*awx_devel*' -aq),docker rmi --force $(image_id);)

docker-clean-volumes: docker-compose-clean docker-compose-container-group-clean
	docker volume rm -f tools_awx_db tools_grafana_storage tools_prometheus_storage $(docker volume ls --filter name=tools_redis_socket_ -q)

docker-refresh: docker-clean docker-compose

## Docker Development Environment with Elastic Stack Connected
docker-compose-elk: awx/projects docker-compose-sources
	$(DOCKER_COMPOSE) -f tools/docker-compose/_sources/docker-compose.yml -f tools/elastic/docker-compose.logstash-link.yml -f tools/elastic/docker-compose.elastic-override.yml up --no-recreate

docker-compose-cluster-elk: awx/projects docker-compose-sources
	$(DOCKER_COMPOSE) -f tools/docker-compose/_sources/docker-compose.yml -f tools/elastic/docker-compose.logstash-link-cluster.yml -f tools/elastic/docker-compose.elastic-override.yml up --no-recreate

docker-compose-container-group:
	MINIKUBE_CONTAINER_GROUP=true make docker-compose

clean-elk:
	docker stop tools_kibana_1
	docker stop tools_logstash_1
	docker stop tools_elasticsearch_1
	docker rm tools_logstash_1
	docker rm tools_elasticsearch_1
	docker rm tools_kibana_1

psql-container:
	docker run -it --net tools_default --rm postgres:12 sh -c 'exec psql -h "postgres" -p "5432" -U postgres'

VERSION:
	@echo "awx: $(VERSION)"

PYTHON_VERSION:
	@echo "$(PYTHON)" | sed 's:python::'

.PHONY: Dockerfile
Dockerfile: tools/ansible/roles/dockerfile/templates/Dockerfile.j2
	ansible-playbook tools/ansible/dockerfile.yml -e receptor_image=$(RECEPTOR_IMAGE)

Dockerfile.kube-dev: tools/ansible/roles/dockerfile/templates/Dockerfile.j2
	ansible-playbook tools/ansible/dockerfile.yml \
	    -e dockerfile_name=Dockerfile.kube-dev \
	    -e kube_dev=True \
	    -e template_dest=_build_kube_dev \
	    -e receptor_image=$(RECEPTOR_IMAGE)

## Build awx_kube_devel image for development on local Kubernetes environment.
awx-kube-dev-build: Dockerfile.kube-dev
	DOCKER_BUILDKIT=1 docker build -f Dockerfile.kube-dev \
	    --build-arg BUILDKIT_INLINE_CACHE=1 \
	    --cache-from=$(DEV_DOCKER_TAG_BASE)/awx_kube_devel:$(COMPOSE_TAG) \
	    -t $(DEV_DOCKER_TAG_BASE)/awx_kube_devel:$(COMPOSE_TAG) .

## Build awx image for deployment on Kubernetes environment.
awx-kube-build: Dockerfile
	DOCKER_BUILDKIT=1 docker build -f Dockerfile \
		--build-arg VERSION=$(VERSION) \
		--build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$(VERSION) \
		--build-arg HEADLESS=$(HEADLESS) \
		-t $(DEV_DOCKER_TAG_BASE)/awx:$(COMPOSE_TAG) .

# Translation TASKS
# --------------------------------------

## generate UI .pot file, an empty template of strings yet to be translated
pot: $(UI_BUILD_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui --loglevel warn run extract-template --clean

## generate UI .po files for each locale (will update translated strings for `en`)
po: $(UI_BUILD_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui --loglevel warn run extract-strings -- --clean

## generate API django .pot .po
messages:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py makemessages -l en_us --keep-pot

print-%:
	@echo $($*)

# HELP related targets
# --------------------------------------

HELP_FILTER=.PHONY

## Display help targets
help:
	@printf "Available targets:\n"
	@make -s help/generate | grep -vE "\w($(HELP_FILTER))"

## Display help for all targets
help/all:
	@printf "Available targets:\n"
	@make -s help/generate

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
