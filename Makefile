PYTHON=python
SITELIB=$(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
PACKER ?= packer

# Get the branch information from git
GIT_DATE := $(shell git log -n 1 --format="%ai")
DATE := $(shell date -u +%Y%m%d%H%M)

VERSION=$(shell $(PYTHON) -c "from awx import __version__; print(__version__.split('-')[0])")
RELEASE=$(shell $(PYTHON) -c "from awx import __version__; print(__version__.split('-')[1])")

# Allow ami license customization
LICENSE_TIER ?= 30
PACKER_LICENSE_FILE ?= test.json

ifneq ($(OFFICIAL),yes)
BUILD=dev$(DATE)
SDIST_TAR_FILE=awx-$(VERSION)-$(BUILD).tar.gz
SETUP_TAR_NAME=awx-setup-$(VERSION)-$(BUILD)
RPM_PKG_RELEASE=$(BUILD)
DEB_BUILD_DIR=deb-build/awx-$(VERSION)-$(BUILD)
DEB_PKG_RELEASE=$(VERSION)-$(BUILD)
PACKER_BUILD_OPTS=-var-file=vars-awxkeys.json -var-file=vars-nightly.json
else
BUILD=
SDIST_TAR_FILE=awx-$(VERSION).tar.gz
SETUP_TAR_NAME=awx-setup-$(VERSION)
RPM_PKG_RELEASE=$(RELEASE)
DEB_BUILD_DIR=deb-build/awx-$(VERSION)
DEB_PKG_RELEASE=$(VERSION)-$(RELEASE)
PACKER_BUILD_OPTS=-var-file=vars-awxkeys.json -var-file=vars-release.json
endif

.PHONY: clean rebase push requirements requirements_pypi develop refresh \
	adduser syncdb migrate dbchange dbshell runserver celeryd test \
	test_coverage coverage_html test_ui test_jenkins dev_build \
	release_build release_clean sdist rpm

# Remove temporary build files, compiled Python files.
clean:
	rm -rf dist/*
	rm -rf build rpm-build *.egg-info
	rm -rf debian deb-build
	rm -f awx/ui/static/js/awx-min.js
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
	    (cd requirements && pip install --no-index -r dev_local.txt); \
	    $(PYTHON) fix_virtualenv_setuptools.py; \
	else \
	    (cd requirements && sudo pip install --no-index -r dev_local.txt); \
	fi

# Install third-party requirements needed for development environment
# (downloading from PyPI if necessary).
requirements_pypi:
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    pip install -r requirements/dev.txt; \
	    $(PYTHON) fix_virtualenv_setuptools.py; \
	else \
	    sudo pip install -r requirements/dev.txt; \
	fi

# "Install" awx package in development mode.  Creates link to working
# copy in site-packages and installs awx-manage command.
develop:
	@if [ "$(VIRTUAL_ENV)" ]; then \
	    $(PYTHON) setup.py develop; \
	else \
	    sudo $(PYTHON) setup.py develop; \
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

# Run the built-in development webserver (by default on http://localhost:8013).
runserver:
	$(PYTHON) manage.py runserver

# Run to start the background celery worker for development.
celeryd:
	$(PYTHON) manage.py celeryd -l DEBUG -B -Ofair

# Run all API unit tests.
test:
	$(PYTHON) manage.py test -v2 main

# Run all API unit tests with coverage enabled.
test_coverage:
	coverage run manage.py test -v2 main

# Output test coverage as HTML (into htmlcov directory).
coverage_html:
	coverage html

# Run UI unit tests using Selenium.
test_ui:
	$(PYTHON) manage.py test -v2 ui

# Run API unit tests across multiple Python/Django versions with Tox.
test_tox:
	tox -v

# Run unit tests to produce output for Jenkins.
test_jenkins:
	$(PYTHON) manage.py jenkins -v2

# Build minified JS/CSS.
minjs:
	(cd tools/ui/ && ./compile.sh)

# Build a pip-installable package into dist/ with a timestamped version number.
dev_build: 
	$(PYTHON) setup.py dev_build

# Build a pip-installable package into dist/ with the release version number.
release_build:
	$(PYTHON) setup.py release_build

# Build AWX setup tarball.
setup_tarball:
	@cp -a setup $(SETUP_TAR_NAME)
	@tar czf $(SETUP_TAR_NAME).tar.gz $(SETUP_TAR_NAME)/
	@rm -rf $(SETUP_TAR_NAME)

release_clean:
	-(rm *.tar)
	-(rm -rf ($RELEASE))

sdist: clean minjs
	if [ "$(OFFICIAL)" = "yes" ] ; then \
	   $(PYTHON) setup.py release_build; \
	else \
	   BUILD=$(BUILD) $(PYTHON) setup.py sdist_awx; \
	fi

rpmtar: sdist
	if [ "$(OFFICIAL)" != "yes" ] ; then \
	   (cd dist/ && tar zxf $(SDIST_TAR_FILE)) ; \
	   (cd dist/ && mv awx-$(VERSION)-$(BUILD) awx-$(VERSION)) ; \
	   (cd dist/ && tar czf awx-$(VERSION).tar.gz awx-$(VERSION)) ; \
	fi

rpm: rpmtar
	@mkdir -p rpm-build
	@cp dist/awx-$(VERSION).tar.gz rpm-build/
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir %{_topdir}" \
	--define '_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
	--define "_sourcedir  %{_topdir}" \
	--define "_pkgrelease  $(RPM_PKG_RELEASE)" \
	-ba packaging/rpm/awx.spec

deb: sdist
	@mkdir -p deb-build
	@cp dist/$(SDIST_TAR_FILE) deb-build/
	(cd deb-build && tar zxf $(SDIST_TAR_FILE))
	(cd $(DEB_BUILD_DIR) && dh_make --indep --yes -f ../$(SDIST_TAR_FILE) -p awx-$(VERSION))
	@rm -rf $(DEB_BUILD_DIR)/debian
	@cp -a packaging/debian $(DEB_BUILD_DIR)/
	@echo "awx_$(DEB_PKG_RELEASE).deb admin optional" > $(DEB_BUILD_DIR)/debian/realfiles
	(cd $(DEB_BUILD_DIR) && PKG_RELEASE=$(DEB_PKG_RELEASE) dpkg-buildpackage -nc -us -uc -b --changes-option="-fdebian/realfiles")

packer_license:
	@python -c "import json; fp = open('packaging/ami/license/$(PACKER_LICENSE)', 'w+'); json.dump(dict(instance_count=$(LICENSE_TIER)), fp); fp.close();"

ami: packer_license
	(cd packaging/ami && $(PACKER) build $(PACKER_BUILD_OPTS) -var "aws_license=$(PACKER_LICENSE_FILE)" awx.json)

install:
	$(PYTHON) setup.py install egg_info -b ""
