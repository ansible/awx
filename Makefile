PYTHON=python
SITELIB=$(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
OFFICIAL ?= no
PACKER ?= packer
GRUNT ?= $(shell [ -t 0 ] && echo "grunt" || echo "grunt --no-color")
TESTEM ?= ./node_modules/.bin/testem
BROCCOLI_BIN ?= ./node_modules/.bin/broccoli
MOCHA_BIN ?= ./node_modules/.bin/mocha
NODE ?= node

CLIENT_TEST_DIR ?= build_test

# Get the branch information from git
GIT_DATE := $(shell git log -n 1 --format="%ai")
DATE := $(shell date -u +%Y%m%d%H%M)

NAME = ansible-tower
VERSION = $(shell $(PYTHON) -c "from awx import __version__; print(__version__.split('-')[0])")
GIT_REMOTE_URL = $(shell git config --get remote.origin.url)
BUILD = 0.git$(DATE)
ifeq ($(OFFICIAL),yes)
    RELEASE ?= 1
else
    RELEASE ?= $(BUILD)
endif

# Allow AMI license customization
AWS_INSTANCE_COUNT ?= 0

# GPG signature parameters (BETA key not yet used)
GPG_RELEASE = 442667A9
GPG_BETA = D7B00447
GPG_RELEASE_FILE = RPM-GPG-KEY-ansible-release
GPG_BETA_FILE = RPM-GPG-KEY-ansible-beta

# Determine GPG key for RPM signing
ifeq ($(OFFICIAL),yes)
    GPG_KEY = $(GPG_RELEASE)
    GPG_FILE = $(GPG_RELEASE_FILE)
endif

# TAR build parameters
ifeq ($(OFFICIAL),yes)
    SETUP_TAR_NAME=$(NAME)-setup-$(VERSION)
    SDIST_TAR_NAME=$(NAME)-$(VERSION)
    PACKER_BUILD_OPTS=-var-file=vars-release.json
else
    SETUP_TAR_NAME=$(NAME)-setup-$(VERSION)-$(BUILD)
    SDIST_TAR_NAME=$(NAME)-$(VERSION)-$(BUILD)
    PACKER_BUILD_OPTS=-var-file=vars-nightly.json
endif
SDIST_TAR_FILE=$(SDIST_TAR_NAME).tar.gz
SETUP_TAR_FILE=$(SETUP_TAR_NAME).tar.gz
SETUP_TAR_LINK=$(NAME)-setup-latest.tar.gz

# DEB build parameters
DEBUILD_BIN ?= debuild
DEBUILD_OPTS = --source-option="-I"
DPUT_BIN ?= dput
DPUT_OPTS ?=
ifeq ($(OFFICIAL),yes)
    DEB_DIST ?= stable
    # Sign OFFICIAL builds using 'DEBSIGN_KEYID'
    # DEBSIGN_KEYID is required when signing
    ifneq ($(DEBSIGN_KEYID),)
        DEBUILD_OPTS += -k$(DEBSIGN_KEYID)
    endif
else
    DEB_DIST ?= unstable
    # Do not sign development builds
    DEBUILD_OPTS += -uc -us
    DPUT_OPTS += -u
endif
DEBUILD = $(DEBUILD_BIN) $(DEBUILD_OPTS)
DEB_PPA ?= reprepro

# RPM build parameters
RPM_SPECDIR= packaging/rpm
RPM_SPEC = $(RPM_SPECDIR)/$(NAME).spec
RPM_DIST ?= $(shell rpm --eval '%{?dist}' 2>/dev/null)
RPM_NVR = $(NAME)-$(VERSION)-$(RELEASE)$(RPM_DIST)
MOCK_BIN ?= mock
MOCK_CFG ?=

.PHONY: clean rebase push requirements requirements_pypi requirements_jenkins \
	develop refresh adduser syncdb migrate dbchange dbshell runserver celeryd \
	receiver test test_coverage coverage_html ui_analysis_report test_ui test_jenkins dev_build \
	release_build release_clean sdist rpmtar mock-rpm mock-srpm rpm-sign \
	deb deb-src debian reprepro setup_tarball sync_ui node-tests \
	virtualbox-ovf virtualbox-centos-7 virtualbox-centos-6

# Remove setup build files
clean-tar:
	rm -rf tar-build

# Remove rpm build files
clean-rpm:
	rm -rf rpm-build

# Remove debian build files
clean-deb:
	rm -rf deb-build reprepro

# Remove grunt build files
clean-grunt:
	rm -f package.json Gruntfile.js Brocfile.js bower.json
	rm -rf node_modules

# Remove UI build files
clean-ui:
	rm -rf DEBUG
	rm -rf awx/ui/build_test
	rm -rf awx/ui/static/
	rm -rf awx/ui/dist

# Remove packer artifacts
clean-packer:
	rm -rf packer_cache
	rm -rf packaging/packer/packer_cache
	rm -rf packaging/packer/output-virtualbox-iso/
	rm -f packaging/packer/ansible-tower-*.box
	rm -rf packaging/packer/ansible-tower*-ova
	rm -f Vagrantfile

# Remove temporary build files, compiled Python files.
clean: clean-rpm clean-deb clean-grunt clean-ui clean-tar clean-packer
	rm -rf dist/*
	rm -rf build $(NAME)-$(VERSION) *.egg-info
	find . -type f -regex ".*\.py[co]$$" -delete

# Fetch from origin, rebase local commits on top of origin commits.
rebase:
	git pull --rebase origin master

# Push changes to origin.
push:
	git push origin master

# Install third-party requirements needed for development environment (using
# locally downloaded packages).
requirements:
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    (cd requirements && pip install --no-index setuptools-12.0.5.tar.gz); \
	    (cd requirements && pip install --no-index Django-1.6.7.tar.gz); \
	    (cd requirements && pip install --no-index -r dev_local.txt); \
	    $(PYTHON) fix_virtualenv_setuptools.py; \
	else \
	    (cd requirements && sudo pip install --no-index -r dev_local.txt); \
	fi

# Install third-party requirements needed for development environment
# (downloading from PyPI if necessary).
requirements_pypi:
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    pip install setuptools==12.0.5; \
	    pip install Django\>=1.6.7,\<1.7; \
	    pip install -r requirements/dev.txt; \
	    $(PYTHON) fix_virtualenv_setuptools.py; \
	else \
	    sudo pip install -r requirements/dev.txt; \
	fi

# Install third-party requirements needed for running unittests in jenkins
# (using locally downloaded packages).
requirements_jenkins:
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    (cd requirements && pip install --no-index distribute-0.7.3.zip || true); \
	    (cd requirements && pip install --no-index pip-1.5.4.tar.gz || true); \
	else \
	    (cd requirements && sudo pip install --no-index distribute-0.7.3.zip || true); \
	    (cd requirements && sudo pip install --no-index pip-1.5.4.tar.gz || true); \
	fi
	$(MAKE) requirements
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    (cd requirements && pip install -r jenkins.txt); \
	    $(PYTHON) fix_virtualenv_setuptools.py; \
	else \
	    (cd requirements && sudo pip install -r jenkins.txt); \
	fi
	npm install csslint jshint

# "Install" ansible-tower package in development mode.  Creates link to working
# copy in site-packages and installs awx-manage command.
develop:
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    pip uninstall -y awx; \
	    $(PYTHON) setup.py develop; \
	else \
	    sudo pip uninstall -y awx; \
	    sudo $(PYTHON) setup.py develop; \
	fi

# Do any one-time init tasks.
init:
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    awx-manage register_instance --primary --hostname=127.0.0.1; \
	else \
	    sudo awx-manage register_instance --primary --hostname=127.0.0.1; \
	fi

# Refresh development environment after pulling new code.
refresh: clean requirements develop migrate

# Create Django superuser.
adduser:
	$(PYTHON) manage.py createsuperuser

# Create initial database tables (excluding migrations).
syncdb:
	$(PYTHON) manage.py syncdb --noinput

# Create database tables and apply any new migrations.
migrate: syncdb
	$(PYTHON) manage.py migrate --noinput

# Run after making changes to the models to create a new migration.
dbchange:
	$(PYTHON) manage.py schemamigration main v14_changes --auto

# access database shell, asks for password
dbshell:
	sudo -u postgres psql -d awx-dev

server_noattach:
	tmux new-session -d -s tower 'exec make runserver'
	tmux rename-window 'Tower'
	tmux select-window -t tower:0
	tmux split-window -v 'exec make celeryd'
	tmux split-window -h 'exec make taskmanager'
	tmux new-window 'exec make receiver'
	tmux select-window -t tower:1
	tmux rename-window 'Extra Services'
	tmux split-window -v 'exec make socketservice'
	tmux split-window -h 'exec make factcacher'

server: server_noattach
	tmux -2 attach-session -t tower

# Use with iterm2's native tmux protocol support
servercc: server_noattach
	tmux -2 -CC attach-session -t tower

# Run the built-in development webserver (by default on http://localhost:8013).
runserver:
	$(PYTHON) manage.py runserver

# Run to start the background celery worker for development.
celeryd:
	$(PYTHON) manage.py celeryd -l DEBUG -B --autoscale=20,2 -Ofair

# Run to start the zeromq callback receiver
receiver:
	$(PYTHON) manage.py run_callback_receiver

taskmanager:
	$(PYTHON) manage.py run_task_system

socketservice:
	$(PYTHON) manage.py run_socketio_service

factcacher:
	$(PYTHON) manage.py run_fact_cache_receiver

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

# Run all API unit tests.
test:
	$(PYTHON) manage.py test -v2 awx.main.tests

# Run all API unit tests with coverage enabled.
test_coverage:
	coverage run manage.py test -v2 awx.main.tests

# Output test coverage as HTML (into htmlcov directory).
coverage_html:
	coverage html

ui_analysis_report: reports/ui_code node_modules Gruntfile.js
	$(GRUNT) plato:report

reports/ui_code: node_modules clean-ui Brocfile.js bower.json Gruntfile.js
	rm -rf reports/ui_code
	$(BROCCOLI_BIN) build reports/ui_code -- --no-concat --no-debug --no-styles --no-sourcemaps

# Run UI unit tests
test_ui: node_modules minjs_ci
	PATH=./node_modules/.bin:$(PATH) $(TESTEM) ci --file testem.yml -p 7359 -R xunit

# Run API unit tests across multiple Python/Django versions with Tox.
test_tox:
	tox -v

# Run unit tests to produce output for Jenkins.
test_jenkins:
	$(PYTHON) manage.py jenkins -v2 --enable-coverage --project-apps-tests

Gruntfile.js: packaging/node/Gruntfile.js
	cp $< $@

Brocfile.js: packaging/node/Brocfile.js
	cp $< $@

bower.json: packaging/node/bower.json
	cp $< $@

package.json: packaging/node/package.template
	sed -e 's#%NAME%#$(NAME)#;s#%VERSION%#$(VERSION)#;s#%GIT_REMOTE_URL%#$(GIT_REMOTE_URL)#;' $< > $@

sync_ui: node_modules Brocfile.js
	$(NODE) tools/ui/timepiece.js awx/ui/static $(WATCHER_FLAGS) -- $(UI_FLAGS)

# Update local npm install
node_modules: package.json
	npm install
	touch $@
	
awx/ui/%: node_modules clean-ui Brocfile.js bower.json
	$(BROCCOLI_BIN) build $@ -- $(UI_FLAGS)

testjs: UI_FLAGS=--node-tests --no-concat --no-styles $(EXTRA_UI_FLAGS)
testjs: awx/ui/build_test node-tests

node-tests:
	NODE_PATH=awx/ui/build_test $(MOCHA_BIN) --full-trace $(shell find  awx/ui/build_test -name '*-test.js')

devjs: awx/ui/static

# Build minified JS/CSS.
minjs: UI_FLAGS=--silent --compress --no-docs --no-debug --no-sourcemaps $(EXTRA_UI_FLAGS)
minjs: awx/ui/static node_modules clean-ui Brocfile.js

minjs_ci: UI_FLAGS=--compress --no-docs --no-debug --browser-tests $(EXTRA_UI_FLAGS)
minjs_ci: awx/ui/static node_modules clean-ui Brocfile.js

# Check .js files for errors and lint
jshint: node_modules Gruntfile.js
	$(GRUNT) $@

ngdocs: devjs Gruntfile.js
	$(GRUNT) $@

# Build a pip-installable package into dist/ with a timestamped version number.
dev_build:
	$(PYTHON) setup.py dev_build

# Build a pip-installable package into dist/ with the release version number.
release_build:
	$(PYTHON) setup.py release_build

# Build setup tarball
tar-build/$(SETUP_TAR_FILE):
	@mkdir -p tar-build
	@cp -a setup tar-build/$(SETUP_TAR_NAME)
	@cd tar-build/$(SETUP_TAR_NAME) && sed -e 's#%NAME%#$(NAME)#;s#%VERSION%#$(VERSION)#;s#%RELEASE%#$(RELEASE)#;' group_vars/all.in > group_vars/all
	@cd tar-build && tar -czf $(SETUP_TAR_FILE) --exclude "*/all.in" $(SETUP_TAR_NAME)/
	@ln -sf $(SETUP_TAR_FILE) tar-build/$(SETUP_TAR_LINK)
	@echo "#############################################"
	@echo "Setup artifacts:"
	@echo tar-build/$(SETUP_TAR_FILE)
	@echo tar-build/$(SETUP_TAR_LINK)
	@echo "#############################################"

setup_tarball: tar-build/$(SETUP_TAR_FILE)

release_clean:
	-(rm *.tar)
	-(rm -rf ($RELEASE))

dist/$(SDIST_TAR_FILE):
	BUILD="$(BUILD)" $(PYTHON) setup.py sdist

sdist: minjs dist/$(SDIST_TAR_FILE)

rpm-build:
	mkdir -p rpm-build

rpm-build/$(SDIST_TAR_FILE): rpm-build dist/$(SDIST_TAR_FILE)
	cp packaging/rpm/$(NAME).spec rpm-build/
	cp packaging/rpm/$(NAME).te rpm-build/
	cp packaging/rpm/$(NAME).sysconfig rpm-build/
	cp packaging/remove_tower_source.py rpm-build/
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
	   --define "tower_version $(VERSION)" --define "tower_release $(RELEASE)"
	@echo "#############################################"
	@echo "SRPM artifacts:"
	@echo rpm-build/$(RPM_NVR).src.rpm
	@echo "#############################################"

mock-srpm: rpmtar rpm-build/$(RPM_NVR).src.rpm

rpm-build/$(RPM_NVR).noarch.rpm: rpm-build/$(RPM_NVR).src.rpm
	$(MOCK_BIN) -r $(MOCK_CFG) --resultdir rpm-build --rebuild rpm-build/$(RPM_NVR).src.rpm \
	   --define "tower_version $(VERSION)" --define "tower_release $(RELEASE)"
	@echo "#############################################"
	@echo "RPM artifacts:"
	@echo rpm-build/$(RPM_NVR).noarch.rpm
	@echo "#############################################"

mock-rpm: rpmtar rpm-build/$(RPM_NVR).noarch.rpm

ifeq ($(OFFICIAL),yes)
rpm-build/$(GPG_FILE): rpm-build
	gpg --export -a "${GPG_KEY}" > "$@"

rpm-sign: rpm-build/$(GPG_FILE) rpmtar rpm-build/$(RPM_NVR).noarch.rpm
	rpm --define "_signature gpg" --define "_gpg_name $(GPG_KEY)" --addsign rpm-build/$(RPM_NVR).noarch.rpm
endif

deb-build/$(SDIST_TAR_NAME):
	mkdir -p deb-build
	tar -C deb-build/ -xvf dist/$(SDIST_TAR_FILE)
	cp -a packaging/debian deb-build/$(SDIST_TAR_NAME)/
	cp packaging/remove_tower_source.py deb-build/$(SDIST_TAR_NAME)/debian/
	sed -ie "s#^$(NAME) (\([^)]*\)) \([^;]*\);#$(NAME) ($(VERSION)-$(RELEASE)) $(DEB_DIST);#" deb-build/$(SDIST_TAR_NAME)/debian/changelog

debian: sdist deb-build/$(SDIST_TAR_NAME)

deb-build/$(NAME)_$(VERSION)-$(RELEASE)_all.deb:
	cd deb-build/$(SDIST_TAR_NAME) && $(DEBUILD) -b
	@echo "#############################################"
	@echo "DEB artifacts:"
	@echo deb-build/$(NAME)_$(VERSION)-$(RELEASE)_all.deb
	@echo "#############################################"

deb: debian deb-build/$(NAME)_$(VERSION)-$(RELEASE)_all.deb

deb-build/$(NAME)_$(VERSION)-$(RELEASE)_source.changes:
	cd deb-build/$(SDIST_TAR_NAME) && $(DEBUILD) -S
	@echo "#############################################"
	@echo "DEB artifacts:"
	@echo deb-build/$(NAME)_$(VERSION)-$(RELEASE)_source.changes
	@echo "#############################################"

deb-src: debian deb-build/$(NAME)_$(VERSION)-$(RELEASE)_source.changes

deb-upload: deb
	$(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$(NAME)_$(VERSION)-$(RELEASE)_amd64.changes ; \

deb-src-upload: deb-src
	$(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$(NAME)_$(VERSION)-$(RELEASE)_source.changes ; \

reprepro: deb
	mkdir -p reprepro/conf
	cp -a packaging/reprepro/* reprepro/conf/
	@DEB=deb-build/$(NAME)_$(VERSION)-$(RELEASE)_all.deb ; \
	for DIST in trusty precise ; do \
	    echo "Removing '$(NAME)' from the $${DIST} apt repo" ; \
	    echo reprepro --export=force -b reprepro remove $${DIST} $(NAME) ; \
	done; \
	reprepro --export=force -b reprepro clearvanished; \
	for DIST in trusty precise ; do \
	    echo "Adding $${DEB} to the $${DIST} apt repo"; \
	    reprepro --keepunreferencedfiles --export=force -b reprepro --ignore=brokenold includedeb $${DIST} $${DEB} ; \
	done; \

amazon-ebs:
	cd packaging/packer && $(PACKER) build -only $@ $(PACKER_BUILD_OPTS) -var "aws_instance_count=$(AWS_INSTANCE_COUNT)" -var "product_version=$(VERSION)" packer-$(NAME).json

virtualbox-ovf: packaging/packer/ansible-tower-$(VERSION)-virtualbox.box

packaging/packer/ansible-tower-$(VERSION)-virtualbox.box: packaging/packer/output-virtualbox-iso/centos-7.ovf
	cd packaging/packer && $(PACKER) build -only virtualbox-ovf $(PACKER_BUILD_OPTS) -var "aws_instance_count=$(AWS_INSTANCE_COUNT)" -var "product_version=$(VERSION)" packer-$(NAME).json

packaging/packer/output-virtualbox-iso/centos-6.ovf:
	cd packaging/packer && $(PACKER) build packer-centos-6.json

virtualbox-centos-6: packaging/packer/output-virtualbox-iso/centos-6.ovf

packaging/packer/output-virtualbox-iso/centos-7.ovf:
	cd packaging/packer && $(PACKER) build packer-centos-7.json

virtualbox-centos-7: packaging/packer/output-virtualbox-iso/centos-7.ovf

docker-dev:
	docker build --no-cache=true --rm=true -t ansible/tower_devel:latest tools/docker

install:
	$(PYTHON) setup.py install egg_info -b ""
