PYTHON ?= python
PYTHON_VERSION = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_version; print(get_python_version())")
SITELIB=$(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
OFFICIAL ?= no
PACKER ?= packer
PACKER_BUILD_OPTS ?= -var 'official=$(OFFICIAL)' -var 'aw_repo_url=$(AW_REPO_URL)'
NODE ?= node
NPM_BIN ?= npm
DEPS_SCRIPT ?= packaging/bundle/deps.py
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
MANAGEMENT_COMMAND ?= awx-manage
IMAGE_REPOSITORY_AUTH ?=
IMAGE_REPOSITORY_BASE ?= https://gcr.io

VERSION=$(shell git describe --long)
VERSION3=$(shell git describe --long | sed 's/\-g.*//')
VERSION3DOT=$(shell git describe --long | sed 's/\-g.*//' | sed 's/\-/\./')
RELEASE_VERSION=$(shell git describe --long | sed 's@\([0-9.]\{1,\}\).*@\1@')

# NOTE: This defaults the container image version to the branch that's active
COMPOSE_TAG ?= $(GIT_BRANCH)
COMPOSE_HOST ?= $(shell hostname)

VENV_BASE ?= /venv
SCL_PREFIX ?=
CELERY_SCHEDULE_FILE ?= /celerybeat-schedule

DEV_DOCKER_TAG_BASE ?= gcr.io/ansible-tower-engineering
# Python packages to install only from source (not from binary wheels)
# Comma separated list
SRC_ONLY_PKGS ?= cffi,pycparser,psycopg2,twilio

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

ifeq ($(OFFICIAL),yes)
    VERSION_TARGET ?= $(RELEASE_VERSION)
else
    VERSION_TARGET ?= $(VERSION3DOT)
endif

# TAR build parameters
ifeq ($(OFFICIAL),yes)
    SDIST_TAR_NAME=$(NAME)-$(RELEASE_VERSION)
    WHEEL_NAME=$(NAME)-$(RELEASE_VERSION)
else
    SDIST_TAR_NAME=$(NAME)-$(VERSION3DOT)
    WHEEL_NAME=$(NAME)-$(VERSION3DOT)
endif

SDIST_COMMAND ?= sdist
WHEEL_COMMAND ?= bdist_wheel
SDIST_TAR_FILE ?= $(SDIST_TAR_NAME).tar.gz
WHEEL_FILE ?= $(WHEEL_NAME)-py2-none-any.whl

# UI flag files
UI_DEPS_FLAG_FILE = awx/ui/.deps_built
UI_RELEASE_FLAG_FILE = awx/ui/.release_built

I18N_FLAG_FILE = .i18n_built

.PHONY: clean clean-tmp clean-venv requirements requirements_dev \
	develop refresh adduser migrate dbchange dbshell runserver celeryd \
	receiver test test_unit test_ansible test_coverage coverage_html \
	dev_build release_build release_clean sdist \
	ui-docker-machine ui-docker ui-release ui-devel \
	ui-test ui-deps ui-test-ci VERSION

# remove ui build artifacts
clean-ui:
	rm -rf awx/ui/static/
	rm -rf awx/ui/node_modules/
	rm -rf awx/ui/coverage/
	rm -rf awx/ui/client/languages/
	rm -f $(UI_DEPS_FLAG_FILE)
	rm -f $(UI_RELEASE_FLAG_FILE)

clean-tmp:
	rm -rf tmp/

clean-venv:
	rm -rf venv/

clean-dist:
	rm -rf dist

# Remove temporary build files, compiled Python files.
clean: clean-ui clean-dist
	rm -rf awx/public
	rm -rf awx/lib/site-packages
	rm -rf awx/job_status
	rm -rf awx/job_output
	rm -rf reports
	rm -f awx/awx_test.sqlite3
	rm -rf requirements/vendor
	rm -rf tmp
	rm -rf $(I18N_FLAG_FILE)
	rm -f VERSION
	mkdir tmp
	rm -rf build $(NAME)-$(VERSION) *.egg-info
	find . -type f -regex ".*\.py[co]$$" -delete
	find . -type d -name "__pycache__" -delete

# convenience target to assert environment variables are defined
guard-%:
	@if [ "$${$*}" = "" ]; then \
	    echo "The required environment variable '$*' is not set"; \
	    exit 1; \
	fi

virtualenv: virtualenv_ansible virtualenv_awx

virtualenv_ansible:
	if [ "$(VENV_BASE)" ]; then \
		if [ ! -d "$(VENV_BASE)" ]; then \
			mkdir $(VENV_BASE); \
		fi; \
		if [ ! -d "$(VENV_BASE)/ansible" ]; then \
			virtualenv --system-site-packages $(VENV_BASE)/ansible && \
			$(VENV_BASE)/ansible/bin/pip install $(PIP_OPTIONS) --ignore-installed six packaging appdirs && \
			$(VENV_BASE)/ansible/bin/pip install $(PIP_OPTIONS) --ignore-installed setuptools==36.0.1 && \
			$(VENV_BASE)/ansible/bin/pip install $(PIP_OPTIONS) --ignore-installed pip==9.0.1; \
		fi; \
	fi

virtualenv_awx:
	if [ "$(VENV_BASE)" ]; then \
		if [ ! -d "$(VENV_BASE)" ]; then \
			mkdir $(VENV_BASE); \
		fi; \
		if [ ! -d "$(VENV_BASE)/awx" ]; then \
			virtualenv --system-site-packages $(VENV_BASE)/awx && \
			$(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) --ignore-installed six packaging appdirs && \
			$(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) --ignore-installed setuptools==36.0.1 && \
			$(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) --ignore-installed pip==9.0.1; \
		fi; \
	fi

requirements_ansible: virtualenv_ansible
	if [[ "$(PIP_OPTIONS)" == *"--no-index"* ]]; then \
	    cat requirements/requirements_ansible.txt requirements/requirements_ansible_local.txt | $(VENV_BASE)/ansible/bin/pip install $(PIP_OPTIONS) --ignore-installed -r /dev/stdin ; \
	else \
	    cat requirements/requirements_ansible.txt requirements/requirements_ansible_git.txt | $(VENV_BASE)/ansible/bin/pip install $(PIP_OPTIONS) --no-binary $(SRC_ONLY_PKGS) --ignore-installed -r /dev/stdin ; \
	fi
	$(VENV_BASE)/ansible/bin/pip uninstall --yes -r requirements/requirements_ansible_uninstall.txt

requirements_ansible_dev:
	if [ "$(VENV_BASE)" ]; then \
		$(VENV_BASE)/ansible/bin/pip install pytest mock; \
	fi

requirements_isolated:
	if [ ! -d "$(VENV_BASE)/awx" ]; then \
		virtualenv --system-site-packages $(VENV_BASE)/awx && \
		$(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) --ignore-installed six packaging appdirs && \
		$(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) --ignore-installed setuptools==35.0.2 && \
		$(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) --ignore-installed pip==9.0.1; \
	fi;
	$(VENV_BASE)/awx/bin/pip install -r requirements/requirements_isolated.txt

# Install third-party requirements needed for AWX's environment.
requirements_awx: virtualenv_awx
	if [[ "$(PIP_OPTIONS)" == *"--no-index"* ]]; then \
	    cat requirements/requirements.txt requirements/requirements_local.txt | $(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) --ignore-installed -r /dev/stdin ; \
	else \
	    cat requirements/requirements.txt requirements/requirements_git.txt | $(VENV_BASE)/awx/bin/pip install $(PIP_OPTIONS) --no-binary $(SRC_ONLY_PKGS) --ignore-installed -r /dev/stdin ; \
	fi
	$(VENV_BASE)/awx/bin/pip uninstall --yes -r requirements/requirements_tower_uninstall.txt

requirements_awx_dev:
	$(VENV_BASE)/awx/bin/pip install -r requirements/requirements_dev.txt
	$(VENV_BASE)/awx/bin/pip uninstall --yes -r requirements/requirements_dev_uninstall.txt

requirements: requirements_ansible requirements_awx

requirements_dev: requirements requirements_awx_dev requirements_ansible_dev

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
	mkdir -p /var/lib/awx/
	python -c "import awx as awx; print awx.__version__" > /var/lib/awx/.awx_version

# Do any one-time init tasks.
comma := ,
init:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(MANAGEMENT_COMMAND) provision_instance --hostname=$(COMPOSE_HOST); \
	$(MANAGEMENT_COMMAND) register_queue --queuename=tower --hostnames=$(COMPOSE_HOST);\
	if [ "$(AWX_GROUP_QUEUES)" == "tower,thepentagon" ]; then \
		$(MANAGEMENT_COMMAND) provision_instance --hostname=isolated; \
		$(MANAGEMENT_COMMAND) register_queue --queuename='thepentagon' --hostnames=isolated --controller=tower; \
		$(MANAGEMENT_COMMAND) generate_isolated_key | ssh -o "StrictHostKeyChecking no" root@isolated 'cat > /root/.ssh/authorized_keys'; \
	elif [ "$(AWX_GROUP_QUEUES)" != "tower" ]; then \
		$(MANAGEMENT_COMMAND) register_queue --queuename=$(firstword $(subst $(comma), ,$(AWX_GROUP_QUEUES))) --hostnames=$(COMPOSE_HOST); \
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
	$(MANAGEMENT_COMMAND) migrate --noinput --fake-initial

# Run after making changes to the models to create a new migration.
dbchange:
	$(MANAGEMENT_COMMAND) makemigrations

# access database shell, asks for password
dbshell:
	sudo -u postgres psql -d awx-dev

server_noattach:
	tmux new-session -d -s awx 'exec make uwsgi'
	tmux rename-window 'AWX'
	tmux select-window -t awx:0
	tmux split-window -v 'exec make celeryd'
	tmux new-window 'exec make daphne'
	tmux select-window -t awx:1
	tmux rename-window 'WebSockets'
	tmux split-window -h 'exec make runworker'
	tmux split-window -v 'exec make nginx'
	tmux new-window 'exec make receiver'
	tmux select-window -t awx:2
	tmux rename-window 'Extra Services'
	tmux select-window -t awx:0

server: server_noattach
	tmux -2 attach-session -t awx

# Use with iterm2's native tmux protocol support
servercc: server_noattach
	tmux -2 -CC attach-session -t awx

supervisor:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	supervisord --configuration /supervisor.conf --pidfile=/tmp/supervisor_pid

# Alternate approach to tmux to run all development tasks specified in
# Procfile.  https://youtu.be/OPMgaibszjk
honcho:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	honcho start -f tools/docker-compose/Procfile

flower:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py celery flower --address=0.0.0.0 --port=5555 --broker=amqp://guest:guest@$(RABBITMQ_HOST):5672//

collectstatic:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	mkdir -p awx/public/static && $(PYTHON) manage.py collectstatic --clear --noinput > /dev/null 2>&1

uwsgi: collectstatic
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
    uwsgi -b 32768 --socket 127.0.0.1:8050 --module=awx.wsgi:application --home=/venv/awx --chdir=/awx_devel/ --vacuum --processes=5 --harakiri=120 --master --no-orphans --py-autoreload 1 --max-requests=1000 --stats /tmp/stats.socket --master-fifo=/awxfifo --lazy-apps --logformat "%(addr) %(method) %(uri) - %(proto) %(status)"

daphne:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	daphne -b 127.0.0.1 -p 8051 awx.asgi:channel_layer

runworker:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py runworker --only-channels websocket.*

# Run the built-in development webserver (by default on http://localhost:8013).
runserver:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py runserver

# Run to start the background celery worker for development.
celeryd:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py celeryd -l DEBUG -B -Ofair --autoreload --autoscale=100,4 --schedule=$(CELERY_SCHEDULE_FILE) -Q tower_scheduler,tower_broadcast_all,$(COMPOSE_HOST),$(AWX_GROUP_QUEUES) -n celery@$(COMPOSE_HOST)
	#$(PYTHON) manage.py celery multi show projects jobs default -l DEBUG -Q:projects projects -Q:jobs jobs -Q:default default -c:projects 1 -c:jobs 3 -c:default 3 -Ofair -B --schedule=$(CELERY_SCHEDULE_FILE)

# Run to start the zeromq callback receiver
receiver:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_callback_receiver

socketservice:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_socketio_service

nginx:
	nginx -g "daemon off;"

rdb:
	$(PYTHON) tools/rdb.py

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

check: flake8 pep8 # pyflakes pylint

TEST_DIRS ?= awx/main/tests/unit awx/main/tests/functional awx/conf/tests awx/sso/tests
# Run all API unit tests.
test: test_ansible
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	py.test $(TEST_DIRS)

test_unit:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	py.test awx/main/tests/unit awx/conf/tests/unit awx/sso/tests/unit

test_ansible:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/ansible/bin/activate; \
	fi; \
	py.test awx/lib/tests -c awx/lib/tests/pytest.ini

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

# generate UI .pot
pot: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run pot

# generate django .pot .po
LANG = "en-us"
messages:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/awx/bin/activate; \
	fi; \
	$(PYTHON) manage.py makemessages -l $(LANG) --keep-pot

# generate l10n .json .mo
languages: $(I18N_FLAG_FILE)

$(I18N_FLAG_FILE): $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run languages
	$(PYTHON) tools/scripts/compilemessages.py
	touch $(I18N_FLAG_FILE)

# End l10n TASKS
# --------------------------------------

# UI TASKS
# --------------------------------------

ui-deps: $(UI_DEPS_FLAG_FILE)

$(UI_DEPS_FLAG_FILE):
	$(NPM_BIN) --unsafe-perm --prefix awx/ui install awx/ui
	touch $(UI_DEPS_FLAG_FILE)

ui-docker-machine: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run ui-docker-machine -- $(MAKEFLAGS)

# Native docker. Builds UI and raises BrowserSync & filesystem polling.
ui-docker: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run ui-docker -- $(MAKEFLAGS)

# Builds UI with development UI without raising browser-sync or filesystem polling.
ui-devel: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run build-devel -- $(MAKEFLAGS)

ui-release: $(UI_RELEASE_FLAG_FILE)

$(UI_RELEASE_FLAG_FILE): $(I18N_FLAG_FILE) $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run build-release
	touch $(UI_RELEASE_FLAG_FILE)

ui-test: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run test

# A standard go-to target for API developers to use building the frontend
ui: clean-ui ui-devel

ui-test-ci: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run test:ci

testjs_ci:
	echo "Update UI unittests later" #ui-test-ci

jshint: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) run --prefix awx/ui jshint

