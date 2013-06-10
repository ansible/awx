RELEASE = ansibleworks-1.2b2

clean:
	rm -rf build *.egg-info
	find . -type f -regex ".*\.py[co]$$" -delete

rebase:
	git pull --rebase origin master

push:
	git push

zero:
	# go back to original database state, be careful!
	python manage.py migrate main zero 

setup:
	# use ansible to ansible ansible commander locally
	ansible-playbook app_setup/setup.yml --verbose -i "127.0.0.1," -c local -e working_dir=`pwd`

develop:
	# "Install" ansibleworks package in development mode.  Creates link to
	# working copy in site-packages, 
	python setup.py develop

refresh: clean develop syncdb migrate
	# update/refresh development environment after pulling new code

adduser:
	python manage.py createsuperuser

syncdb:
	# only run from initial setup
	python manage.py syncdb --noinput

runserver:
	# run for testing the server
	python manage.py runserver

celeryd:
	# run to start the background celery worker
	python manage.py celeryd -l DEBUG -B --autoreload

# already done and should not have to happen again:
#
#south_init:
#	python manage.py schemamigration main --initial

dbchange:
	# run this each time we make changes to the model
	python manage.py schemamigration main changes --auto

migrate: syncdb
	# This command fixes migrations following the cleanup for the 1.2b1 release.
	-(python manage.py migrate main 2>&1 | grep 0017_changes) && (python manage.py migrate main --delete-ghost-migrations --fake 0001_v12b1_initial || python manage.py migrate main --fake)
        # run this to apply changes to the model
	python manage.py migrate --noinput

dbshell:
	# access database shell
	# asks for password # PYTHON_PATH=./acom python acom/manage.py dbshell
	sudo -u postgres psql -d acom

test:
	python manage.py test main

test_coverage:
	# Run tests with coverage enabled.
	coverage run manage.py test main

coverage_html:
	# Output test coverage as HTML (into htmlcov directory).
	coverage html

dev_build:
	python setup.py dev_build

release_build:
	python setup.py release_build

release_ball: clean 
	make release_build
	(cd ../ansible-doc; make)
	-(rm -rf $(RELEASE))
	mkdir -p $(RELEASE)/dist
	cp -a dist/* $(release)/dist
	mkdir -p $(RELEASE)/setup
	cp -a setup/* $(RELEASE)/setup
	mkdir -p $(RELEASE)/docs
	cp -a ../ansible-doc/*.pdf $(RELEASE)/docs
	tar -cvf $(RELEASE)-all.tar $(RELEASE)

release_clean:
	-(rm *.tar)
	-(rm -rf ($RELEASE))
