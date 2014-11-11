PYTHON=python
SITELIB=$(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
OFFICIAL ?= no
PACKER ?= packer
GRUNT ?= $(shell [ -t 0 ] && echo "grunt" || echo "grunt --no-color")

# Get the branch information from git
GIT_DATE := $(shell git log -n 1 --format="%ai")
DATE := $(shell date -u +%Y%m%d%H%M)

NAME = ansible-tower
VERSION = $(shell $(PYTHON) -c "from awx import __version__; print(__version__.split('-')[0])")
RELEASE ?= 1
GIT_REMOTE_URL = $(shell git config --get remote.origin.url)
BUILD ?= 0.git$(DATE)

# Allow AMI license customization
AWS_INSTANCE_COUNT ?= 100

# TAR build parameters
ifneq ($(OFFICIAL),yes)
    SETUP_TAR_NAME=$(NAME)-setup-$(VERSION)-$(BUILD)
    SDIST_TAR_NAME=$(NAME)-$(VERSION)-$(BUILD)
    PACKER_BUILD_OPTS=-var-file=vars-aws-keys.json -var-file=vars-nightly.json
else
    SETUP_TAR_NAME=$(NAME)-setup-$(VERSION)
    SDIST_TAR_NAME=$(NAME)-$(VERSION)
    PACKER_BUILD_OPTS=-var-file=vars-aws-keys.json -var-file=vars-release.json
endif
SDIST_TAR_FILE=$(SDIST_TAR_NAME).tar.gz

# DEB build parameters
DEBUILD_BIN ?= debuild
DEBUILD_OPTS = --source-option="-I"
DPUT_BIN ?= dput
DPUT_OPTS ?=
ifeq ($(OFFICIAL),yes)
    DEB_DIST ?= stable
    DEB_RELEASE = $(RELEASE)
    # Sign OFFICIAL builds using 'DEBSIGN_KEYID'
    # DEBSIGN_KEYID is required when signing
    ifneq ($(DEBSIGN_KEYID),)
        DEBUILD_OPTS += -k$(DEBSIGN_KEYID)
    endif
else
    DEB_DIST ?= unstable
    DEB_RELEASE = $(BUILD)
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
ifeq ($(OFFICIAL),yes)
    RPM_RELEASE = $(RELEASE)
else
    RPM_RELEASE = $(BUILD)
endif
RPM_NVR = $(NAME)-$(VERSION)-$(RPM_RELEASE)$(RPM_DIST)
MOCK_BIN ?= mock
MOCK_CFG ?=

.PHONY: clean rebase push requirements requirements_pypi requirements_jenkins \
	develop refresh adduser syncdb migrate dbchange dbshell runserver celeryd \
	receiver test test_coverage coverage_html test_ui test_jenkins dev_build \
	release_build release_clean sdist rpmtar mock-rpm mock-srpm \
	deb deb-src debian reprepro

# Remove rpm build files
clean-rpm:
	rm -rf rpm-build

# Remove debian build files
clean-deb:
	rm -rf deb-build reprepro

# Remove grunt build files
clean-grunt:
	rm -f package.json Gruntfile.js bower.json
	rm -rf node_modules

# Remove UI build files
clean-ui:
	rm -f awx/ui/static/{js,css}/awx*.{js,css}
	rm -rf awx/ui/static/docs

# Remove temporary build files, compiled Python files.
clean: clean-rpm clean-deb clean-grunt clean-ui
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
	    (cd requirements && pip install --no-index setuptools-2.2.tar.gz); \
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
	    pip install setuptools==2.2; \
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
	    (cd requirements && pip install -U -r jenkins.txt); \
	    $(PYTHON) fix_virtualenv_setuptools.py; \
	else \
	    (cd requirements && sudo pip install -U -r jenkins.txt); \
	fi
	npm install -g csslint jshint

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
	    awx-manage register_instance --primary --ip-address=127.0.0.1; \
	else \
	    sudo awx-manage register_instance --primary --ip-address=127.0.0.1; \
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
	tmux split-window -h 'exec make socketservice'
	tmux select-pane -U
	tmux split-window -v 'exec make receiver'
	tmux split-window -h 'exec make taskmanager'

server: server_noattach
	tmux -2 attach-session -t tower

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

pep8:
	pep8 -r awx/

pyflakes:
	pyflakes awx/

# Run all API unit tests.
test:
	$(PYTHON) manage.py test -v2 awx.main.tests

# Run all API unit tests with coverage enabled.
test_coverage:
	coverage run manage.py test -v2 awx.main.tests

# Output test coverage as HTML (into htmlcov directory).
coverage_html:
	coverage html

# Run UI unit tests using Selenium.
test_ui:
	$(PYTHON) manage.py test -v2 awx.ui.tests

# Run API unit tests across multiple Python/Django versions with Tox.
test_tox:
	tox -v

# Run unit tests to produce output for Jenkins.
test_jenkins:
	$(PYTHON) manage.py jenkins -v2 --enable-coverage --project-apps-tests

Gruntfile.js:
	cp packaging/grunt/$@ $@

bower.json:
	cp packaging/grunt/$@ $@

package.json:
	sed -e 's#%NAME%#$(NAME)#;s#%VERSION%#$(VERSION)#;s#%GIT_REMOTE_URL%#$(GIT_REMOTE_URL)#;' packaging/grunt/package.template > $@

# Update local npm install
node_modules: Gruntfile.js bower.json package.json
	npm install

# Build minified JS/CSS.
minjs: node_modules
	$(GRUNT)

# Check .js files for errors and lint
jshint: node_modules
	$(GRUNT) $@

ngdocs: node_modules
	$(GRUNT) $@

# Build a pip-installable package into dist/ with a timestamped version number.
dev_build:
	$(PYTHON) setup.py dev_build

# Build a pip-installable package into dist/ with the release version number.
release_build:
	$(PYTHON) setup.py release_build

# Build AWX setup tarball.
$(SETUP_TAR_NAME).tar.gz:
	@cp -a setup $(SETUP_TAR_NAME)
	@tar czf $(SETUP_TAR_NAME).tar.gz $(SETUP_TAR_NAME)/
	@rm -rf $(SETUP_TAR_NAME)
	@echo "#############################################"
	@echo "Setup artifacts:"
	@echo $(SETUP_TAR_NAME).tar.gz
	@echo "#############################################"

setup_tarball: $(SETUP_TAR_NAME).tar.gz

release_clean:
	-(rm *.tar)
	-(rm -rf ($RELEASE))

dist/$(SDIST_TAR_FILE):
	BUILD="$(BUILD)" $(PYTHON) setup.py sdist

sdist: minjs dist/$(SDIST_TAR_FILE)

rpm-build/$(SDIST_TAR_FILE): dist/$(SDIST_TAR_FILE)
	mkdir -p rpm-build
	cp packaging/rpm/$(NAME).spec rpm-build/
	cp packaging/rpm/$(NAME).te rpm-build/
	cp packaging/remove_tower_source.py rpm-build/
	if [ "$(OFFICIAL)" != "yes" ] ; then \
	  (cd dist/ && tar zxf $(SDIST_TAR_FILE)) ; \
	  (cd dist/ && mv $(NAME)-$(VERSION)-$(BUILD) $(NAME)-$(VERSION)) ; \
	  (cd dist/ && tar czf ../rpm-build/$(SDIST_TAR_FILE) $(NAME)-$(VERSION)) ; \
	  ln -sf $(SDIST_TAR_FILE) rpm-build/$(NAME)-$(VERSION).tar.gz ; \
	else \
	  ln -sf ../dist/$(SDIST_TAR_FILE) rpm-build/ ; \
	fi

rpmtar: sdist rpm-build/$(SDIST_TAR_FILE)

rpm-build/$(RPM_NVR).src.rpm: /etc/mock/$(MOCK_CFG).cfg
	$(MOCK_BIN) -r $(MOCK_CFG) --resultdir rpm-build --buildsrpm --spec rpm-build/$(NAME).spec --sources rpm-build \
	   --define "tower_version $(VERSION)" --define "tower_release $(RPM_RELEASE)"
	@echo "#############################################"
	@echo "SRPM artifacts:"
	@echo rpm-build/$(RPM_NVR).src.rpm
	@echo "#############################################"

mock-srpm: rpmtar rpm-build/$(RPM_NVR).src.rpm

rpm-build/$(RPM_NVR).noarch.rpm: rpm-build/$(RPM_NVR).src.rpm
	$(MOCK_BIN) -r $(MOCK_CFG) --resultdir rpm-build --rebuild rpm-build/$(RPM_NVR).src.rpm \
	   --define "tower_version $(VERSION)" --define "tower_release $(RPM_RELEASE)"
	@echo "#############################################"
	@echo "RPM artifacts:"
	@echo rpm-build/$(RPM_NVR).noarch.rpm
	@echo "#############################################"

mock-rpm: rpmtar rpm-build/$(RPM_NVR).noarch.rpm

deb-build/$(SDIST_TAR_NAME):
	mkdir -p deb-build
	tar -C deb-build/ -xvf dist/$(SDIST_TAR_FILE)
	cp -a packaging/debian deb-build/$(SDIST_TAR_NAME)/
	cp packaging/remove_tower_source.py deb-build/$(SDIST_TAR_NAME)/debian/
	sed -ie "s#^$(NAME) (\([^)]*\)) \([^;]*\);#$(NAME) ($(VERSION)-$(DEB_RELEASE)) $(DEB_DIST);#" deb-build/$(SDIST_TAR_NAME)/debian/changelog

debian: sdist deb-build/$(SDIST_TAR_NAME)

deb-build/$(NAME)_$(VERSION)-$(DEB_RELEASE)_all.deb:
	cd deb-build/$(SDIST_TAR_NAME) && $(DEBUILD) -b
	@echo "#############################################"
	@echo "DEB artifacts:"
	@echo deb-build/$(NAME)_$(VERSION)-$(DEB_RELEASE)_all.deb
	@echo "#############################################"

deb: debian deb-build/$(NAME)_$(VERSION)-$(DEB_RELEASE)_all.deb

deb-build/$(NAME)_$(VERSION)-$(DEB_RELEASE)_source.changes:
	cd deb-build/$(SDIST_TAR_NAME) && $(DEBUILD) -S
	@echo "#############################################"
	@echo "DEB artifacts:"
	@echo deb-build/$(NAME)_$(VERSION)-$(DEB_RELEASE)_source.changes
	@echo "#############################################"

deb-src: debian deb-build/$(NAME)_$(VERSION)-$(DEB_RELEASE)_source.changes

deb-upload: deb
	$(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$(NAME)_$(VERSION)-$(DEB_RELEASE)_amd64.changes ; \

deb-src-upload: deb-src
	$(DPUT_BIN) $(DPUT_OPTS) $(DEB_PPA) deb-build/$(NAME)_$(VERSION)-$(DEB_RELEASE)_source.changes ; \

reprepro: deb
	mkdir -p reprepro/conf
	cp -a packaging/reprepro/* reprepro/conf/
	@DEB=deb-build/$(NAME)_$(VERSION)-$(DEB_RELEASE)_all.deb ; \
	for DIST in trusty precise ; do \
	    echo "Removing '$(NAME)' from the $${DIST} apt repo" ; \
	    echo reprepro --export=force -b reprepro remove $${DIST} $(NAME) ; \
	done; \
	reprepro --export=force -b reprepro clearvanished; \
	for DIST in trusty precise ; do \
	    echo "Adding $${DEB} to the $${DIST} apt repo"; \
	    reprepro --keepunreferencedfiles --export=force -b reprepro --ignore=brokenold includedeb $${DIST} $${DEB} ; \
	done; \

ami:
	(cd packaging/ami && $(PACKER) build $(PACKER_BUILD_OPTS) -var "aws_instance_count=$(AWS_INSTANCE_COUNT)" -var "product_version=$(VERSION)" -var "official=$(OFFICIAL)" $(NAME).json)

install:
	$(PYTHON) setup.py install egg_info -b ""
