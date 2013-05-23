clean:
	rm -rf build dist *.egg-info
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

refresh: clean
	# update/refresh development environment after pulling new code
	python setup.py develop
	python manage.py syncdb
	python manage.py migrate

adduser:
	python manage.py createsuperuser

syncdb:
	# only run from initial setup
	python manage.py syncdb

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
        # run this to apply changes to the model
	python manage.py migrate

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
