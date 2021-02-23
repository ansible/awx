PYTHON ?= python3
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
PYCURL_SSL_LIBRARY ?= openssl

# NOTE: This defaults the container image version to the branch that's active
COMPOSE_TAG ?= $(GIT_BRANCH)
COMPOSE_HOST ?= $(shell hostname)

VENV_BASE ?= /var/lib/awx/venv/
COLLECTION_BASE ?= /var/lib/awx/vendor/awx_ansible_collections
SCL_PREFIX ?=
CELERY_SCHEDULE_FILE ?= /var/lib/awx/beat.db

DEV_DOCKER_TAG_BASE ?= gcr.io/ansible-tower-engineering
DEVEL_IMAGE_NAME ?= $(DEV_DOCKER_TAG_BASE)/awx_devel:$(COMPOSE_TAG)

# Python packages to install only from source (not from binary wheels)
# Comma separated list
SRC_ONLY_PKGS ?= cffi,pycparser,psycopg2,twilio,pycurl
# These should be upgraded in the AWX and Ansible venv before attempting
# to install the actual requirements
VENV_BOOTSTRAP ?= pip==19.3.1 setuptools==41.6.0

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
	develop refresh adduser migrate dbchange runserver \
	receiver test test_unit test_coverage coverage_html \
	dev_build release_build release_clean sdist \
	ui-docker-machine ui-docker ui-release ui-devel \
	ui-test ui-deps ui-test-ci VERSION docker-compose-sources

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
	find . -type f -regex ".*\.mo$$" -delete

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

virtualenv: virtualenv_ansible virtualenv_awx

# virtualenv_* targets do not use --system-site-packages to prevent bugs installing packages
# but Ansible venvs are expected to have this, so that must be done after venv creation
virtualenv_ansible:
	if [ "$(VENV_BASE)" ]; then \
		if [ ! -d "$(VENV_BASE)" ]; then \
			mkdir $(VENV_BASE); \
		fi; \
		if [ ! -d "$(VENV_BASE)/ansible" ]; then \
			virtualenv -p python $(VENV_BASE)/ansible && \
			$(VENV_BASE)/ansible/bin/pip install $(PIP_OPTIONS) $(VENV_BOOTSTRAP); \
		fi; \
	fi

virtualenv_ansible_py3:
	if [ "$(VENV_BASE)" ]; then \
		if [ ! -d "$(VENV_BASE)" ]; then \
			mkdir $(VENV_BASE); \
		fi; \
		if [ ! -d "$(VENV_BASE)/ansible" ]; then \
			virtualenv -p $(PYTHON) $(VENV_BASE)/ansible; \
			$(VENV_BASE)/ansible/bin/pip install $(PIP_OPTIONS) $(VENV_BOOTSTRAP); \
		fi; \
	fi

# flit is needed for offline install of certain packages, specifically ptyprocess
# it is needed for setup, but not always recognized as a setup dependency
# similar to pip, setuptools, and wheel, these are all needed here as a bootstrapping issues
virtualenv_awx:
	if [ "$(VENV_BASE)" ]; then \
		if [ ! -d "$(VENV_BASE)" ]; then \
			mkdir $(VENV_BASE); \
		fi; \
		if [ ! -d "$(VENV_BASE)/awx" ]; then \
			virtualenv -p $(PYTHON) $(VENV_BASE)/awx; \
			$(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) $(VENV_BOOTSTRAP); \
		fi; \
	fi

