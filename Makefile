PYTHON = python
PYTHON_VERSION = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_version; print get_python_version()")
SITELIB=$(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
OFFICIAL ?= no
PACKER ?= packer
PACKER_BUILD_OPTS ?= -var 'official=$(OFFICIAL)' -var 'aw_repo_url=$(AW_REPO_URL)'
GRUNT ?= $(shell [ -t 0 ] && echo "grunt" || echo "grunt --no-color")
NODE ?= node
NPM_BIN ?= npm
DEPS_SCRIPT ?= packaging/bundle/deps.py
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)

GCLOUD_AUTH ?= $(shell gcloud auth print-access-token)
COMPOSE_TAG ?= devel
# NOTE: This defaults the container image version to the branch that's active
# COMPOSE_TAG ?= $(GIT_BRANCH)

COMPOSE_HOST ?= $(shell hostname)

VENV_BASE ?= /venv
SCL_PREFIX ?=
CELERY_SCHEDULE_FILE ?= /celerybeat-schedule

# Python packages to install only from source (not from binary wheels)
# Comma separated list
SRC_ONLY_PKGS ?= cffi,pycparser

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

NAME = ansible-tower
VERSION = $(shell $(PYTHON) -c "from awx import __version__; print(__version__.split('-')[0])")
GIT_REMOTE_URL = $(shell git config --get remote.origin.url)
BUILD = 0.git$(DATE)
ifeq ($(OFFICIAL),yes)
    RELEASE ?= 1
    AW_REPO_URL ?= http://releases.ansible.com/ansible-tower
else
    RELEASE ?= $(BUILD)
    AW_REPO_URL ?= http://jenkins.testing.ansible.com/ansible-tower_nightlies_RTYUIOPOIUYTYU/$(GIT_BRANCH)
endif

# Allow AMI license customization
AWS_INSTANCE_COUNT ?= 0

# GPG signature parameters (BETA key not yet used)
GPG_BIN ?= gpg
GPG_RELEASE = 442667A9
GPG_RELEASE_FILE = GPG-KEY-ansible-release
GPG_BETA = D7B00447
GPG_BETA_FILE = GPG-KEY-ansible-beta

# Determine GPG key for package signing
ifeq ($(OFFICIAL),yes)
    GPG_KEY = $(GPG_RELEASE)
    GPG_FILE = $(GPG_RELEASE_FILE)
endif

# TAR build parameters
ifeq ($(OFFICIAL),yes)
    SETUP_TAR_NAME=$(NAME)-setup-$(VERSION)
    SDIST_TAR_NAME=$(NAME)-$(VERSION)
else
    SETUP_TAR_NAME=$(NAME)-setup-$(VERSION)-$(RELEASE)
    SDIST_TAR_NAME=$(NAME)-$(VERSION)-$(RELEASE)
endif
SDIST_TAR_FILE=$(SDIST_TAR_NAME).tar.gz
SETUP_TAR_FILE=$(SETUP_TAR_NAME).tar.gz
SETUP_TAR_LINK=$(NAME)-setup-latest.tar.gz
SETUP_TAR_CHECKSUM=$(NAME)-setup-CHECKSUM

# DEB build parameters
DEBUILD_BIN ?= debuild
DEBUILD_OPTS =
DPUT_BIN ?= dput
DPUT_OPTS ?= -c .dput.cf -u
REPREPRO_BIN ?= reprepro
REPREPRO_OPTS ?= -b reprepro --export=changed
DEB_DIST ?=
ifeq ($(OFFICIAL),yes)
    # Sign official builds
    DEBUILD_OPTS += -k$(GPG_KEY)
    REPREPRO_OPTS += --ask-passphrase
else
    # Do not sign development builds
    DEBUILD_OPTS += -uc -us
endif
DEBUILD = $(DEBUILD_BIN) $(DEBUILD_OPTS)
DEB_PPA ?= mini_dinstall
DEB_ARCH ?= amd64
DEB_NVR = $(NAME)_$(VERSION)-$(RELEASE)~$(DEB_DIST)
DEB_NVRA = $(DEB_NVR)_$(DEB_ARCH)
DEB_NVRS = $(DEB_NVR)_source
DEB_TAR_NAME=$(NAME)-$(VERSION)
DEB_TAR_FILE=$(NAME)_$(VERSION).orig.tar.gz

