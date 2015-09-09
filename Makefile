PYTHON=python
SITELIB=$(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
OFFICIAL ?= no
PACKER ?= packer
GRUNT ?= $(shell [ -t 0 ] && echo "grunt" || echo "grunt --no-color")
BROCCOLI ?= ./node_modules/.bin/broccoli
NODE ?= node
DEPS_SCRIPT ?= packaging/bundle/deps.py
AW_REPO_URL ?= "http://releases.ansible.com/ansible-tower"

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
else
    RELEASE ?= $(BUILD)
endif

# Allow AMI license customization
AWS_INSTANCE_COUNT ?= 0

# GPG signature parameters (BETA key not yet used)
GPG_BIN ?= gpg
RPM_GPG_RELEASE = 442667A9
RPM_GPG_RELEASE_FILE = RPM-GPG-KEY-ansible-release
RPM_GPG_BETA = D7B00447
RPM_GPG_BETA_FILE = RPM-GPG-KEY-ansible-beta
DEB_GPG_RELEASE = 3DD29021
DEB_GPG_RELEASE_FILE = DEB-GPG-KEY-ansible-release

# Determine GPG key for package signing
ifeq ($(OFFICIAL),yes)
    TAR_GPG_KEY = $(RPM_GPG_RELEASE)
    RPM_GPG_KEY = $(RPM_GPG_RELEASE)
    RPM_GPG_FILE = $(RPM_GPG_RELEASE_FILE)
    DEB_GPG_KEY = $(DEB_GPG_RELEASE)
    DEB_GPG_FILE = $(DEB_GPG_RELEASE_FILE)
endif

# TAR build parameters
ifeq ($(OFFICIAL),yes)
    SETUP_TAR_NAME=$(NAME)-setup-$(VERSION)
    SDIST_TAR_NAME=$(NAME)-$(VERSION)
    PACKER_BUILD_OPTS=-var-file=vars-release.json
else
    SETUP_TAR_NAME=$(NAME)-setup-$(VERSION)-$(RELEASE)
    SDIST_TAR_NAME=$(NAME)-$(VERSION)-$(RELEASE)
    PACKER_BUILD_OPTS=-var-file=vars-nightly.json
endif
SDIST_TAR_FILE=$(SDIST_TAR_NAME).tar.gz
SETUP_TAR_FILE=$(SETUP_TAR_NAME).tar.gz
SETUP_TAR_LINK=$(NAME)-setup-latest.tar.gz
SETUP_TAR_CHECKSUM=$(NAME)-setup-CHECKSUM

# DEB build parameters
DEBUILD_BIN ?= debuild
DEBUILD_OPTS = --source-option="-I"
DPUT_BIN ?= dput
DPUT_OPTS ?=
ifeq ($(OFFICIAL),yes)
    DEB_DIST ?= stable
    # Sign official builds
    DEBUILD_OPTS += -k$(DEB_GPG_KEY)
else
    DEB_DIST ?= unstable
    # Do not sign development builds
    DEBUILD_OPTS += -uc -us
    DPUT_OPTS += -u
endif
DEBUILD = $(DEBUILD_BIN) $(DEBUILD_OPTS)
DEB_PPA ?= reprepro
DEB_ARCH ?= amd64

# RPM build parameters
MOCK_BIN ?= mock
MOCK_CFG ?=
RPM_SPECDIR= packaging/rpm
RPM_SPEC = $(RPM_SPECDIR)/$(NAME).spec
# Provide a fallback value for RPM_DIST
RPM_DIST ?= $(shell rpm --eval '%{?dist}' 2>/dev/null)
ifeq ($(RPM_DIST),)
RPM_DIST = .el6
endif
RPM_ARCH ?= $(shell rpm --eval '%{_arch}' 2>/dev/null)
ifeq ($(RPM_ARCH),)
RPM_ARCH = $(shell uname -m)
endif
RPM_NVR = $(NAME)-$(VERSION)-$(RELEASE)$(RPM_DIST)

# TAR Bundle build parameters
DIST = $(shell echo $(RPM_DIST) | sed -e 's|^\.\(el\)\([0-9]\).*|\1|')
DIST_MAJOR = $(shell echo $(RPM_DIST) | sed -e 's|^\.\(el\)\([0-9]\).*|\2|')
DIST_FULL = $(DIST)$(DIST_MAJOR)
OFFLINE_TAR_NAME = $(NAME)-setup-bundle-$(VERSION)-$(RELEASE).$(DIST_FULL)
OFFLINE_TAR_FILE = $(OFFLINE_TAR_NAME).tar.gz
OFFLINE_TAR_LINK = $(NAME)-setup-bundle-latest.$(DIST_FULL).tar.gz
OFFLINE_TAR_CHECKSUM=$(NAME)-setup-bundle-CHECKSUM

DISTRO := $(shell . /etc/os-release 2>/dev/null && echo $${ID} || echo redhat)
ifeq ($(DISTRO),ubuntu)
    SETUP_INSTALL_ARGS = --skip-build --no-compile --root=$(DESTDIR) -v --install-layout=deb
else
    SETUP_INSTALL_ARGS = --skip-build --no-compile --root=$(DESTDIR) -v
endif

.DEFAULT_GOAL := build

.PHONY: clean rebase push requirements requirements_dev requirements_jenkins \
	real-requirements real-requirements_dev real-requirements_jenkins \
	develop refresh adduser syncdb migrate dbchange dbshell runserver celeryd \
	receiver test test_coverage coverage_html ui_analysis_report test_ui test_jenkins dev_build \
	release_build release_clean sdist rpmtar mock-rpm mock-srpm rpm-sign \
	devjs minjs testjs testjs_ci node-tests browser-tests jshint ngdocs sync_ui \
	deb deb-src debian reprepro setup_tarball \
	virtualbox-ovf virtualbox-centos-7 virtualbox-centos-6 \
	clean-bundle setup_bundle_tarball

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
	rm -rf awx/ui/static/dist
	rm -rf awx/ui/dist
	rm -rf awx/ui/static/docs

# Remove packer artifacts
clean-packer:
	rm -rf packer_cache
	rm -rf packaging/packer/packer_cache
	rm -rf packaging/packer/output-virtualbox-iso/
	rm -f packaging/packer/ansible-tower-*.box
	rm -rf packaging/packer/ansible-tower*-ova
	rm -f Vagrantfile

clean-bundle:
	rm -rf setup-bundle-build

# Remove temporary build files, compiled Python files.
clean: clean-rpm clean-deb clean-grunt clean-ui clean-tar clean-packer clean-bundle
	rm -rf awx/lib/site-packages
	rm -rf dist/*
	rm -rf build $(NAME)-$(VERSION) *.egg-info
	find . -type f -regex ".*\.py[co]$$" -delete

# Fetch from origin, rebase local commits on top of origin commits.
rebase:
	git pull --rebase origin master

# Push changes to origin.
push:
	git push origin master

# Install runtime, development and jenkins requirements
requirements requirements_dev requirements_jenkins: %: real-%

# Install third-party requirements needed for development environment.
# NOTE:
#  * --target is only supported on newer versions of pip
#  * https://github.com/pypa/pip/issues/3056 - the workaround is to override the `install-platlib`
#  * --user (in conjunction with PYTHONUSERBASE="awx" may be a better option
#  * --target implies --ignore-installed
real-requirements:
	pip install -r requirements/requirements.txt --target awx/lib/site-packages/ --install-option="--install-platlib=\$$base/lib/python"

real-requirements_dev:
	pip install -r requirements/requirements_dev.txt --target awx/lib/site-packages/ --install-option="--install-platlib=\$$base/lib/python"

# Install third-party requirements needed for running unittests in jenkins
real-requirements_jenkins:
	pip install -r requirements/requirements_jenkins.txt
	npm install csslint jshint

# "Install" ansible-tower package in development mode.
develop:
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    pip uninstall -y awx; \
	    $(PYTHON) setup.py develop; \
	else \
	    sudo pip uninstall -y awx; \
	    sudo $(PYTHON) setup.py develop; \
	fi

version_file:
	mkdir -p /var/lib/awx/
	python -c "import awx as awx; print awx.__version__" > /var/lib/awx/.tower_version

# Do any one-time init tasks.
init:
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    awx-manage register_instance --primary --hostname=127.0.0.1; \
	else \
	    sudo awx-manage register_instance --primary --hostname=127.0.0.1; \
	fi

# Refresh development environment after pulling new code.
refresh: clean requirements_dev version_file develop migrate

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
	$(BROCCOLI) build reports/ui_code -- --no-concat --no-tests --no-styles --no-sourcemaps

# Run UI unit tests
test_ui: node_modules minjs_ci Gruntfile.js
	$(GRUNT) karma:ci

# Run API unit tests across multiple Python/Django versions with Tox.
test_tox:
	tox -v

# Run unit tests to produce output for Jenkins.
test_jenkins:
	$(PYTHON) manage.py jenkins -v2 --enable-coverage --project-apps-tests

Gruntfile.js: packaging/grunt/Gruntfile.js
	cp $< $@

Brocfile.js: packaging/grunt/Brocfile.js
	cp $< $@

bower.json: packaging/grunt/bower.json
	cp $< $@

package.json: packaging/grunt/package.template
	sed -e 's#%NAME%#$(NAME)#;s#%VERSION%#$(VERSION)#;s#%GIT_REMOTE_URL%#$(GIT_REMOTE_URL)#;' $< > $@

sync_ui: node_modules Brocfile.js
	$(NODE) tools/ui/timepiece.js awx/ui/dist -- --debug

# Update local npm install
node_modules: package.json
	npm install
	touch $@

devjs: node_modules clean-ui Brocfile.js bower.json Gruntfile.js
	$(BROCCOLI) build awx/ui/dist -- --debug

# Build minified JS/CSS.
minjs: node_modules clean-ui Brocfile.js
	$(BROCCOLI) build awx/ui/dist -- --silent --no-debug --no-tests --compress --no-docs --no-sourcemaps

minjs_ci: node_modules clean-ui Brocfile.js
	$(BROCCOLI) build awx/ui/dist -- --no-debug --compress --no-docs

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

tar-build/$(SETUP_TAR_CHECKSUM):
	@if [ "$(OFFICIAL)" != "yes" ] ; then \
	    cd tar-build && $(SHASUM_BIN) $(NAME)*.tar.gz > $(notdir $@) ; \
	else \
	    cd tar-build && $(SHASUM_BIN) $(NAME)*.tar.gz | $(GPG_BIN) --clearsign -u "$(TAR_GPG_KEY)" -o $(notdir $@) - ; \
	fi

setup_tarball: tar-build/$(SETUP_TAR_FILE) tar-build/$(SETUP_TAR_CHECKSUM)
	@echo "#############################################"
	@echo "Setup artifacts:"
	@echo tar-build/$(SETUP_TAR_FILE)
	@echo tar-build/$(SETUP_TAR_LINK)
	@echo tar-build/$(SETUP_TAR_CHECKSUM)
	@echo "#############################################"

release_clean:
	-(rm *.tar)
	-(rm -rf ($RELEASE))

dist/$(SDIST_TAR_FILE):
	BUILD="$(BUILD)" $(PYTHON) setup.py sdist

sdist: minjs dist/$(SDIST_TAR_FILE)

# Build setup bundle tarball
setup-bundle-build:
	mkdir -p $@

# TODO - Somehow share implementation with setup_tarball
setup-bundle-build/$(OFFLINE_TAR_FILE):
	cp -a setup setup-bundle-build/$(OFFLINE_TAR_NAME)
	cd setup-bundle-build/$(OFFLINE_TAR_NAME) && sed -e 's#%NAME%#$(NAME)#;s#%VERSION%#$(VERSION)#;s#%RELEASE%#$(RELEASE)#;' group_vars/all.in > group_vars/all
	$(PYTHON) $(DEPS_SCRIPT) -d $(DIST) -r $(DIST_MAJOR) -u $(AW_REPO_URL) -s setup-bundle-build/$(OFFLINE_TAR_NAME) -v -v -v
	cd setup-bundle-build && tar -czf $(OFFLINE_TAR_FILE) --exclude "*/all.in" $(OFFLINE_TAR_NAME)/
	ln -sf $(OFFLINE_TAR_FILE) setup-bundle-build/$(OFFLINE_TAR_LINK)

setup-bundle-build/$(OFFLINE_TAR_CHECKSUM):
	@if [ "$(OFFICIAL)" != "yes" ] ; then \
        cd setup-bundle-build && $(SHASUM_BIN) $(NAME)*.tar.gz > $(notdir $@) ; \
	else \
        cd setup-bundle-build && $(SHASUM_BIN) $(NAME)*.tar.gz | $(GPG_BIN) --clearsign -u "$(TAR_GPG_KEY)" -o $(notdir $@) - ; \
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

rpm-build/$(RPM_NVR).$(RPM_ARCH).rpm: rpm-build/$(RPM_NVR).src.rpm
	$(MOCK_BIN) -r $(MOCK_CFG) --resultdir rpm-build --rebuild rpm-build/$(RPM_NVR).src.rpm \
	   --define "tower_version $(VERSION)" --define "tower_release $(RELEASE)"
	@echo "#############################################"
	@echo "RPM artifacts:"
	@echo rpm-build/$(RPM_NVR).$(RPM_ARCH).rpm
	@echo "#############################################"

mock-rpm: rpmtar rpm-build/$(RPM_NVR).$(RPM_ARCH).rpm

ifeq ($(OFFICIAL),yes)
rpm-build/$(RPM_GPG_FILE): rpm-build
	$(GPG_BIN) --export -a "${RPM_GPG_KEY}" > "$@"

rpm-sign: rpm-build/$(RPM_GPG_FILE) rpmtar rpm-build/$(RPM_NVR).$(RPM_ARCH).rpm
	rpm --define "_signature gpg" --define "_gpg_name $(RPM_GPG_KEY)" --addsign rpm-build/$(RPM_NVR).$(RPM_ARCH).rpm
endif

deb-build:
	mkdir -p $@

deb-build/$(SDIST_TAR_NAME):
	mkdir -p deb-build
	tar -C deb-build/ -xvf dist/$(SDIST_TAR_FILE)
	cp -a packaging/debian deb-build/$(SDIST_TAR_NAME)/
	cp packaging/remove_tower_source.py deb-build/$(SDIST_TAR_NAME)/debian/
	sed -ie "s#^$(NAME) (\([^)]*\)) \([^;]*\);#$(NAME) ($(VERSION)-$(RELEASE)) $(DEB_DIST);#" deb-build/$(SDIST_TAR_NAME)/debian/changelog

ifeq ($(OFFICIAL),yes)
debian: sdist deb-build/$(SDIST_TAR_NAME) deb-build/$(DEB_GPG_FILE)

deb-build/$(DEB_GPG_FILE): deb-build
	$(GPG_BIN) --export -a "${DEB_GPG_KEY}" > "$@"
else
debian: sdist deb-build/$(SDIST_TAR_NAME)
endif

deb-build/$(NAME)_$(VERSION)-$(RELEASE)_$(DEB_ARCH).deb:
	cd deb-build/$(SDIST_TAR_NAME) && $(DEBUILD) -b
	@echo "#############################################"
	@echo "DEB artifacts:"
	@echo deb-build/$(NAME)_$(VERSION)-$(RELEASE)_$(DEB_ARCH).deb
	@echo "#############################################"

deb: debian deb-build/$(NAME)_$(VERSION)-$(RELEASE)_$(DEB_ARCH).deb

deb-build/$(NAME)_$(VERSION)-$(RELEASE)_source.changes:
	cd deb-build/$(SDIST_TAR_NAME) && $(DEBUILD) -S
	@echo "#############################################"
	@echo "DEB artifacts:"
	@echo deb-build/$(NAME)_$(VERSION)-$(RELEASE)_source.changes
	@echo "#############################################"

deb-src: debian deb-build/$(NAME)_$(VERSION)-$(RELEASE)_source.changes

deb-upload: deb
	$(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$(NAME)_$(VERSION)-$(RELEASE)_$(DEB_ARCH).changes ; \

deb-src-upload: deb-src
	$(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$(NAME)_$(VERSION)-$(RELEASE)_source.changes ; \

reprepro: deb
	mkdir -p $@/conf
	cp -a packaging/reprepro $@/conf
	if [ "$(OFFICIAL)" = "yes" ] ; then \
        echo "ask-passphrase" >> $@/conf/options; \
        sed -i -e 's|^\(Codename:\)|SignWith: $(DEB_GPG_KEY)\n\1|' $@/conf/distributions ; \
    fi
	@DEB=deb-build/$(NAME)_$(VERSION)-$(RELEASE)_$(DEB_ARCH).deb ; \
	for DIST in trusty precise ; do \
	    echo "Removing '$(NAME)' from the $${DIST} apt repo" ; \
	    echo reprepro --export=force -b $@ remove $${DIST} $(NAME) ; \
	done; \
	reprepro --export=force -b $@ clearvanished; \
	for DIST in trusty precise ; do \
	    echo "Adding $${DEB} to the $${DIST} apt repo"; \
	    reprepro --keepunreferencedfiles --export=force -b $@ --ignore=brokenold includedeb $${DIST} $${DEB} ; \
	done; \

#
# Packer build targets
#

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

# TODO - figure out how to build the front-end and python requirements with
# 'build'
build:
	$(PYTHON) setup.py build

install:
	$(PYTHON) setup.py install $(SETUP_INSTALL_ARGS)