# END UI TASKS
# --------------------------------------

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
	if [ "$(IMAGE_REPOSITORY_AUTH)" ]; then \
		docker login -u oauth2accesstoken -p "$(IMAGE_REPOSITORY_AUTH)" $(IMAGE_REPOSITORY_BASE); \
	fi;

# Docker isolated rampart
docker-isolated:
	TAG=$(COMPOSE_TAG) DEV_DOCKER_TAG_BASE=$(DEV_DOCKER_TAG_BASE) docker-compose -f tools/docker-compose.yml -f tools/docker-isolated-override.yml create
	docker start tools_awx_1
	docker start tools_isolated_1
	if [ "`docker exec -i -t tools_isolated_1 cat /root/.ssh/authorized_keys`" == "`docker exec -t tools_awx_1 cat /root/.ssh/id_rsa.pub`" ]; then \
		echo "SSH keys already copied to isolated instance"; \
	else \
		docker exec "tools_isolated_1" bash -c "mkdir -p /root/.ssh && rm -f /root/.ssh/authorized_keys && echo $$(docker exec -t tools_awx_1 cat /root/.ssh/id_rsa.pub) >> /root/.ssh/authorized_keys"; \
	fi
	TAG=$(COMPOSE_TAG) DEV_DOCKER_TAG_BASE=$(DEV_DOCKER_TAG_BASE) docker-compose -f tools/docker-compose.yml -f tools/docker-isolated-override.yml up