# pbuilder parameters
PBUILDER_CACHE_DIR = /var/cache/pbuilder
PBUILDER_BIN ?= pbuilder
PBUILDER_OPTS ?= --debootstrapopts --variant=buildd --distribution $(DEB_DIST) --architecture $(DEB_ARCH) --basetgz $(PBUILDER_CACHE_DIR)/$(DEB_DIST)-$(DEB_ARCH)-base.tgz --buildresult $(PWD)/deb-build

# RPM build parameters
MOCK_BIN ?= mock
MOCK_CFG ?=
RPM_SPECDIR= packaging/rpm
RPM_SPEC = $(RPM_SPECDIR)/$(NAME).spec
RPM_DIST ?= $(shell rpm --eval '%{?dist}' 2>/dev/null)

# Provide a fallback value for RPM_DIST
ifeq ($(RPM_DIST),)
    RPM_DIST = .el6
endif
RPM_ARCH ?= $(shell rpm --eval '%{_arch}' 2>/dev/null)
# Provide a fallback value for RPM_ARCH
ifeq ($(RPM_ARCH),)
    RPM_ARCH = $(shell uname -m)
endif

# Software collections settings if on EL6
ifeq ($(RPM_DIST),.el6)
    SCL_PREFIX = python27-
    SCL_DEFINES = --define 'scl python27'
else
    SCL_PREFIX =
    SCL_DEFINES =
endif

RPM_NVR = $(SCL_PREFIX)$(NAME)-$(VERSION)-$(RELEASE)$(RPM_DIST)

# TAR Bundle build parameters
DIST = $(shell echo $(RPM_DIST) | sed -e 's|^\.\(el\)\([0-9]\).*|\1|')
DIST_MAJOR = $(shell echo $(RPM_DIST) | sed -e 's|^\.\(el\)\([0-9]\).*|\2|')
DIST_FULL = $(DIST)$(DIST_MAJOR)
OFFLINE_TAR_NAME = $(NAME)-setup-bundle-$(VERSION)-$(RELEASE).$(DIST_FULL)
OFFLINE_TAR_FILE = $(OFFLINE_TAR_NAME).tar.gz
OFFLINE_TAR_LINK = $(NAME)-setup-bundle-latest.$(DIST_FULL).tar.gz
OFFLINE_TAR_CHECKSUM=$(NAME)-setup-bundle-CHECKSUM

# Detect underlying OS distribution
DISTRO ?=
ifneq (,$(wildcard /etc/lsb-release))
    DISTRO = $(shell . /etc/lsb-release && echo $${DISTRIB_ID} | tr '[:upper:]' '[:lower:]')
endif
ifneq (,$(wildcard /etc/os-release))
    DISTRO = $(shell . /etc/os-release && echo $${ID})
endif
ifneq (,$(wildcard /etc/fedora-release))
    DISTRO = fedora
endif
ifneq (,$(wildcard /etc/centos-release))
    DISTRO = centos
endif
ifneq (,$(wildcard /etc/redhat-release))
    DISTRO = redhat
endif

# Adjust `setup.py install` parameters based on OS distribution
SETUP_INSTALL_ARGS = --skip-build --no-compile --root=$(DESTDIR) -v
ifeq ($(DISTRO),ubuntu)
    SETUP_INSTALL_ARGS += --install-layout=deb
endif

# UI flag files
UI_DEPS_FLAG_FILE = awx/ui/.deps_built
UI_RELEASE_FLAG_FILE = awx/ui/.release_built

.DEFAULT_GOAL := build

.PHONY: clean clean-tmp clean-venv rebase push requirements requirements_dev \
	requirements_jenkins \
	develop refresh adduser migrate dbchange dbshell runserver celeryd \
	receiver test test_unit test_coverage coverage_html test_jenkins dev_build \
	release_build release_clean sdist rpmtar mock-rpm mock-srpm rpm-sign \
	deb deb-src debian debsign pbuilder reprepro setup_tarball \
	virtualbox-ovf virtualbox-centos-7 virtualbox-centos-6 \
	clean-bundle setup_bundle_tarball \
	ui-docker-machine ui-docker ui-release ui-devel \
	ui-test ui-deps ui-test-ci ui-test-saucelabs jlaska


# Remove setup build files
clean-tar:
	rm -rf tar-build

# Remove rpm build files
clean-rpm:
	rm -rf rpm-build

# Remove debian build files
clean-deb:
	rm -rf deb-build reprepro

