PYTHON=python
SITELIB=$(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
OFFICIAL ?= no
PACKER ?= packer
GRUNT ?= $(shell [ -t 0 ] && echo "grunt" || echo "grunt --no-color")

# Get the branch information from git
GIT_DATE := $(shell git log -n 1 --format="%ai")
DATE := $(shell date -u +%Y%m%d%H%M)

NAME=ansible-tower
VERSION=$(shell $(PYTHON) -c "from awx import __version__; print(__version__.split('-')[0])")
RELEASE=$(shell $(PYTHON) -c "from awx import __version__; print(__version__.split('-')[1])")
GIT_REMOTE_URL=$(shell git config --get remote.origin.url)

# Allow AMI license customization
AWS_INSTANCE_COUNT ?= 10

ifneq ($(OFFICIAL),yes)
BUILD=0.dev$(DATE)
SDIST_TAR_FILE=$(NAME)-$(VERSION)-$(BUILD).tar.gz
SETUP_TAR_NAME=$(NAME)-setup-$(VERSION)-$(BUILD)
RPM_PKG_RELEASE=$(BUILD)
DEB_BUILD_DIR=deb-build/$(NAME)-$(VERSION)-$(BUILD)
DEB_PKG_RELEASE=$(VERSION)-$(BUILD)
PACKER_BUILD_OPTS=-var-file=vars-aws-keys.json -var-file=vars-nightly.json
else
BUILD=
SDIST_TAR_FILE=$(NAME)-$(VERSION).tar.gz
SETUP_TAR_NAME=$(NAME)-setup-$(VERSION)
RPM_PKG_RELEASE=$(RELEASE)
DEB_BUILD_DIR=deb-build/$(NAME)-$(VERSION)
DEB_PKG_RELEASE=$(VERSION)-$(RELEASE)
PACKER_BUILD_OPTS=-var-file=vars-aws-keys.json -var-file=vars-release.json
endif

MOCK_BIN ?= mock
MOCK_CFG ?=

.PHONY: clean rebase push requirements requirements_pypi requirements_jenkins \
	develop refresh adduser syncdb migrate dbchange dbshell runserver celeryd \
	receiver test test_coverage coverage_html test_ui test_jenkins dev_build \
	release_build release_clean sdist rpm

# Remove temporary build files, compiled Python files.
clean:
	rm -rf dist/*
	rm -rf build rpm-build *.egg-info
	rm -rf debian deb-build
	rm -f awx/ui/static/{js,css}/awx*.{js,css}
	rm -rf awx/ui/static/docs
	rm -rf node_modules package.json Gruntfile.js bower.json
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
	    (cd requirements && pip install -r jenkins.txt); \
	    (cd requirements && pip install -U pyflakes pep8 pylint); \
	    (cd requirements && pip install -U pycrypto); \
	    $(PYTHON) fix_virtualenv_setuptools.py; \
	else \
	    (cd requirements && sudo pip install -r jenkins.txt); \
	    (cd requirements && sudo pip install -U pyflakes pep8 pylint); \
	    (cd requirements && sudo pip install -U pycrypto); \
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
setup_tarball:
	@cp -a setup $(SETUP_TAR_NAME)
	@tar czf $(SETUP_TAR_NAME).tar.gz $(SETUP_TAR_NAME)/
	@rm -rf $(SETUP_TAR_NAME)

release_clean:
	-(rm *.tar)
	-(rm -rf ($RELEASE))

# Traditional 'sdist'
sdist: clean minjs
	if [ "$(OFFICIAL)" = "yes" ] ; then \
	   $(PYTHON) setup.py release_rpm; \
	else \
	   BUILD=$(BUILD) $(PYTHON) setup.py dev_rpm; \
	fi

# Differs from 'sdist' because it includes 'byte-compiled' files in the tarball
sdist_deb: clean minjs
	if [ "$(OFFICIAL)" = "yes" ] ; then \
	   $(PYTHON) setup.py release_deb ; \
	else \
	   BUILD=$(BUILD) $(PYTHON) setup.py dev_deb; \
	fi

rpmtar: sdist
	mkdir -p rpm-build
	cp packaging/rpm/$(NAME).te rpm-build/
	sed -e 's#^Version:.*#Version: $(VERSION)#' -e 's#^Release:.*#Release: $(RPM_PKG_RELEASE)%{?dist}#' packaging/rpm/$(NAME).spec >rpm-build/$(NAME).spec
	if [ "$(OFFICIAL)" != "yes" ] ; then \
	   (cd dist/ && tar zxf $(SDIST_TAR_FILE)) ; \
	   (cd dist/ && mv $(NAME)-$(VERSION)-$(BUILD) $(NAME)-$(VERSION)) ; \
	   (cd dist/ && tar czf $(NAME)-$(VERSION).tar.gz $(NAME)-$(VERSION)) ; \
	fi
	cp dist/$(NAME)-$(VERSION).tar.gz rpm-build/

mock-srpm: /etc/mock/$(MOCK_CFG).cfg rpmtar
	$(MOCK_BIN) -r $(MOCK_CFG) --resultdir rpm-build --buildsrpm --spec rpm-build/$(NAME).spec --sources rpm-build

mock-rpm: /etc/mock/$(MOCK_CFG).cfg mock-srpm
	$(MOCK_BIN) -r $(MOCK_CFG) --resultdir rpm-build --rebuild rpm-build/$(NAME)-*.src.rpm

srpm: rpmtar
	@rpmbuild \
        --define "_pkgrelease $(RPM_PKG_RELEASE)" \
        --define "_topdir %(pwd)/rpm-build" \
        --define "_builddir %{_topdir}" \
        --define "_rpmdir %{_topdir}" \
        --define "_srcrpmdir %{_topdir}" \
        --define "_specdir %{_topdir}" \
        --define "_sourcedir  %{_topdir}" \
        --define '_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
        -bs rpm-build/$(NAME).spec

rpm: rpmtar
	@rpmbuild \
        --define "_pkgrelease $(RPM_PKG_RELEASE)" \
        --define "_topdir %(pwd)/rpm-build" \
        --define "_builddir %{_topdir}" \
        --define "_rpmdir %{_topdir}" \
        --define "_srcrpmdir %{_topdir}" \
        --define "_specdir %{_topdir}" \
        --define "_sourcedir  %{_topdir}" \
        --define '_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
        -ba rpm-build/$(NAME).spec

deb: sdist_deb
	@mkdir -p deb-build
	@cp dist/$(SDIST_TAR_FILE) deb-build/
	(cd deb-build && tar zxf $(SDIST_TAR_FILE))
	(cd $(DEB_BUILD_DIR) && dh_make --indep --yes -f ../$(SDIST_TAR_FILE) -p $(NAME)-$(VERSION))
	@rm -rf $(DEB_BUILD_DIR)/debian
	@cp -a packaging/debian $(DEB_BUILD_DIR)/
	@echo "$(NAME)-$(DEB_PKG_RELEASE).deb admin optional" > $(DEB_BUILD_DIR)/debian/realfiles
	(cd $(DEB_BUILD_DIR) && PKG_RELEASE=$(DEB_PKG_RELEASE) dpkg-buildpackage -nc -us -uc -b --changes-option="-fdebian/realfiles")

ami:
	(cd packaging/ami && $(PACKER) build $(PACKER_BUILD_OPTS) -var "aws_instance_count=$(AWS_INSTANCE_COUNT)" -var "product_version=$(VERSION)" -var "official=$(OFFICIAL)" $(NAME).json)

install:
	$(PYTHON) setup.py install egg_info -b ""