# Docker Compose Development environment
docker-compose: docker-auth
	TAG=$(COMPOSE_TAG) DEV_DOCKER_TAG_BASE=$(DEV_DOCKER_TAG_BASE) docker-compose -f tools/docker-compose.yml up --no-recreate awx

docker-compose-cluster: docker-auth
	TAG=$(COMPOSE_TAG) DEV_DOCKER_TAG_BASE=$(DEV_DOCKER_TAG_BASE) docker-compose -f tools/docker-compose-cluster.yml up

docker-compose-test: docker-auth
	cd tools && TAG=$(COMPOSE_TAG) DEV_DOCKER_TAG_BASE=$(DEV_DOCKER_TAG_BASE) docker-compose run --rm --service-ports awx /bin/bash

docker-compose-build: awx-devel-build

# Base development image build
awx-devel-build:
	docker build -t ansible/awx_devel -f tools/docker-compose/Dockerfile .
	docker tag ansible/awx_devel $(DEV_DOCKER_TAG_BASE)/awx_devel:$(COMPOSE_TAG)
	#docker push $(DEV_DOCKER_TAG_BASE)/awx_devel:$(COMPOSE_TAG)

# For use when developing on "isolated" AWX deployments
awx-isolated-build:
	docker build -t ansible/awx_isolated -f tools/docker-isolated/Dockerfile .
	docker tag ansible/awx_isolated $(DEV_DOCKER_TAG_BASE)/awx_isolated:$(COMPOSE_TAG)
	#docker push $(DEV_DOCKER_TAG_BASE)/awx_isolated:$(COMPOSE_TAG)