# Remove packer artifacts
clean-packer:
	rm -rf packer_cache
	rm -rf packaging/packer/packer_cache
	rm -rf packaging/packer/output-virtualbox-iso/
	rm -rf packaging/packer/output-vmware-iso
	rm -f packaging/packer/ansible-tower-*.box
	rm -rf packaging/packer/ansible-tower*-ova
	rm -rf packaging/packer/ansible-tower*-vmx
	rm -f Vagrantfile

clean-bundle:
	rm -rf setup-bundle-build

# remove ui build artifacts
clean-ui:
	rm -rf awx/ui/static/
	rm -rf awx/ui/node_modules/
	rm -f $(UI_DEPS_FLAG_FILE)
	rm -f $(UI_RELEASE_FLAG_FILE)

clean-tmp:
	rm -rf tmp/

clean-venv:
	rm -rf venv/

# Remove temporary build files, compiled Python files.
clean: clean-rpm clean-deb clean-ui clean-tar clean-packer clean-bundle
	rm -rf awx/public
	rm -rf awx/lib/site-packages
	rm -rf dist/*
	rm -rf tmp
	mkdir tmp
	rm -rf build $(NAME)-$(VERSION) *.egg-info
	find . -type f -regex ".*\.py[co]$$" -delete

# convenience target to assert environment variables are defined
guard-%:
	@if [ "$${$*}" = "" ]; then \
	    echo "The required environment variable '$*' is not set"; \
	    exit 1; \
	fi

# Fetch from origin, rebase local commits on top of origin commits.
rebase:
	git pull --rebase origin master

# Push changes to origin.
push:
	git push origin master

virtualenv: virtualenv_ansible virtualenv_tower

virtualenv_ansible:
	if [ "$(VENV_BASE)" ]; then \
		if [ ! -d "$(VENV_BASE)" ]; then \
			mkdir $(VENV_BASE); \
		fi; \
		if [ ! -d "$(VENV_BASE)/ansible" ]; then \
			virtualenv --system-site-packages --setuptools $(VENV_BASE)/ansible && \
			$(VENV_BASE)/ansible/bin/pip install -I setuptools==23.0.0 && \
			$(VENV_BASE)/ansible/bin/pip install -I pip==8.1.2; \
		fi; \
	fi

virtualenv_tower:
	if [ "$(VENV_BASE)" ]; then \
		if [ ! -d "$(VENV_BASE)" ]; then \
			mkdir $(VENV_BASE); \
		fi; \
		if [ ! -d "$(VENV_BASE)/tower" ]; then \
			virtualenv --system-site-packages --setuptools $(VENV_BASE)/tower && \
			$(VENV_BASE)/tower/bin/pip install -I setuptools==23.0.0 && \
			$(VENV_BASE)/tower/bin/pip install -I pip==8.1.2; \
		fi; \
	fi

requirements_ansible: virtualenv_ansible
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/ansible/bin/activate; \
		$(VENV_BASE)/ansible/bin/pip install --no-binary $(SRC_ONLY_PKGS) -r requirements/requirements_ansible.txt ;\
	else \
	pip install --no-binary $(SRC_ONLY_PKGS) -r requirements/requirements_ansible.txt ; \
	fi

# Install third-party requirements needed for Tower's environment.
requirements_tower: virtualenv_tower
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
		$(VENV_BASE)/tower/bin/pip install --no-binary $(SRC_ONLY_PKGS) -r requirements/requirements.txt ;\
	else \
	pip install --no-binary $(SRC_ONLY_PKGS) -r requirements/requirements.txt ; \
	fi

requirements_tower_dev:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
		$(VENV_BASE)/tower/bin/pip install -r requirements/requirements_dev.txt; \
	fi

# Install third-party requirements needed for running unittests in jenkins
requirements_jenkins:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate && pip install -Ir requirements/requirements_jenkins.txt; \
	else \
		pip install -Ir requirements/requirements_jenkins.txt; \
	fi

requirements: requirements_ansible requirements_tower

requirements_dev: requirements requirements_tower_dev

requirements_test: requirements requirements_jenkins

# "Install" ansible-tower package in development mode.
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
	python -c "import awx as awx; print awx.__version__" > /var/lib/awx/.tower_version

# Do any one-time init tasks.
init:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	tower-manage register_instance --hostname=$(COMPOSE_HOST); \

# Refresh development environment after pulling new code.
refresh: clean requirements_dev version_file develop migrate

# Create Django superuser.
adduser:
	tower-manage createsuperuser

# Create database tables and apply any new migrations.
migrate:
	if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	tower-manage migrate --noinput --fake-initial

# Run after making changes to the models to create a new migration.
dbchange:
	tower-manage makemigrations

# access database shell, asks for password
dbshell:
	sudo -u postgres psql -d awx-dev

server_noattach:
	tmux new-session -d -s tower 'exec make uwsgi'
	tmux rename-window 'Tower'
	tmux select-window -t tower:0
	tmux split-window -v 'exec make celeryd'
	tmux new-window 'exec make daphne'
	tmux select-window -t tower:1
	tmux rename-window 'WebSockets'
	tmux split-window -h 'exec make runworker'
	tmux new-window 'exec make receiver'
	tmux select-window -t tower:2
	tmux rename-window 'Extra Services'
	tmux split-window -h 'exec make factcacher'

server: server_noattach
	tmux -2 attach-session -t tower

# Use with iterm2's native tmux protocol support
servercc: server_noattach
	tmux -2 -CC attach-session -t tower

# Alternate approach to tmux to run all development tasks specified in
# Procfile.  https://youtu.be/OPMgaibszjk
honcho:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	honcho start

flower:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	$(PYTHON) manage.py celery flower --address=0.0.0.0 --port=5555 --broker=amqp://guest:guest@$(RABBITMQ_HOST):5672//

collectstatic:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	mkdir -p awx/public/static && $(PYTHON) manage.py collectstatic --clear --noinput > /dev/null 2>&1

uwsgi: collectstatic
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
    uwsgi -b 32768 --socket :8050 --module=awx.wsgi:application --home=/venv/tower --chdir=/tower_devel/ --vacuum --processes=5 --harakiri=60 --py-autoreload 1

daphne:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	daphne -b 0.0.0.0 -p 8051 awx.asgi:channel_layer

runworker:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	$(PYTHON) manage.py runworker --only-channels websocket.*

# Run the built-in development webserver (by default on http://localhost:8013).
runserver:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	$(PYTHON) manage.py runserver

# Run to start the background celery worker for development.
celeryd:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	$(PYTHON) manage.py celeryd -l DEBUG -B --autoreload --autoscale=20,3 --schedule=$(CELERY_SCHEDULE_FILE) -Q projects,jobs,default,scheduler,$(COMPOSE_HOST)
	#$(PYTHON) manage.py celery multi show projects jobs default -l DEBUG -Q:projects projects -Q:jobs jobs -Q:default default -c:projects 1 -c:jobs 3 -c:default 3 -Ofair -B --schedule=$(CELERY_SCHEDULE_FILE)

# Run to start the zeromq callback receiver
receiver:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_callback_receiver

socketservice:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_socketio_service

factcacher:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	$(PYTHON) manage.py run_fact_cache_receiver

nginx:
	nginx -g "daemon off;"

reports:
	mkdir -p $@

pep8: reports
	@(set -o pipefail && $@ | tee reports/$@.report)

flake8: reports
	@$@ --output-file=reports/$@.report

pyflakes: reports
	@(set -o pipefail && $@ | tee reports/$@.report)

pylint: reports
	@(set -o pipefail && $@ | reports/$@.report)

check: flake8 pep8 # pyflakes pylint

TEST_DIRS ?= awx/main/tests
# Run all API unit tests.
test:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	py.test $(TEST_DIRS)

test_unit:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	py.test awx/main/tests/unit

# Run all API unit tests with coverage enabled.
test_coverage:
	@if [ "$(VENV_BASE)" ]; then \
		. $(VENV_BASE)/tower/bin/activate; \
	fi; \
	py.test --create-db --cov=awx --cov-report=xml --junitxml=./reports/junit.xml $(TEST_DIRS)

# Output test coverage as HTML (into htmlcov directory).
coverage_html:
	coverage html

# Run API unit tests across multiple Python/Django versions with Tox.
test_tox:
	tox -v

# Run unit tests to produce output for Jenkins.
# Alias existing make target so old versions run against Jekins the same way
test_jenkins : test_coverage

# UI TASKS
# --------------------------------------

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

# generate l10n .json
languages: $(UI_DEPS_FLAG_FILE) check-po
	$(NPM_BIN) --prefix awx/ui run languages

# generate .pot
pot: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run pot

ui-deps: $(UI_DEPS_FLAG_FILE)

$(UI_DEPS_FLAG_FILE): awx/ui/package.json
	$(NPM_BIN) --unsafe-perm --prefix awx/ui install awx/ui
	touch $(UI_DEPS_FLAG_FILE)

ui-docker-machine: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run build-docker-machine

ui-docker: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run build-docker-cid

# Builds UI with development/debug settings enabled. Does not raise browser-sync or filesystem polling.
ui-devel: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run build-devel

ui-release: $(UI_RELEASE_FLAG_FILE)

# todo: include languages target when .po deliverables are added to source control
$(UI_RELEASE_FLAG_FILE): $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run build-release
	touch $(UI_RELEASE_FLAG_FILE)

ui-test: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run test

ui-test-ci: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run test:ci

testjs_ci:
	echo "Update UI unittests later" #ui-test-ci

jshint:
	$(GRUNT) --gruntfile awx/ui/Gruntfile.js jshint #Depends on node 6.x and npm 3.x installed on Jenkins slave

ui-test-saucelabs: $(UI_DEPS_FLAG_FILE)
	$(NPM_BIN) --prefix awx/ui run test:saucelabs

# END UI TASKS
# --------------------------------------

# Build a pip-installable package into dist/ with a timestamped version number.
dev_build:
	$(PYTHON) setup.py dev_build

# Build a pip-installable package into dist/ with the release version number.
release_build:
	$(PYTHON) setup.py release_build

# Build setup tarball
tar-build/$(SETUP_TAR_FILE):
	@mkdir -p tar-build
	@rsync -az --exclude /test setup/ tar-build/$(SETUP_TAR_NAME)
	@rsync -az docs/licenses tar-build/$(SETUP_TAR_NAME)/
	@cd tar-build/$(SETUP_TAR_NAME) && sed -e 's#%NAME%#$(NAME)#;s#%VERSION%#$(VERSION)#;s#%RELEASE%#$(RELEASE)#;' group_vars/all.in > group_vars/all
	@cd tar-build && tar -czf $(SETUP_TAR_FILE) --exclude "*/all.in" $(SETUP_TAR_NAME)/
	@ln -sf $(SETUP_TAR_FILE) tar-build/$(SETUP_TAR_LINK)