# --ignore-install flag is not used because *.txt files should specify exact versions
requirements_ansible: virtualenv_ansible
	if [[ "$(PIP_OPTIONS)" == *"--no-index"* ]]; then \
	    cat requirements/requirements_ansible.txt requirements/requirements_ansible_local.txt | PYCURL_SSL_LIBRARY=$(PYCURL_SSL_LIBRARY) $(VENV_BASE)/ansible/bin/pip install $(PIP_OPTIONS) -r /dev/stdin ; \
	else \
	    cat requirements/requirements_ansible.txt requirements/requirements_ansible_git.txt | PYCURL_SSL_LIBRARY=$(PYCURL_SSL_LIBRARY) $(VENV_BASE)/ansible/bin/pip install $(PIP_OPTIONS) --no-binary $(SRC_ONLY_PKGS) -r /dev/stdin ; \
	fi
	$(VENV_BASE)/ansible/bin/pip uninstall --yes -r requirements/requirements_ansible_uninstall.txt
	# Same effect as using --system-site-packages flag on venv creation
	rm $(shell ls -d $(VENV_BASE)/ansible/lib/python* | head -n 1)/no-global-site-packages.txt

requirements_ansible_py3: virtualenv_ansible_py3
	if [[ "$(PIP_OPTIONS)" == *"--no-index"* ]]; then \
	    cat requirements/requirements_ansible.txt requirements/requirements_ansible_local.txt | PYCURL_SSL_LIBRARY=$(PYCURL_SSL_LIBRARY) $(VENV_BASE)/ansible/bin/pip3 install $(PIP_OPTIONS) -r /dev/stdin ; \
	else \
	    cat requirements/requirements_ansible.txt requirements/requirements_ansible_git.txt | PYCURL_SSL_LIBRARY=$(PYCURL_SSL_LIBRARY) $(VENV_BASE)/ansible/bin/pip3 install $(PIP_OPTIONS) --no-binary $(SRC_ONLY_PKGS) -r /dev/stdin ; \
	fi
	$(VENV_BASE)/ansible/bin/pip3 uninstall --yes -r requirements/requirements_ansible_uninstall.txt
	# Same effect as using --system-site-packages flag on venv creation
	rm $(shell ls -d $(VENV_BASE)/ansible/lib/python* | head -n 1)/no-global-site-packages.txt

requirements_ansible_dev:
	if [ "$(VENV_BASE)" ]; then \
		$(VENV_BASE)/ansible/bin/pip install pytest mock; \
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

requirements_collections:
	mkdir -p $(COLLECTION_BASE)
	n=0; \
	until [ "$$n" -ge 5 ]; do \
	    ansible-galaxy collection install -r requirements/collections_requirements.yml -p $(COLLECTION_BASE) && break; \
	    n=$$((n+1)); \
	done

requirements: requirements_ansible requirements_awx requirements_collections

requirements_dev: requirements_awx requirements_ansible_py3 requirements_awx_dev requirements_ansible_dev

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
	python -c "import awx; print(awx.__version__)" > /var/lib/awx/.awx_version; \

# Do any one-time init tasks.
comma := ,
init:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(MANAGEMENT_COMMAND) provision_instance --hostname=$(COMPOSE_HOST); \
	$(MANAGEMENT_COMMAND) register_queue --queuename=tower --instance_percent=100;\
	if [ "$(AWX_GROUP_QUEUES)" == "tower,thepentagon" ]; then \
		$(MANAGEMENT_COMMAND) provision_instance --hostname=isolated; \
		$(MANAGEMENT_COMMAND) register_queue --queuename='thepentagon' --hostnames=isolated --controller=tower; \
		$(MANAGEMENT_COMMAND) generate_isolated_key > /awx_devel/awx/main/isolated/authorized_keys; \
	fi;

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

pep8: reports
	@(set -o pipefail && $@ | tee reports/$@.report)

flake8: reports
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	(set -o pipefail && $@ | tee reports/$@.report)

pyflakes: reports
	@(set -o pipefail && $@ | tee reports/$@.report)

pylint: reports
	@(set -o pipefail && $@ | reports/$@.report)

genschema: reports
	$(MAKE) swagger PYTEST_ARGS="--genschema --create-db "
	mv swagger.json schema.json

swagger: reports
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	(set -o pipefail && py.test $(PYTEST_ARGS) awx/conf/tests/functional awx/main/tests/functional/api awx/main/tests/docs --release=$(VERSION_TARGET) | tee reports/$@.report)

check: flake8 pep8 # pyflakes pylint

