PYTHON ?= python3.8
PYTHON_VERSION = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_version; print(get_python_version())")
SITELIB=$(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
OFFICIAL ?= no
PACKER ?= packer
PACKER_BUILD_OPTS ?= -var 'official=$(OFFICIAL)' -var 'aw_repo_url=$(AW_REPO_URL)'
NODE ?= node
NPM_BIN ?= npm
CHROMIUM_BIN=/tmp/chrome-linux/chrome
DEPS_SCRIPT ?= packaging/bundle/deps.py
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
MANAGEMENT_COMMAND ?= awx-manage
IMAGE_REPOSITORY_AUTH ?=
IMAGE_REPOSITORY_BASE ?= https://gcr.io
VERSION := $(shell cat VERSION)

# NOTE: This defaults the container image version to the branch that's active
COMPOSE_TAG ?= $(GIT_BRANCH)
COMPOSE_HOST ?= $(shell hostname)
MAIN_NODE_TYPE ?= hybrid

VENV_BASE ?= /var/lib/awx/venv/
SCL_PREFIX ?=
CELERY_SCHEDULE_FILE ?= /var/lib/awx/beat.db

DEV_DOCKER_TAG_BASE ?= quay.io/awx
DEVEL_IMAGE_NAME ?= $(DEV_DOCKER_TAG_BASE)/awx_devel:$(COMPOSE_TAG)

# Python packages to install only from source (not from binary wheels)
# Comma separated list
SRC_ONLY_PKGS ?= cffi,pycparser,psycopg2,twilio
# These should be upgraded in the AWX and Ansible venv before attempting
# to install the actual requirements
VENV_BOOTSTRAP ?= pip==19.3.1 setuptools==41.6.0 wheel==0.36.2

# Determine appropriate shasum command
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    SHASUM_BIN ?= sha256sum
endif
ifeq ($(UNAME_S),Darwin)
    SHASUM_BIN ?= shasum -a 256
endif

# Get the branch information from git
GIT_DATE := $(shell git log -n 1 --format="%ai")
DATE := $(shell date -u +%Y%m%d%H%M)

NAME ?= awx
GIT_REMOTE_URL = $(shell git config --get remote.origin.url)

# TAR build parameters
SDIST_TAR_NAME=$(NAME)-$(VERSION)
WHEEL_NAME=$(NAME)-$(VERSION)

SDIST_COMMAND ?= sdist
WHEEL_COMMAND ?= bdist_wheel
SDIST_TAR_FILE ?= $(SDIST_TAR_NAME).tar.gz
WHEEL_FILE ?= $(WHEEL_NAME)-py2-none-any.whl

I18N_FLAG_FILE = .i18n_built

.PHONY: awx-link clean clean-tmp clean-venv requirements requirements_dev \
	develop refresh adduser migrate dbchange \
	receiver test test_unit test_coverage coverage_html \
	dev_build release_build sdist \
	ui-release ui-devel \
	VERSION docker-compose-sources \
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
	find ./awx/locale/ -type f -regex ".*\.mo$" -delete

# Remove temporary build files, compiled Python files.
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
	find . -type f -regex ".*\.py[co]$$" -delete
	find . -type d -name "__pycache__" -delete
	rm -f awx/awx_test.sqlite3*
	rm -rf requirements/vendor
	rm -rf awx/projects

clean-awxkit:
	rm -rf awxkit/*.egg-info awxkit/.tox awxkit/build/*

# convenience target to assert environment variables are defined
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

# Install third-party requirements needed for AWX's environment.
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

# "Install" awx package in development mode.
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

# Do any one-time init tasks.
comma := ,
init:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(MANAGEMENT_COMMAND) provision_instance --hostname=$(COMPOSE_HOST) --node_type=$(MAIN_NODE_TYPE); \
	$(MANAGEMENT_COMMAND) register_queue --queuename=controlplane --instance_percent=100;\
	$(MANAGEMENT_COMMAND) register_queue --queuename=default --instance_percent=100;
	if [ ! -f /etc/receptor/certs/awx.key ]; then \
		rm -f /etc/receptor/certs/*; \
		receptor --cert-init commonname="AWX Test CA" bits=2048 outcert=/etc/receptor/certs/ca.crt outkey=/etc/receptor/certs/ca.key; \
		for node in $(RECEPTOR_MUTUAL_TLS); do \
			receptor --cert-makereq bits=2048 commonname="$$node test cert" dnsname=$$node nodeid=$$node outreq=/etc/receptor/certs/$$node.csr outkey=/etc/receptor/certs/$$node.key; \
			receptor --cert-signreq req=/etc/receptor/certs/$$node.csr cacert=/etc/receptor/certs/ca.crt cakey=/etc/receptor/certs/ca.key outcert=/etc/receptor/certs/$$node.crt verify=yes; \
		done; \
	fi

# Refresh development environment after pulling new code.
refresh: clean requirements_dev version_file develop migrate

# Create Django superuser.
adduser:
	$(MANAGEMENT_COMMAND) createsuperuser

# Create database tables and apply any new migrations.
migrate:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(MANAGEMENT_COMMAND) migrate --noinput

# Run after making changes to the models to create a new migration.
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
	mkdir -p awx/public/static && $(PYTHON) manage.py collectstatic --clear --noinput > /dev/null 2>&1

UWSGI_DEV_RELOAD_COMMAND ?= supervisorctl restart tower-processes:awx-dispatcher tower-processes:awx-receiver

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
	    --py-autoreload 1 \
	    --max-requests=1000 \
	    --stats /tmp/stats.socket \
	    --lazy-apps \
	    --logformat "%(addr) %(method) %(uri) - %(proto) %(status)" \
	    --hook-accepting1="exec: $(UWSGI_DEV_RELOAD_COMMAND)"

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

# Run to start the background task dispatcher for development.
dispatcher:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_dispatcher


# Run to start the zeromq callback receiver
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
	[ -d "/awx_devel/awx.egg-info" ] || $(PYTHON) /awx_devel/setup.py egg_info_dev
	cp -f /tmp/awx.egg-link /var/lib/awx/venv/awx/lib/python$(PYTHON_VERSION)/site-packages/awx.egg-link

TEST_DIRS ?= awx/main/tests/unit awx/main/tests/functional awx/conf/tests awx/sso/tests

# Run all API unit tests.
test:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	PYTHONDONTWRITEBYTECODE=1 py.test -p no:cacheprovider -n auto $(TEST_DIRS)
	cmp VERSION awxkit/VERSION || "VERSION and awxkit/VERSION *must* match"
	cd awxkit && $(VENV_BASE)/awx/bin/tox -re py3
	awx-manage check_migrations --dry-run --check  -n 'missing_migration_file'

COLLECTION_TEST_DIRS ?= awx_collection/test/awx
COLLECTION_TEST_TARGET ?=
COLLECTION_PACKAGE ?= awx
COLLECTION_NAMESPACE ?= awx
COLLECTION_INSTALL = ~/.ansible/collections/ansible_collections/$(COLLECTION_NAMESPACE)/$(COLLECTION_PACKAGE)

test_collection:
	rm -f $(shell ls -d $(VENV_BASE)/awx/lib/python* | head -n 1)/no-global-site-packages.txt
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi && \
	pip install ansible-core && \
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

build_collection:
	ansible-playbook -i localhost, awx_collection/tools/template_galaxy.yml -e collection_package=$(COLLECTION_PACKAGE) -e collection_namespace=$(COLLECTION_NAMESPACE) -e collection_version=$(VERSION) -e '{"awx_template_version":false}'
	ansible-galaxy collection build awx_collection_build --force --output-path=awx_collection_build

install_collection: build_collection
	rm -rf $(COLLECTION_INSTALL)
	ansible-galaxy collection install awx_collection_build/$(COLLECTION_NAMESPACE)-$(COLLECTION_PACKAGE)-$(VERSION).tar.gz

test_collection_sanity: install_collection
	cd $(COLLECTION_INSTALL) && ansible-test sanity

test_collection_integration: install_collection
	cd $(COLLECTION_INSTALL) && ansible-test integration $(COLLECTION_TEST_TARGET)

test_unit:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	py.test awx/main/tests/unit awx/conf/tests/unit awx/sso/tests/unit

# Run all API unit tests with coverage enabled.
test_coverage:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	py.test --create-db --cov=awx --cov-report=xml --junitxml=./reports/junit.xml $(TEST_DIRS)

# Output test coverage as HTML (into htmlcov directory).
coverage_html:
	coverage html

# Run API unit tests across multiple Python/Django versions with Tox.
test_tox:
	tox -v

# Make fake data
DATA_GEN_PRESET = ""
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

awx/ui/node_modules:
	NODE_OPTIONS=--max-old-space-size=4096 $(NPM_BIN) --prefix awx/ui --loglevel warn ci

$(UI_BUILD_FLAG_FILE):
	$(PYTHON) tools/scripts/compilemessages.py
	$(NPM_BIN) --prefix awx/ui --loglevel warn run compile-strings
	$(NPM_BIN) --prefix awx/ui --loglevel warn run build
	mkdir -p awx/public/static/css
	mkdir -p awx/public/static/js
	mkdir -p awx/public/static/media
	cp -r awx/ui/build/static/css/* awx/public/static/css
	cp -r awx/ui/build/static/js/* awx/public/static/js
	cp -r awx/ui/build/static/media/* awx/public/static/media
	touch $@

ui-release: awx/ui/node_modules $(UI_BUILD_FLAG_FILE)

ui-devel: awx/ui/node_modules
	@$(MAKE) -B $(UI_BUILD_FLAG_FILE)

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
	$(NPM_BIN) run --prefix awx/ui test -- --coverage --maxWorkers=4 --watchAll=false


# Build a pip-installable package into dist/ with a timestamped version number.
dev_build:
	$(PYTHON) setup.py dev_build

# Build a pip-installable package into dist/ with the release version number.
release_build:
	$(PYTHON) setup.py release_build

dist/$(SDIST_TAR_FILE): ui-release VERSION
	$(PYTHON) setup.py $(SDIST_COMMAND)

dist/$(WHEEL_FILE): ui-release
	$(PYTHON) setup.py $(WHEEL_COMMAND)

sdist: dist/$(SDIST_TAR_FILE)
	@echo "#############################################"
	@echo "Artifacts:"
	@echo dist/$(SDIST_TAR_FILE)
	@echo "#############################################"

wheel: dist/$(WHEEL_FILE)
	@echo "#############################################"
	@echo "Artifacts:"
	@echo dist/$(WHEEL_FILE)
	@echo "#############################################"

# Build setup bundle tarball
setup-bundle-build:
	mkdir -p $@

docker-auth:
	@if [ "$(IMAGE_REPOSITORY_AUTH)" ]; then \
		echo "$(IMAGE_REPOSITORY_AUTH)" | docker login -u oauth2accesstoken --password-stdin $(IMAGE_REPOSITORY_BASE); \
	fi;

# This directory is bind-mounted inside of the development container and
# needs to be pre-created for permissions to be set correctly. Otherwise,
# Docker will create this directory as root.
awx/projects:
	@mkdir -p $@

COMPOSE_UP_OPTS ?=
COMPOSE_OPTS ?=
CONTROL_PLANE_NODE_COUNT ?= 1
EXECUTION_NODE_COUNT ?= 2
MINIKUBE_CONTAINER_GROUP ?= false

docker-compose-sources: .git/hooks/pre-commit
	@if [ $(MINIKUBE_CONTAINER_GROUP) = true ]; then\
	    ansible-playbook -i tools/docker-compose/inventory tools/docker-compose-minikube/deploy.yml; \
	fi;

	ansible-playbook -i tools/docker-compose/inventory tools/docker-compose/ansible/sources.yml \
	    -e awx_image=$(DEV_DOCKER_TAG_BASE)/awx_devel \
	    -e awx_image_tag=$(COMPOSE_TAG) \
	    -e control_plane_node_count=$(CONTROL_PLANE_NODE_COUNT) \
	    -e execution_node_count=$(EXECUTION_NODE_COUNT) \
	    -e minikube_container_group=$(MINIKUBE_CONTAINER_GROUP)


docker-compose: docker-auth awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml $(COMPOSE_OPTS) up $(COMPOSE_UP_OPTS)

docker-compose-credential-plugins: docker-auth awx/projects docker-compose-sources
	echo -e "\033[0;31mTo generate a CyberArk Conjur API key: docker exec -it tools_conjur_1 conjurctl account create quick-start\033[0m"
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml -f tools/docker-credential-plugins-override.yml up --no-recreate awx_1

docker-compose-test: docker-auth awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports awx_1 /bin/bash

docker-compose-runtest: awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports awx_1 /start_tests.sh

docker-compose-build-swagger: awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports --no-deps awx_1 /start_tests.sh swagger

detect-schema-change: genschema
	curl https://s3.amazonaws.com/awx-public-ci-files/schema.json -o reference-schema.json
	# Ignore differences in whitespace with -b
	diff -u -b reference-schema.json schema.json

docker-compose-clean: awx/projects
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml rm -sf

docker-compose-container-group-clean:
	@if [ -f "tools/docker-compose-minikube/_sources/minikube" ]; then \
	    tools/docker-compose-minikube/_sources/minikube delete; \
	fi
	rm -rf tools/docker-compose-minikube/_sources/

# Base development image build
docker-compose-build:
	ansible-playbook tools/ansible/dockerfile.yml -e build_dev=True
	DOCKER_BUILDKIT=1 docker build -t $(DEVEL_IMAGE_NAME) \
	    --build-arg BUILDKIT_INLINE_CACHE=1 \
	    --cache-from=$(DEV_DOCKER_TAG_BASE)/awx_devel:$(COMPOSE_TAG) .

docker-clean:
	$(foreach container_id,$(shell docker ps -f name=tools_awx -aq),docker stop $(container_id); docker rm -f $(container_id);)
	docker images | grep "awx_devel" | awk '{print $$3}' | xargs docker rmi

docker-clean-volumes: docker-compose-clean docker-compose-container-group-clean
	docker volume rm tools_awx_db

docker-refresh: docker-clean docker-compose

# Docker Development Environment with Elastic Stack Connected
docker-compose-elk: docker-auth awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml -f tools/elastic/docker-compose.logstash-link.yml -f tools/elastic/docker-compose.elastic-override.yml up --no-recreate

docker-compose-cluster-elk: docker-auth awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml -f tools/elastic/docker-compose.logstash-link-cluster.yml -f tools/elastic/docker-compose.elastic-override.yml up --no-recreate

prometheus:
	docker run -u0 --net=tools_default --link=`docker ps | egrep -o "tools_awx(_run)?_([^ ]+)?"`:awxweb --volume `pwd`/tools/prometheus:/prometheus --name prometheus -d -p 0.0.0.0:9090:9090 prom/prometheus --web.enable-lifecycle --config.file=/prometheus/prometheus.yml

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

Dockerfile: tools/ansible/roles/dockerfile/templates/Dockerfile.j2
	ansible-playbook tools/ansible/dockerfile.yml

Dockerfile.kube-dev: tools/ansible/roles/dockerfile/templates/Dockerfile.j2
	ansible-playbook tools/ansible/dockerfile.yml \
	    -e dockerfile_name=Dockerfile.kube-dev \
	    -e kube_dev=True \
	    -e template_dest=_build_kube_dev

awx-kube-dev-build: Dockerfile.kube-dev
	docker build -f Dockerfile.kube-dev \
	    --build-arg BUILDKIT_INLINE_CACHE=1 \
	    -t $(DEV_DOCKER_TAG_BASE)/awx_kube_devel:$(COMPOSE_TAG) .


# Translation TASKS
# --------------------------------------

# generate UI .pot file, an empty template of strings yet to be translated
pot: $(UI_BUILD_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui --loglevel warn run extract-template --clean

# generate UI .po files for each locale (will update translated strings for `en`)
po: $(UI_BUILD_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui --loglevel warn run extract-strings -- --clean

# generate API django .pot .po
LANG = "en-us"
messages:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py makemessages -l $(LANG) --keep-pot