tar-build/$(SETUP_TAR_CHECKSUM):
	@if [ "$(OFFICIAL)" != "yes" ] ; then \
	    cd tar-build && $(SHASUM_BIN) $(NAME)*.tar.gz > $(notdir $@) ; \
	else \
	    cd tar-build && $(SHASUM_BIN) $(NAME)*.tar.gz | $(GPG_BIN) --clearsign --batch --passphrase "$(GPG_PASSPHRASE)" -u "$(GPG_KEY)" -o $(notdir $@) - ; \
	fi

setup_tarball: tar-build/$(SETUP_TAR_FILE) tar-build/$(SETUP_TAR_CHECKSUM)
	@echo "#############################################"
	@echo "Artifacts:"
	@echo tar-build/$(SETUP_TAR_FILE)
	@echo tar-build/$(SETUP_TAR_LINK)
	@echo tar-build/$(SETUP_TAR_CHECKSUM)
	@echo "#############################################"

release_clean:
	-(rm *.tar)
	-(rm -rf ($RELEASE))

dist/$(SDIST_TAR_FILE): ui-release
	BUILD="$(BUILD)" $(PYTHON) setup.py sdist

sdist: dist/$(SDIST_TAR_FILE)
	@echo "#############################################"
	@echo "Artifacts:"
	@echo dist/$(SDIST_TAR_FILE)
	@echo "#############################################"