awx-link:
	[ -d "/awx_devel/awx.egg-info" ] || python3 /awx_devel/setup.py egg_info_dev
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
	pip install ansible && \
	py.test $(COLLECTION_TEST_DIRS) -v
	# The python path needs to be modified so that the tests can find Ansible within the container
	# First we will use anything expility set as PYTHONPATH
	# Second we will load any libraries out of the virtualenv (if it's unspecified that should be ok because python should not load out of an empty directory)
	# Finally we will add the system path so that the tests can find the ansible libraries

flake8_collection:
	flake8 awx_collection/  # Different settings, in main exclude list

test_collection_all: test_collection flake8_collection

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

# l10n TASKS
# --------------------------------------

# check for UI po files
HAVE_PO := $(shell ls awx/ui/po/*.po 2>/dev/null)
check-po:
ifdef HAVE_PO
	# Should be 'Language: zh-CN' but not 'Language: zh_CN' in zh_CN.po
	for po in awx/ui/po/*.po ; do \
	    echo $$po; \
	    mo="awx/ui/po/`basename $$po .po`.mo"; \
	    msgfmt --check --verbose $$po -o $$mo; \
	    if test "$$?" -ne 0 ; then \
	        exit -1; \
	    fi; \
	    rm $$mo; \
	    name=`echo "$$po" | grep '-'`; \
	    if test "x$$name" != x ; then \
	        right_name=`echo $$language | sed -e 's/-/_/'`; \
	        echo "ERROR: WRONG $$name CORRECTION: $$right_name"; \
	        exit -1; \
	    fi; \
	    language=`grep '^"Language:' "$$po" | grep '_'`; \
	    if test "x$$language" != x ; then \
	        right_language=`echo $$language | sed -e 's/_/-/'`; \
	        echo "ERROR: WRONG $$language CORRECTION: $$right_language in $$po"; \
	        exit -1; \
	    fi; \
	done;
else
	@echo No PO files
endif


# UI TASKS
# --------------------------------------

UI_BUILD_FLAG_FILE = awx/ui_next/.ui-built

clean-ui:
	rm -rf node_modules
	rm -rf awx/ui_next/node_modules
	rm -rf awx/ui_next/build
	rm -rf awx/ui_next/src/locales/_build
	rm -rf $(UI_BUILD_FLAG_FILE)
	git checkout awx/ui_next/src/locales

awx/ui_next/node_modules:
	$(NPM_BIN) --prefix awx/ui_next --loglevel warn --ignore-scripts install

$(UI_BUILD_FLAG_FILE):
	$(NPM_BIN) --prefix awx/ui_next --loglevel warn run extract-strings
	$(NPM_BIN) --prefix awx/ui_next --loglevel warn run compile-strings
	$(NPM_BIN) --prefix awx/ui_next --loglevel warn run build
	git checkout awx/ui_next/src/locales
	mkdir -p awx/public/static/css
	mkdir -p awx/public/static/js
	mkdir -p awx/public/static/media
	cp -r awx/ui_next/build/static/css/* awx/public/static/css
	cp -r awx/ui_next/build/static/js/* awx/public/static/js
	cp -r awx/ui_next/build/static/media/* awx/public/static/media
	touch $@

ui-release: awx/ui_next/node_modules $(UI_BUILD_FLAG_FILE)

ui-devel: awx/ui_next/node_modules
	@$(MAKE) -B $(UI_BUILD_FLAG_FILE)

ui-devel-instrumented: awx/ui_next/node_modules
	$(NPM_BIN) --prefix awx/ui_next --loglevel warn run start-instrumented

ui-devel-test: awx/ui_next/node_modules
	$(NPM_BIN) --prefix awx/ui_next --loglevel warn run start

ui-zuul-lint-and-test:
	$(NPM_BIN) --prefix awx/ui_next install
	$(NPM_BIN) run --prefix awx/ui_next lint
	$(NPM_BIN) run --prefix awx/ui_next prettier-check
	$(NPM_BIN) run --prefix awx/ui_next test -- --coverage --watchAll=false


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

docker-compose-sources:
	ansible-playbook -i tools/docker-compose/inventory tools/docker-compose/ansible/sources.yml \
	    -e awx_image=$(DEV_DOCKER_TAG_BASE)/awx_devel \
	    -e awx_image_tag=$(COMPOSE_TAG)

docker-compose: docker-auth awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml $(COMPOSE_UP_OPTS) up --no-recreate awx

docker-compose-cluster: docker-auth awx/projects
	docker-compose -f tools/docker-compose-cluster.yml up

docker-compose-credential-plugins: docker-auth awx/projects docker-compose-sources
	echo -e "\033[0;31mTo generate a CyberArk Conjur API key: docker exec -it tools_conjur_1 conjurctl account create quick-start\033[0m"
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml -f tools/docker-credential-plugins-override.yml up --no-recreate awx

docker-compose-test: docker-auth awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports awx /bin/bash

docker-compose-runtest: awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports awx /start_tests.sh

docker-compose-build-swagger: awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml run --rm --service-ports --no-deps awx /start_tests.sh swagger

detect-schema-change: genschema
	curl https://s3.amazonaws.com/awx-public-ci-files/schema.json -o reference-schema.json
	# Ignore differences in whitespace with -b
	diff -u -b reference-schema.json schema.json

docker-compose-clean: awx/projects
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml rm -sf

# Base development image build
docker-compose-build:
	ansible-playbook tools/ansible/dockerfile.yml -e build_dev=True
	DOCKER_BUILDKIT=1 docker build -t $(DEVEL_IMAGE_NAME) \
	    --build-arg BUILDKIT_INLINE_CACHE=1 \
	    --cache-from=$(DEV_DOCKER_TAG_BASE)/awx_devel:$(COMPOSE_TAG) .

docker-clean:
	$(foreach container_id,$(shell docker ps -f name=tools_awx -aq),docker stop $(container_id); docker rm -f $(container_id);)
	docker images | grep "awx_devel" | awk '{print $$1 ":" $$2}' | xargs docker rmi

docker-clean-volumes: docker-compose-clean
	docker volume rm tools_awx_db

docker-refresh: docker-clean docker-compose

# Docker Development Environment with Elastic Stack Connected
docker-compose-elk: docker-auth awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml -f tools/elastic/docker-compose.logstash-link.yml -f tools/elastic/docker-compose.elastic-override.yml up --no-recreate

docker-compose-cluster-elk: docker-auth awx/projects docker-compose-sources
	docker-compose -f tools/docker-compose/_sources/docker-compose.yml -f tools/elastic/docker-compose.logstash-link-cluster.yml -f tools/elastic/docker-compose.elastic-override.yml up --no-recreate

prometheus:
	docker run -u0 --net=tools_default --link=`docker ps | egrep -o "tools_awx(_run)?_([^ ]+)?"`:awxweb --volume `pwd`/tools/prometheus:/prometheus --name prometheus -d -p 0.0.0.0:9090:9090 prom/prometheus --web.enable-lifecycle --config.file=/prometheus/prometheus.yml

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

# TODO: test kube-dev target after changing dockerfile.yml location - refer to https://github.com/ansible/awx/commit/7c8bd471980d26083d4c4e11067bb53730175496
Dockerfile.kube-dev: tools/ansible/roles/dockerfile/templates/Dockerfile.j2
	ansible-playbook tools/ansible/dockerfile.yml \
	    -e dockerfile_name=Dockerfile.kube-dev \
	    -e kube_dev=True \
	    -e template_dest=_build_kube_dev

awx-kube-dev-build: Dockerfile.kube-dev
	docker build -f Dockerfile.kube-dev \
	    --build-arg BUILDKIT_INLINE_CACHE=1 \
	    -t $(DEV_DOCKER_TAG_BASE)/awx_kube_devel:$(COMPOSE_TAG) .