MACHINE?=default
docker-clean:
	eval $$(docker-machine env $(MACHINE))
	$(foreach container_id,$(shell docker ps -f name=tools_awx -aq),docker stop $(container_id); docker rm -f $(container_id);)
	-docker images | grep "awx_devel" | awk '{print $$1 ":" $$2}' | xargs docker rmi

docker-refresh: docker-clean docker-compose

# Docker Development Environment with Elastic Stack Connected
docker-compose-elk: docker-auth
	TAG=$(COMPOSE_TAG) DEV_DOCKER_TAG_BASE=$(DEV_DOCKER_TAG_BASE) docker-compose -f tools/docker-compose.yml -f tools/elastic/docker-compose.logstash-link.yml -f tools/elastic/docker-compose.elastic-override.yml up --no-recreate

docker-compose-cluster-elk: docker-auth
	TAG=$(COMPOSE_TAG) DEV_DOCKER_TAG_BASE=$(DEV_DOCKER_TAG_BASE) docker-compose -f tools/docker-compose-cluster.yml -f tools/elastic/docker-compose.logstash-link-cluster.yml -f tools/elastic/docker-compose.elastic-override.yml up --no-recreate

clean-elk:
	docker stop tools_kibana_1
	docker stop tools_logstash_1
	docker stop tools_elasticsearch_1
	docker rm tools_logstash_1
	docker rm tools_elasticsearch_1
	docker rm tools_kibana_1

psql-container:
	docker run -it --net tools_default --rm postgres:9.4.1 sh -c 'exec psql -h "postgres" -p "5432" -U postgres'

VERSION:
	@echo $(VERSION_TARGET) > $@
	@echo "awx: $(VERSION_TARGET)"