# Build setup bundle tarball
setup-bundle-build:
	mkdir -p $@

# TODO - Somehow share implementation with setup_tarball
setup-bundle-build/$(OFFLINE_TAR_FILE):
	rsync -az --exclude /test setup/ setup-bundle-build/$(OFFLINE_TAR_NAME)
	rsync -az docs/licenses setup-bundle-build/$(OFFLINE_TAR_NAME)/
	cd setup-bundle-build/$(OFFLINE_TAR_NAME) && sed -e 's#%NAME%#$(NAME)#;s#%VERSION%#$(VERSION)#;s#%RELEASE%#$(RELEASE)#;' group_vars/all.in > group_vars/all
	$(PYTHON) $(DEPS_SCRIPT) -d $(DIST) -r $(DIST_MAJOR) -u $(AW_REPO_URL) -s setup-bundle-build/$(OFFLINE_TAR_NAME) -v -v -v
	cd setup-bundle-build && tar -czf $(OFFLINE_TAR_FILE) --exclude "*/all.in" $(OFFLINE_TAR_NAME)/
	ln -sf $(OFFLINE_TAR_FILE) setup-bundle-build/$(OFFLINE_TAR_LINK)

setup-bundle-build/$(OFFLINE_TAR_CHECKSUM):
	@if [ "$(OFFICIAL)" != "yes" ] ; then \
	    cd setup-bundle-build && $(SHASUM_BIN) $(NAME)*.tar.gz > $(notdir $@) ; \
	else \
	    cd setup-bundle-build && $(SHASUM_BIN) $(NAME)*.tar.gz | $(GPG_BIN) --clearsign --batch --passphrase "$(GPG_PASSPHRASE)" -u "$(GPG_KEY)" -o $(notdir $@) - ; \
	fi

setup_bundle_tarball: setup-bundle-build setup-bundle-build/$(OFFLINE_TAR_FILE) setup-bundle-build/$(OFFLINE_TAR_CHECKSUM)
	@echo "#############################################"
	@echo "Offline artifacts:"
	@echo setup-bundle-build/$(OFFLINE_TAR_FILE)
	@echo setup-bundle-build/$(OFFLINE_TAR_LINK)
	@echo setup-bundle-build/$(OFFLINE_TAR_CHECKSUM)
	@echo "#############################################"

rpm-build:
	mkdir -p $@

rpm-build/$(SDIST_TAR_FILE): rpm-build dist/$(SDIST_TAR_FILE)
	cp packaging/rpm/$(NAME).spec rpm-build/
	cp packaging/rpm/$(NAME).te rpm-build/
	cp packaging/rpm/$(NAME).sysconfig rpm-build/
	cp packaging/remove_tower_source.py rpm-build/
	cp packaging/bytecompile.sh rpm-build/
	if [ "$(OFFICIAL)" != "yes" ] ; then \
	  (cd dist/ && tar zxf $(SDIST_TAR_FILE)) ; \
	  (cd dist/ && mv $(NAME)-$(VERSION)-$(BUILD) $(NAME)-$(VERSION)) ; \
	  (cd dist/ && tar czf ../rpm-build/$(SDIST_TAR_FILE) $(NAME)-$(VERSION)) ; \
	  ln -sf $(SDIST_TAR_FILE) rpm-build/$(NAME)-$(VERSION).tar.gz ; \
	else \
	  cp -a dist/$(SDIST_TAR_FILE) rpm-build/ ; \
	fi

rpmtar: sdist rpm-build/$(SDIST_TAR_FILE)

rpm-build/$(RPM_NVR).src.rpm: /etc/mock/$(MOCK_CFG).cfg
	$(MOCK_BIN) -r $(MOCK_CFG) --resultdir rpm-build --buildsrpm --spec rpm-build/$(NAME).spec --sources rpm-build \
	   --define "tower_version $(VERSION)" --define "tower_release $(RELEASE)" $(SCL_DEFINES)

mock-srpm: rpmtar rpm-build/$(RPM_NVR).src.rpm
	@echo "#############################################"
	@echo "Artifacts:"
	@echo rpm-build/$(RPM_NVR).src.rpm
	@echo "#############################################"

rpm-build/$(RPM_NVR).$(RPM_ARCH).rpm: rpm-build/$(RPM_NVR).src.rpm
	$(MOCK_BIN) -r $(MOCK_CFG) --resultdir rpm-build --rebuild rpm-build/$(RPM_NVR).src.rpm \
	   --define "tower_version $(VERSION)" --define "tower_release $(RELEASE)" $(SCL_DEFINES)

mock-rpm: rpmtar rpm-build/$(RPM_NVR).$(RPM_ARCH).rpm
	@echo "#############################################"
	@echo "Artifacts:"
	@echo rpm-build/$(RPM_NVR).$(RPM_ARCH).rpm
	@echo "#############################################"

ifeq ($(OFFICIAL),yes)
rpm-build/$(GPG_FILE): rpm-build
	$(GPG_BIN) --export -a "${GPG_KEY}" > "$@"

rpm-sign: rpm-build/$(GPG_FILE) rpmtar rpm-build/$(RPM_NVR).$(RPM_ARCH).rpm
	rpm --define "_signature gpg" --define "_gpg_name $(GPG_KEY)" --addsign rpm-build/$(RPM_NVR).$(RPM_ARCH).rpm
endif

deb-build:
	mkdir -p $@

deb-build/$(DEB_TAR_NAME): dist/$(SDIST_TAR_FILE)
	mkdir -p $(dir $@)
	@if [ "$(OFFICIAL)" != "yes" ] ; then \
	  tar -C deb-build/ -xvf dist/$(SDIST_TAR_FILE) ; \
	  mv deb-build/$(SDIST_TAR_NAME) deb-build/$(DEB_TAR_NAME) ; \
	  cd deb-build && tar czf $(DEB_TAR_FILE) $(DEB_TAR_NAME) ; \
	else \
	  cp -a dist/$(SDIST_TAR_FILE) deb-build/$(DEB_TAR_FILE) ; \
	fi
	cd deb-build && tar -xf $(DEB_TAR_FILE)
	cp -a packaging/debian deb-build/$(DEB_TAR_NAME)/
	cp packaging/remove_tower_source.py deb-build/$(DEB_TAR_NAME)/debian/
	sed -ie "s#^$(NAME) (\([^)]*\)) \([^;]*\);#$(NAME) ($(VERSION)-$(RELEASE)~$(DEB_DIST)) $(DEB_DIST);#" deb-build/$(DEB_TAR_NAME)/debian/changelog

ifeq ($(OFFICIAL),yes)
debian: deb-build/$(DEB_TAR_NAME) deb-build/$(GPG_FILE)

deb-build/$(GPG_FILE): deb-build
	$(GPG_BIN) --export -a "${GPG_KEY}" > "$@"
else
debian: deb-build/$(DEB_TAR_NAME)
endif

deb-build/$(DEB_NVR).dsc: deb-build/$(DEB_TAR_NAME)
	cd deb-build/$(DEB_TAR_NAME) && \
		cp debian/control.$(DEB_DIST) debian/control && \
		$(DEBUILD) -S

deb-src: deb-build/$(DEB_NVR).dsc
	@echo "#############################################"
	@echo "Artifacts:"
	@echo deb-build/$(DEB_NVR).dsc
	@echo deb-build/$(DEB_NVRS).changes
	@echo "#############################################"

$(PBUILDER_CACHE_DIR)/$(DEB_DIST)-$(DEB_ARCH)-base.tgz:
	$(PBUILDER_BIN) create $(PBUILDER_OPTS)

pbuilder: $(PBUILDER_CACHE_DIR)/$(DEB_DIST)-$(DEB_ARCH)-base.tgz deb-build/$(DEB_NVRA).deb

deb-build/$(DEB_NVRA).deb: deb-build/$(DEB_NVR).dsc $(PBUILDER_CACHE_DIR)/$(DEB_DIST)-$(DEB_ARCH)-base.tgz
	# cd deb-build/$(DEB_TAR_NAME) && $(DEBUILD) -b
	$(PBUILDER_BIN) update $(PBUILDER_OPTS)
	$(PBUILDER_BIN) execute $(PBUILDER_OPTS) --save-after-exec packaging/pbuilder/setup.sh $(DEB_DIST)
	$(PBUILDER_BIN) build $(PBUILDER_OPTS) deb-build/$(DEB_NVR).dsc

deb: guard-DEB_DIST deb-build/$(DEB_NVRA).deb
	@echo "#############################################"
	@echo "Artifacts:"
	@echo deb-build/$(DEB_NVRA).deb
	@echo "#############################################"

deb-upload: deb-build/$(DEB_NVRA).changes
	$(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$(DEB_NVRA).changes

dput: deb-build/$(DEB_NVRA).changes
	$(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$(DEB_NVRA).changes

deb-src-upload: deb-build/$(DEB_NVRS).changes
	$(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$(DEB_NVRS).changes

debsign: deb-build/$(DEB_NVRS).changes debian deb-build/$(DEB_NVR).dsc
	debsign -k$(GPG_KEY) deb-build/$(DEB_NVRS).changes deb-build/$(DEB_NVR).dsc

reprepro/conf:
	mkdir -p $@
	cp -a packaging/reprepro/* $@/
	if [ "$(OFFICIAL)" = "yes" ] ; then \
	    sed -i -e 's|^\(Codename:\)|SignWith: $(GPG_KEY)\n\1|' $@/distributions ; \
	fi

reprepro: deb-build/$(DEB_NVRA).deb reprepro/conf
	$(REPREPRO_BIN) $(REPREPRO_OPTS) clearvanished
	for COMPONENT in non-free $(VERSION); do \
	  $(REPREPRO_BIN) $(REPREPRO_OPTS) -C $$COMPONENT remove $(DEB_DIST) $(NAME) ; \
	  $(REPREPRO_BIN) $(REPREPRO_OPTS) -C $$COMPONENT --keepunreferencedfiles --ignore=brokenold includedeb $(DEB_DIST) deb-build/$(DEB_NVRA).deb ; \
	done


#
# Packer build targets
#

amazon-ebs:
	cd packaging/packer && $(PACKER) build -only $@ $(PACKER_BUILD_OPTS) -var "aws_instance_count=$(AWS_INSTANCE_COUNT)" -var "product_version=$(VERSION)" packer-$(NAME).json

# Vagrant box using virtualbox provider
vagrant-virtualbox: packaging/packer/ansible-tower-$(VERSION)-virtualbox.box

packaging/packer/ansible-tower-$(VERSION)-virtualbox.box: packaging/packer/output-virtualbox-iso/centos-7.ovf
	cd packaging/packer && $(PACKER) build -only virtualbox-ovf $(PACKER_BUILD_OPTS) -var "aws_instance_count=$(AWS_INSTANCE_COUNT)" -var "product_version=$(VERSION)" packer-$(NAME).json

packaging/packer/output-virtualbox-iso/centos-7.ovf:
	cd packaging/packer && $(PACKER) build -only virtualbox-iso packer-centos-7.json

virtualbox-iso: packaging/packer/output-virtualbox-iso/centos-7.ovf

# Vagrant box using VMware provider
vagrant-vmware: packaging/packer/ansible-tower-$(VERSION)-vmware.box

packaging/packer/output-vmware-iso/centos-7.vmx:
	cd packaging/packer && $(PACKER) build -only vmware-iso packer-centos-7.json

packaging/packer/ansible-tower-$(VERSION)-vmware.box: packaging/packer/output-vmware-iso/centos-7.vmx
	cd packaging/packer && $(PACKER) build -only vmware-vmx $(PACKER_BUILD_OPTS) -var "aws_instance_count=$(AWS_INSTANCE_COUNT)" -var "product_version=$(VERSION)" packer-$(NAME).json

# TODO - figure out how to build the front-end and python requirements with
# 'build'
build:
	export SCL_PREFIX
	$(PYTHON) setup.py build

install:
	export SCL_PREFIX HTTPD_SCL_PREFIX
	$(PYTHON) setup.py install $(SETUP_INSTALL_ARGS)

docker-auth:
	docker login -e 1234@5678.com -u oauth2accesstoken -p "$(GCLOUD_AUTH)" https://gcr.io

# Docker Compose Development environment
docker-compose: docker-auth
	TAG=$(COMPOSE_TAG) docker-compose -f tools/docker-compose.yml up --no-recreate tower

docker-compose-cluster: docker-auth
	TAG=$(COMPOSE_TAG) docker-compose -f tools/docker-compose-cluster.yml up

docker-compose-test: docker-auth
	cd tools && TAG=$(COMPOSE_TAG) docker-compose run --rm --service-ports tower /bin/bash

docker-compose-build:
	docker build -t ansible/tower_devel -f tools/docker-compose/Dockerfile .
	docker tag ansible/tower_devel gcr.io/ansible-tower-engineering/tower_devel:$(COMPOSE_TAG)
	#docker push gcr.io/ansible-tower-engineering/tower_devel:$(COMPOSE_TAG)

MACHINE?=default
docker-clean:
	eval $$(docker-machine env $(MACHINE))
	$(foreach container_id,$(shell docker ps -f name=tools_tower -aq),docker stop $(container_id); docker rm -f $(container_id);)
	-docker images | grep "tower_devel" | awk '{print $$1 ":" $$2}' | xargs docker rmi

docker-refresh: docker-clean docker-compose

mongo-debug-ui:
	docker run -it --rm --name mongo-express --link tools_mongo_1:mongo -e ME_CONFIG_OPTIONS_EDITORTHEME=ambiance -e ME_CONFIG_BASICAUTH_USERNAME=admin -e ME_CONFIG_BASICAUTH_PASSWORD=password -p 8081:8081 knickers/mongo-express

mongo-container:
	docker run -it --link tools_mongo_1:mongo --rm mongo sh -c 'exec mongo "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT/system_tracking_dev"'

psql-container:
	docker run -it --link tools_postgres_1:postgres --rm postgres:9.4.1 sh -c 'exec psql -h "$$POSTGRES_PORT_5432_TCP_ADDR" -p "$$POSTGRES_PORT_5432_TCP_PORT" -U postgres'
